import os

# ─────────────────────────────────────────────
#  Paths  (edit BASE_DIR if your archive moves)
# ─────────────────────────────────────────────
BASE_DIR        = r"C:\Users\546ut\Downloads\archive"
TRAIN_DIR       = os.path.join(BASE_DIR, "Train")
TEST_DIR        = os.path.join(BASE_DIR, "Test")
MODEL_SAVE_PATH = "lrcn_theft_model.keras"

# ─────────────────────────────────────────────
#  Class definitions
#  All crime folders → label 1 (Theft/Anomaly)
#  Normal folders    → label 0
#
#  Why include all crime classes?
#  More diverse abnormal behaviour during
#  training makes the model generalise better.
#  You can remove classes you don't care about.
# ─────────────────────────────────────────────
THEFT_CLASSES = [
    "Shoplifting",
    "Stealing",
    "Robbery",
    "Burglary",
    "Vandalism",
    "Assault",
    "Arson",
    "Arrest",
    "Abuse",
    "Explosion",
    "Fighting",
    "Shooting",
]

NORMAL_CLASSES = [
    "NormalVideos",
    "RoadAccidents",   # road footage is background-like; treated as normal
]

CLASS_NAMES = ["Normal", "Theft"]  # index 0 → Normal, index 1 → Theft

# ─────────────────────────────────────────────
#  Frame / sequence settings
#  Images are already 64×64 in your dataset.
#  SEQUENCE_LEN = how many frames per clip fed
#  to the LRCN at once.
# ─────────────────────────────────────────────
SEQUENCE_LEN  = 20          # frames sampled per video sequence
FRAME_HEIGHT  = 64
FRAME_WIDTH   = 64
CHANNELS      = 1           # grayscale

# ─────────────────────────────────────────────
#  Augmentation
# ─────────────────────────────────────────────
TILT_ANGLE = 30             # degrees used for rotation augmentation

# ─────────────────────────────────────────────
#  Training hyper-parameters
# ─────────────────────────────────────────────
BATCH_SIZE    = 8           # keep low — sequences are memory-heavy
EPOCHS        = 50
LEARNING_RATE = 1e-4
VAL_SPLIT     = 0.2
