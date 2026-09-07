"""Real-time Hand Detection using MediaPipe Hands and OpenCV.

Tracks up to 2 hands in real-time, draws all 21 keypoint landmarks
with finger connection lines, and displays a live FPS counter.
Press 'Q' to quit cleanly.
"""

import sys
import time

import cv2
import mediapipe as mp


def run_hand_detection():
    """Runs the real-time hand detection loop using the default webcam."""
    # Initialize MediaPipe Hands solution and drawing utilities
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    # Open default webcam (device 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access the webcam. Please ensure a camera is connected.")
        sys.exit(1)

    print("=" * 60)
    print("GestureForge — Real-Time Hand Landmark Detection")
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

                # MediaPipe expects RGB images; convert from BGR
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Performance optimization: mark image as non-writeable before inference
                rgb_frame.flags.writeable = False
                results = hands.process(rgb_frame)
                rgb_frame.flags.writeable = True

                # Draw 21 hand landmarks and connection lines if detected
                hand_count = 0
                if results.multi_hand_landmarks:
                    hand_count = len(results.multi_hand_landmarks)
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style(),
                        )

                # Calculate live FPS
                current_time = time.time()
                fps = (
                    1.0 / (current_time - prev_time)
                    if (current_time - prev_time) > 0
                    else 0.0
                )
                prev_time = current_time

                # Draw HUD Telemetry: FPS counter & Hand count
                cv2.putText(
                    frame,
                    f"FPS: {int(fps)}",
                    (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 128),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    f"Hands Detected: {hand_count}",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 220, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    "Press 'Q' to Exit",
                    (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (180, 180, 180),
                    1,
                    cv2.LINE_AA,
                )

                # Display the live webcam feed
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
