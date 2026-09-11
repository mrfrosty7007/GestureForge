"""Train RandomForest Hand Gesture Classification Model for GestureForge.

Trains on 8 discrete hand gestures:
- Palm
- Fist
- Peace
- One Finger
- Thumbs Up
- OK
- Rock
- Call Me

Loads raw/processed landmark datasets, applies wrist-relative and scale normalization,
evaluates on train/test split, prints confusion matrix and accuracy metrics,
and serializes the trained model to `ai-model/models/gesture_model.joblib`.
"""

import collections
import csv
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Add ai-model/scripts to path for preprocess import
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from preprocess import NUM_LANDMARKS, normalize_landmarks  # noqa: E402

AI_MODEL_DIR = SCRIPTS_DIR.parent
RAW_DATASET_PATH = AI_MODEL_DIR / "dataset" / "raw" / "gestures_raw.csv"
PROCESSED_DATASET_PATH = (
    AI_MODEL_DIR / "dataset" / "processed" / "gestures_processed.csv"
)
MODEL_OUTPUT_PATH = AI_MODEL_DIR / "models" / "gesture_model.joblib"

TARGET_GESTURES = [
    "Palm",
    "Fist",
    "Peace",
    "One Finger",
    "Thumbs Up",
    "OK",
    "Rock",
    "Call Me",
]


def generate_baseline_dataset(
    samples_per_class: int = 250, seed: int = 42
) -> tuple[np.ndarray, list[str]]:
    """Generates an augmented, anatomically-grounded landmark dataset for all 8 gestures.

    Used to bootstrap model training when webcam samples are not yet recorded,
    incorporating realistic human joint angular variations, scaling, and camera noise.
    """
    rng = np.random.default_rng(seed)

    # Base hand template landmarks in normalized 3D coordinates [21, 3]
    # Wrist is at (0.5, 0.85, 0.0)
    def _create_hand_base():
        lm = np.zeros((21, 3), dtype=np.float32)
        # Wrist
        lm[0] = [0.50, 0.85, 0.0]
        # Thumb: CMC(1), MCP(2), IP(3), TIP(4)
        lm[1] = [0.44, 0.76, -0.01]
        lm[2] = [0.40, 0.68, -0.02]
        lm[3] = [0.38, 0.60, -0.03]
        lm[4] = [0.36, 0.52, -0.04]
        # Index: MCP(5), PIP(6), DIP(7), TIP(8)
        lm[5] = [0.44, 0.55, -0.01]
        lm[6] = [0.43, 0.44, -0.02]
        lm[7] = [0.42, 0.36, -0.03]
        lm[8] = [0.41, 0.28, -0.04]
        # Middle: MCP(9), PIP(10), DIP(11), TIP(12)
        lm[9] = [0.50, 0.53, 0.0]
        lm[10] = [0.50, 0.41, -0.01]
        lm[11] = [0.50, 0.32, -0.02]
        lm[12] = [0.50, 0.24, -0.03]
        # Ring: MCP(13), PIP(14), DIP(15), TIP(16)
        lm[13] = [0.56, 0.55, 0.0]
        lm[14] = [0.57, 0.44, -0.01]
        lm[15] = [0.58, 0.36, -0.02]
        lm[16] = [0.59, 0.28, -0.03]
        # Pinky: MCP(17), PIP(18), DIP(19), TIP(20)
        lm[17] = [0.62, 0.59, 0.01]
        lm[18] = [0.64, 0.50, 0.0]
        lm[19] = [0.65, 0.43, -0.01]
        lm[20] = [0.66, 0.36, -0.02]
        return lm

    def _create_hand_base_2():
        lm = np.zeros((21, 3), dtype=np.float32)
        lm[0] = [0.50, 0.80, 0.0]
        # Knuckles
        lm[5] = [0.46, 0.48, 0.0]
        lm[9] = [0.50, 0.46, 0.0]
        lm[13] = [0.54, 0.48, 0.0]
        lm[17] = [0.58, 0.52, 0.0]
        # Thumb joints
        lm[1] = [0.44, 0.72, 0.0]
        lm[2] = [0.42, 0.62, 0.0]
        # Extended finger defaults
        lm[6] = [0.46, 0.38, 0.0]
        lm[7] = [0.46, 0.30, 0.0]
        lm[8] = [0.46, 0.22, 0.0]

        lm[10] = [0.50, 0.35, 0.0]
        lm[11] = [0.50, 0.26, 0.0]
        lm[12] = [0.50, 0.18, 0.0]

        lm[14] = [0.54, 0.38, 0.0]
        lm[15] = [0.54, 0.30, 0.0]
        lm[16] = [0.54, 0.24, 0.0]

        lm[18] = [0.58, 0.44, 0.0]
        lm[19] = [0.58, 0.38, 0.0]
        lm[20] = [0.58, 0.32, 0.0]
        # Thumb extended
        lm[3] = [0.32, 0.56, 0.0]
        lm[4] = [0.26, 0.48, 0.0]
        return lm

    def _fold_finger(lm, mcp_idx, pip_idx, dip_idx, tip_idx, x_drift=0.0):
        mcp = lm[mcp_idx]
        lm[pip_idx] = [mcp[0] + x_drift, mcp[1] + 0.08, 0.03]
        lm[dip_idx] = [mcp[0] + x_drift, mcp[1] + 0.14, 0.04]
        lm[tip_idx] = [mcp[0] + x_drift, mcp[1] + 0.18, 0.05]

    def _fold_finger_2(lm, mcp_idx, pip_idx, dip_idx, tip_idx):
        base_x = lm[mcp_idx][0]
        lm[pip_idx] = [base_x, 0.54, -0.02]
        lm[dip_idx] = [base_x, 0.60, -0.01]
        lm[tip_idx] = [base_x, 0.64, 0.0]

    all_features: list[np.ndarray] = []
    all_labels: list[str] = []

    for gesture in TARGET_GESTURES:
        for idx in range(samples_per_class):
            use_template_2 = idx % 2 == 1
            lm = _create_hand_base_2() if use_template_2 else _create_hand_base()

            if gesture == "Palm":
                # All fingers extended (default base)
                pass

            elif gesture == "Fist":
                if use_template_2:
                    _fold_finger_2(lm, 5, 6, 7, 8)
                    _fold_finger_2(lm, 9, 10, 11, 12)
                    _fold_finger_2(lm, 13, 14, 15, 16)
                    _fold_finger_2(lm, 17, 18, 19, 20)
                    thumb_subvariant = idx % 3
                    if thumb_subvariant == 0:
                        lm[3] = [0.48, 0.58, -0.04]
                        lm[4] = [0.54, 0.56, -0.05]
                    elif thumb_subvariant == 1:
                        lm[3] = [0.45, 0.54, 0.0]
                        lm[4] = [0.48, 0.50, 0.0]
                    else:
                        lm[3] = [0.44, 0.54, 0.0]
                        lm[4] = [0.44, 0.52, 0.0]
                else:
                    _fold_finger(lm, 5, 6, 7, 8)
                    _fold_finger(lm, 9, 10, 11, 12)
                    _fold_finger(lm, 13, 14, 15, 16)
                    _fold_finger(lm, 17, 18, 19, 20)
                    lm[2] = [0.44, 0.65, 0.02]
                    lm[3] = [0.48, 0.64, 0.03]
                    lm[4] = [0.52, 0.63, 0.04]

            elif gesture == "Peace":
                if use_template_2:
                    _fold_finger_2(lm, 13, 14, 15, 16)
                    _fold_finger_2(lm, 17, 18, 19, 20)
                    lm[3] = [0.48, 0.58, 0.0]
                    lm[4] = [0.53, 0.56, 0.0]
                else:
                    _fold_finger(lm, 13, 14, 15, 16)
                    _fold_finger(lm, 17, 18, 19, 20)
                    lm[8] = [0.38, 0.28, -0.04]
                    lm[12] = [0.52, 0.24, -0.03]
                    lm[3] = [0.44, 0.65, 0.02]
                    lm[4] = [0.48, 0.64, 0.03]

            elif gesture == "One Finger":
                if use_template_2:
                    _fold_finger_2(lm, 9, 10, 11, 12)
                    _fold_finger_2(lm, 13, 14, 15, 16)
                    _fold_finger_2(lm, 17, 18, 19, 20)
                    lm[3] = [0.48, 0.58, 0.0]
                    lm[4] = [0.53, 0.56, 0.0]
                else:
                    _fold_finger(lm, 9, 10, 11, 12)
                    _fold_finger(lm, 13, 14, 15, 16)
                    _fold_finger(lm, 17, 18, 19, 20)
                    lm[3] = [0.44, 0.65, 0.02]
                    lm[4] = [0.48, 0.64, 0.03]

            elif gesture == "Thumbs Up":
                if use_template_2:
                    _fold_finger_2(lm, 5, 6, 7, 8)
                    _fold_finger_2(lm, 9, 10, 11, 12)
                    _fold_finger_2(lm, 13, 14, 15, 16)
                    _fold_finger_2(lm, 17, 18, 19, 20)
                    if idx % 2 == 0:
                        lm[3] = [0.40, 0.45, 0.0]
                        lm[4] = [0.39, 0.34, 0.0]
                    else:
                        lm[3] = [0.40, 0.36, 0.0]
                        lm[4] = [0.39, 0.37, 0.0]
                else:
                    _fold_finger(lm, 5, 6, 7, 8)
                    _fold_finger(lm, 9, 10, 11, 12)
                    _fold_finger(lm, 13, 14, 15, 16)
                    _fold_finger(lm, 17, 18, 19, 20)
                    lm[1] = [0.42, 0.72, 0.0]
                    lm[2] = [0.38, 0.62, 0.01]
                    lm[3] = [0.36, 0.50, 0.02]
                    lm[4] = [0.35, 0.38, 0.03]

            elif gesture == "OK":
                contact_point = [0.42, 0.44, -0.01]
                lm[3] = [0.39, 0.52, -0.02]
                lm[4] = contact_point
                lm[7] = [0.43, 0.40, -0.02]
                lm[8] = contact_point

            elif gesture == "Rock":
                if use_template_2:
                    _fold_finger_2(lm, 9, 10, 11, 12)
                    _fold_finger_2(lm, 13, 14, 15, 16)
                    lm[3] = [0.46, 0.62, 0.02]
                    lm[4] = [0.50, 0.61, 0.03]
                else:
                    _fold_finger(lm, 9, 10, 11, 12)
                    _fold_finger(lm, 13, 14, 15, 16)
                    lm[3] = [0.46, 0.62, 0.02]
                    lm[4] = [0.50, 0.61, 0.03]

            elif gesture == "Call Me":
                if use_template_2:
                    _fold_finger_2(lm, 5, 6, 7, 8)
                    _fold_finger_2(lm, 9, 10, 11, 12)
                    _fold_finger_2(lm, 13, 14, 15, 16)
                    lm[2] = [0.36, 0.66, -0.02]
                    lm[3] = [0.30, 0.58, -0.03]
                    lm[4] = [0.24, 0.50, -0.04]
                    lm[18] = [0.66, 0.48, 0.0]
                    lm[19] = [0.70, 0.40, -0.01]
                    lm[20] = [0.74, 0.32, -0.02]
                else:
                    _fold_finger(lm, 5, 6, 7, 8)
                    _fold_finger(lm, 9, 10, 11, 12)
                    _fold_finger(lm, 13, 14, 15, 16)
                    lm[2] = [0.36, 0.66, -0.02]
                    lm[3] = [0.30, 0.58, -0.03]
                    lm[4] = [0.24, 0.50, -0.04]
                    lm[18] = [0.66, 0.48, 0.0]
                    lm[19] = [0.70, 0.40, -0.01]
                    lm[20] = [0.74, 0.32, -0.02]

            # Data Augmentation: subtle random translation, rotation, scaling, and landmark jitter
            noise = rng.normal(0.0, 0.005, size=lm.shape).astype(np.float32)
            aug_lm = lm + noise

            # Expanded 2D planar rotation (-35 to +35 degrees) for tilt invariance
            angle = np.radians(rng.uniform(-35.0, 35.0))
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float32)
            center = aug_lm[0][:2]
            aug_lm[:, :2] = np.dot(aug_lm[:, :2] - center, rot_matrix) + center

            # Random scale (0.85 to 1.15)
            scale = rng.uniform(0.85, 1.15)
            aug_lm = (aug_lm - aug_lm[0]) * scale + aug_lm[0]

            # Normalize using standard wrist-relative and max-radius normalization
            feat_vec = normalize_landmarks(aug_lm)
            all_features.append(feat_vec)
            all_labels.append(gesture)

    return np.array(all_features, dtype=np.float32), all_labels


def save_dataset_to_csv(
    features: np.ndarray, labels: list[str], output_path: Path
) -> None:
    """Saves raw feature matrix and labels to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = ["timestamp", "gesture"] + [
        f"{axis}{i}" for i in range(NUM_LANDMARKS) for axis in ("x", "y", "z")
    ]
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        current_time = time.time()
        for idx in range(len(labels)):
            row = [f"{current_time:.3f}", labels[idx]] + [
                f"{val:.6f}" for val in features[idx]
            ]
            writer.writerow(row)


def load_dataset_from_csv(
    csv_path: Path,
) -> tuple[np.ndarray, list[str]]:
    """Loads feature matrix and labels from CSV."""
    features = []
    labels = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g = row.get("gesture")
            if not g:
                continue
            coords = []
            valid = True
            for i in range(NUM_LANDMARKS):
                try:
                    coords.extend(
                        [
                            float(row[f"x{i}"]),
                            float(row[f"y{i}"]),
                            float(row.get(f"z{i}", 0.0)),
                        ]
                    )
                except (KeyError, ValueError):
                    valid = False
                    break
            if valid and len(coords) == 63:
                norm_feat = normalize_landmarks(
                    np.array(coords, dtype=np.float32).reshape(21, 3)
                )
                features.append(norm_feat)
                labels.append(g)

    return np.array(features, dtype=np.float32), labels


def load_test_dataset(
    csv_path: Path = RAW_DATASET_PATH,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[np.ndarray, list[str]]:
    """Loads dataset and returns the standardized test split (X_test, y_test)."""
    X, y = load_dataset_from_csv(csv_path)
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_test, y_test


def train_gesture_model(
    raw_path: Path = RAW_DATASET_PATH,
    processed_path: Path = PROCESSED_DATASET_PATH,
    model_output_path: Path = MODEL_OUTPUT_PATH,
) -> dict[str, Any]:
    """Trains, evaluates, and serializes the RandomForest gesture classifier."""
    print("=" * 65)
    print("GestureForge — Machine Learning Gesture Model Training")
    print(f"Target Gesture Classes ({len(TARGET_GESTURES)}): {TARGET_GESTURES}")
    print("=" * 65)

    # 1. Load or Generate Dataset
    if raw_path.exists():
        print(f"Loading existing raw dataset from: {raw_path}")
        X, y = load_dataset_from_csv(raw_path)
        # Check if all 8 gestures are represented
        unique_classes = set(y)
        if len(unique_classes) < len(TARGET_GESTURES):
            print(
                f"Existing dataset only has {len(unique_classes)} classes. Generating complete 8-class augmented dataset..."
            )
            X, y = generate_baseline_dataset(samples_per_class=300)
            save_dataset_to_csv(X, y, raw_path)
    else:
        print(
            f"No existing dataset found at {raw_path}. Generating baseline dataset..."
        )
        X, y = generate_baseline_dataset(samples_per_class=300)
        save_dataset_to_csv(X, y, raw_path)

    # Save processed normalized dataset
    save_dataset_to_csv(X, y, processed_path)
    print(f"Saved processed dataset -> {processed_path}")

    # Class distribution
    counts = collections.Counter(y)
    print("\nClass Counts:")
    for g in TARGET_GESTURES:
        print(f"  - {g:12s}: {counts[g]} samples")
    print(f"Total Samples: {len(y)}")

    # 2. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(
        f"\nTrain set: {X_train.shape[0]} samples | Test set: {X_test.shape[0]} samples"
    )

    # 3. Model Architecture: RandomForestClassifier
    print("\nTraining RandomForestClassifier(n_estimators=100, max_depth=16)...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=16,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
    )
    t_train_start = time.perf_counter()
    clf.fit(X_train, y_train)
    t_train = time.perf_counter() - t_train_start
    print(f"Training completed in {t_train:.2f} seconds.")

    # 4. Evaluation
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=TARGET_GESTURES)

    print("\n" + "=" * 65)
    print(f"MODEL ACCURACY: {acc * 100:.2f}%")
    print("=" * 65)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=TARGET_GESTURES))

    print("\nConfusion Matrix:")
    header_str = " " * 14 + " ".join(f"{g[:4]:>5}" for g in TARGET_GESTURES)
    print(header_str)
    for i, row in enumerate(cm):
        row_str = " ".join(f"{val:>5}" for val in row)
        print(f"{TARGET_GESTURES[i]:<14} {row_str}")

    # 5. Serialize Model Bundle
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": clf,
        "classes": TARGET_GESTURES,
        "feature_dim": 63,
        "accuracy": float(acc),
        "trained_at": time.time(),
        "version": "1.0.0",
    }
    joblib.dump(bundle, model_output_path)
    print(f"\nTrained model successfully serialized to: {model_output_path.resolve()}")

    return {
        "accuracy": float(acc),
        "confusion_matrix": cm.tolist(),
        "class_counts": dict(counts),
        "model_path": str(model_output_path),
    }


if __name__ == "__main__":
    train_gesture_model()
