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
#  Multi-Camera Management
# ─────────────────────────────────────────────────────────────

class CameraInstance:
    """Encapsulates everything for a single camera stream."""

    def __init__(self, camera_id, source, app):
        self.camera_id = camera_id
        self.source = source
        self.app = app
        self.running = False
        self.capture = None
        self.thread = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.detector = TheftDetector()
        
        # Determine labels/dir for this camera's clips
        clips_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            os.getenv("ALERTS_DIR", "storage/clips"),
        )
        self.detector.clips_dir = clips_dir

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        if self.capture:
            self.capture.release()
        self.capture = None

    def _loop(self):
        print(f"[Camera {self.camera_id}] Starting loop with source: {self.source}")
        cap = cv2.VideoCapture(self.source)
        self.capture = cap
        
        if not cap.isOpened():
            print(f"[Camera {self.camera_id}] ✗ Cannot open source")
            self.running = False
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                if isinstance(self.source, str) and not self.source.isdigit() and "rtsp" not in self.source.lower():
                    # If it's a file, loop it
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            
            if frame is None:
                continue

            try:
                annotated = self.detector.process_frame(frame, fps=fps)
                with self.frame_lock:
                    self.latest_frame = annotated
            except Exception as e:
                print(f"[Camera {self.camera_id}] Inference error: {e}")

            # Save alerts
            pending = self.detector.pop_pending_alerts()
            if pending:
                try:
                    with self.app.app_context():
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
                    print(f"[Camera {self.camera_id}] DB error: {e}")

            time.sleep(1.0 / 30)
            
        cap.release()
        self.running = False
        print(f"[Camera {self.camera_id}] Thread stopped")

_cameras = {} # camera_id -> CameraInstance
_cameras_lock = threading.Lock()

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "change-this-secret")
    app.config["JWT_EXPIRE_HOURS"] = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "storage", "visionguard.db"
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174")
    CORS(app, origins=cors_origins.split(","))

    db.init_app(app)
    with app.app_context():
        db.create_all()

    _register_routes(app)
    return app

# ─────────────────────────────────────────────────────────────
#  JWT helpers (unchanged)
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
#  MJPEG generator
# ─────────────────────────────────────────────────────────────
def _generate_mjpeg(camera_id):
    while True:
        with _cameras_lock:
            cam = _cameras.get(camera_id)
        
        if not cam:
            break

        with cam.frame_lock:
            frame = cam.latest_frame

        if frame is None:
            blank = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(blank, f"Cam {camera_id} Initializing...", (120, 185),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 2)
            _, buf = cv2.imencode(".jpg", blank)
        else:
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        time.sleep(1.0 / 20)

# ─────────────────────────────────────────────────────────────
#  Route registration
# ─────────────────────────────────────────────────────────────
def _register_routes(app):

    @app.errorhandler(Exception)
    def handle_error(e):
        print(f"[ERROR] Global: {e}")
        return jsonify({"error": str(e)}), 500

    # ── Auth ──────────────────────────────────────────────────
    @app.route("/api/auth/register", methods=["POST"])
    def auth_register():
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(email=email, password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()
        token = _encode_token(user.id, app.config["SECRET_KEY"], app.config["JWT_EXPIRE_HOURS"])
        return jsonify({"token": token, "user": user.to_dict()}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def auth_login():
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return jsonify({"error": "Invalid credentials"}), 401
        token = _encode_token(user.id, app.config["SECRET_KEY"], app.config["JWT_EXPIRE_HOURS"])
        return jsonify({"token": token, "user": user.to_dict()})

    # ── Video feed ────────────────────────────────────────────
    @app.route("/api/video-feed/<camera_id>")
    @_token_required
    def video_feed(camera_id):
        return Response(_generate_mjpeg(camera_id), mimetype="multipart/x-mixed-replace; boundary=frame")

    # ── Camera controls ───────────────────────────────────────
    @app.route("/api/start-camera", methods=["POST"])
    @_token_required
    def start_camera():
        data = request.get_json(silent=True) or {}
        source_raw = data.get("source") or os.getenv("CAMERA_SOURCE", "0")
        camera_id = data.get("id") or "default"
        
        try:
            source = int(source_raw)
        except ValueError:
            source = source_raw

        with _cameras_lock:
            if camera_id in _cameras:
                _cameras[camera_id].stop()
            
            cam = CameraInstance(camera_id, source, app)
            _cameras[camera_id] = cam
            cam.start()
        
        return jsonify({"message": f"Camera {camera_id} started", "camera_id": camera_id})

    @app.route("/api/stop-camera", methods=["POST"])
    @_token_required
    def stop_camera():
        data = request.get_json(silent=True) or {}
        camera_id = data.get("id") or "default"
        with _cameras_lock:
            if camera_id in _cameras:
                _cameras[camera_id].stop()
                del _cameras[camera_id]
                return jsonify({"message": f"Camera {camera_id} stopped"})
        return jsonify({"error": "Camera not found"}), 404

    @app.route("/api/upload-video", methods=["POST"])
    @_token_required
    def upload_video():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        save_path = os.path.join(uploads_dir, file.filename)
        file.save(save_path)
        
        camera_id = f"demo_{int(time.time())}"
        with _cameras_lock:
            cam = CameraInstance(camera_id, save_path, app)
            _cameras[camera_id] = cam
            cam.start()
        
        return jsonify({"message": "Demo video started", "camera_id": camera_id})

    # ── System status ─────────────────────────────────────────
    @app.route("/api/system-status")
    @_token_required
    def system_status():
        today_start = datetime.datetime.now(datetime.timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        total_today = Alert.query.filter(Alert.timestamp >= today_start).count()
        
        cams_status = []
        with _cameras_lock:
            for cid, cam in _cameras.items():
                cams_status.append({
                    "id": cid,
                    "connected": cam.running,
                    "model_running": cam.running and cam.detector.model_loaded,
                    "fps": cam.detector.processing_fps
                })

        return jsonify({
            "cameras": cams_status,
            "total_alerts_today": total_today,
            "camera_connected": any(c["connected"] for c in cams_status) if cams_status else False,
            "model_running": any(c["model_running"] for c in cams_status) if cams_status else False,
            "processing_fps": round(sum(c["fps"] for c in cams_status) / len(cams_status), 1) if cams_status else 0
        })

    # ── Alerts & Evidence ─────────────────────────────────────
    @app.route("/api/alerts")
    @_token_required
    def get_alerts():
        since = request.args.get("since")
        query = Alert.query.order_by(Alert.timestamp.desc())
        if since:
            try:
                since_dt = datetime.datetime.fromisoformat(since.replace("Z", "+00:00"))
                query = query.filter(Alert.timestamp > since_dt)
            except ValueError: pass
        alerts = query.limit(50).all()
        return jsonify({"alerts": [a.to_dict() for a in alerts]})

    @app.route("/api/evidence")
    @_token_required
    def get_evidence():
        query = Alert.query.filter(Alert.clip_filename.isnot(None)).order_by(Alert.timestamp.desc())
        evidence = query.limit(100).all()
        return jsonify({"evidence": [a.to_dict() for a in evidence]})

    @app.route("/api/evidence/<path:filename>")
    @_token_required
    def serve_evidence(filename):
        clips_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "clips")
        return send_from_directory(clips_dir, filename)

    @app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
    @_token_required
    def delete_alert(alert_id):
        alert = Alert.query.get(alert_id)
        if not alert: return jsonify({"error": "Alert not found"}), 404
        db.session.delete(alert)
        db.session.commit()
        return jsonify({"message": "Deleted"})

    @app.route("/api/analytics")
    @_token_required
    def get_analytics():
        total_alerts = Alert.query.count()
        from sqlalchemy import func
        avg_conf = db.session.query(func.avg(Alert.confidence)).scalar() or 0.0
        return jsonify({
            "total_alerts": total_alerts,
            "detection_accuracy": round(float(avg_conf) * 100, 1),
            "threat_distribution": [{"name": "Shoplifting", "value": total_alerts}]
        })
