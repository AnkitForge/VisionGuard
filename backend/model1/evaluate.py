"""
evaluate.py
───────────
Evaluate the trained LRCN model on the held-out test set.

Run from VS Code terminal:
    python evaluate.py
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf

from config import TEST_DIR, MODEL_SAVE_PATH, CLASS_NAMES
from dataset import load_dataset


def main():
    # ── 1. Load test set ─────────────────────────────────────────
    print("=" * 50)
    print("  Loading test set from:", TEST_DIR)
    print("=" * 50)

    X_test, y_test = load_dataset(TEST_DIR, augment=False)
    print(f"\nTest samples : {len(y_test)}")
    print(f"  Normal  : {(y_test == 0).sum()}")
    print(f"  Theft   : {(y_test == 1).sum()}")

    # ── 2. Load model ────────────────────────────────────────────
    print(f"\nLoading model from: {MODEL_SAVE_PATH}")
    model = tf.keras.models.load_model(MODEL_SAVE_PATH)

    # ── 3. Evaluate ──────────────────────────────────────────────
    print("\nEvaluating …")
    loss, acc = model.evaluate(X_test, y_test, verbose=1)
    print(f"\nTest Accuracy : {acc * 100:.2f}%")
    print(f"Test Loss     : {loss:.4f}")

    # ── 4. Per-class report ──────────────────────────────────────
    y_pred = np.argmax(model.predict(X_test), axis=1)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES))

    # ── 5. Confusion matrix ──────────────────────────────────────
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
    plt.title("Confusion Matrix – Theft Detection")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png")
    print("Confusion matrix saved → confusion_matrix.png")


if __name__ == "__main__":
    main()
