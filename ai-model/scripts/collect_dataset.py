"""Interactive Hand Gesture Dataset Recorder for GestureForge.

Captures 21 3D MediaPipe hand landmarks from a live webcam feed, labels them with
the selected gesture class, and saves labeled samples to CSV for model training.

Recording Controls:
- Keys '1' - '8': Switch active gesture class:
    1: Palm | 2: Fist | 3: Peace | 4: One Finger | 5: Thumbs Up | 6: OK | 7: Rock | 8: Call Me
- 'R' or Space: Toggle recording ON / OFF
- 'C': Clear last recorded sample for current gesture
- 'Q': Quit cleanly and save dataset

Saved Format (CSV):
timestamp, gesture, x0, y0, z0, ..., x20, y20, z20
"""

import csv
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp

# Default dataset path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_DATASET_PATH = PROJECT_DIR / "dataset" / "raw" / "gestures_raw.csv"

# Supported gesture classes for Phase 2 expansion
GESTURE_CLASSES = [
    "Palm",
    "Fist",
    "Peace",
    "One Finger",
    "Thumbs Up",
    "OK",
    "Rock",
    "Call Me",
]

CSV_HEADER = ["timestamp", "gesture"] + [
    f"{axis}{i}" for i in range(21) for axis in ("x", "y", "z")
]


def run_dataset_recorder(output_path: Path | str = DEFAULT_DATASET_PATH) -> None:
    """Runs the interactive dataset collection loop with live camera and HUD feedback."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize CSV if not present
    if not out_file.exists():
        with open(out_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)

    # Count existing samples per gesture
    sample_counts: dict[str, int] = {g: 0 for g in GESTURE_CLASSES}
    if out_file.exists():
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                g = row.get("gesture")
                if g in sample_counts:
                    sample_counts[g] += 1

    # MediaPipe setup
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access webcam for dataset recording.")
        sys.exit(1)

    active_gesture_idx = 0
    is_recording = False
    total_session_samples = 0

    print("=" * 65)
    print("GestureForge — Interactive Dataset Recorder")
    print(f"Output File: {out_file.resolve()}")
    print("Hotkeys:")
    print("  [1-8] Select gesture")
    print("  [R] / [SPACE] Toggle Recording")
    print("  [Q] Exit")
    print("=" * 65)

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    continue

                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                rgb_frame.flags.writeable = False
                results = hands.process(rgb_frame)
                rgb_frame.flags.writeable = True

                active_gesture = GESTURE_CLASSES[active_gesture_idx]
                hand_present = False

                if results.multi_hand_landmarks:
                    hand_present = True
                    hand_landmarks = results.multi_hand_landmarks[0]

                    # Draw landmarks on frame
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style(),
                    )

                    # If recording active, record this frame's landmarks
                    if is_recording:
                        current_ts = round(time.time(), 4)
                        row = [str(current_ts), active_gesture]
                        for lm in hand_landmarks.landmark:
                            row.extend([f"{lm.x:.6f}", f"{lm.y:.6f}", f"{lm.z:.6f}"])

                        with open(
                            out_file, mode="a", newline="", encoding="utf-8"
                        ) as f:
                            writer = csv.writer(f)
                            writer.writerow(row)

                        sample_counts[active_gesture] += 1
                        total_session_samples += 1

                # -------------------------------------------------------------
                # Visual Feedback HUD
                # -------------------------------------------------------------
                # Top header banner
                banner_color = (0, 0, 180) if is_recording else (30, 30, 30)
                cv2.rectangle(frame, (0, 0), (w, 55), banner_color, -1)
                cv2.rectangle(frame, (0, 54), (w, 55), (0, 240, 255), 1)

                rec_status = (
                    "● RECORDING ACTIVE" if is_recording else "○ STANDBY (Press R)"
                )
                rec_color = (0, 255, 0) if is_recording else (180, 180, 180)
                cv2.putText(
                    frame,
                    rec_status,
                    (20, 36),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    rec_color,
                    2,
                    cv2.LINE_AA,
                )

                label_text = (
                    f"Target: [{active_gesture_idx + 1}] {active_gesture.upper()}"
                )
                cv2.putText(
                    frame,
                    label_text,
                    (320, 36),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                count_text = f"Samples: {sample_counts[active_gesture]}"
                cv2.putText(
                    frame,
                    count_text,
                    (w - 200, 36),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 240, 255),
                    2,
                    cv2.LINE_AA,
                )

                # Bottom control palette showing all 8 classes
                cv2.rectangle(frame, (0, h - 45), (w, h), (20, 20, 20), -1)
                for idx, g_name in enumerate(GESTURE_CLASSES):
                    is_current = idx == active_gesture_idx
                    color = (0, 255, 128) if is_current else (150, 150, 150)
                    slot_text = f"[{idx + 1}]{g_name[:5]}"
                    x_pos = 15 + idx * (w // 8)
                    cv2.putText(
                        frame,
                        slot_text,
                        (x_pos, h - 18),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.48,
                        color,
                        1 if not is_current else 2,
                        cv2.LINE_AA,
                    )

                if is_recording and not hand_present:
                    cv2.putText(
                        frame,
                        "NO HAND DETECTED - PLACE HAND IN FRAME",
                        (w // 2 - 220, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 140, 255),
                        2,
                        cv2.LINE_AA,
                    )

                cv2.imshow("GestureForge Dataset Recorder", frame)

                # Hotkey event handler
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    print("\nExiting recorder...")
                    break
                elif key in (ord("r"), ord("R"), ord(" ")):
                    is_recording = not is_recording
                    state_str = "STARTED" if is_recording else "PAUSED"
                    print(
                        f"[Recorder] {state_str} for gesture: {active_gesture} (total: {sample_counts[active_gesture]})"
                    )
                elif ord("1") <= key <= ord("8"):
                    active_gesture_idx = key - ord("1")
                    active_gesture = GESTURE_CLASSES[active_gesture_idx]
                    print(
                        f"[Selection] Switched to gesture: [{active_gesture_idx + 1}] {active_gesture}"
                    )

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("=" * 65)
            print(f"Session finished! Total samples recorded: {total_session_samples}")
            print("Dataset breakdown:")
            for g, cnt in sample_counts.items():
                print(f"  - {g:12s}: {cnt} samples")
            print(f"Saved to: {out_file.resolve()}")
            print("=" * 65)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Record hand landmark dataset with MediaPipe"
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to output raw CSV file",
    )
    args = parser.parse_args()
    run_dataset_recorder(args.output)
