"""
test.py
───────
Test the trained LRCN theft-detection model.

Three modes:
  1. Single folder of frames (one video sequence)
     python test.py --folder "C:/path/to/frames_folder"

  2. Single image (treated as a 1-frame sequence, padded)
     python test.py --image "C:/path/to/frame.png"

  3. Entire test dataset (all class folders inside Test/)
     python test.py --dataset

Run from VS Code terminal.
"""

import os
import re
import sys
import argparse
import cv2
import numpy as np
import tensorflow as tf

from config import (
    MODEL_SAVE_PATH, TEST_DIR,
    SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH,
    CLASS_NAMES,
)
from preprocess import apply_frame_diff
from dataset    import load_dataset, group_frames_by_video, load_sequence


# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────

def load_model():
    if not os.path.exists(MODEL_SAVE_PATH):
        print(f"[ERROR] Model not found at: {MODEL_SAVE_PATH}")
        print("        Run  python train.py  first.")
        sys.exit(1)
    print(f"Loading model from: {MODEL_SAVE_PATH}")
    return tf.keras.models.load_model(MODEL_SAVE_PATH)


def predict_sequence(model, seq_array):
    """
    Parameters
    ----------
    seq_array : np.ndarray  shape (seq_len, H, W, 1)  float32

    Returns
    -------
    label      : str   CLASS_NAMES[predicted_index]
    confidence : float  0-100
    probs      : np.ndarray  per-class probabilities
    """
    inp   = seq_array[np.newaxis, ...]          # add batch dim → (1, seq_len, H, W, 1)
    probs = model.predict(inp, verbose=0)[0]    # shape (num_classes,)
    idx   = int(np.argmax(probs))
    return CLASS_NAMES[idx], float(probs[idx]) * 100, probs


def frames_from_folder(folder_path):
    """
    Load all PNG files from a folder, sort by frame number,
    and return a (seq_len, H, W, 1) array ready for inference.
    """
    files = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith(".png")],
        key=lambda f: int(re.search(r"(\d+)\.png$", f).group(1))
                      if re.search(r"(\d+)\.png$", f) else 0,
    )

    if not files:
        print(f"[ERROR] No PNG files found in: {folder_path}")
        sys.exit(1)

    frames = []
    for fname in files:
        img = cv2.imread(os.path.join(folder_path, fname), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))
        frames.append(img.astype(np.float32) / 255.0)

    if len(frames) < 2:
        print("[ERROR] Need at least 2 frames for motion differencing.")
        sys.exit(1)

    frames = apply_frame_diff(frames)

    # Sample or pad to SEQUENCE_LEN
    if len(frames) >= SEQUENCE_LEN:
        idxs   = np.linspace(0, len(frames) - 1, SEQUENCE_LEN, dtype=int)
        frames = [frames[i] for i in idxs]
    else:
        while len(frames) < SEQUENCE_LEN:
            frames.append(frames[-1])

    arr = np.array(frames, dtype=np.float32)[..., np.newaxis]   # (seq_len, H, W, 1)
    return arr


def frame_from_image(image_path):
    """
    Load a single PNG image and build a padded sequence from it.
    All SEQUENCE_LEN slots are filled with the same frame-diff
    (all zeros, since there is no prior frame).
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"[ERROR] Cannot read image: {image_path}")
        sys.exit(1)

    img    = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT)).astype(np.float32) / 255.0
    # No prior frame → diff with a blank frame → keep as-is
    frames = [img] * SEQUENCE_LEN
    arr    = np.array(frames, dtype=np.float32)[..., np.newaxis]
    return arr


def print_result(label, confidence, probs, source=""):
    bar_len  = 40
    filled   = int(bar_len * confidence / 100)
    bar      = "█" * filled + "░" * (bar_len - filled)

    print("\n" + "═" * 52)
    if source:
        print(f"  Source     : {source}")
    print(f"  Prediction : {label}")
    print(f"  Confidence : {confidence:.1f}%  [{bar}]")
    print("  Per-class probabilities:")
    for i, name in enumerate(CLASS_NAMES):
        pct  = probs[i] * 100
        pfil = int(bar_len * pct / 100)
        pbar = "█" * pfil + "░" * (bar_len - pfil)
        print(f"    {name:<10} {pct:5.1f}%  [{pbar}]")
    print("═" * 52 + "\n")


# ──────────────────────────────────────────────────────────────
#  Mode 1 – single folder of frames
# ──────────────────────────────────────────────────────────────

def test_folder(model, folder_path):
    print(f"\nTesting folder: {folder_path}")
    arr              = frames_from_folder(folder_path)
    label, conf, probs = predict_sequence(model, arr)
    print_result(label, conf, probs, source=os.path.basename(folder_path))


# ──────────────────────────────────────────────────────────────
#  Mode 2 – single image
# ──────────────────────────────────────────────────────────────

def test_image(model, image_path):
    print(f"\nTesting image: {image_path}")
    arr              = frame_from_image(image_path)
    label, conf, probs = predict_sequence(model, arr)
    print_result(label, conf, probs, source=os.path.basename(image_path))


# ──────────────────────────────────────────────────────────────
#  Mode 3 – full test dataset
# ──────────────────────────────────────────────────────────────

def test_dataset(model):
    """Run evaluation on every sequence in the Test/ directory."""
    from sklearn.metrics import (
        classification_report, confusion_matrix, accuracy_score
    )
    import seaborn as sns
    import matplotlib.pyplot as plt

    print(f"\nRunning full dataset evaluation on: {TEST_DIR}")
    X_test, y_test = load_dataset(TEST_DIR, augment=False)
    print(f"Total test sequences: {len(y_test)}")

    # Predict in batches
    y_prob = model.predict(X_test, batch_size=8, verbose=1)
    y_pred = np.argmax(y_prob, axis=1)

    acc = accuracy_score(y_test, y_pred) * 100
    print(f"\nOverall Accuracy: {acc:.2f}%")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"Confusion Matrix  (Accuracy: {acc:.1f}%)")
    plt.tight_layout()
    plt.savefig("test_confusion_matrix.png")
    print("Confusion matrix saved → test_confusion_matrix.png")

    # Per-sequence results
    print("\nPer-sequence breakdown:")
    print(f"  {'Actual':<12} {'Predicted':<12} {'Confidence':>10}  {'Status'}")
    print("  " + "-" * 50)
    for i in range(len(y_test)):
        actual    = CLASS_NAMES[y_test[i]]
        predicted = CLASS_NAMES[y_pred[i]]
        conf      = y_prob[i][y_pred[i]] * 100
        status    = "✓ Correct" if y_test[i] == y_pred[i] else "✗ Wrong"
        print(f"  {actual:<12} {predicted:<12} {conf:>9.1f}%  {status}")


# ──────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Test the LRCN Theft Detection model.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--folder",
        metavar="PATH",
        help='Path to a folder of PNG frames (one video sequence).\n'
             'Example: --folder "C:/archive/Test/Shoplifting"',
    )
    group.add_argument(
        "--image",
        metavar="PATH",
        help='Path to a single PNG frame.\n'
             'Example: --image "C:/archive/Test/Shoplifting/frame_60.png"',
    )
    group.add_argument(
        "--dataset",
        action="store_true",
        help="Evaluate on the full Test/ dataset defined in config.py.",
    )
    return parser.parse_args()


def main():
    args  = parse_args()
    model = load_model()

    if args.folder:
        test_folder(model, args.folder)
    elif args.image:
        test_image(model, args.image)
    elif args.dataset:
        test_dataset(model)


if __name__ == "__main__":
    main()
