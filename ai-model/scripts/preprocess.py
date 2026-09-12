"""Landmark Preprocessing and Normalization Utilities for GestureForge.

Normalizes 21 3D MediaPipe hand landmarks to be invariant to:
1. Translation (hand position within the camera frame) by setting wrist (0) as the origin.
2. Scale (distance of the hand from the camera) by dividing coordinates by the maximum
   Euclidean distance from the wrist to any landmark.

Produces a standard 63-dimensional feature vector suitable for machine learning classification.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np

# Total MediaPipe hand landmarks
NUM_LANDMARKS = 21
COORDINATES_PER_LANDMARK = 3  # x, y, z
FEATURE_VECTOR_LENGTH = NUM_LANDMARKS * COORDINATES_PER_LANDMARK  # 63

# Default column names for CSV datasets
CSV_COLUMNS = ["timestamp", "gesture"] + [
    f"{axis}{i}" for i in range(NUM_LANDMARKS) for axis in ("x", "y", "z")
]


def extract_raw_coordinates(landmarks: list[Any] | Any) -> np.ndarray:
    """Extracts raw (21, 3) coordinates from MediaPipe landmark containers or lists.

    Args:
        landmarks: MediaPipe NormalizedLandmarkList, list of landmark objects with
            .x, .y, .z attributes, or a (21, 3) numpy array.

    Returns:
        np.ndarray: Array of shape (21, 3) with float coordinates.
    """
    if isinstance(landmarks, np.ndarray):
        if landmarks.shape == (21, 3):
            return landmarks.astype(np.float32)
        if landmarks.shape == (63,):
            return landmarks.reshape(21, 3).astype(np.float32)

    lm_list = landmarks.landmark if hasattr(landmarks, "landmark") else landmarks

    coords = np.zeros((NUM_LANDMARKS, 3), dtype=np.float32)
    for i in range(min(len(lm_list), NUM_LANDMARKS)):
        lm = lm_list[i]
        x = getattr(lm, "x", 0.0)
        y = getattr(lm, "y", 0.0)
        z = getattr(lm, "z", 0.0)
        coords[i] = [x, y, z]

    return coords


def normalize_landmarks(landmarks: list[Any] | Any) -> np.ndarray:
    """Normalizes 21 MediaPipe hand landmarks.

    Steps:
    1. Translation bias removal: Subtract wrist coordinates (landmark 0) from all landmarks,
       so the wrist is placed at (0, 0, 0).
    2. Scale invariance: Compute the maximum Euclidean distance from the wrist across all
       landmarks, and divide relative coordinates by this maximum distance (if > 0).

    Args:
        landmarks: List of landmark objects, MediaPipe container, or numpy array.

    Returns:
        np.ndarray: 1D array of length 63 containing normalized [x0, y0, z0, ..., x20, y20, z20].
    """
    coords = extract_raw_coordinates(landmarks)

    # 1. Translation: wrist-relative origin
    wrist = coords[0].copy()
    translated = coords - wrist

    # 2. Scale: divide by max distance from wrist
    distances = np.linalg.norm(translated, axis=1)
    max_distance = np.max(distances)

    normalized = translated / max_distance if max_distance > 1e-6 else translated

    return normalized.flatten().astype(np.float32)


def extract_raw_landmark_features(landmarks: list[Any] | Any) -> np.ndarray:
    """Extracts raw unnormalized 63-dimensional coordinate feature vector [x0, y0, z0, ..., x20, y20, z20]."""
    coords = extract_raw_coordinates(landmarks)
    return coords.flatten().astype(np.float32)


def extract_invariant_geometric_features(landmarks: list[Any] | Any) -> np.ndarray:
    """Extracts 8 scale- and translation-invariant geometric features from 21 hand landmarks.

    Features engineered:
    1. Thumb Tip (4) to Wrist (0) distance, normalized by wrist-to-MCP scale.
    2. Index Tip (8) to Index MCP (5) distance, normalized by wrist-to-MCP scale.
    3. Middle Tip (12) to Middle MCP (9) distance, normalized by wrist-to-MCP scale.
    4. Ring Tip (16) to Ring MCP (13) distance, normalized by wrist-to-MCP scale.
    5. Pinky Tip (20) to Pinky MCP (17) distance, normalized by wrist-to-MCP scale.
    6. Inter-finger 3D angle between Thumb vector (4->2) and Index vector (8->5).
    7. Inter-finger 3D angle between Index vector (8->5) and Middle vector (12->9).
    8. Inter-finger 3D angle between Middle vector (12->9) and Ring vector (16->13).

    Returns:
        np.ndarray: 1D array of length 8 with invariant float32 features.
    """
    coords = extract_raw_coordinates(landmarks)

    # Reference scale: Wrist (0) to Middle MCP (9) distance
    wrist = coords[0]
    middle_mcp = coords[9]
    scale = float(np.linalg.norm(middle_mcp - wrist))
    if scale < 1e-6:
        # Fallback scale: Wrist (0) to Index MCP (5)
        scale = float(np.linalg.norm(coords[5] - wrist))
        if scale < 1e-6:
            scale = 1.0

    # 1-5: Normalized distances
    d_thumb = float(np.linalg.norm(coords[4] - wrist)) / scale
    d_index = float(np.linalg.norm(coords[8] - coords[5])) / scale
    d_middle = float(np.linalg.norm(coords[12] - coords[9])) / scale
    d_ring = float(np.linalg.norm(coords[16] - coords[13])) / scale
    d_pinky = float(np.linalg.norm(coords[20] - coords[17])) / scale

    # Helper for angle between two 3D vectors (in radians)
    def _vector_angle(v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0
        cos_theta = np.dot(v1, v2) / (norm1 * norm2)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        return float(np.arccos(cos_theta))

    # 6-8: Inter-finger 3D angles
    v_thumb = coords[4] - coords[2]
    v_index = coords[8] - coords[5]
    v_middle = coords[12] - coords[9]
    v_ring = coords[16] - coords[13]

    angle_thumb_index = _vector_angle(v_thumb, v_index)
    angle_index_middle = _vector_angle(v_index, v_middle)
    angle_middle_ring = _vector_angle(v_middle, v_ring)

    return np.array(
        [
            d_thumb,
            d_index,
            d_middle,
            d_ring,
            d_pinky,
            angle_thumb_index,
            angle_index_middle,
            angle_middle_ring,
        ],
        dtype=np.float32,
    )


def preprocess_csv(input_csv_path: str | Path, output_csv_path: str | Path) -> int:
    """Reads a raw dataset CSV, applies translation and scale normalization to all samples,

    and writes the processed samples to output_csv_path.

    Returns:
        int: Number of processed samples written.
    """
    in_path = Path(input_csv_path)
    out_path = Path(output_csv_path)

    if not in_path.exists():
        raise FileNotFoundError(f"Input dataset CSV not found: {in_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows_processed = 0
    with (
        open(in_path, newline="", encoding="utf-8") as f_in,
        open(out_path, mode="w", newline="", encoding="utf-8") as f_out,
    ):
        reader = csv.DictReader(f_in)
        fieldnames = CSV_COLUMNS
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            timestamp = row.get("timestamp", "0")
            gesture = row.get("gesture", "Unknown")

            # Extract 21 landmark triplets
            coords = np.zeros((NUM_LANDMARKS, 3), dtype=np.float32)
            valid = True
            for i in range(NUM_LANDMARKS):
                try:
                    x = float(row[f"x{i}"])
                    y = float(row[f"y{i}"])
                    z = float(row.get(f"z{i}", 0.0))
                    coords[i] = [x, y, z]
                except (KeyError, ValueError):
                    valid = False
                    break

            if not valid:
                continue

            normalized = normalize_landmarks(coords)

            out_row: dict[str, Any] = {
                "timestamp": timestamp,
                "gesture": gesture,
            }
            for i in range(NUM_LANDMARKS):
                out_row[f"x{i}"] = f"{normalized[i * 3 + 0]:.6f}"
                out_row[f"y{i}"] = f"{normalized[i * 3 + 1]:.6f}"
                out_row[f"z{i}"] = f"{normalized[i * 3 + 2]:.6f}"

            writer.writerow(out_row)
            rows_processed += 1

    return rows_processed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess and normalize hand landmark dataset"
    )
    parser.add_argument("--input", required=True, help="Path to raw dataset CSV")
    parser.add_argument(
        "--output", required=True, help="Path to save normalized dataset CSV"
    )
    args = parser.parse_args()

    count = preprocess_csv(args.input, args.output)
    print(f"Preprocessed {count} samples successfully -> {args.output}")
