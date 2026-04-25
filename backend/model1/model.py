"""
model.py
────────
LRCN architecture following the paper, adjusted for 64×64 input.

Spatial dimension trace (64×64 input):
  Conv2D(16) → MaxPool(4,4) → 16×16
  Conv2D(32) → MaxPool(4,4) →  4×4
  Conv2D(64) → MaxPool(2,2) →  2×2
  Conv2D(64) → MaxPool(2,2) →  1×1
  Flatten → 64 values per frame
  → LSTM(64) → LSTM(128) → Dense(128) → Dense(2)
"""

from tensorflow.keras import layers, models, Input


def build_lrcn(seq_len, height, width, channels, num_classes=2):
    """
    Long-term Recurrent Convolutional Network (LRCN).

    Parameters
    ----------
    seq_len    : int   – number of frames per sequence  (e.g. 20)
    height     : int   – frame height in pixels          (e.g. 64)
    width      : int   – frame width  in pixels          (e.g. 64)
    channels   : int   – 1 for grayscale
    num_classes: int   – 2 (Normal / Theft)
    """
    inp = Input(shape=(seq_len, height, width, channels),
                name="frame_sequence")

    # ── CNN feature extractor (TimeDistributed = applied to each frame) ──
    # Block 1
    x = layers.TimeDistributed(
            layers.Conv2D(16, (3, 3), activation="relu", padding="same"),
            name="conv1")(inp)
    x = layers.TimeDistributed(layers.MaxPooling2D((4, 4)), name="pool1")(x)
    x = layers.TimeDistributed(layers.Dropout(0.25),        name="drop1")(x)

    # Block 2
    x = layers.TimeDistributed(
            layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
            name="conv2")(x)
    x = layers.TimeDistributed(layers.MaxPooling2D((4, 4)), name="pool2")(x)
    x = layers.TimeDistributed(layers.Dropout(0.25),        name="drop2")(x)

    # Block 3
    x = layers.TimeDistributed(
            layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
            name="conv3")(x)
    x = layers.TimeDistributed(layers.MaxPooling2D((2, 2)), name="pool3")(x)
    x = layers.TimeDistributed(layers.Dropout(0.25),        name="drop3")(x)

    # Block 4
    x = layers.TimeDistributed(
            layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
            name="conv4")(x)
    x = layers.TimeDistributed(layers.MaxPooling2D((2, 2)), name="pool4")(x)
    x = layers.TimeDistributed(layers.Dropout(0.25),        name="drop4")(x)

    # Flatten spatial dims → vector per frame
    x = layers.TimeDistributed(layers.Flatten(), name="flatten")(x)

    # ── LSTM temporal reasoning ──
    x = layers.LSTM(64,  return_sequences=True,  name="lstm1")(x)
    x = layers.LSTM(128, return_sequences=False, name="lstm2")(x)

    # ── Classification head ──
    x   = layers.Dense(128, activation="relu", name="dense1")(x)
    x   = layers.Dropout(0.25,                 name="drop5")(x)
    out = layers.Dense(num_classes, activation="softmax", name="output")(x)

    return models.Model(inputs=inp, outputs=out, name="LRCN_Theft_Detector")


if __name__ == "__main__":
    from config import SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH, CHANNELS
    m = build_lrcn(SEQUENCE_LEN, FRAME_HEIGHT, FRAME_WIDTH, CHANNELS)
    m.summary()
