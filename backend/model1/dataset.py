"""
dataset.py
──────────
Loads pre-extracted frame images organised as:
  <split>/<ClassName>/VideoName_frameNumber.png

Example path:
  Train/Shoplifting/Shoplifting055_x264_60.png
                    ^─── video prefix ──^  ^frame^

Images are grouped by their video prefix, sorted by frame number,
then sampled/padded to SEQUENCE_LEN frames to form one training
example (just as if we loaded a video file).
"""

import os
import re
import cv2
import numpy as np
from collections import defaultdict
from tqdm import tqdm

from config import (
    THEFT_CLASSES, NORMAL_CLASSES,
    SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH,
)
from preprocess import apply_frame_diff, augment_sequence


# ──────────────────────────────────────────────────────────────
#  Step 1 – group PNG files inside one class folder by video prefix
# ──────────────────────────────────────────────────────────────

def group_frames_by_video(folder_path):
    """
    Scan a class folder and return a dict:
        { video_prefix: [(frame_number, full_path), ...] }

    Filename pattern expected:  <prefix>_<number>.png
    e.g. Shoplifting055_x264_60.png  →  prefix='Shoplifting055_x264', frame=60
    """
    groups = defaultdict(list)

    for fname in os.listdir(folder_path):
        if not fname.lower().endswith(".png"):
            continue

        # Match everything except the last _NUMBER suffix
        m = re.match(r"^(.+)_(\d+)\.png$", fname)
        if not m:
            continue

        prefix    = m.group(1)
        frame_num = int(m.group(2))
        groups[prefix].append((frame_num, os.path.join(folder_path, fname)))

    # Sort each group by ascending frame number
    for prefix in groups:
        groups[prefix].sort(key=lambda x: x[0])

    return groups


# ──────────────────────────────────────────────────────────────
#  Step 2 – load one video's frames into a fixed-length array
# ──────────────────────────────────────────────────────────────

def load_sequence(sorted_frame_list, seq_len=SEQUENCE_LEN):
    """
    Parameters
    ----------
    sorted_frame_list : list of (frame_number, path)
        Already sorted by frame number.
    seq_len : int
        Fixed output length.

    Returns
    -------
    np.ndarray  shape (seq_len, H, W)  dtype float32  values in [0, 1]
    or None if the clip has fewer than 2 valid frames.
    """
    frames = []
    for _, path in sorted_frame_list:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))
        frames.append(img.astype(np.float32) / 255.0)

    if len(frames) < 2:
        return None

    # ── Background removal via consecutive-frame differencing ──
    # (mirrors the paper's "background subtraction" step)
    frames = apply_frame_diff(frames)

    # ── Sample or pad to seq_len ──
    if len(frames) >= seq_len:
        idxs   = np.linspace(0, len(frames) - 1, seq_len, dtype=int)
        frames = [frames[i] for i in idxs]
    else:
        while len(frames) < seq_len:
            frames.append(frames[-1])

    return np.array(frames, dtype=np.float32)   # (seq_len, H, W)


# ──────────────────────────────────────────────────────────────
#  Step 3 – walk all class folders and build X, y arrays
# ──────────────────────────────────────────────────────────────

def load_dataset(data_dir, augment=True):
    """
    Walk every class folder inside data_dir, load frame sequences,
    and return:
        X  –  (N, seq_len, H, W, 1)   float32
        y  –  (N,)                     int32   0=Normal, 1=Theft
    """
    X, y = [], []

    label_map = {cls: 1 for cls in THEFT_CLASSES}
    label_map.update({cls: 0 for cls in NORMAL_CLASSES})

    for folder, label in label_map.items():
        folder_path = os.path.join(data_dir, folder)

        if not os.path.isdir(folder_path):
            print(f"[WARNING] Folder not found, skipping: {folder_path}")
            continue

        groups = group_frames_by_video(folder_path)
        print(f"\nLoading '{folder}'  ({len(groups)} video sequences)  → label {label}")

        for prefix, frame_list in tqdm(groups.items(), desc=folder):
            frames = load_sequence(frame_list)
            if frames is None:
                continue

            seq = frames[..., np.newaxis]          # (seq_len, H, W, 1)
            X.append(seq)
            y.append(label)

            if augment:
                # augment_sequence works on the (seq_len, H, W) array
                flipped, tilted = augment_sequence(frames)
                for aug in (flipped, tilted):
                    aug_arr = np.array(aug, dtype=np.float32)[..., np.newaxis]
                    X.append(aug_arr)
                    y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)
