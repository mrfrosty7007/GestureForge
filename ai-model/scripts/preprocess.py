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
