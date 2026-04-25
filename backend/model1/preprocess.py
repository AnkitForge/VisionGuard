"""
preprocess.py
─────────────
Image-level preprocessing utilities for the theft-detection LRCN.

Changes from the original (video-based) version:
  • remove_background() renamed → apply_frame_diff()
    (same logic, clearer name for an image-sequence pipeline)
  • preprocess_frame() kept for optional use on raw BGR images
  • augment_sequence() unchanged
"""

import cv2
import numpy as np


# ──────────────────────────────────────────────────────────────
#  Motion highlighting
# ──────────────────────────────────────────────────────────────

def apply_frame_diff(frames):
    """
    Highlight motion by computing absolute difference between
    consecutive frames.  Equivalent to the paper's background-
    subtraction step.

    Parameters
    ----------
    frames : list of np.ndarray  (H, W)  float32 in [0, 1]

    Returns
    -------
    list of np.ndarray – same length as input (first frame padded),
    each value is |frame[i] - frame[i-1]|.
    """
    diffs = []
    for i in range(1, len(frames)):
        diff = np.abs(frames[i].astype(np.float32) - frames[i - 1].astype(np.float32))
        diffs.append(diff)
    # Pad so output length == input length
    diffs.insert(0, diffs[0].copy())
    return diffs


# ──────────────────────────────────────────────────────────────
#  Shadow / noise removal  (used when loading raw BGR images)
# ──────────────────────────────────────────────────────────────

def remove_shadow(frame, threshold=10):
    """Zero-out pixel values below threshold (removes cast shadows)."""
    frame = frame.copy()
    frame[frame < threshold] = 0
    return frame


def remove_noise(frame, ksize=5):
    """Gaussian blur to suppress irrelevant small movements."""
    return cv2.GaussianBlur(frame, (ksize, ksize), 0)


def preprocess_frame(frame, height, width):
    """
    Full single-frame pipeline for raw BGR images.
    Converts to grayscale → resize → shadow removal → denoise.
    (Used if you ever want to load raw frames instead of PNGs.)
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    gray = cv2.resize(gray, (width, height))
    gray = remove_shadow(gray)
    gray = remove_noise(gray)
    return gray


# ──────────────────────────────────────────────────────────────
#  Data augmentation
# ──────────────────────────────────────────────────────────────

def augment_sequence(frames):
    """
    Generate two augmented copies of a frame sequence:
      1. Horizontally flipped
      2. Rotated by TILT_ANGLE degrees (simulates tilted camera)

    Parameters
    ----------
    frames : np.ndarray  (seq_len, H, W)  float32

    Returns
    -------
    flipped : list of (H, W) arrays
    tilted  : list of (H, W) arrays
    """
    from config import TILT_ANGLE, FRAME_HEIGHT, FRAME_WIDTH

    h, w = FRAME_HEIGHT, FRAME_WIDTH
    M    = cv2.getRotationMatrix2D((w // 2, h // 2), TILT_ANGLE, 1.0)

    flipped = [cv2.flip(f, 1) for f in frames]
    tilted  = [cv2.warpAffine(f, M, (w, h)) for f in frames]

    return flipped, tilted
