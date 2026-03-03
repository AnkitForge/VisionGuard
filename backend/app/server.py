import datetime as dt
import json
import os
import smtplib
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
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

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
        self.prev_gray = None
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def start(self) -> bool:
        if self.running:
            return True
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

            detection = self._detect_suspicious(frame)
            frame_to_show = frame.copy()
            if detection:
                x, y, w, h = detection.get("box", (0, 0, 0, 0))
                if w > 0 and h > 0:
                    cv2.rectangle(frame_to_show, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(
                        frame_to_show,
                        f"{detection['activity_type']} {detection['confidence']:.2f}",
                        (x, max(30, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                self._handle_detection(frame, detection)

            with self.lock:
                self.latest_frame = frame_to_show
                self.alert_buffer.append(frame.copy())

    def _detect_suspicious(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
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
            "confidence": round(confidence, 2),
            "activity_type": activity_type,
            "severity": severity,
            "box": box,
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
    }

    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": cors_origins if cors_origins != ["*"] else "*"}})

    store = create_store(cfg)
    camera = CameraManager(store, Path(cfg["ALERTS_DIR"]), cfg)

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
            except Exception:
                return jsonify({"error": "Invalid token"}), 401
            request.user = user
            return fn(*args, **kwargs)

        wrapper.__name__ = fn.__name__
        return wrapper

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

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
            }
        )

    @app.get("/api/video-feed")
    @auth_required
    def video_feed():
        return Response(camera.generate_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5001"))
    app.run(host=host, port=port, debug=os.getenv("FLASK_ENV") == "development", threaded=True)
