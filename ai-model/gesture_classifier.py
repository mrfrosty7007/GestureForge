"""Hybrid ML & Rule-Based Hand Gesture Classifier for GestureForge.

Combines a trained scikit-learn machine learning classifier (RandomForest)
with orientation-aware geometric heuristic rules as a robust fallback mechanism.

Supported ML Gestures:
- Palm
- Fist
- Peace
- One Finger
- Thumbs Up
- OK
- Rock
- Call Me

Supported Fallback Geometric Gestures:
- Palm
- Fist
- Thumbs Up
- One Finger
- Peace

Includes orientation-aware vector angle calculation for robust thumb detection,
wrist-relative translation and scale normalization for invariant ML inference,
and temporal hysteresis smoothing to eliminate frame-to-frame jitter.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# Ensure scripts directory can be imported for preprocessing utilities
_scripts_dir = str(Path(__file__).resolve().parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

try:
    from preprocess import normalize_landmarks
except ImportError:
    try:
        from scripts.preprocess import normalize_landmarks
    except ImportError:

        def normalize_landmarks(landmarks: Any) -> np.ndarray:
            """Fallback normalization if scripts/preprocess.py is unreachable."""
            lm_list = (
                landmarks.landmark if hasattr(landmarks, "landmark") else landmarks
            )
            coords = np.zeros((21, 3), dtype=np.float32)
            for i in range(min(len(lm_list), 21)):
                lm = lm_list[i]
                coords[i] = [
                    getattr(lm, "x", 0.0),
                    getattr(lm, "y", 0.0),
                    getattr(lm, "z", 0.0),
                ]
            wrist = coords[0].copy()
            translated = coords - wrist
            distances = np.linalg.norm(translated, axis=1)
            max_d = float(np.max(distances))
            if max_d > 1e-6:
                return (translated / max_d).flatten().astype(np.float32)
            return translated.flatten().astype(np.float32)


class GestureClassifier:
    """Classifies 21 MediaPipe hand landmarks using a hybrid pipeline:

    1. ML Model (RandomForest) on normalized landmarks.
    2. Geometric heuristic rules as a graceful fallback when ML confidence is low.
    3. Multi-hand temporal hysteresis smoothing to eliminate jitter.
    """

    # MediaPipe Hands landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8

    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12

    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16

    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(
        self,
        hysteresis_frames: int = 2,
        model_path: str | Path | None = None,
        min_ml_confidence: float = 0.55,
    ) -> None:
        """Initializes the classifier with configurable hysteresis and ML model.

        Args:
            hysteresis_frames: Number of consecutive frames a gesture must be
                consistently observed before replacing the currently active gesture.
                Defaults to 2 frames.
            model_path: Optional path to a trained joblib model. Defaults to
                ai-model/models/gesture_model.joblib. If the model file is not found
                or fails to load, the classifier seamlessly falls back to geometric rules.
            min_ml_confidence: Minimum prediction probability required from the ML model
                (between 0.0 and 1.0). Predictions below this threshold fall back to
                geometric rules. Defaults to 0.55.
        """
        self.hysteresis_frames = hysteresis_frames
        self.min_ml_confidence = min_ml_confidence
        # State tracking per hand ID: {hand_id: state_dict}
        self._states: dict[int, dict[str, Any]] = {}

        # ML Model attributes
        self.model: Any = None
        self.class_names: list[str] = []

        # Attempt to load ML model bundle
        default_model_path = (
            Path(__file__).resolve().parent / "models" / "gesture_model.joblib"
        )
        resolved_path = (
            Path(model_path) if model_path is not None else default_model_path
        )

        if resolved_path and resolved_path.exists():
            try:
                loaded = joblib.load(resolved_path)
                if isinstance(loaded, dict) and "model" in loaded:
                    self.model = loaded["model"]
                    self.class_names = list(
                        loaded.get("classes", getattr(self.model, "classes_", []))
                    )
                else:
                    self.model = loaded
                    self.class_names = list(getattr(self.model, "classes_", []))
            except Exception:
                # Corrupted or incompatible model file; fall back gracefully
                self.model = None
                self.class_names = []

    @staticmethod
    def _distance(p1: Any, p2: Any) -> float:
        """Computes Euclidean distance between two 3D landmarks."""
        z1 = getattr(p1, "z", 0.0)
        z2 = getattr(p2, "z", 0.0)
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (z1 - z2) ** 2)

    @staticmethod
    def _compute_angle(v1: tuple[float, ...], v2: tuple[float, ...]) -> float:
        """Computes the angle in degrees between two 2D or 3D vectors."""
        dot = sum(a * b for a, b in zip(v1, v2, strict=True))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 180.0
        cos_val = max(-1.0, min(1.0, dot / (norm1 * norm2)))
        return math.degrees(math.acos(cos_val))

    def reset(self, hand_id: int | None = None) -> None:
        """Resets the temporal hysteresis state."""
        if hand_id is None:
            self._states.clear()
        elif hand_id in self._states:
            del self._states[hand_id]

    def get_finger_states(self, landmarks: list[Any]) -> dict[str, bool]:
        """Determines whether each finger is extended or folded.

        Landmark y-coordinates in MediaPipe run top-to-bottom (0.0 at top, 1.0 at bottom).
        For the four fingers (Index, Middle, Ring, Pinky), a finger is extended when
        its tip y-coordinate is positioned above both its PIP joint and MCP knuckle.

        Thumb extension is evaluated using:
        1. Orientation-aware vector angle:
           - Thumb direction vector: Thumb MCP (2) -> Thumb Tip (4)
           - Palm direction vector: Wrist (0) -> Middle MCP (9)
           - Evaluates whether the angle between vectors is <= 50.0 degrees and thumb tip
             is elevated above Thumb MCP.
        2. Radial extension: Thumb spread outward to the side, away from pinky knuckle.

        Args:
            landmarks: List of 21 landmark objects with .x, .y, and optional .z attributes.

        Returns:
            dict: Boolean state for each finger and thumb orientation.
        """
        # Non-thumb fingers: compare tip y with PIP and MCP joint y
        index_extended = (
            landmarks[self.INDEX_TIP].y < landmarks[self.INDEX_PIP].y
            and landmarks[self.INDEX_TIP].y < landmarks[self.INDEX_MCP].y
        )
        middle_extended = (
            landmarks[self.MIDDLE_TIP].y < landmarks[self.MIDDLE_PIP].y
            and landmarks[self.MIDDLE_TIP].y < landmarks[self.MIDDLE_MCP].y
        )
        ring_extended = (
            landmarks[self.RING_TIP].y < landmarks[self.RING_PIP].y
            and landmarks[self.RING_TIP].y < landmarks[self.RING_MCP].y
        )
        pinky_extended = (
            landmarks[self.PINKY_TIP].y < landmarks[self.PINKY_PIP].y
            and landmarks[self.PINKY_TIP].y < landmarks[self.PINKY_MCP].y
        )

        # ---------------------------------------------------------------------
        # Orientation-aware thumb detection
        # ---------------------------------------------------------------------
        p_wrist = landmarks[self.WRIST]
        p_middle_mcp = landmarks[self.MIDDLE_MCP]
        p_thumb_mcp = landmarks[self.THUMB_MCP]
        p_thumb_tip = landmarks[self.THUMB_TIP]

        # Palm direction vector: Wrist (0) -> Middle MCP (9)
        palm_dir = (
            p_middle_mcp.x - p_wrist.x,
            p_middle_mcp.y - p_wrist.y,
            getattr(p_middle_mcp, "z", 0.0) - getattr(p_wrist, "z", 0.0),
        )

        # Thumb direction vector: Thumb MCP (2) -> Thumb Tip (4)
        thumb_dir = (
            p_thumb_tip.x - p_thumb_mcp.x,
            p_thumb_tip.y - p_thumb_mcp.y,
            getattr(p_thumb_tip, "z", 0.0) - getattr(p_thumb_mcp, "z", 0.0),
        )

        thumb_angle = self._compute_angle(palm_dir, thumb_dir)

        # Thumb pointing up: vector aligned with palm direction (<= 50 deg)
        # and thumb tip elevated above thumb MCP in camera view space
        thumb_pointing_up = thumb_angle <= 50.0 and p_thumb_tip.y < p_thumb_mcp.y

        # Thumb radial extension (spread open sideways from palm)
        dist_thumb_tip_pinky = self._distance(
            landmarks[self.THUMB_TIP], landmarks[self.PINKY_MCP]
        )
        dist_thumb_ip_pinky = self._distance(
            landmarks[self.THUMB_IP], landmarks[self.PINKY_MCP]
        )
        thumb_opened_wide = dist_thumb_tip_pinky > dist_thumb_ip_pinky

        thumb_extended = thumb_pointing_up or thumb_opened_wide

        return {
            "thumb": thumb_extended,
            "thumb_up": thumb_pointing_up,
            "index": index_extended,
            "middle": middle_extended,
            "ring": ring_extended,
            "pinky": pinky_extended,
        }

    def _fingertip_cluster_spread(self, landmarks: list[Any]) -> float:
        """Computes the average pairwise Euclidean distance between the four

        fingertips: Index (8), Middle (12), Ring (16), Pinky (20).
        """
        tips = [
            landmarks[self.INDEX_TIP],
            landmarks[self.MIDDLE_TIP],
            landmarks[self.RING_TIP],
            landmarks[self.PINKY_TIP],
        ]
        total_dist = 0.0
        pair_count = 0
        for i in range(len(tips)):
            for j in range(i + 1, len(tips)):
                total_dist += self._distance(tips[i], tips[j])
                pair_count += 1
        return total_dist / pair_count if pair_count > 0 else 0.0

    def classify_raw(self, landmarks: Any) -> tuple[str, str]:
        """Classifies the hand gesture from landmarks without temporal smoothing.

        Execution pipeline:
        1. Evaluate normalized landmark coordinates with trained ML model.
        2. If confidence >= min_ml_confidence, return (predicted_gesture, confidence).
        3. If ML confidence is low or model is unavailable, fall back to geometric rules.

        Recognized gestures:
        - ML: Palm, Fist, Peace, One Finger, Thumbs Up, OK, Rock, Call Me.
        - Geometric Fallback: Palm, Fist, Thumbs Up, One Finger, Peace.

        Args:
            landmarks: MediaPipe NormalizedLandmarkList or list of 21 landmark objects.

        Returns:
            tuple[str, str]: (gesture_name, confidence_level)
        """
        # Extract landmark list if encapsulated inside MediaPipe container
        lm_list = landmarks.landmark if hasattr(landmarks, "landmark") else landmarks

        if not lm_list or len(lm_list) < 21:
            return "None", "N/A"

        # -----------------------------------------------------------------
        # Step 1: Machine Learning Model Inference
        # -----------------------------------------------------------------
        if self.model is not None:
            try:
                features = normalize_landmarks(lm_list).reshape(1, -1)
                if hasattr(self.model, "predict_proba"):
                    probabilities = self.model.predict_proba(features)[0]
                    best_idx = int(np.argmax(probabilities))
                    max_prob = float(probabilities[best_idx])
                    predicted_class = str(self.model.classes_[best_idx])

                    if max_prob >= self.min_ml_confidence:
                        confidence = "High" if max_prob >= 0.80 else "Medium"
                        return predicted_class, confidence
                else:
                    prediction = self.model.predict(features)[0]
                    return str(prediction), "Medium"
            except Exception:
                # Any ML inference error falls through gracefully to geometric rules
                pass

        # -----------------------------------------------------------------
        # Step 2: Geometric Heuristic Fallback
        # -----------------------------------------------------------------

        states = self.get_finger_states(lm_list)

        is_thumb_up = states["thumb_up"]
        is_thumb_ext = states["thumb"]
        is_index_ext = states["index"]
        is_middle_ext = states["middle"]
        is_ring_ext = states["ring"]
        is_pinky_ext = states["pinky"]

        # Reference palm size for scale-invariant distance thresholds
        palm_size = self._distance(lm_list[self.WRIST], lm_list[self.MIDDLE_MCP])
        if palm_size < 0.05:
            palm_size = 0.30

        # Cluster spread among the 4 fingertips (8, 12, 16, 20)
        cluster_spread = self._fingertip_cluster_spread(lm_list)
        is_compact_cluster = cluster_spread <= max(0.20, 0.50 * palm_size)

        # Distance from thumb tip (4) to index MCP (5)
        dist_thumb_index_mcp = self._distance(
            lm_list[self.THUMB_TIP], lm_list[self.INDEX_MCP]
        )
        thumb_close_to_index = dist_thumb_index_mcp <= max(0.12, 0.38 * palm_size)
        thumb_separated_from_index = dist_thumb_index_mcp > max(0.12, 0.38 * palm_size)

        all_four_folded = (
            not is_index_ext
            and not is_middle_ext
            and not is_ring_ext
            and not is_pinky_ext
        )

        # -----------------------------------------------------------------
        # Rule 1: Palm (all 4 main fingers extended)
        # -----------------------------------------------------------------
        if is_index_ext and is_middle_ext and is_ring_ext and is_pinky_ext:
            if is_thumb_ext:
                return "Palm", "High"
            return "Palm", "Medium"

        # -----------------------------------------------------------------
        # Rule 2: Peace (index and middle extended; ring and pinky folded)
        # -----------------------------------------------------------------
        if is_index_ext and is_middle_ext and not is_ring_ext and not is_pinky_ext:
            if not is_thumb_up:
                return "Peace", "High"
            return "Peace", "Medium"

        # -----------------------------------------------------------------
        # Rule 3: One Finger (only index extended; middle, ring, pinky folded)
        # -----------------------------------------------------------------
        if is_index_ext and not is_middle_ext and not is_ring_ext and not is_pinky_ext:
            if not is_thumb_up:
                return "One Finger", "High"
            return "One Finger", "Medium"

        # -----------------------------------------------------------------
        # Decision Priority when all four fingers are curled:
        # Evaluate Fist rule BEFORE Thumbs Up rule
        # -----------------------------------------------------------------
        if all_four_folded:
            # Rule 4: Fist
            # Require compact fingertip cluster AND thumb tip close to index MCP (or thumb down)
            if is_compact_cluster and (thumb_close_to_index or not is_thumb_up):
                return "Fist", "High"

            # Rule 5: Thumbs Up
            # Only allow Thumbs Up if the thumb clearly points upward
            # and is sufficiently separated from index MCP
            if is_thumb_up and thumb_separated_from_index:
                if lm_list[self.THUMB_TIP].y < lm_list[self.INDEX_MCP].y:
                    return "Thumbs Up", "High"
                return "Thumbs Up", "Medium"

            # Secondary fallback: Fist if thumb is not pointing up
            if not is_thumb_up:
                return "Fist", "High"

        return "Unknown", "Low"

    def classify(self, landmarks: Any, hand_id: int = 0) -> tuple[str, str]:
        """Classifies hand gesture with 2-consecutive-frame hysteresis smoothing.

        A candidate gesture must remain valid for 2 consecutive frames before
        replacing the currently displayed gesture, eliminating rapid single-frame
        flickering.

        Args:
            landmarks: MediaPipe NormalizedLandmarkList or list of 21 landmark objects.
            hand_id: Hand index for multi-hand independent hysteresis tracking.

        Returns:
            tuple[str, str]: (stabilized_gesture, stabilized_confidence)
        """
        raw_gesture, raw_confidence = self.classify_raw(landmarks)

        if self.hysteresis_frames <= 1:
            return raw_gesture, raw_confidence

        if hand_id not in self._states:
            self._states[hand_id] = {
                "current_gesture": "None",
                "current_confidence": "N/A",
                "candidate_gesture": "None",
                "candidate_confidence": "N/A",
                "candidate_count": 0,
            }

        state = self._states[hand_id]
        current_g = state["current_gesture"]

        # Case 1: Same as current confirmed gesture
        if raw_gesture == current_g:
            state["candidate_gesture"] = raw_gesture
            state["candidate_confidence"] = raw_confidence
            state["candidate_count"] = 0
            state["current_confidence"] = raw_confidence
            return current_g, state["current_confidence"]

        # Case 2: New candidate gesture observed
        if raw_gesture == state["candidate_gesture"]:
            state["candidate_count"] += 1
            state["candidate_confidence"] = raw_confidence
        else:
            state["candidate_gesture"] = raw_gesture
            state["candidate_confidence"] = raw_confidence
            state["candidate_count"] = 1

        # Check if candidate has persisted for required consecutive frames
        if state["candidate_count"] >= self.hysteresis_frames:
            state["current_gesture"] = state["candidate_gesture"]
            state["current_confidence"] = state["candidate_confidence"]
            state["candidate_count"] = 0
            return state["current_gesture"], state["current_confidence"]

        # Retain current confirmed gesture until candidate meets 2 consecutive frames
        return state["current_gesture"], state["current_confidence"]
