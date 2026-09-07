"""Real-time Hand Detection and Gesture Recognition using MediaPipe and OpenCV.

Tracks up to 2 hands in real-time, extracts 21 3D landmarks with skeletal
connection lines, classifies hand poses into discrete gestures (Palm, Fist,
Thumbs Up, One Finger, Peace) using geometric rules, and renders live HUD
telemetry (FPS, detected gesture, confidence).

Press 'Q' to quit cleanly.
"""

import sys
import time

import cv2
import mediapipe as mp
from gesture_classifier import GestureClassifier


def run_hand_detection():
    """Runs the real-time hand detection and gesture recognition loop."""
    # Initialize MediaPipe Hands solution and drawing utilities
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    # Initialize rule-based gesture classifier
    classifier = GestureClassifier()

    # Open default webcam (device index 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(
            "Error: Could not access the webcam. Please ensure a camera is connected."
        )
        sys.exit(1)

    print("=" * 60)
    print("GestureForge — Real-Time Hand Detection & Gesture Recognition")
    print("Supported Gestures: Palm | Fist | Thumbs Up | One Finger | Peace")
    print("Tracking up to 2 hands with 21 landmarks each.")
    print("Press 'Q' in the video window to quit.")
    print("=" * 60)

    prev_time = time.time()

    # Configure MediaPipe Hands
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Warning: Empty frame received from webcam. Skipping...")
                    continue

                # Flip the frame horizontally for an intuitive mirror view
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                # MediaPipe expects RGB images; convert from BGR
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Performance optimization: mark image as non-writeable before inference
                rgb_frame.flags.writeable = False
                results = hands.process(rgb_frame)
                rgb_frame.flags.writeable = True

                hand_count = 0
                active_gesture = "None"
                active_confidence = "N/A"

                # Process detected hands
                if results.multi_hand_landmarks:
                    hand_count = len(results.multi_hand_landmarks)

                    for hand_idx, hand_landmarks in enumerate(
                        results.multi_hand_landmarks
                    ):
                        # 1. Draw 21 landmarks and skeletal connection lines
                        mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style(),
                        )

                        # 2. Classify gesture using geometric landmark rules
                        gesture, confidence = classifier.classify(hand_landmarks)

                        # Track primary hand gesture for main HUD overlay
                        if hand_idx == 0:
                            active_gesture = gesture
                            active_confidence = confidence

                        # 3. Render per-hand floating tag near the wrist
                        wrist = hand_landmarks.landmark[GestureClassifier.WRIST]
                        wrist_px = (int(wrist.x * w), int(wrist.y * h) + 25)
                        tag_text = f"{gesture} ({confidence})"
                        cv2.putText(
                            frame,
                            tag_text,
                            wrist_px,
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )

                # Calculate live FPS
                current_time = time.time()
                fps = (
                    1.0 / (current_time - prev_time)
                    if (current_time - prev_time) > 0
                    else 0.0
                )
                prev_time = current_time

                # -------------------------------------------------------------
                # UI Overlay (Telemetry HUD)
                # -------------------------------------------------------------
                # Dark translucent background for HUD telemetry readability
                cv2.rectangle(frame, (10, 10), (320, 185), (20, 20, 20), -1)
                cv2.rectangle(frame, (10, 10), (320, 185), (80, 80, 80), 1)

                # 1. FPS counter
                cv2.putText(
                    frame,
                    f"FPS: {int(fps)}",
                    (25, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 128),
                    2,
                    cv2.LINE_AA,
                )

                # 2. Hands detected count
                cv2.putText(
                    frame,
                    f"Hands: {hand_count}",
                    (200, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 220, 255),
                    2,
                    cv2.LINE_AA,
                )

                # 3. Recognized Gesture
                cv2.putText(
                    frame,
                    f"Gesture: {active_gesture}",
                    (25, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                # 4. Classification Confidence
                conf_color = (
                    (0, 255, 0) if active_confidence == "High" else (0, 200, 255)
                )
                if active_confidence == "N/A":
                    conf_color = (150, 150, 150)
                cv2.putText(
                    frame,
                    f"Confidence: {active_confidence}",
                    (25, 125),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    conf_color,
                    2,
                    cv2.LINE_AA,
                )

                # 5. Controls instructions
                cv2.putText(
                    frame,
                    "Press 'Q' to Exit",
                    (25, 165),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (180, 180, 180),
                    1,
                    cv2.LINE_AA,
                )

                # Display the live webcam window
                cv2.imshow("GestureForge Hand Detection", frame)

                # Check for 'Q' or 'q' key to exit cleanly
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    print("\nExit key pressed. Closing...")
                    break

        finally:
            # Clean up and release hardware resources
            cap.release()
            cv2.destroyAllWindows()
            print("Webcam released and OpenCV windows destroyed cleanly.")


if __name__ == "__main__":
    run_hand_detection()
