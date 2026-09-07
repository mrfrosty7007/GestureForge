"""Rule-based Hand Gesture Classifier for GestureForge.

Determines whether individual fingers are extended or folded by comparing
MediaPipe landmark geometric positions, and classifies the resulting pose
into one of five supported gestures:
- Palm
- Fist
- Thumbs Up
- One Finger
- Peace
"""

import math
from typing import Any


class GestureClassifier:
    """Classifies 21 MediaPipe hand landmarks into discrete gesture classes

    using geometric heuristic rules.
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

    @staticmethod
    def _distance(p1: Any, p2: Any) -> float:
        """Computes Euclidean distance between two 3D landmarks."""
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2)

    def get_finger_states(self, landmarks: list[Any]) -> dict[str, bool]:
        """Determines whether each finger is extended or folded.

        Landmark y-coordinates in MediaPipe run top-to-bottom (0.0 at top, 1.0 at bottom).
        For the four fingers (Index, Middle, Ring, Pinky), a finger is extended when
        its tip y-coordinate is positioned above (lower numerical value than) both its
        PIP joint and MCP knuckle.

        Thumb extension is evaluated in two ways:
        1. Vertical extension (thumb pointing upwards, tip above IP and MCP joints).
        2. Radial extension (thumb spread outward to the side, away from palm center).

        Args:
            landmarks: List of 21 landmark objects with .x, .y, .z attributes.

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

        # Thumb vertical orientation (pointing upward)
        thumb_pointing_up = (
            landmarks[self.THUMB_TIP].y < landmarks[self.THUMB_IP].y
            and landmarks[self.THUMB_TIP].y < landmarks[self.THUMB_MCP].y
        )

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

    def classify(self, landmarks: Any) -> tuple[str, str]:
        """Classifies the hand gesture from MediaPipe hand landmarks.

        Recognized gestures:
        - Palm: All five fingers extended.
        - Fist: All fingers folded.
        - Thumbs Up: Thumb pointing up; Index, Middle, Ring, Pinky folded.
        - One Finger: Only index finger extended.
        - Peace: Index and Middle fingers extended; Ring and Pinky folded.

        Args:
            landmarks: MediaPipe NormalizedLandmarkList or list of 21 landmark objects.

        Returns:
            tuple[str, str]: (gesture_name, confidence_level)
                e.g. ("Peace", "High"), ("Fist", "High"), ("Unknown", "Low")
        """
        # Extract landmark list if encapsulated inside MediaPipe container
        lm_list = landmarks.landmark if hasattr(landmarks, "landmark") else landmarks

        if not lm_list or len(lm_list) < 21:
            return "None", "N/A"

        states = self.get_finger_states(lm_list)

        is_thumb_up = states["thumb_up"]
        is_thumb_ext = states["thumb"]
        is_index_ext = states["index"]
        is_middle_ext = states["middle"]
        is_ring_ext = states["ring"]
        is_pinky_ext = states["pinky"]

        # Rule 1: Thumbs Up
        # Thumb pointing up while index, middle, ring, pinky are folded
        if is_thumb_up and (
            not is_index_ext
            and not is_middle_ext
            and not is_ring_ext
            and not is_pinky_ext
        ):
            # Verify thumb tip is distinctly elevated above index knuckle
            if lm_list[self.THUMB_TIP].y < lm_list[self.INDEX_MCP].y:
                return "Thumbs Up", "High"
            return "Thumbs Up", "Medium"

        # Rule 2: Palm
        # All 5 fingers extended (or 4 main fingers extended with relaxed thumb)
        if is_index_ext and is_middle_ext and is_ring_ext and is_pinky_ext:
            if is_thumb_ext:
                return "Palm", "High"
            return "Palm", "Medium"

        # Rule 3: Peace
        # Index and Middle extended; Ring and Pinky folded
        if is_index_ext and is_middle_ext and not is_ring_ext and not is_pinky_ext:
            if not is_thumb_up:
                return "Peace", "High"
            return "Peace", "Medium"

        # Rule 4: One Finger
        # Only Index extended; Middle, Ring, Pinky folded
        if is_index_ext and not is_middle_ext and not is_ring_ext and not is_pinky_ext:
            if not is_thumb_up:
                return "One Finger", "High"
            return "One Finger", "Medium"

        # Rule 5: Fist
        # All fingers folded inward
        if (
            not is_index_ext
            and not is_middle_ext
            and not is_ring_ext
            and not is_pinky_ext
            and not is_thumb_up
        ):
            return "Fist", "High"

        return "Unknown", "Low"
