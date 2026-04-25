"""
predict_video.py
────────────────
Feed a video file to the trained LRCN theft-detection model.

Two output modes
  • Quick summary  – one prediction per sliding window
  • Annotated video – saves a new .mp4 with labels burned in

Usage
-----
  # Basic prediction (prints results to terminal)
  python predict_video.py --video "C:/path/to/myvideo.mp4"

  # Also save an annotated output video
  python predict_video.py --video "C:/path/to/myvideo.mp4" --save

  # Change how many frames per window (default = SEQUENCE_LEN from config)
  python predict_video.py --video "C:/path/to/myvideo.mp4" --seq_len 20 --save
"""

import os
import sys
import argparse
import cv2
import numpy as np
import tensorflow as tf

from config import (
    MODEL_SAVE_PATH,
    SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH,
    CLASS_NAMES,
)
from preprocess import apply_frame_diff


# ─────────────────────────────────────────────────────────────
#  Colour palette  (BGR for OpenCV)
# ─────────────────────────────────────────────────────────────
COLOURS = {
    "Normal": (0, 200, 0),    # green
    "Theft":  (0, 0, 220),    # red
}


# ─────────────────────────────────────────────────────────────
#  Load model
# ─────────────────────────────────────────────────────────────
def load_model():
    if not os.path.exists(MODEL_SAVE_PATH):
        print(f"[ERROR] Model not found: {MODEL_SAVE_PATH}")
        print("        Train first with:  python train.py")
        sys.exit(1)
    print(f"✔ Model loaded from: {MODEL_SAVE_PATH}")
    return tf.keras.models.load_model(MODEL_SAVE_PATH)


# ─────────────────────────────────────────────────────────────
#  Extract & preprocess one window of frames from the video
# ─────────────────────────────────────────────────────────────
def build_sequence(raw_frames):
    """
    Parameters
    ----------
    raw_frames : list of BGR np.ndarray  – consecutive frames from cv2

    Returns
    -------
    np.ndarray  shape (1, SEQUENCE_LEN, H, W, 1)  ready for model.predict()
    """
    # Convert to grayscale + resize
    processed = []
    for frame in raw_frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (FRAME_WIDTH, FRAME_HEIGHT))
        processed.append(gray.astype(np.float32) / 255.0)

    # Motion highlight via frame differencing
    processed = apply_frame_diff(processed)

    # Sample to fixed length
    seq_len = SEQUENCE_LEN
    if len(processed) >= seq_len:
        idxs      = np.linspace(0, len(processed) - 1, seq_len, dtype=int)
        processed = [processed[i] for i in idxs]
    else:
        while len(processed) < seq_len:
            processed.append(processed[-1])

    arr = np.array(processed, dtype=np.float32)[..., np.newaxis]   # (seq_len, H, W, 1)
    return arr[np.newaxis, ...]                                      # add batch dim


# ─────────────────────────────────────────────────────────────
#  Annotate one frame with prediction overlay
# ─────────────────────────────────────────────────────────────
def annotate_frame(frame, label, confidence, probs):
    h, w = frame.shape[:2]
    colour = COLOURS.get(label, (255, 255, 255))

    # Semi-transparent dark banner at the top
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 70), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # Label + confidence
    text = f"{label}  {confidence:.1f}%"
    cv2.putText(frame, text, (12, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, colour, 3, cv2.LINE_AA)

    # Per-class mini-bars
    bar_x, bar_y0 = 12, 58
    bar_w_max     = min(300, w - 24)
    for i, name in enumerate(CLASS_NAMES):
        pct   = probs[i]
        bw    = int(bar_w_max * pct)
        col_i = COLOURS.get(name, (200, 200, 200))
        y     = bar_y0 + i * 14
        cv2.rectangle(frame, (bar_x, y - 10), (bar_x + bw, y), col_i, -1)
        cv2.putText(frame, f"{name} {pct*100:.0f}%",
                    (bar_x + bw + 4, y - 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)

    return frame


# ─────────────────────────────────────────────────────────────
#  Main inference loop
# ─────────────────────────────────────────────────────────────
def predict_video(video_path, save_output, seq_len_override=None):
    seq_len = seq_len_override if seq_len_override else SEQUENCE_LEN

    # ── Open video ────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 25
    orig_w       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\n{'─'*52}")
    print(f"  Video      : {os.path.basename(video_path)}")
    print(f"  Resolution : {orig_w}×{orig_h}  |  FPS: {fps:.1f}")
    print(f"  Frames     : {total_frames}")
    print(f"  Window     : {seq_len} frames per prediction")
    print(f"{'─'*52}\n")

    # ── Output writer ─────────────────────────────────────────
    writer = None
    out_path = None
    if save_output:
        name, ext = os.path.splitext(os.path.basename(video_path))
        out_path  = f"{name}_annotated.mp4"
        fourcc    = cv2.VideoWriter_fourcc(*"mp4v")
        writer    = cv2.VideoWriter(out_path, fourcc, fps, (orig_w, orig_h))

    # ── Load model ────────────────────────────────────────────
    model = load_model()

    # ── Sliding-window inference ──────────────────────────────
    # We collect `seq_len` frames, predict, then slide by seq_len//2
    # (50% overlap) for smoother results.
    stride       = max(1, seq_len // 2)
    buffer       = []
    frame_idx    = 0
    results      = []          # (start_frame, end_frame, label, confidence)
    current_label, current_conf, current_probs = "…", 0.0, np.zeros(len(CLASS_NAMES))

    print("Processing …  (press Ctrl+C to stop early)\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        buffer.append(frame.copy())
        frame_idx += 1

        # When buffer is full, run a prediction
        if len(buffer) == seq_len:
            seq    = build_sequence(buffer)
            probs  = model.predict(seq, verbose=0)[0]
            idx    = int(np.argmax(probs))
            label  = CLASS_NAMES[idx]
            conf   = float(probs[idx]) * 100

            start_t = (frame_idx - seq_len) / fps
            end_t   = frame_idx / fps
            results.append((frame_idx - seq_len, frame_idx, label, conf))

            # Update display label
            current_label = label
            current_conf  = conf
            current_probs = probs

            colour = COLOURS.get(label, (255,255,255))
            status = "⚠  THEFT DETECTED" if label == "Theft" else "✓  Normal"
            print(f"  Frames {frame_idx-seq_len:>5}–{frame_idx:<5} "
                  f"[{start_t:5.1f}s–{end_t:5.1f}s]  "
                  f"{label:<8}  {conf:5.1f}%   {status}")

            # Slide the window
            buffer = buffer[stride:]

        # Write annotated frame to output video
        if save_output and writer:
            ann = annotate_frame(frame, current_label, current_conf, current_probs)
            writer.write(ann)

    cap.release()
    if writer:
        writer.release()

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'═'*52}")
    print("  SUMMARY")
    print(f"{'═'*52}")

    if not results:
        print("  Not enough frames for a prediction.")
        return

    theft_windows  = [r for r in results if r[2] == "Theft"]
    normal_windows = [r for r in results if r[2] == "Normal"]
    avg_conf       = np.mean([r[3] for r in results])

    print(f"  Total windows  : {len(results)}")
    print(f"  Theft windows  : {len(theft_windows)}  "
          f"({100*len(theft_windows)/len(results):.0f}%)")
    print(f"  Normal windows : {len(normal_windows)}")
    print(f"  Avg confidence : {avg_conf:.1f}%")

    # Overall verdict: majority vote
    verdict = "Theft" if len(theft_windows) >= len(normal_windows) else "Normal"
    col     = "🔴" if verdict == "Theft" else "🟢"
    print(f"\n  {col}  OVERALL VERDICT: {verdict.upper()}")

    if theft_windows:
        print("\n  Theft-activity windows (approx. timestamps):")
        for (sf, ef, lbl, conf) in theft_windows:
            print(f"    Frame {sf:>5}–{ef:<5}  "
                  f"({sf/fps:5.1f}s – {ef/fps:5.1f}s)  conf {conf:.1f}%")

    print(f"{'═'*52}\n")

    if save_output and out_path:
        print(f"  Annotated video saved → {out_path}")


# ─────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Run theft detection on a video file.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--video", required=True, metavar="PATH",
        help='Path to input video.\n'
             'Example: --video "C:/videos/shop_cam.mp4"',
    )
    p.add_argument(
        "--save", action="store_true",
        help="Save an annotated output video with predictions burned in.",
    )
    p.add_argument(
        "--seq_len", type=int, default=None, metavar="N",
        help=f"Frames per prediction window (default: {SEQUENCE_LEN} from config).",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    predict_video(
        video_path=args.video,
        save_output=args.save,
        seq_len_override=args.seq_len,
    )
