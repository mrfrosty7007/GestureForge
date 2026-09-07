"""Unit Tests for Machine Learning Gesture Recognition and Pipeline.

Validates:
- Landmark dataset normalization (translation invariance, scale invariance, bounds)
- Model bundle serialization and loading
- ML prediction with confidence scoring
- Prediction fallback to geometric heuristic rules on low confidence
- Missing or corrupted model handling
- Recognition of newly added gestures (OK, Rock, Call Me)
- Dataset CSV preprocessing utilities
"""

import math
from pathlib import Path

import joblib
import numpy as np
import pytest
from gesture_classifier import GestureClassifier
from preprocess import (
    NUM_LANDMARKS,
    extract_raw_coordinates,
    normalize_landmarks,
    preprocess_csv,
)

# Paths for test data and models
tests_dir = Path(__file__).resolve().parent
repo_root = tests_dir.parent.parent
ai_model_dir = repo_root / "ai-model"


class MockLandmark:
    """Mock MediaPipe landmark with x, y, z attributes."""

    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


def create_sample_hand(
    wrist_x: float = 0.5, wrist_y: float = 0.8, scale: float = 1.0
) -> list[MockLandmark]:
    """Generates 21 synthetic landmarks with configurable wrist position and scale."""
    landmarks = []
    # Wrist (0)
    landmarks.append(MockLandmark(wrist_x, wrist_y, 0.0))
    # 20 remaining finger joints
    for i in range(1, 21):
        # Place joints in a fan pattern above the wrist
        angle = math.radians(60 + (i * 3))
        dist = (0.10 + (i % 4) * 0.05) * scale
        x = wrist_x + math.cos(angle) * dist
        y = wrist_y - math.sin(angle) * dist
        z = (i * 0.005) * scale
        landmarks.append(MockLandmark(x, y, z))
    return landmarks


def test_dataset_normalization_shape_and_bounds() -> None:
    """Verifies that normalize_landmarks outputs a 63-D bounded vector."""
    hand = create_sample_hand()
    normalized = normalize_landmarks(hand)

    assert isinstance(normalized, np.ndarray)
    assert normalized.shape == (63,)
    assert normalized.dtype == np.float32

    # Wrist (landmark 0) must be translated to the origin (0, 0, 0)
    assert normalized[0] == pytest.approx(0.0, abs=1e-5)
    assert normalized[1] == pytest.approx(0.0, abs=1e-5)
    assert normalized[2] == pytest.approx(0.0, abs=1e-5)

    # All points must have distance from wrist <= 1.0 (scale bounded)
    reshaped = normalized.reshape(NUM_LANDMARKS, 3)
    distances = np.linalg.norm(reshaped, axis=1)
    assert np.all(distances <= 1.00001)
    # The maximum distance must be exactly 1.0 (or 0 if all points coincide)
    assert np.max(distances) == pytest.approx(1.0, abs=1e-5)


def test_dataset_normalization_translation_invariance() -> None:
    """Verifies that translation bias is completely removed regardless of hand position."""
    hand_a = create_sample_hand(wrist_x=0.2, wrist_y=0.3)
    hand_b = create_sample_hand(wrist_x=0.8, wrist_y=0.9)

    norm_a = normalize_landmarks(hand_a)
    norm_b = normalize_landmarks(hand_b)

    np.testing.assert_allclose(norm_a, norm_b, atol=1e-5)


def test_dataset_normalization_scale_invariance() -> None:
    """Verifies that scale normalization standardizes hands of different sizes."""
    hand_small = create_sample_hand(scale=0.5)
    hand_large = create_sample_hand(scale=2.0)

    norm_small = normalize_landmarks(hand_small)
    norm_large = normalize_landmarks(hand_large)

    np.testing.assert_allclose(norm_small, norm_large, atol=1e-5)


def test_extract_raw_coordinates_varieties() -> None:
    """Verifies coordinate extraction from objects, lists, and numpy arrays."""
    # From MockLandmark list
    hand = create_sample_hand()
    coords = extract_raw_coordinates(hand)
    assert coords.shape == (21, 3)

    # From numpy array (21, 3)
    arr = np.ones((21, 3), dtype=np.float32)
    extracted_arr = extract_raw_coordinates(arr)
    assert extracted_arr.shape == (21, 3)
    assert np.all(extracted_arr == 1.0)

    # From flattened array (63,)
    flat = np.ones((63,), dtype=np.float32)
    extracted_flat = extract_raw_coordinates(flat)
    assert extracted_flat.shape == (21, 3)


def test_model_loading_and_classes() -> None:
    """Verifies that the serialized gesture_model.joblib exists and loads with 8 classes."""
    model_path = ai_model_dir / "models" / "gesture_model.joblib"
    assert model_path.exists(), f"Model file not found at {model_path}"

    loaded = joblib.load(model_path)
    model = loaded["model"] if isinstance(loaded, dict) else loaded
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")

    expected_classes = {
        "Palm",
        "Fist",
        "Peace",
        "One Finger",
        "Thumbs Up",
        "OK",
        "Rock",
        "Call Me",
    }
    actual_classes = set(model.classes_)
    assert expected_classes.issubset(actual_classes)

    # Test GestureClassifier auto-loading
    classifier = GestureClassifier()
    assert classifier.model is not None
    assert set(classifier.class_names) == expected_classes


def test_missing_model_handling(tmp_path: Path) -> None:
    """Verifies that missing model file is handled gracefully without crashing."""
    missing_path = tmp_path / "non_existent_gesture_model.joblib"
    classifier = GestureClassifier(model_path=missing_path)

    # Model should be None, class names empty
    assert classifier.model is None
    assert classifier.class_names == []

    # Still classifies using geometric fallback
    hand = create_sample_hand()
    gesture, confidence = classifier.classify_raw(hand)
    assert isinstance(gesture, str)
    assert isinstance(confidence, str)


def test_corrupted_model_handling(tmp_path: Path) -> None:
    """Verifies that corrupted model files are caught cleanly."""
    corrupted_path = tmp_path / "corrupted_model.joblib"
    corrupted_path.write_text("not a real joblib pickle bundle", encoding="utf-8")

    classifier = GestureClassifier(model_path=corrupted_path)
    assert classifier.model is None
    assert classifier.class_names == []


def test_prediction_fallback_on_low_confidence() -> None:
    """Verifies that classifier falls back to geometric rules when ML confidence is low."""

    class MockLowConfidenceModel:
        """Mock model that always returns low confidence probabilities below threshold."""

        classes_ = np.array(
            [
                "Palm",
                "Fist",
                "Peace",
                "One Finger",
                "Thumbs Up",
                "OK",
                "Rock",
                "Call Me",
            ]
        )

        def predict_proba(self, X: np.ndarray) -> np.ndarray:  # noqa: N803
            # Return uniform 1/8 = 0.125 probabilities (well below 0.55 min_ml_confidence)
            return np.ones((X.shape[0], len(self.classes_)), dtype=np.float32) / 8.0

    classifier = GestureClassifier(min_ml_confidence=0.55)
    classifier.model = MockLowConfidenceModel()

    # Create an unambiguous Peace hand pose
    from backend.tests.test_gesture_classifier import build_peace_hand

    peace_hand = build_peace_hand()

    # Because ML confidence (0.125) < min_ml_confidence (0.55),
    # classify_raw should execute geometric fallback and return Peace!
    gesture, confidence = classifier.classify_raw(peace_hand)
    assert gesture == "Peace"
    assert confidence in ("High", "Medium")


def test_new_gestures_classification() -> None:
    """Tests that the ML pipeline recognizes new gestures: OK, Rock, Call Me."""
    classifier = GestureClassifier()
    assert classifier.model is not None

    # Load a sample of each new gesture from the processed dataset
    dataset_path = ai_model_dir / "dataset" / "processed" / "gestures_processed.csv"
    assert dataset_path.exists()

    samples: dict[str, np.ndarray] = {}
    with open(dataset_path, encoding="utf-8") as f:
        import csv

        reader = csv.DictReader(f)
        for row in reader:
            g = row["gesture"]
            if g in ("OK", "Rock", "Call Me") and g not in samples:
                coords = np.zeros(63, dtype=np.float32)
                for i in range(21):
                    coords[i * 3 + 0] = float(row[f"x{i}"])
                    coords[i * 3 + 1] = float(row[f"y{i}"])
                    coords[i * 3 + 2] = float(row[f"z{i}"])
                samples[g] = coords
            if len(samples) == 3:
                break

    for expected_gesture, feat in samples.items():
        # Pass features directly to model
        pred = classifier.model.predict(feat.reshape(1, -1))[0]
        assert pred == expected_gesture


def test_preprocess_csv_utility(tmp_path: Path) -> None:
    """Verifies that preprocess_csv reads raw CSV and writes normalized coordinates."""
    raw_csv = tmp_path / "raw.csv"
    processed_csv = tmp_path / "processed.csv"

    # Write header and 2 sample rows
    header = ["timestamp", "gesture"] + [
        f"{axis}{i}" for i in range(21) for axis in ("x", "y", "z")
    ]
    sample_hand = create_sample_hand()
    row_values = ["1700000000", "Palm"]
    for lm in sample_hand:
        row_values.extend([f"{lm.x:.4f}", f"{lm.y:.4f}", f"{lm.z:.4f}"])

    import csv

    with open(raw_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(row_values)
        writer.writerow(row_values)

    count = preprocess_csv(raw_csv, processed_csv)
    assert count == 2
    assert processed_csv.exists()

    with open(processed_csv, encoding="utf-8") as f:
        lines = f.readlines()
        # header + 2 rows = 3 lines
        assert len(lines) == 3
