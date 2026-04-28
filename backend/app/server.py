"""
server.py
─────────
Flask application for VisionGuard — real-time shoplifting detection.

Provides:
  • JWT-based authentication (register / login)
  • Live MJPEG video stream with theft-detection overlay
  • Camera start / stop / demo-video upload
  • Alerts, evidence clip serving, and analytics APIs
"""

import os
import sys
import time
import datetime
import threading
import functools

import cv2
import jwt
import bcrypt
import numpy as np
from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_from_directory,
)
from flask_cors import CORS
from dotenv import load_dotenv

from app.models import db, User, Alert
from app.inference import TheftDetector

# ─────────────────────────────────────────────────────────────
#  Global state shared across requests
# ─────────────────────────────────────────────────────────────
_camera_lock = threading.Lock()
_capture: cv2.VideoCapture | None = None
_camera_thread: threading.Thread | None = None
_camera_running = False
_latest_frame: np.ndarray | None = None
_frame_lock = threading.Lock()

detector = TheftDetector()


# ─────────────────────────────────────────────────────────────
#  App factory
# ─────────────────────────────────────────────────────────────
def create_app():
    load_dotenv()

    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "change-this-secret")
    app.config["JWT_EXPIRE_HOURS"] = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

    # ── Database ──────────────────────────────────────────────
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "storage", "visionguard.db"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    CORS(app, origins=cors_origins.split(","))

    # ── Database ──────────────────────────────────────────────
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # ── Clips directory ───────────────────────────────────────
    clips_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        os.getenv("ALERTS_DIR", "storage/clips"),
    )
    os.makedirs(clips_dir, exist_ok=True)
    detector.clips_dir = clips_dir

    # ── Register routes ───────────────────────────────────────
    _register_routes(app)

    return app


# ─────────────────────────────────────────────────────────────
#  JWT helpers
# ─────────────────────────────────────────────────────────────
def _encode_token(user_id: int, secret: str, hours: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _decode_token(token: str, secret: str) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _token_required(f):
    """Decorator — pulls the JWT from Authorization header or ?token= query."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from flask import current_app

        secret = current_app.config["SECRET_KEY"]

        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.args.get("token")

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        payload = _decode_token(token, secret)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.user_id = payload["sub"]
        return f(*args, **kwargs)

    return wrapper


# ─────────────────────────────────────────────────────────────
#  Camera / video capture thread
# ─────────────────────────────────────────────────────────────
def _camera_loop(source, app):
    """
    Background thread: reads frames, runs detector, and stores
    the latest annotated frame for MJPEG streaming.
    """
    global _capture, _camera_running, _latest_frame

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[Server] ✗ Cannot open video source: {source}")
        _camera_running = False
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    print(f"[Server] ✔ Video source opened  (FPS={fps:.1f})")

    with _camera_lock:
        _capture = cap

    _camera_running = True

    while _camera_running:
        try:
            ret, frame = cap.read()
            if not ret:
                # If reading a file, loop back to start
                if isinstance(source, (str, bytes)):
                    print(f"[Server] Video reached end, looping: {source}")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    # Some codecs might fail to seek, so re-open if needed
                    ret, frame = cap.read()
                    if not ret:
                        print("[Server] Seek failed, re-opening video source")
                        cap.release()
                        cap = cv2.VideoCapture(source)
                        ret, frame = cap.read()
                        if not ret:
                            print("[Server] Failed to re-open video. Stopping.")
                            break
                else:
                    break

            if frame is None:
                continue

            try:
                annotated = detector.process_frame(frame, fps=fps)
            except Exception as e:
                print(f"[ERROR] Inference failed: {e}")
                annotated = frame # Fallback to raw frame

            with _frame_lock:
                _latest_frame = annotated

            # Flush pending alerts to DB
            try:
                pending = detector.pop_pending_alerts()
                if pending:
                    with app.app_context():
                        for a in pending:
                            alert = Alert(
                                activity_type=a["activity_type"],
                                confidence=a["confidence"],
                                severity=a["severity"],
                                clip_filename=a.get("clip_filename"),
                            )
                            db.session.add(alert)
                        db.session.commit()
            except Exception as e:
                print(f"[ERROR] Alert saving failed: {e}")

            # Throttle to ~30 FPS max to avoid CPU burn
            time.sleep(max(0.001, 1.0 / 30.0))
        except Exception as e:
            print(f"[ERROR] Camera loop iteration failed: {e}")
            time.sleep(0.1)

    cap.release()
    with _camera_lock:
        _capture = None
    _camera_running = False
    print("[Server] Camera thread stopped")


def _start_source(source, app):
    """Start the camera thread with the given source (int or filepath)."""
    global _camera_thread, _camera_running

    _stop_source()

    detector.reset()
    _camera_running = True
    _camera_thread = threading.Thread(
        target=_camera_loop, args=(source, app), daemon=True
    )
    _camera_thread.start()

    # Wait briefly for the thread to initialize
    time.sleep(1.0)
    return _camera_running


def _stop_source():
    """Stop the camera thread."""
    global _camera_running, _camera_thread, _latest_frame

    _camera_running = False
    if _camera_thread and _camera_thread.is_alive():
        _camera_thread.join(timeout=3.0)
    _camera_thread = None

    with _frame_lock:
        _latest_frame = None


# ─────────────────────────────────────────────────────────────
#  MJPEG generator
# ─────────────────────────────────────────────────────────────
def _generate_mjpeg():
    """Yield MJPEG frames for the live-feed <img> tag."""
    while True:
        with _frame_lock:
            frame = _latest_frame

        if frame is None:
            # Send a blank frame while waiting
            blank = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(
                blank, "Waiting for frames...", (160, 185),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2,
            )
            _, buf = cv2.imencode(".jpg", blank)
        else:
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
        )
        time.sleep(1.0 / 25)


# ─────────────────────────────────────────────────────────────
#  Route registration
# ─────────────────────────────────────────────────────────────
def _register_routes(app):

    # ── Auth ──────────────────────────────────────────────────

    @app.route("/api/auth/register", methods=["POST"])
    def auth_register():
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        if len(password) < 4:
            return jsonify({"error": "Password must be at least 4 characters"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(email=email, password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()

        token = _encode_token(
            user.id, app.config["SECRET_KEY"], app.config["JWT_EXPIRE_HOURS"]
        )
        return jsonify({"token": token, "user": user.to_dict()}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def auth_login():
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(
            password.encode(), user.password_hash.encode()
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        token = _encode_token(
            user.id, app.config["SECRET_KEY"], app.config["JWT_EXPIRE_HOURS"]
        )
        return jsonify({"token": token, "user": user.to_dict()})

    # ── Video feed ────────────────────────────────────────────

    @app.route("/api/video-feed")
    @_token_required
    def video_feed():
        return Response(
            _generate_mjpeg(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    # ── Camera controls ───────────────────────────────────────

    @app.route("/api/start-camera", methods=["POST"])
    @_token_required
    def start_camera():
        source_raw = os.getenv("CAMERA_SOURCE", "0")
        try:
            source = int(source_raw)
        except ValueError:
            source = source_raw

        ok = _start_source(source, app)
        if ok:
            return jsonify({"message": "Camera started"})
        return jsonify({"error": "Failed to open camera"}), 500

    @app.route("/api/stop-camera", methods=["POST"])
    @_token_required
    def stop_camera():
        _stop_source()
        return jsonify({"message": "Camera stopped"})

    @app.route("/api/upload-video", methods=["POST"])
    @_token_required
    def upload_video():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400

        uploads_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "storage", "uploads"
        )
        os.makedirs(uploads_dir, exist_ok=True)
        save_path = os.path.join(uploads_dir, file.filename)
        file.save(save_path)

        ok = _start_source(save_path, app)
        if ok:
            return jsonify({"message": f"Demo video loaded: {file.filename}"})
        return jsonify({"error": "Failed to open video file"}), 500

    # ── System status ─────────────────────────────────────────

    @app.route("/api/system-status")
    @_token_required
    def system_status():
        today_start = datetime.datetime.now(datetime.timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        total_today = Alert.query.filter(Alert.timestamp >= today_start).count()

        return jsonify(
            {
                "camera_connected": _camera_running,
                "model_running": _camera_running and detector.model_loaded,
                "processing_fps": detector.processing_fps if _camera_running else 0,
                "total_alerts_today": total_today,
            }
        )

    # ── Alerts ────────────────────────────────────────────────

    @app.route("/api/alerts")
    @_token_required
    def get_alerts():
        since = request.args.get("since")
        query = Alert.query.order_by(Alert.timestamp.desc())

        if since:
            try:
                since_dt = datetime.datetime.fromisoformat(
                    since.replace("Z", "+00:00")
                )
                query = query.filter(Alert.timestamp > since_dt)
            except ValueError:
                pass

        alerts = query.limit(50).all()
        return jsonify({"alerts": [a.to_dict() for a in alerts]})

    # ── Evidence ──────────────────────────────────────────────

    @app.route("/api/evidence")
    @_token_required
    def get_evidence():
        severity = request.args.get("severity")
        date_str = request.args.get("date")

        query = Alert.query.filter(Alert.clip_filename.isnot(None)).order_by(
            Alert.timestamp.desc()
        )

        if severity:
            query = query.filter_by(severity=severity)

        if date_str:
            try:
                date_obj = datetime.date.fromisoformat(date_str)
                start = datetime.datetime.combine(
                    date_obj, datetime.time.min, tzinfo=datetime.timezone.utc
                )
                end = datetime.datetime.combine(
                    date_obj, datetime.time.max, tzinfo=datetime.timezone.utc
                )
                query = query.filter(Alert.timestamp.between(start, end))
            except ValueError:
                pass

        evidence = query.limit(100).all()
        return jsonify({"evidence": [a.to_dict() for a in evidence]})

    @app.route("/api/evidence/<path:filename>")
    @_token_required
    def serve_evidence(filename):
        clips_dir = detector.clips_dir
        as_download = request.args.get("download") == "1"
        return send_from_directory(
            clips_dir,
            filename,
            as_attachment=as_download,
        )

    # ── Analytics ─────────────────────────────────────────────

    @app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
    @_token_required
    def delete_alert(alert_id):
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404

        # Delete associated clip file if it exists
        if alert.clip_filename:
            clip_path = os.path.join(detector.clips_dir, alert.clip_filename)
            if os.path.exists(clip_path):
                try:
                    os.remove(clip_path)
                except Exception as e:
                    print(f"[ERROR] Failed to delete clip file: {e}")

        db.session.delete(alert)
        db.session.commit()
        return jsonify({"message": "Alert and associated clip deleted"})

    @app.route("/api/alerts/all", methods=["DELETE"])
    @_token_required
    def delete_all_alerts():
        # Optional: also delete all files in clips_dir
        for filename in os.listdir(detector.clips_dir):
            if filename.endswith(".mp4"):
                try:
                    os.remove(os.path.join(detector.clips_dir, filename))
                except Exception as e:
                    print(f"[ERROR] Failed to delete file {filename}: {e}")

        try:
            db.session.query(Alert).delete()
            db.session.commit()
            return jsonify({"message": "All alerts and clips cleared"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/analytics")
    @_token_required
    def get_analytics():
        total_alerts = Alert.query.count()

        # Alerts per day (last 14 days)
        alerts_per_day = []
        today = datetime.date.today()
        for i in range(13, -1, -1):
            d = today - datetime.timedelta(days=i)
            start = datetime.datetime.combine(
                d, datetime.time.min, tzinfo=datetime.timezone.utc
            )
            end = datetime.datetime.combine(
                d, datetime.time.max, tzinfo=datetime.timezone.utc
            )
            count = Alert.query.filter(Alert.timestamp.between(start, end)).count()
            alerts_per_day.append({"date": d.isoformat(), "count": count})

        # Threat distribution
        shoplifting_count = Alert.query.filter_by(
            activity_type="Shoplifting"
        ).count()
        other_count = total_alerts - shoplifting_count
        threat_distribution = [
            {"name": "Shoplifting", "value": shoplifting_count},
        ]
        if other_count > 0:
            threat_distribution.append({"name": "Other", "value": other_count})

        # Detection accuracy — average confidence of all alerts
        from sqlalchemy import func

        avg_conf = (
            db.session.query(func.avg(Alert.confidence)).scalar() or 0.0
        )
        detection_accuracy = round(float(avg_conf) * 100, 1)

        return jsonify(
            {
                "total_alerts": total_alerts,
                "detection_accuracy": detection_accuracy,
                "alerts_per_day": alerts_per_day,
                "threat_distribution": threat_distribution,
            }
        )
