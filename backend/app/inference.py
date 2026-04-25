"""
inference.py
────────────
Real-time theft detection using the trained LRCN model.

Wraps the model in a thread-safe TheftDetector class that:
  • Maintains a sliding window of preprocessed frames
  • Runs LRCN predictions on each complete window
  • Records evidence clips when theft is detected
  • Annotates frames with prediction overlays for the MJPEG stream
"""

import os
import sys
import time
import threading
import cv2
import numpy as np

# ── Ensure model1/ is importable ─────────────────────────────
MODEL1_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model1")
if MODEL1_DIR not in sys.path:
    sys.path.insert(0, MODEL1_DIR)

from config import SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH, CLASS_NAMES
from preprocess import apply_frame_diff


# ── Colour palette (BGR for OpenCV) ──────────────────────────
COLOURS = {
    "Normal": (0, 200, 0),      # green
    "Theft":  (0, 0, 220),      # red
}

# ── Detection thresholds ─────────────────────────────────────
THEFT_CONFIDENCE_THRESHOLD = 0.60     # 60 % to consider a window "Theft"
CONSECUTIVE_WINDOWS_FOR_ALERT = 2     # need N consecutive theft windows to fire
ALERT_COOLDOWN_SECONDS = 30           # don't fire again within this window
CLIP_DURATION_SECONDS = 5             # evidence clip length


class TheftDetector:
    """
    Thread-safe, stateful detector that processes frames one-by-one
    and returns annotated frames + fires alerts when shoplifting is detected.
    """

    def __init__(self, clips_dir="storage/clips"):
        self.clips_dir = clips_dir
        os.makedirs(self.clips_dir, exist_ok=True)

        # ── Model (lazy loaded) ──────────────────────────────
        self._model = None
        self._model_lock = threading.Lock()

        # ── Frame buffer for sliding window ──────────────────
        self._raw_buffer = []            # original-size BGR frames for clip recording
        self._gray_buffer = []           # preprocessed grayscale 64×64 floats
        self._stride = max(1, SEQUENCE_LEN // 2)
        self._frames_since_predict = 0

        # ── Current prediction state ─────────────────────────
        self.current_label = "Normal"
        self.current_confidence = 0.0
        self.current_probs = np.zeros(len(CLASS_NAMES))

        # ── Alert state ──────────────────────────────────────
        self._consecutive_theft = 0
        self._last_alert_time = 0.0
        self._pending_alerts = []        # list of dicts to be saved by server
        self._alerts_lock = threading.Lock()

        # ── Evidence clip recording ──────────────────────────
        self._clip_writer = None
        self._clip_filename = None
        self._clip_frames_written = 0
        self._clip_max_frames = 0

        # ── FPS tracking ─────────────────────────────────────
        self._frame_count = 0
        self._fps_start = time.time()
        self.processing_fps = 0.0

    # ─────────────────────────────────────────────────────────
    #  Model loading
    # ─────────────────────────────────────────────────────────
    def _load_model(self):
        """Lazy-load the Keras model on first use."""
        if self._model is not None:
            return
        with self._model_lock:
            if self._model is not None:
                return
            import tensorflow as tf

            model_path = os.path.join(MODEL1_DIR, "lrcn_theft_model.keras")
            if not os.path.exists(model_path):
                print(f"[ERROR] Model not found: {model_path}")
                return
            print(f"[TheftDetector] Loading model from {model_path} …")
            self._model = tf.keras.models.load_model(model_path)
            print("[TheftDetector] ✔ Model loaded successfully")

    @property
    def model_loaded(self):
        return self._model is not None

    # ─────────────────────────────────────────────────────────
    #  Preprocessing
    # ─────────────────────────────────────────────────────────
    def _preprocess_frame(self, bgr_frame):
        """Convert BGR → grayscale → resize → normalise to [0,1]."""
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (FRAME_WIDTH, FRAME_HEIGHT))
        return gray.astype(np.float32) / 255.0

    def _build_sequence(self):
        """
        Build a model-ready array from the current gray buffer.
        Applies frame differencing and returns shape (1, SEQUENCE_LEN, H, W, 1).
        """
        frames = list(self._gray_buffer[-SEQUENCE_LEN:])
        if len(frames) < 2:
            return None

        # Motion highlighting via frame differencing
        diffed = apply_frame_diff(frames)

        # Pad or sample to SEQUENCE_LEN
        if len(diffed) >= SEQUENCE_LEN:
            idxs = np.linspace(0, len(diffed) - 1, SEQUENCE_LEN, dtype=int)
            diffed = [diffed[i] for i in idxs]
        else:
            while len(diffed) < SEQUENCE_LEN:
                diffed.append(diffed[-1])

        arr = np.array(diffed, dtype=np.float32)[..., np.newaxis]  # (seq, H, W, 1)
        return arr[np.newaxis, ...]                                  # (1, seq, H, W, 1)

    # ─────────────────────────────────────────────────────────
    #  Frame annotation
    # ─────────────────────────────────────────────────────────
    def _annotate_frame(self, frame):
        """Draw prediction overlay on the frame."""
        h, w = frame.shape[:2]
        colour = COLOURS.get(self.current_label, (255, 255, 255))

        # Semi-transparent dark banner at the top
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (15, 15, 15), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Label + confidence
        text = f"{self.current_label}  {self.current_confidence:.1f}%"
        cv2.putText(
            frame, text, (14, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, colour, 2, cv2.LINE_AA,
        )

        # Per-class mini probability bars
        bar_x, bar_y0 = 14, 52
        bar_w_max = min(280, w - 28)
        for i, name in enumerate(CLASS_NAMES):
            pct = self.current_probs[i]
            bw = int(bar_w_max * pct)
            col_i = COLOURS.get(name, (200, 200, 200))
            y = bar_y0 + i * 16
            cv2.rectangle(frame, (bar_x, y - 10), (bar_x + bw, y), col_i, -1)
            cv2.putText(
                frame, f"{name} {pct * 100:.0f}%",
                (bar_x + bw + 6, y - 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1,
            )

        # Red border flash on theft
        if self.current_label == "Theft":
            thickness = 4
            cv2.rectangle(
                frame, (0, 0), (w - 1, h - 1), (0, 0, 255), thickness,
            )
            cv2.putText(
                frame, "!! SHOPLIFTING DETECTED !!",
                (w // 2 - 180, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA,
            )

        return frame

    # ─────────────────────────────────────────────────────────
    #  Evidence clip recording
    # ─────────────────────────────────────────────────────────
    def _start_clip(self, fps, width, height):
        """Begin recording an evidence clip."""
        if self._clip_writer is not None:
            return  # already recording

        import datetime as _dt
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._clip_filename = f"theft_{ts}.mp4"
        path = os.path.join(self.clips_dir, self._clip_filename)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._clip_writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
        self._clip_max_frames = int(fps * CLIP_DURATION_SECONDS)
        self._clip_frames_written = 0
        print(f"[TheftDetector] 📹 Recording evidence clip → {path}")

    def _write_clip_frame(self, frame):
        """Write a frame to the evidence clip if recording."""
        if self._clip_writer is None:
            return
        self._clip_writer.write(frame)
        self._clip_frames_written += 1
        if self._clip_frames_written >= self._clip_max_frames:
            self._stop_clip()

    def _stop_clip(self):
        """Finish recording the evidence clip."""
        if self._clip_writer is not None:
            self._clip_writer.release()
            self._clip_writer = None
            print(f"[TheftDetector] ✔ Evidence clip saved: {self._clip_filename}")

    # ─────────────────────────────────────────────────────────
    #  Main processing entry point
    # ─────────────────────────────────────────────────────────
    def process_frame(self, bgr_frame, fps=25.0):
        """
        Process one BGR frame from the camera / video.

        Returns
        -------
        annotated_frame : np.ndarray  BGR frame with overlay drawn
        """
        self._load_model()

        h, w = bgr_frame.shape[:2]

        # Preprocess and add to buffers
        gray = self._preprocess_frame(bgr_frame)
        self._gray_buffer.append(gray)
        self._raw_buffer.append(bgr_frame.copy())
        self._frames_since_predict += 1

        # Keep buffers bounded
        max_buf = SEQUENCE_LEN * 3
        if len(self._gray_buffer) > max_buf:
            self._gray_buffer = self._gray_buffer[-max_buf:]
        if len(self._raw_buffer) > max_buf:
            self._raw_buffer = self._raw_buffer[-max_buf:]

        # Run prediction when we have enough frames and have slid enough
        if (
            len(self._gray_buffer) >= SEQUENCE_LEN
            and self._frames_since_predict >= self._stride
            and self._model is not None
        ):
            seq = self._build_sequence()
            if seq is not None:
                probs = self._model.predict(seq, verbose=0)[0]
                idx = int(np.argmax(probs))
                self.current_label = CLASS_NAMES[idx]
                self.current_confidence = float(probs[idx]) * 100
                self.current_probs = probs
                self._frames_since_predict = 0

                # Alert logic
                if (
                    self.current_label == "Theft"
                    and probs[idx] >= THEFT_CONFIDENCE_THRESHOLD
                ):
                    self._consecutive_theft += 1
                else:
                    self._consecutive_theft = 0

                now = time.time()
                if (
                    self._consecutive_theft >= CONSECUTIVE_WINDOWS_FOR_ALERT
                    and (now - self._last_alert_time) > ALERT_COOLDOWN_SECONDS
                ):
                    self._last_alert_time = now
                    # Start evidence clip
                    self._start_clip(fps, w, h)
                    # Queue alert
                    severity = "high" if probs[idx] >= 0.80 else "medium"
                    alert_data = {
                        "activity_type": "Shoplifting",
                        "confidence": float(probs[idx]),
                        "severity": severity,
                        "clip_filename": self._clip_filename,
                    }
                    with self._alerts_lock:
                        self._pending_alerts.append(alert_data)
                    print(
                        f"[TheftDetector] 🚨 ALERT — Shoplifting detected "
                        f"({self.current_confidence:.1f}% confidence)"
                    )

        # Write to evidence clip if recording
        annotated = self._annotate_frame(bgr_frame.copy())
        self._write_clip_frame(annotated)

        # FPS tracking
        self._frame_count += 1
        elapsed = time.time() - self._fps_start
        if elapsed >= 2.0:
            self.processing_fps = round(self._frame_count / elapsed, 1)
            self._frame_count = 0
            self._fps_start = time.time()

        return annotated

    # ─────────────────────────────────────────────────────────
    #  Alert retrieval (consumed by server.py)
    # ─────────────────────────────────────────────────────────
    def pop_pending_alerts(self):
        """Return and clear any queued alert dicts."""
        with self._alerts_lock:
            alerts = list(self._pending_alerts)
            self._pending_alerts.clear()
        return alerts

    # ─────────────────────────────────────────────────────────
    #  Cleanup
    # ─────────────────────────────────────────────────────────
    def reset(self):
        """Reset all buffers and state."""
        self._gray_buffer.clear()
        self._raw_buffer.clear()
        self._frames_since_predict = 0
        self.current_label = "Normal"
        self.current_confidence = 0.0
        self.current_probs = np.zeros(len(CLASS_NAMES))
        self._consecutive_theft = 0
        self._stop_clip()
