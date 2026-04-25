"""
train.py
────────
Train the LRCN theft-detection model on the image-sequence dataset.

Run from VS Code terminal:
    python train.py
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
)

from config import (
    TRAIN_DIR, MODEL_SAVE_PATH,
    SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH, CHANNELS,
    BATCH_SIZE, EPOCHS, LEARNING_RATE, VAL_SPLIT,
    CLASS_NAMES,
)
from dataset import load_dataset
from model   import build_lrcn


def plot_history(history):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(history.history["accuracy"],     label="train")
    axes[0].plot(history.history["val_accuracy"], label="val")
    axes[0].set_title("Accuracy");  axes[0].legend()

    axes[1].plot(history.history["loss"],     label="train")
    axes[1].plot(history.history["val_loss"], label="val")
    axes[1].set_title("Loss");  axes[1].legend()

    plt.tight_layout()
    plt.savefig("training_curves.png")
    print("Training curves saved → training_curves.png")


def main():
    # ── 1. Load dataset ──────────────────────────────────────────
    print("=" * 50)
    print("  Loading dataset from:", TRAIN_DIR)
    print("=" * 50)

    X, y = load_dataset(TRAIN_DIR, augment=True)

    print(f"\nDataset loaded:")
    print(f"  X shape : {X.shape}  (samples, seq_len, H, W, channels)")
    print(f"  y shape : {y.shape}")
    print(f"  Normal  : {(y == 0).sum()} samples")
    print(f"  Theft   : {(y == 1).sum()} samples")

    # ── 2. Train / validation split ──────────────────────────────
    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=VAL_SPLIT,
        random_state=42,
        stratify=y,
    )
    print(f"\nTrain: {len(y_train)}  |  Val: {len(y_val)}")

    # ── 3. Class weights (handle imbalance) ──────────────────────
    cw = compute_class_weight("balanced",
                               classes=np.unique(y_train),
                               y=y_train)
    class_weight_dict = dict(enumerate(cw))
    print(f"Class weights: {class_weight_dict}")

    # ── 4. Build model ───────────────────────────────────────────
    print("\nBuilding LRCN model …")
    model = build_lrcn(SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH, CHANNELS)
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    # ── 5. Callbacks ─────────────────────────────────────────────
    callbacks = [
        ModelCheckpoint(
            MODEL_SAVE_PATH,
            save_best_only=True,
            monitor="val_accuracy",
            verbose=1,
        ),
        EarlyStopping(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            verbose=1,
        ),
    ]

    # ── 6. Train ─────────────────────────────────────────────────
    print("\nTraining …")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        class_weight=class_weight_dict,
        callbacks=callbacks,
    )

    plot_history(history)
    print(f"\nBest model saved → {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    main()
