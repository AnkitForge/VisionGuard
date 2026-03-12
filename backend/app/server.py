import datetime as dt
import json
import os
import smtplib
import tempfile
import threading
import time
import uuid
from collections import Counter, defaultdict, deque
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import jwt
import numpy as np
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from app.theft_model import TheftDetectionModel

try:
    from pymongo import MongoClient
except Exception:  # pragma: no cover
    MongoClient = None


class LocalStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self._write({"users": [], "alerts": []})

    def _read(self) -> Dict[str, Any]:
        with self.lock:
            return json.loads(self.db_path.read_text())

    def _write(self, payload: Dict[str, Any]) -> None:
        with self.lock:
            self.db_path.write_text(json.dumps(payload, indent=2))

    def create_user(self, email: str, password_hash: str) -> Dict[str, Any]:
        data = self._read()
        if any(user["email"] == email for user in data["users"]):
            raise ValueError("Email already registered")
        user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": password_hash,
            "created_at": dt.datetime.utcnow().isoformat(),
        }
        data["users"].append(user)
        self._write(data)
        return user

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        data = self._read()
        return next((u for u in data["users"] if u["email"] == email), None)

    def create_alert(self, alert: Dict[str, Any]) -> None:
        data = self._read()
        data["alerts"].append(alert)
        self._write(data)

    def get_alerts(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._read()
        alerts = data["alerts"]
        if since:
            alerts = [a for a in alerts if a["timestamp"] > since]
        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)


class MongoStore:
    def __init__(self, mongo_uri: str, db_name: str):
        if MongoClient is None:
            raise RuntimeError("pymongo is not installed")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.users = self.db.users
        self.alerts = self.db.alerts
        self.users.create_index("email", unique=True)
        self.alerts.create_index("timestamp")

    def create_user(self, email: str, password_hash: str) -> Dict[str, Any]:
        user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": password_hash,
            "created_at": dt.datetime.utcnow().isoformat(),
        }
        self.users.insert_one(user)
        return user

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.users.find_one({"email": email}, {"_id": 0})

    def create_alert(self, alert: Dict[str, Any]) -> None:
        self.alerts.insert_one(alert)

    def get_alerts(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"timestamp": {"$gt": since}} if since else {}
        cursor = self.alerts.find(query, {"_id": 0}).sort("timestamp", -1)
        return list(cursor)


class CameraManager:
    def __init__(self, store, clip_dir: Path, config: Dict[str, Any]):
        self.store = store
        self.clip_dir = clip_dir
        self.config = config
        clip_frames = int(self.config.get("THEFT_MODEL_CLIP_FRAMES", 64))
        self.clip_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.capture = None
        self.thread = None
        self.lock = threading.Lock()
        self.latest_frame = None
        self.fps = 0.0
        self.last_alert_at = 0.0
        self.model_running = False
        self.camera_connected = False
        self.alert_buffer = deque(maxlen=180)  # ~12 sec at ~15fps
        self.clip_buffer = deque(maxlen=max(clip_frames + 32, clip_frames))
        self.prev_gray = None
        self.frame_counter = 0
        self.last_inference_frame = 0
        self.latest_prediction = None
        self.latest_prediction_at = 0.0
        self.model_detector = None
        self.detector_error = None
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def start(self) -> bool:
        if self.running:
            return True
        self._ensure_model_detector()
        source = self.config.get("CAMERA_SOURCE", "0")
        source = int(source) if str(source).isdigit() else source
        self.capture = cv2.VideoCapture(source)
        self.camera_connected = self.capture.isOpened()
        if not self.camera_connected:
            return False

        self.running = True
        self.model_running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self) -> None:
        self.running = False
        self.model_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        if self.capture is not None:
            self.capture.release()
        self.capture = None
        self.camera_connected = False
        self.clip_buffer.clear()
        self.latest_prediction = None
        self.latest_prediction_at = 0.0

    def _ensure_model_detector(self) -> None:
        if self.model_detector is not None:
            return

        weights_path = (self.config.get("THEFT_MODEL_WEIGHTS") or "").strip()
        if not weights_path:
            self.detector_error = "No theft model weights configured"
            return

        try:
            detector = TheftDetectionModel(
                weights_path=weights_path,
                threshold=float(self.config.get("THEFT_MODEL_THRESHOLD", 0.6)),
                clip_frames=int(self.config.get("THEFT_MODEL_CLIP_FRAMES", 64)),
            )
            detector.ensure_loaded()
            self.model_detector = detector
            self.detector_error = None
        except Exception as exc:
            self.model_detector = None
            self.detector_error = str(exc)

    def _loop(self) -> None:
        last = time.time()
        while self.running and self.capture is not None:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.1)
                continue

            now = time.time()
            delta = max(now - last, 1e-6)
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / delta) if self.fps else (1.0 / delta)
            last = now

            with self.lock:
                self.alert_buffer.append(frame.copy())
                self.clip_buffer.append(frame.copy())

            detection = self._detect_suspicious(frame)
            frame_to_show = frame.copy()
            if detection:
                self._annotate_detection(frame_to_show, detection)
                if detection.get("detected", True):
                    self._handle_detection(frame, detection)
            elif self.latest_prediction and now - self.latest_prediction_at <= 2.0:
                self._annotate_detection(frame_to_show, self.latest_prediction)

            with self.lock:
                self.latest_frame = frame_to_show

    def _annotate_detection(self, frame: np.ndarray, detection: Dict[str, Any]) -> None:
        x, y, w, h = detection.get("box", (0, 0, 0, 0))
        if w > 0 and h > 0:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        detected = bool(detection.get("detected", True))
        color = (0, 0, 255) if detected else (0, 160, 0)
        lines = [
            detection.get("activity_type", "Analyzing"),
            f"Confidence: {float(detection.get('confidence', 0.0)):.2f}",
        ]
        if "bag" in detection and "clothes" in detection and "normal" in detection:
            lines.extend(
                [
                    f"Bag: {float(detection['bag']):.2f}",
                    f"Clothes: {float(detection['clothes']):.2f}",
                    f"Normal: {float(detection['normal']):.2f}",
                ]
            )

        height = 30 + len(lines) * 26
        cv2.rectangle(frame, (12, 12), (360, height), (255, 255, 255), -1)
        for index, line in enumerate(lines):
            cv2.putText(frame, line, (24, 40 + index * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

    def _detect_suspicious(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        self.frame_counter += 1
        if self.model_detector is not None:
            return self._detect_suspicious_with_model()
        return self._detect_suspicious_heuristic(frame)

    def _detect_suspicious_with_model(self) -> Optional[Dict[str, Any]]:
        clip_frames = int(self.config.get("THEFT_MODEL_CLIP_FRAMES", 64))
        if len(self.clip_buffer) < clip_frames:
            return None

        inference_interval = max(int(self.config.get("THEFT_MODEL_INFERENCE_INTERVAL", 16)), 1)
        if self.frame_counter - self.last_inference_frame < inference_interval:
            return None

        try:
            self.last_inference_frame = self.frame_counter
            prediction = self.model_detector.predict_frames(list(self.clip_buffer))
            self.latest_prediction = prediction
            self.latest_prediction_at = time.time()
            return prediction
        except Exception as exc:
            self.model_detector = None
            self.detector_error = str(exc)
            return None

    def _detect_suspicious_heuristic(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion_score = 0.0

        if self.prev_gray is not None:
            diff = cv2.absdiff(self.prev_gray, gray)
            _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)
            motion_score = float(np.count_nonzero(thresh)) / thresh.size
        self.prev_gray = gray

        boxes, _ = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(16, 16), scale=1.05)
        people_count = len(boxes)

        if people_count == 0 and motion_score < 0.15:
            return None

        confidence = min(0.99, 0.35 + motion_score * 2.0 + min(people_count, 3) * 0.1)
        if confidence < 0.7:
            return None

        activity_type = "Shoplifting" if confidence >= 0.86 else "Suspicious Behavior"
        severity = "high" if confidence >= 0.86 else "medium"
        box = tuple(map(int, boxes[0])) if people_count else (0, 0, 0, 0)

        return {
            "detected": True,
            "confidence": round(confidence, 2),
            "activity_type": activity_type,
            "severity": severity,
            "box": box,
            "source": "heuristic",
        }

    def _handle_detection(self, frame: np.ndarray, detection: Dict[str, Any]) -> None:
        now = time.time()
        if now - self.last_alert_at < 10:
            return
        self.last_alert_at = now

        alert_id = str(uuid.uuid4())
        clip_name = f"{alert_id}.mp4"
        clip_path = self.clip_dir / clip_name
        self._save_clip(clip_path)

        alert = {
            "id": alert_id,
            "timestamp": dt.datetime.utcnow().isoformat(),
            "confidence": detection["confidence"],
            "activity_type": detection["activity_type"],
            "severity": detection["severity"],
            "clip": clip_name,
        }
        self.store.create_alert(alert)

        if alert["severity"] == "high":
            self._send_email(alert)

    def _save_clip(self, clip_path: Path) -> None:
        with self.lock:
            frames = list(self.alert_buffer)

        if not frames:
            return

        h, w, _ = frames[0].shape
        writer = cv2.VideoWriter(str(clip_path), cv2.VideoWriter_fourcc(*"mp4v"), 15, (w, h))
        try:
            for frame in frames:
                writer.write(frame)
        finally:
            writer.release()

    def _send_email(self, alert: Dict[str, Any]) -> None:
        host = self.config.get("SMTP_HOST")
        to_addr = self.config.get("ALERT_EMAIL_TO")
        if not host or not to_addr:
            return

        msg = EmailMessage()
        msg["Subject"] = "VisionGuard High-Risk Alert"
        msg["From"] = self.config.get("SMTP_USER", "visionguard@localhost")
        msg["To"] = to_addr
        msg.set_content(
            f"High-risk activity detected\n"
            f"Time: {alert['timestamp']}\n"
            f"Type: {alert['activity_type']}\n"
            f"Confidence: {alert['confidence']}\n"
        )

        port = int(self.config.get("SMTP_PORT", 587))
        user = self.config.get("SMTP_USER")
        password = self.config.get("SMTP_PASS")

        try:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        except Exception:
            # Best-effort notification; avoid crashing detection loop.
            pass

    def generate_stream(self):
        while True:
            if not self.running:
                time.sleep(0.2)
                continue
            with self.lock:
                frame = None if self.latest_frame is None else self.latest_frame.copy()
            if frame is None:
                time.sleep(0.05)
                continue

            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            payload = encoded.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
            )


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200 MB


class VideoUploadProcessor:
    """Processes an uploaded video file through the theft detection model,
    streaming annotated frames live via MJPEG and raising alerts."""

    def __init__(self, store, clip_dir: Path, config: Dict[str, Any]):
        self.store = store
        self.clip_dir = clip_dir
        self.config = config
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        # Per-job latest annotated frame for MJPEG live streaming
        self._latest_frames: Dict[str, Optional[np.ndarray]] = {}
        # Per-job latest detection result for dashboard polling
        self._latest_detections: Dict[str, Optional[Dict[str, Any]]] = {}
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def _build_detector(self) -> Optional[TheftDetectionModel]:
        weights_path = (self.config.get("THEFT_MODEL_WEIGHTS") or "").strip()
        if not weights_path:
            return None
        try:
            detector = TheftDetectionModel(
                weights_path=weights_path,
                threshold=float(self.config.get("THEFT_MODEL_THRESHOLD", 0.6)),
                clip_frames=int(self.config.get("THEFT_MODEL_CLIP_FRAMES", 64)),
            )
            detector.ensure_loaded()
            return detector
        except Exception:
            return None

    def create_job(self, video_path: str, original_name: str) -> str:
        job_id = str(uuid.uuid4())
        with self.lock:
            self.jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "progress": 0,
                "total_frames": 0,
                "processed_frames": 0,
                "detections": [],
                "alerts": [],
                "output_video": None,
                "video_path": video_path,
                "original_name": original_name,
                "error": None,
                "detector_type": "pending",
            }
            self._latest_frames[job_id] = None
            self._latest_detections[job_id] = None
        thread = threading.Thread(target=self._process, args=(job_id,), daemon=True)
        thread.start()
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                return None
            return {k: v for k, v in job.items() if k != "video_path"}

    def get_latest_detection(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self._latest_detections.get(job_id)

    def _update_job(self, job_id: str, **kwargs) -> None:
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(kwargs)

    def _set_latest_frame(self, job_id: str, frame: np.ndarray) -> None:
        with self.lock:
            self._latest_frames[job_id] = frame.copy()

    def _set_latest_detection(self, job_id: str, detection: Optional[Dict[str, Any]]) -> None:
        with self.lock:
            self._latest_detections[job_id] = detection

    def _detect_heuristic(self, frame: np.ndarray, prev_gray) -> tuple:
        """Fallback heuristic detection using motion + HOG people detection."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion_score = 0.0

        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)
            motion_score = float(np.count_nonzero(thresh)) / thresh.size

        boxes, _ = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(16, 16), scale=1.05)
        people_count = len(boxes)

        result = None
        if people_count > 0 or motion_score >= 0.15:
            confidence = min(0.99, 0.35 + motion_score * 2.0 + min(people_count, 3) * 0.1)
            if confidence >= 0.7:
                activity_type = "Shoplifting" if confidence >= 0.86 else "Suspicious Behavior"
                severity = "high" if confidence >= 0.86 else "medium"
                box = tuple(map(int, boxes[0])) if people_count else (0, 0, 0, 0)
                result = {
                    "detected": True,
                    "confidence": round(confidence, 2),
                    "activity_type": activity_type,
                    "severity": severity,
                    "box": box,
                    "source": "heuristic",
                }

        return result, gray

    def _process(self, job_id: str) -> None:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            video_path = job["video_path"]

        self._update_job(job_id, status="processing")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self._update_job(job_id, status="error", error="Could not open video file")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._update_job(job_id, total_frames=total_frames)

        detector = self._build_detector()
        using_model = detector is not None
        detector_type = "ml-model" if using_model else "heuristic"
        self._update_job(job_id, detector_type=detector_type)

        clip_frames_needed = int(self.config.get("THEFT_MODEL_CLIP_FRAMES", 64))
        clip_buffer: deque = deque(maxlen=clip_frames_needed)

        output_name = f"upload_{job_id}.mp4"
        output_path = self.clip_dir / output_name
        writer = cv2.VideoWriter(
            str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

        frame_idx = 0
        inference_interval = max(int(self.config.get("THEFT_MODEL_INFERENCE_INTERVAL", 16)), 1)
        last_inference_frame = 0
        latest_prediction = None
        prev_gray = None
        detections = []
        alerts_created = []
        last_alert_time = 0.0
        frame_delay = 1.0 / fps  # Pace to approximate real-time playback

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frame_start = time.time()
                frame_idx += 1
                clip_buffer.append(frame.copy())
                annotated = frame.copy()

                prediction = None

                # --- ML model detection ---
                if using_model and len(clip_buffer) >= clip_frames_needed:
                    if frame_idx - last_inference_frame >= inference_interval:
                        last_inference_frame = frame_idx
                        try:
                            prediction = detector.predict_frames(list(clip_buffer))
                            latest_prediction = prediction
                        except Exception:
                            pass

                # --- Heuristic fallback detection ---
                if not using_model:
                    heuristic_result, prev_gray = self._detect_heuristic(frame, prev_gray)
                    if heuristic_result:
                        prediction = heuristic_result
                        latest_prediction = prediction

                # Handle detection → alert
                if prediction and prediction.get("detected"):
                    detections.append({
                        "frame": frame_idx,
                        "time_sec": round(frame_idx / fps, 2),
                        **prediction,
                    })

                    now = time.time()
                    if now - last_alert_time >= 10:
                        last_alert_time = now
                        alert_id = str(uuid.uuid4())
                        alert = {
                            "id": alert_id,
                            "timestamp": dt.datetime.utcnow().isoformat(),
                            "confidence": prediction["confidence"],
                            "activity_type": prediction["activity_type"],
                            "severity": prediction["severity"],
                            "clip": output_name,
                            "source": "video-upload",
                        }
                        self.store.create_alert(alert)
                        alerts_created.append(alert)

                # Annotate frame
                display_pred = prediction if prediction else latest_prediction
                if display_pred:
                    self._annotate_frame(annotated, display_pred)

                writer.write(annotated)

                # Update live frame for MJPEG streaming
                self._set_latest_frame(job_id, annotated)
                self._set_latest_detection(job_id, display_pred)

                progress = int((frame_idx / max(total_frames, 1)) * 100)
                self._update_job(
                    job_id,
                    processed_frames=frame_idx,
                    progress=min(progress, 99),
                    detections=list(detections),
                    alerts=list(alerts_created),
                )

                # Pace processing for live feel
                elapsed = time.time() - frame_start
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as exc:
            self._update_job(job_id, status="error", error=str(exc))
            return
        finally:
            cap.release()
            writer.release()

        self._update_job(
            job_id,
            status="completed",
            progress=100,
            processed_frames=frame_idx,
            output_video=output_name,
            detections=list(detections),
            alerts=list(alerts_created),
        )

        # Clean up uploaded source file
        try:
            os.unlink(video_path)
        except OSError:
            pass

    def generate_stream(self, job_id: str):
        """MJPEG stream of annotated frames for live monitoring."""
        while True:
            with self.lock:
                job = self.jobs.get(job_id)
                frame = self._latest_frames.get(job_id)

            if job is None:
                break
            if job["status"] in ("completed", "error"):
                # Send final frame then stop
                if frame is not None:
                    ok, encoded = cv2.imencode(".jpg", frame)
                    if ok:
                        payload = encoded.tobytes()
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
                        )
                break

            if frame is None:
                time.sleep(0.05)
                continue

            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                time.sleep(0.02)
                continue
            payload = encoded.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
            )
            time.sleep(0.03)  # ~30 fps cap for streaming

    @staticmethod
    def _annotate_frame(frame: np.ndarray, detection: Dict[str, Any]) -> None:
        detected = bool(detection.get("detected", False))
        color = (0, 0, 255) if detected else (0, 160, 0)

        # Draw bounding box if present
        x, y, w, h_box = detection.get("box", (0, 0, 0, 0))
        if w > 0 and h_box > 0:
            cv2.rectangle(frame, (x, y), (x + w, y + h_box), (0, 0, 255), 2)

        lines = [
            detection.get("activity_type", "Analyzing"),
            f"Confidence: {float(detection.get('confidence', 0.0)):.2f}",
        ]
        if "bag" in detection and "clothes" in detection and "normal" in detection:
            lines.extend([
                f"Bag: {float(detection['bag']):.2f}",
                f"Clothes: {float(detection['clothes']):.2f}",
                f"Normal: {float(detection['normal']):.2f}",
            ])
        h = 30 + len(lines) * 26
        cv2.rectangle(frame, (12, 12), (360, h), (255, 255, 255), -1)
        for idx, line in enumerate(lines):
            cv2.putText(frame, line, (24, 40 + idx * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)


def create_store(config: Dict[str, Any]):
    mode = config.get("DATA_MODE", "local").lower()
    if mode == "mongo":
        try:
            return MongoStore(config["MONGO_URI"], config["MONGO_DB"])
        except Exception:
            pass
    return LocalStore(Path("storage/db.json"))


def create_token(secret: str, expire_hours: int, payload: Dict[str, Any]) -> str:
    exp = dt.datetime.utcnow() + dt.timedelta(hours=expire_hours)
    token_data = {**payload, "exp": exp}
    return jwt.encode(token_data, secret, algorithm="HS256")


def decode_token(secret: str, token: str) -> Dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)

    cfg = {
        "JWT_SECRET": os.getenv("JWT_SECRET", "dev-secret"),
        "JWT_EXPIRE_HOURS": int(os.getenv("JWT_EXPIRE_HOURS", "24")),
        "DATA_MODE": os.getenv("DATA_MODE", "local"),
        "MONGO_URI": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "MONGO_DB": os.getenv("MONGO_DB", "visionguard"),
        "ALERTS_DIR": os.getenv("ALERTS_DIR", "storage/clips"),
        "CAMERA_SOURCE": os.getenv("CAMERA_SOURCE", "0"),
        "SMTP_HOST": os.getenv("SMTP_HOST", ""),
        "SMTP_PORT": os.getenv("SMTP_PORT", "587"),
        "SMTP_USER": os.getenv("SMTP_USER", ""),
        "SMTP_PASS": os.getenv("SMTP_PASS", ""),
        "ALERT_EMAIL_TO": os.getenv("ALERT_EMAIL_TO", ""),
        "THEFT_MODEL_WEIGHTS": os.getenv("THEFT_MODEL_WEIGHTS", ""),
        "THEFT_MODEL_THRESHOLD": os.getenv("THEFT_MODEL_THRESHOLD", "0.6"),
        "THEFT_MODEL_CLIP_FRAMES": os.getenv("THEFT_MODEL_CLIP_FRAMES", "64"),
        "THEFT_MODEL_INFERENCE_INTERVAL": os.getenv("THEFT_MODEL_INFERENCE_INTERVAL", "16"),
    }

    CORS(app, resources={r"/api/*": {"origins": "*"}},
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    store = create_store(cfg)
    camera = CameraManager(store, Path(cfg["ALERTS_DIR"]), cfg)
    video_processor = VideoUploadProcessor(store, Path(cfg["ALERTS_DIR"]), cfg)

    upload_dir = Path(cfg["ALERTS_DIR"]) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    def get_bearer_token() -> Optional[str]:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1]
        token = request.args.get("token")
        return token

    def auth_required(fn):
        def wrapper(*args, **kwargs):
            token = get_bearer_token()
            if not token:
                return jsonify({"error": "Missing token"}), 401
            try:
                user = decode_token(cfg["JWT_SECRET"], token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired, please login again"}), 401
            except jwt.InvalidTokenError as e:
                app.logger.warning("JWT invalid: %s | token[:20]=%s", e, token[:20] if token else "")
                return jsonify({"error": "Invalid token"}), 401
            except Exception as e:
                app.logger.error("JWT unexpected error: %s %s", type(e).__name__, e)
                return jsonify({"error": "Invalid token"}), 401
            request.user = user
            return fn(*args, **kwargs)

        wrapper.__name__ = fn.__name__
        return wrapper

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/debug-token")
    def debug_token():
        """Temporary debug endpoint — remove in production."""
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "No token provided", "hint": "Send Authorization: Bearer <token>"}), 400
        info = {"token_length": len(token), "first_20": token[:20], "last_20": token[-20:]}
        try:
            decoded = decode_token(cfg["JWT_SECRET"], token)
            info["decoded"] = decoded
            info["status"] = "valid"
        except jwt.ExpiredSignatureError:
            info["status"] = "expired"
        except jwt.InvalidTokenError as e:
            info["status"] = "invalid"
            info["jwt_error"] = str(e)
        except Exception as e:
            info["status"] = "error"
            info["exception"] = f"{type(e).__name__}: {e}"
        return jsonify(info)

    @app.post("/api/auth/register")
    def register():
        payload = request.get_json(force=True, silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        if not email or not password or len(password) < 6:
            return jsonify({"error": "Email and password (min 6 chars) are required"}), 400
        try:
            user = store.create_user(email, generate_password_hash(password))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 409
        except Exception:
            return jsonify({"error": "Could not create user"}), 500

        token = create_token(cfg["JWT_SECRET"], cfg["JWT_EXPIRE_HOURS"], {"sub": user["id"], "email": email})
        return jsonify({"token": token, "user": {"id": user["id"], "email": email}}), 201

    @app.post("/api/auth/login")
    def login():
        payload = request.get_json(force=True, silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        user = store.find_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid credentials"}), 401
        token = create_token(cfg["JWT_SECRET"], cfg["JWT_EXPIRE_HOURS"], {"sub": user["id"], "email": email})
        return jsonify({"token": token, "user": {"id": user["id"], "email": email}})

    @app.get("/api/alerts")
    @auth_required
    def get_alerts():
        since = request.args.get("since")
        severity = request.args.get("severity")
        date = request.args.get("date")
        alerts = store.get_alerts(since=since)
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        if date:
            alerts = [a for a in alerts if a.get("timestamp", "").startswith(date)]
        return jsonify({"alerts": alerts})

    @app.get("/api/evidence")
    @auth_required
    def get_evidence():
        severity = request.args.get("severity")
        date = request.args.get("date")
        alerts = store.get_alerts()
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        if date:
            alerts = [a for a in alerts if a.get("timestamp", "").startswith(date)]
        evidence = [
            {
                "id": a["id"],
                "timestamp": a["timestamp"],
                "severity": a["severity"],
                "activity_type": a["activity_type"],
                "confidence": a["confidence"],
                "clip": a.get("clip"),
                "download_url": f"/api/evidence/{a.get('clip')}" if a.get("clip") else None,
            }
            for a in alerts
        ]
        return jsonify({"evidence": evidence})

    @app.get("/api/evidence/<path:clip_name>")
    @auth_required
    def download_evidence(clip_name: str):
        as_download = request.args.get("download") == "1"
        return send_from_directory(camera.clip_dir, clip_name, as_attachment=as_download)

    @app.get("/api/analytics")
    @auth_required
    def analytics():
        alerts = store.get_alerts()
        per_day = defaultdict(int)
        distribution = Counter()
        confidences = []

        for alert in alerts:
            day = alert["timestamp"][:10]
            per_day[day] += 1
            distribution[alert["activity_type"]] += 1
            confidences.append(float(alert["confidence"]))

        line_data = [{"date": day, "count": per_day[day]} for day in sorted(per_day)]
        pie_data = [{"name": name, "value": value} for name, value in distribution.items()]
        accuracy = round((sum(confidences) / len(confidences) * 100), 2) if confidences else 0

        return jsonify({
            "alerts_per_day": line_data,
            "threat_distribution": pie_data,
            "detection_accuracy": accuracy,
            "total_alerts": len(alerts),
        })

    @app.post("/api/start-camera")
    @auth_required
    def start_camera():
        started = camera.start()
        if not started:
            return jsonify({"error": "Failed to connect to camera"}), 500
        return jsonify({"status": "running"})

    @app.post("/api/stop-camera")
    @auth_required
    def stop_camera():
        camera.stop()
        return jsonify({"status": "stopped"})

    @app.get("/api/system-status")
    @auth_required
    def system_status():
        alerts = store.get_alerts()
        today = dt.datetime.utcnow().date().isoformat()
        today_count = sum(1 for a in alerts if a.get("timestamp", "").startswith(today))
        return jsonify(
            {
                "camera_connected": camera.camera_connected,
                "model_running": camera.model_running,
                "processing_fps": round(camera.fps, 2),
                "total_alerts_today": today_count,
                "detector_loaded": camera.model_detector is not None,
                "detector_error": camera.detector_error,
                "active_detector": "ml-model" if camera.model_detector is not None else "heuristic",
            }
        )

    @app.get("/api/video-feed")
    @auth_required
    def video_feed():
        return Response(camera.generate_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

    # ── Video Upload Endpoints ──────────────────────────────────────────

    @app.post("/api/upload-video")
    @auth_required
    def upload_video():
        if "video" not in request.files:
            return jsonify({"error": "No video file provided"}), 400

        file = request.files["video"]
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            return jsonify({"error": f"Unsupported format. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"}), 400

        safe_name = secure_filename(file.filename)
        save_path = upload_dir / f"{uuid.uuid4()}_{safe_name}"
        file.save(str(save_path))

        if save_path.stat().st_size > MAX_VIDEO_SIZE:
            save_path.unlink(missing_ok=True)
            return jsonify({"error": "File too large (max 200 MB)"}), 400

        job_id = video_processor.create_job(str(save_path), safe_name)
        return jsonify({"job_id": job_id, "status": "queued"}), 202

    @app.get("/api/upload-video/<job_id>/status")
    @auth_required
    def upload_video_status(job_id: str):
        job = video_processor.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(job)

    @app.get("/api/upload-video/<job_id>/stream")
    @auth_required
    def upload_video_stream(job_id: str):
        """SSE stream that pushes job progress updates."""
        def generate():
            last_progress = -1
            while True:
                job = video_processor.get_job(job_id)
                if not job:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break
                if job["progress"] != last_progress or job["status"] in ("completed", "error"):
                    last_progress = job["progress"]
                    yield f"data: {json.dumps(job)}\n\n"
                if job["status"] in ("completed", "error"):
                    break
                time.sleep(1)

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/upload-video/<job_id>/output")
    @auth_required
    def upload_video_output(job_id: str):
        job = video_processor.get_job(job_id)
        if not job or not job.get("output_video"):
            return jsonify({"error": "Output not available"}), 404
        as_download = request.args.get("download") == "1"
        return send_from_directory(camera.clip_dir, job["output_video"], as_attachment=as_download)

    @app.get("/api/upload-video/<job_id>/feed")
    @auth_required
    def upload_video_feed(job_id: str):
        """Live MJPEG stream of annotated frames from the upload job."""
        job = video_processor.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return Response(
            video_processor.generate_stream(job_id),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.get("/api/upload-video/<job_id>/detection")
    @auth_required
    def upload_video_detection(job_id: str):
        """Latest detection result from the upload job for dashboard polling."""
        job = video_processor.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        detection = video_processor.get_latest_detection(job_id)
        return jsonify({
            "job": job,
            "latest_detection": detection,
        })

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5001"))
    app.run(host=host, port=port, debug=os.getenv("FLASK_ENV") == "development", threaded=True)
