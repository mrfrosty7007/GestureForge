"""Unit Tests for GestureClassifier.

Validates:
- Orientation-aware thumb detection (Thumbs Up vs Fist)
- Invariance to thumb IP curvature (prevents Thumbs Up / Fist flickering)
- Recognition of Palm, Peace, and One Finger
- 2-consecutive-frame temporal hysteresis smoothing
- Multi-hand independent smoothing
"""

from gesture_classifier import GestureClassifier


class MockLandmark:
    """Mock MediaPipe landmark with x, y, z attributes."""

    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


def create_base_landmarks() -> list[MockLandmark]:
    """Creates a default baseline 21-landmark hand with wrist at bottom."""
    # Initialize 21 landmarks
    lm = [MockLandmark(0.5, 0.8, 0.0) for _ in range(21)]
    # Wrist
    lm[0] = MockLandmark(0.5, 0.8, 0.0)
    return lm


def create_folded_fingers(lm: list[MockLandmark]) -> None:
    """Folds index, middle, ring, pinky fingers (tip.y > pip.y)."""
    # Index: MCP=5, PIP=6, DIP=7, TIP=8
    lm[5] = MockLandmark(0.46, 0.48, 0.0)
    lm[6] = MockLandmark(0.46, 0.54, -0.02)
    lm[7] = MockLandmark(0.46, 0.60, -0.01)
    lm[8] = MockLandmark(0.46, 0.64, 0.0)

    # Middle: MCP=9, PIP=10, DIP=11, TIP=12
    lm[9] = MockLandmark(0.50, 0.46, 0.0)
    lm[10] = MockLandmark(0.50, 0.54, -0.02)
    lm[11] = MockLandmark(0.50, 0.60, -0.01)
    lm[12] = MockLandmark(0.50, 0.64, 0.0)

    # Ring: MCP=13, PIP=14, DIP=15, TIP=16
    lm[13] = MockLandmark(0.54, 0.48, 0.0)
    lm[14] = MockLandmark(0.54, 0.54, -0.02)
    lm[15] = MockLandmark(0.54, 0.60, -0.01)
    lm[16] = MockLandmark(0.54, 0.64, 0.0)

    # Pinky: MCP=17, PIP=18, DIP=19, TIP=20
    lm[17] = MockLandmark(0.58, 0.52, 0.0)
    lm[18] = MockLandmark(0.58, 0.58, -0.02)
    lm[19] = MockLandmark(0.58, 0.62, -0.01)
    lm[20] = MockLandmark(0.58, 0.66, 0.0)


def build_thumbs_up_hand(tip_below_ip: bool = False) -> list[MockLandmark]:
    """Builds landmarks for a Thumbs Up hand pose."""
    lm = create_base_landmarks()
    create_folded_fingers(lm)

    # Thumb: CMC=1, MCP=2, IP=3, TIP=4
    lm[1] = MockLandmark(0.44, 0.72, 0.0)
    lm[2] = MockLandmark(0.42, 0.62, 0.0)

    if tip_below_ip:
        # Simulate slight curvature where tip.y >= ip.y (previously caused flicker to Fist)
        lm[3] = MockLandmark(0.40, 0.36, 0.0)
        lm[4] = MockLandmark(0.39, 0.37, 0.0)  # tip.y slightly > ip.y
    else:
        lm[3] = MockLandmark(0.40, 0.45, 0.0)
        lm[4] = MockLandmark(0.39, 0.34, 0.0)  # tip.y < ip.y

    return lm


def build_fist_hand() -> list[MockLandmark]:
    """Builds landmarks for a Fist hand pose (thumb folded across fingers)."""
    lm = create_base_landmarks()
    create_folded_fingers(lm)

    # Thumb folded across the curled fingers
    lm[1] = MockLandmark(0.44, 0.72, 0.0)
    lm[2] = MockLandmark(0.42, 0.62, 0.0)
    lm[3] = MockLandmark(0.48, 0.58, -0.04)
    lm[4] = MockLandmark(0.54, 0.56, -0.05)  # Points sideways across knuckles
    return lm


def build_palm_hand() -> list[MockLandmark]:
    """Builds landmarks for an open Palm hand pose."""
    lm = create_base_landmarks()

    # All fingers extended (tip.y < pip.y and tip.y < mcp.y)
    # Index
    lm[5] = MockLandmark(0.46, 0.48)
    lm[6] = MockLandmark(0.46, 0.38)
    lm[7] = MockLandmark(0.46, 0.30)
    lm[8] = MockLandmark(0.46, 0.22)

    # Middle
    lm[9] = MockLandmark(0.50, 0.46)
    lm[10] = MockLandmark(0.50, 0.35)
    lm[11] = MockLandmark(0.50, 0.26)
    lm[12] = MockLandmark(0.50, 0.18)

    # Ring
    lm[13] = MockLandmark(0.54, 0.48)
    lm[14] = MockLandmark(0.54, 0.38)
    lm[15] = MockLandmark(0.54, 0.30)
    lm[16] = MockLandmark(0.54, 0.24)

    # Pinky
    lm[17] = MockLandmark(0.58, 0.52)
    lm[18] = MockLandmark(0.58, 0.44)
    lm[19] = MockLandmark(0.58, 0.38)
    lm[20] = MockLandmark(0.58, 0.32)

    # Thumb spread open
    lm[1] = MockLandmark(0.44, 0.72)
    lm[2] = MockLandmark(0.38, 0.64)
    lm[3] = MockLandmark(0.32, 0.56)
    lm[4] = MockLandmark(0.26, 0.48)

    return lm


def build_peace_hand() -> list[MockLandmark]:
    """Builds landmarks for a Peace hand pose (index and middle extended)."""
    lm = create_base_landmarks()
    create_folded_fingers(lm)

    # Extend Index & Middle
    lm[6] = MockLandmark(0.46, 0.38)
    lm[7] = MockLandmark(0.46, 0.30)
    lm[8] = MockLandmark(0.46, 0.22)

    lm[10] = MockLandmark(0.50, 0.35)
    lm[11] = MockLandmark(0.50, 0.26)
    lm[12] = MockLandmark(0.50, 0.18)

    # Thumb folded
    lm[1] = MockLandmark(0.44, 0.72)
    lm[2] = MockLandmark(0.42, 0.62)
    lm[3] = MockLandmark(0.48, 0.58)
    lm[4] = MockLandmark(0.53, 0.56)
    return lm


def build_one_finger_hand() -> list[MockLandmark]:
    """Builds landmarks for a One Finger hand pose (only index extended)."""
    lm = create_base_landmarks()
    create_folded_fingers(lm)

    # Extend only Index
    lm[6] = MockLandmark(0.46, 0.38)
    lm[7] = MockLandmark(0.46, 0.30)
    lm[8] = MockLandmark(0.46, 0.22)

    # Thumb folded
    lm[1] = MockLandmark(0.44, 0.72)
    lm[2] = MockLandmark(0.42, 0.62)
    lm[3] = MockLandmark(0.48, 0.58)
    lm[4] = MockLandmark(0.53, 0.56)
    return lm


def test_thumbs_up_raw_classification() -> None:
    """Tests that orientation-aware classification correctly identifies Thumbs Up."""
    classifier = GestureClassifier()
    lm = build_thumbs_up_hand(tip_below_ip=False)
    gesture, confidence = classifier.classify_raw(lm)
    assert gesture == "Thumbs Up"
    assert confidence == "High"


def test_thumbs_up_curvature_does_not_flicker_to_fist() -> None:
    """Verifies that thumb curvature (tip.y >= ip.y) does NOT flip to Fist."""
    classifier = GestureClassifier()
    lm = build_thumbs_up_hand(tip_below_ip=True)
    gesture, confidence = classifier.classify_raw(lm)
    assert gesture == "Thumbs Up"
    assert confidence == "High"


def test_fist_raw_classification() -> None:
    """Tests that a folded fist classifies as Fist."""
    classifier = GestureClassifier()
    lm = build_fist_hand()
    gesture, confidence = classifier.classify_raw(lm)
    assert gesture == "Fist"
    assert confidence == "High"


def test_front_facing_fist() -> None:
    """Tests that a front-facing closed fist is robustly recognized as Fist,

    even when thumb wraps diagonally across the front of the knuckles.
    """
    classifier = GestureClassifier()
    lm = create_base_landmarks()
    create_folded_fingers(lm)
    # Thumb tip wrapped close to Index MCP (5)
    lm[1] = MockLandmark(0.44, 0.72)
    lm[2] = MockLandmark(0.42, 0.62)
    lm[3] = MockLandmark(0.45, 0.54)
    lm[4] = MockLandmark(0.48, 0.50)  # Close to Index MCP (0.46, 0.48)
    gesture, confidence = classifier.classify_raw(lm)
    assert gesture == "Fist"
    assert confidence == "High"


def test_side_facing_fist() -> None:
    """Tests that a side-facing fist is correctly recognized as Fist."""
    classifier = GestureClassifier()
    lm = create_base_landmarks()
    create_folded_fingers(lm)
    lm[1] = MockLandmark(0.44, 0.72)
    lm[2] = MockLandmark(0.42, 0.62)
    lm[3] = MockLandmark(0.44, 0.54)
    lm[4] = MockLandmark(0.44, 0.52)  # Thumb resting along index finger
    gesture, confidence = classifier.classify_raw(lm)
    assert gesture == "Fist"
    assert confidence == "High"


def test_tilted_fist() -> None:
    """Tests that a rotated/tilted closed fist is correctly recognized as Fist."""
    import math

    classifier = GestureClassifier()
    lm = create_base_landmarks()
    create_folded_fingers(lm)
    lm[1] = MockLandmark(0.44, 0.72)
    lm[2] = MockLandmark(0.42, 0.62)
    lm[3] = MockLandmark(0.45, 0.54)
    lm[4] = MockLandmark(0.48, 0.50)

    # Rotate all landmarks by 30 degrees around center
    rad = math.radians(30)
    cx, cy = 0.5, 0.6
    tilted_lm = []
    for p in lm:
        nx = cx + (p.x - cx) * math.cos(rad) - (p.y - cy) * math.sin(rad)
        ny = cy + (p.x - cx) * math.sin(rad) + (p.y - cy) * math.cos(rad)
        tilted_lm.append(MockLandmark(nx, ny, p.z))

    gesture, confidence = classifier.classify_raw(tilted_lm)
    assert gesture == "Fist"
    assert confidence == "High"


def test_palm_peace_one_finger_preserved() -> None:
    """Ensures Palm, Peace, and One Finger gestures are not broken."""
    classifier = GestureClassifier()

    palm_lm = build_palm_hand()
    assert classifier.classify_raw(palm_lm) == ("Palm", "High")

    peace_lm = build_peace_hand()
    assert classifier.classify_raw(peace_lm) == ("Peace", "High")

    one_lm = build_one_finger_hand()
    assert classifier.classify_raw(one_lm) == ("One Finger", "High")


def test_gesture_hysteresis_smoothing() -> None:
    """Tests that a candidate gesture must persist for 2 consecutive frames

    before replacing the currently displayed gesture.
    """
    classifier = GestureClassifier(hysteresis_frames=2)
    fist_lm = build_fist_hand()
    thumbs_up_lm = build_thumbs_up_hand()

    # Frame 1: Fist arrives (first candidate, not yet confirmed)
    g1, c1 = classifier.classify(fist_lm)
    assert g1 == "None"

    # Frame 2: Fist arrives again (2nd consecutive frame -> confirmed)
    g2, c2 = classifier.classify(fist_lm)
    assert g2 == "Fist"
    assert c2 == "High"

    # Frame 3: Transient 1-frame glitch (Thumbs Up) occurs
    g3, c3 = classifier.classify(thumbs_up_lm)
    # Hysteresis must retain "Fist" because Thumbs Up only occurred for 1 frame
    assert g3 == "Fist"

    # Frame 4: Returns back to Fist
    g4, c4 = classifier.classify(fist_lm)
    assert g4 == "Fist"

    # Frame 5: Intentional transition to Thumbs Up (Frame 1 of candidate)
    g5, c5 = classifier.classify(thumbs_up_lm)
    assert g5 == "Fist"  # still Fist on frame 1

    # Frame 6: Intentional transition to Thumbs Up (Frame 2 of candidate -> confirmed!)
    g6, c6 = classifier.classify(thumbs_up_lm)
    assert g6 == "Thumbs Up"
    assert c6 == "High"


def test_multi_hand_independent_hysteresis() -> None:
    """Tests that hand_id=0 and hand_id=1 do not interfere with each other."""
    classifier = GestureClassifier(hysteresis_frames=2)
    fist_lm = build_fist_hand()
    palm_lm = build_palm_hand()

    # Frame 1
    classifier.classify(fist_lm, hand_id=0)
    classifier.classify(palm_lm, hand_id=1)

    # Frame 2
    g0, _ = classifier.classify(fist_lm, hand_id=0)
    g1, _ = classifier.classify(palm_lm, hand_id=1)

    assert g0 == "Fist"
    assert g1 == "Palm"
