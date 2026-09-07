"""Real-time Hand Detection and Gesture Recognition using MediaPipe and OpenCV.

Tracks up to 2 hands in real-time, extracts 21 3D landmarks with skeletal
connection lines, classifies hand poses into discrete gestures (Palm, Fist,
Thumbs Up, One Finger, Peace) using geometric rules, and dispatches detected
multi-hand gestures to the GestureForge FastAPI backend with smart debouncing.

Press 'Q' to quit cleanly.
"""

import collections
import contextlib
import queue
import sys
import threading
import time
from typing import Any

import cv2
import mediapipe as mp
import requests
from gesture_classifier import GestureClassifier

# Backend API Configuration
BACKEND_URL = "http://127.0.0.1:8000/gesture"
VIDEO_WS_URL = "ws://127.0.0.1:8000/ws/video"
REQUEST_TIMEOUT_SEC = 0.5
DEBOUNCE_COOLDOWN_SEC = 0.25
HEARTBEAT_INTERVAL_SEC = 0.5
VALID_GESTURES = {
    "Palm",
    "Fist",
    "Thumbs Up",
    "One Finger",
    "Peace",
    "OK",
    "Rock",
    "Call Me",
}


class VideoFramePublisher:
    """Asynchronously publishes encoded JPEG frames to the FastAPI WebSocket /ws/video.

    Maintains a single-frame buffer to guarantee zero queuing lag and drops
    stale frames if the network or client connection slows down. Reconnects
    automatically if the backend restarts.
    """

    def __init__(self, ws_url: str = VIDEO_WS_URL) -> None:
        self.ws_url = ws_url
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=1)
        self._running = True
        self._connected = False
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def send_frame(self, frame_bytes: bytes) -> None:
        """Enqueues the latest frame for transmission, dropping any stale unsent frame."""
        if not self._running:
            return
        if self._queue.full():
            with contextlib.suppress(queue.Empty):
                self._queue.get_nowait()
        with contextlib.suppress(queue.Full):
            self._queue.put_nowait(frame_bytes)

    def _worker(self) -> None:
        """Background daemon thread maintaining the WebSocket connection and sending frames."""
        import websockets.sync.client

        while self._running:
            try:
                with websockets.sync.client.connect(
                    self.ws_url, close_timeout=1.0
                ) as ws:
                    self._connected = True
                    print(f"[Video Stream] Connected to {self.ws_url}")
                    while self._running:
                        try:
                            frame_data = self._queue.get(timeout=0.5)
                            ws.send(frame_data)
                        except queue.Empty:
                            continue
            except Exception:
                self._connected = False
                time.sleep(1.0)

    def stop(self) -> None:
        """Stops the background worker thread."""
        self._running = False


def send_gesture_async(
    hands_or_gesture: list[dict[str, Any]] | str,
    confidence: str | None = None,
    telemetry: dict[str, Any] | None = None,
) -> None:
    """Dispatches a gesture prediction payload to the FastAPI backend

    in a non-blocking background thread. Supports multi-hand lists,
    legacy single-gesture calls, and real hardware telemetry.
    """
    if isinstance(hands_or_gesture, str):
        hands = [
            {
                "id": 0,
                "label": "Unknown",
                "gesture": hands_or_gesture,
                "confidence": confidence or "High",
            }
        ]
    else:
        hands = hands_or_gesture

    timestamp = int(time.time())
    payload: dict[str, Any] = {
        "hands": hands,
        "timestamp": timestamp,
    }
    if telemetry is not None:
        payload["telemetry"] = telemetry

    def _worker():
        try:
            resp = requests.post(
                BACKEND_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT_SEC,
            )
            if resp.status_code == 200:
                summary = (
                    ", ".join(
                        f"[{h.get('label', 'Hand')} #{h.get('id', 0)}] {h.get('gesture')} ({h.get('confidence')})"
                        for h in hands
                    )
                    if hands
                    else "Heartbeat (0 hands)"
                )
                telem_info = (
                    f" | FPS: {telemetry.get('fps')} Latency: {telemetry.get('latency_ms')}ms"
                    if telemetry
                    else ""
                )
                print(f"Sent: {summary}{telem_info}")
            else:
                print(f"[API Warning] Backend returned status {resp.status_code}")
        except requests.exceptions.RequestException as exc:
            # Print non-fatal error message without interrupting webcam feed
            print(
                f"[API Error] Could not reach backend at {BACKEND_URL}: {type(exc).__name__}"
            )

    # Launch daemon thread so network I/O never blocks the camera loop
    threading.Thread(target=_worker, daemon=True).start()


def run_hand_detection():
    """Runs the real-time hand detection, gesture recognition, and backend streaming loop."""
    # Initialize MediaPipe Hands solution and drawing utilities
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    # Initialize rule-based gesture classifier and video stream publisher
    classifier = GestureClassifier()
    video_publisher = VideoFramePublisher()

    # Open default webcam (device index 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(
            "Error: Could not access the webcam. Please ensure a camera is connected."
        )
        sys.exit(1)

    print("=" * 65)
    print("GestureForge — Real-Time Hand Detection & Gesture Recognition")
    print(
        "Supported Gestures: Palm | Fist | Thumbs Up | One Finger | Peace | OK | Rock | Call Me"
    )
    print(f"Streaming to Backend: {BACKEND_URL}")
    print("Press 'Q' in the video window to quit.")
    print("=" * 65)

    prev_perf = time.perf_counter()
    frame_durations: collections.deque[float] = collections.deque(maxlen=20)
    frame_count = 0
    last_sent_hands_state = None
    last_sent_time = 0.0

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

                frame_count += 1
                current_time = time.time()

                # Calculate smoothed rolling FPS using a sliding window
                current_perf = time.perf_counter()
                frame_delta = current_perf - prev_perf
                prev_perf = current_perf
                if frame_delta > 0:
                    frame_durations.append(frame_delta)
                rolling_fps = (
                    round(len(frame_durations) / sum(frame_durations), 1)
                    if frame_durations
                    else 0.0
                )

                # Flip the frame horizontally for an intuitive mirror view
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                # MediaPipe expects RGB images; convert from BGR
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Measure actual MediaPipe inference latency with perf_counter
                rgb_frame.flags.writeable = False
                inference_start = time.perf_counter()
                results = hands.process(rgb_frame)
                inference_latency_ms = round(
                    (time.perf_counter() - inference_start) * 1000.0, 2
                )
                rgb_frame.flags.writeable = True

                detected_hands: list[dict[str, Any]] = []
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
                        gesture, confidence = classifier.classify(
                            hand_landmarks, hand_id=hand_idx
                        )

                        # Determine handedness label if available from MediaPipe
                        label = "Unknown"
                        if results.multi_handedness and hand_idx < len(
                            results.multi_handedness
                        ):
                            classification = results.multi_handedness[
                                hand_idx
                            ].classification
                            if classification:
                                label = classification[0].label

                        # Collect valid gestures for multi-hand payload
                        if gesture in VALID_GESTURES:
                            detected_hands.append(
                                {
                                    "id": hand_idx,
                                    "label": label,
                                    "gesture": gesture,
                                    "confidence": confidence,
                                }
                            )

                        # Track primary hand gesture for main HUD overlay text
                        if hand_idx == 0:
                            active_gesture = gesture
                            active_confidence = confidence

                        # 3. Render per-hand floating tag near the wrist
                        wrist = hand_landmarks.landmark[GestureClassifier.WRIST]
                        wrist_px = (int(wrist.x * w), int(wrist.y * h) + 25)
                        tag_text = f"[{label}] {gesture} ({confidence})"
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

                # -------------------------------------------------------------
                # Construct Real-Time Hardware Telemetry Payload
                # -------------------------------------------------------------
                telemetry_data = {
                    "fps": rolling_fps,
                    "latency_ms": inference_latency_ms,
                    "frame_timestamp": round(current_time, 3),
                    "frame": frame_count,
                    "hand_count": hand_count,
                }

                # -------------------------------------------------------------
                # Smart Debounced API Streaming to Backend (Multi-Hand + Telemetry)
                # -------------------------------------------------------------
                if detected_hands:
                    current_hands_state = tuple(
                        (h["id"], h["label"], h["gesture"]) for h in detected_hands
                    )
                    hands_changed = current_hands_state != last_sent_hands_state
                    cooldown_expired = (
                        current_time - last_sent_time
                    ) >= DEBOUNCE_COOLDOWN_SEC

                    if hands_changed or cooldown_expired:
                        send_gesture_async(detected_hands, telemetry=telemetry_data)
                        last_sent_hands_state = current_hands_state
                        last_sent_time = current_time
                else:
                    # Reset tracker when no valid gesture is detected
                    last_sent_hands_state = None
                    # Send periodic telemetry heartbeat even when 0 hands are in view
                    if (current_time - last_sent_time) >= HEARTBEAT_INTERVAL_SEC:
                        send_gesture_async([], telemetry=telemetry_data)
                        last_sent_time = current_time

                # -------------------------------------------------------------
                # UI Overlay (Telemetry HUD)
                # -------------------------------------------------------------
                # Dark translucent background for HUD telemetry readability
                cv2.rectangle(frame, (10, 10), (330, 215), (20, 20, 20), -1)
                cv2.rectangle(frame, (10, 10), (330, 215), (80, 80, 80), 1)

                # 1. FPS counter & Inference Latency
                cv2.putText(
                    frame,
                    f"FPS: {rolling_fps:.1f}",
                    (25, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 128),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    f"Latency: {inference_latency_ms:.1f}ms",
                    (170, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 220, 255),
                    2,
                    cv2.LINE_AA,
                )

                # 2. Hands detected count
                cv2.putText(
                    frame,
                    f"Hands Tracked: {hand_count}",
                    (25, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 220, 255),
                    2,
                    cv2.LINE_AA,
                )

                # 3. Recognized Gesture
                cv2.putText(
                    frame,
                    f"Gesture: {active_gesture}",
                    (25, 115),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
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
                    (25, 155),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    conf_color,
                    2,
                    cv2.LINE_AA,
                )

                # 5. Controls instructions
                cv2.putText(
                    frame,
                    "Press 'Q' to Exit",
                    (25, 195),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (180, 180, 180),
                    1,
                    cv2.LINE_AA,
                )

                # Encode and stream binary JPEG frame to FastAPI /ws/video
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                video_publisher.send_frame(buffer.tobytes())

                # Display the live webcam window
                cv2.imshow("GestureForge Hand Detection", frame)

                # Check for 'Q' or 'q' key to exit cleanly
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    print("\nExit key pressed. Closing...")
                    break

        finally:
            # Clean up and release hardware resources
            video_publisher.stop()
            cap.release()
            cv2.destroyAllWindows()
            print("Webcam released and OpenCV windows destroyed cleanly.")


if __name__ == "__main__":
    run_hand_detection()
