"""Real-time Hand Detection and Gesture Recognition using MediaPipe and OpenCV.

Tracks up to 2 hands in real-time, extracts 21 3D landmarks with skeletal
connection lines, classifies hand poses into discrete gestures (Palm, Fist,
Thumbs Up, One Finger, Peace, OK, Rock, Call Me) using geometric rules, and
dispatches detected multi-hand gestures to the GestureForge FastAPI backend.

Operates in headless mode by default (no GUI windows), with an optional
--preview flag for visual debugging.
"""

import collections
import contextlib
import queue
import threading
import time
from collections.abc import Callable
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
    """Dispatches a gesture prediction payload to the FastAPI backend.

    Executed in a non-blocking background thread. Supports multi-hand lists,
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

    def _worker() -> None:
        with contextlib.suppress(requests.exceptions.RequestException):
            requests.post(
                BACKEND_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT_SEC,
            )

    # Launch daemon thread so network I/O never blocks the camera loop
    threading.Thread(target=_worker, daemon=True).start()


class AIWorker:
    """Headless AI background worker running OpenCV and MediaPipe perception.

    Responsibilities:
    - Owns cv2.VideoCapture hardware lifecycle with auto-recovery.
    - Real-time MediaPipe hand landmark tracking and gesture classification.
    - Decoupled frame rates: ~30 FPS camera perception, 10–15 FPS dashboard streaming.
    - Zero GUI/windowing overhead in headless mode (default).
    - In-process thread-safe dispatch or standalone HTTP/WS transmission.
    - Camera health status reporting (active, degraded, offline).
    """

    def __init__(
        self,
        camera_index: int = 0,
        headless: bool = True,
        target_camera_fps: float = 30.0,
        target_stream_fps: float = 15.0,
        on_gesture: Callable[[dict[str, Any]], None] | None = None,
        on_frame: Callable[[bytes], None] | None = None,
    ) -> None:
        self.camera_index = camera_index
        self.headless = headless
        self.target_camera_fps = target_camera_fps
        self.target_stream_fps = target_stream_fps
        self.on_gesture = on_gesture
        self.on_frame = on_frame

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._camera_status: str = "offline"  # "active", "degraded", "offline"
        self._worker_status: str = "stopped"  # "running", "stopped", "failed"
        self._lock = threading.Lock()
        self._last_stream_time: float = 0.0

    def configure(
        self,
        on_gesture: Callable[[dict[str, Any]], None] | None = None,
        on_frame: Callable[[bytes], None] | None = None,
        camera_index: int | None = None,
        headless: bool | None = None,
    ) -> None:
        """Configures or updates worker callbacks and settings."""
        with self._lock:
            if on_gesture is not None:
                self.on_gesture = on_gesture
            if on_frame is not None:
                self.on_frame = on_frame
            if camera_index is not None:
                self.camera_index = camera_index
            if headless is not None:
                self.headless = headless

    @property
    def camera_status(self) -> str:
        """Current camera hardware state: 'active', 'degraded', or 'offline'."""
        return self._camera_status

    @property
    def worker_status(self) -> str:
        """Current worker thread state: 'running', 'stopped', or 'failed'."""
        return self._worker_status

    def is_running(self) -> bool:
        """Returns True if the background worker thread is currently running."""
        return self._worker_status == "running" and bool(
            self._thread and self._thread.is_alive()
        )

    def start(self) -> None:
        """Starts the AI worker on a dedicated daemon background thread."""
        with self._lock:
            if self.is_running():
                return
            self._stop_event.clear()
            self._worker_status = "running"
            self._thread = threading.Thread(
                target=self._run_loop,
                name="GestureForge-AIWorker",
                daemon=True,
            )
            self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        """Stops the AI worker cleanly and releases hardware resources."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        with self._lock:
            self._worker_status = "stopped"
            self._camera_status = "offline"

    def _run_loop(self) -> None:
        """Continuous execution loop owning capture, classification, and streaming."""
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles

        classifier = GestureClassifier()
        video_publisher: VideoFramePublisher | None = None

        # In standalone mode (no in-process on_frame callback), initialize publisher
        if self.on_frame is None:
            video_publisher = VideoFramePublisher()

        prev_perf = time.perf_counter()
        frame_durations: collections.deque[float] = collections.deque(maxlen=20)
        frame_count = 0
        last_sent_hands_state = None
        last_sent_time = 0.0

        try:
            with mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
            ) as hands:
                while not self._stop_event.is_set():
                    # ---------------------------------------------------------
                    # Camera Acquisition & Health Management
                    # ---------------------------------------------------------
                    cap = cv2.VideoCapture(self.camera_index)
                    if not cap.isOpened():
                        self._camera_status = "offline"
                        # Wait before retrying camera acquisition
                        self._stop_event.wait(1.0)
                        continue

                    self._camera_status = "active"

                    try:
                        while not self._stop_event.is_set() and cap.isOpened():
                            loop_start = time.perf_counter()
                            success, frame = cap.read()
                            if not success or frame is None:
                                self._camera_status = "degraded"
                                self._stop_event.wait(0.5)
                                break

                            self._camera_status = "active"
                            frame_count += 1
                            current_time = time.time()

                            # Rolling FPS calculation
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

                            # Horizontal flip for intuitive mirror view
                            frame = cv2.flip(frame, 1)
                            h, w, _ = frame.shape

                            # MediaPipe RGB processing
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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

                            if results.multi_hand_landmarks:
                                hand_count = len(results.multi_hand_landmarks)
                                for hand_idx, hand_landmarks in enumerate(
                                    results.multi_hand_landmarks
                                ):
                                    mp_drawing.draw_landmarks(
                                        frame,
                                        hand_landmarks,
                                        mp_hands.HAND_CONNECTIONS,
                                        mp_drawing_styles.get_default_hand_landmarks_style(),
                                        mp_drawing_styles.get_default_hand_connections_style(),
                                    )

                                    gesture, confidence = classifier.classify(
                                        hand_landmarks, hand_id=hand_idx
                                    )

                                    label = "Unknown"
                                    if results.multi_handedness and hand_idx < len(
                                        results.multi_handedness
                                    ):
                                        c = results.multi_handedness[
                                            hand_idx
                                        ].classification
                                        if c:
                                            label = c[0].label

                                    if gesture in VALID_GESTURES:
                                        detected_hands.append(
                                            {
                                                "id": hand_idx,
                                                "label": label,
                                                "gesture": gesture,
                                                "confidence": confidence,
                                            }
                                        )

                                    if hand_idx == 0:
                                        active_gesture = gesture
                                        active_confidence = confidence

                                    # Per-hand wrist tag
                                    wrist = hand_landmarks.landmark[
                                        GestureClassifier.WRIST
                                    ]
                                    wrist_px = (
                                        int(wrist.x * w),
                                        int(wrist.y * h) + 25,
                                    )
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

                            # -------------------------------------------------
                            # Telemetry & Gesture Dispatch
                            # -------------------------------------------------
                            telemetry_data = {
                                "fps": rolling_fps,
                                "latency_ms": inference_latency_ms,
                                "frame_timestamp": round(current_time, 3),
                                "frame": frame_count,
                                "hand_count": hand_count,
                            }

                            current_hands_state = (
                                tuple(
                                    (h["id"], h["label"], h["gesture"])
                                    for h in detected_hands
                                )
                                if detected_hands
                                else None
                            )

                            should_dispatch = False
                            if detected_hands:
                                hands_changed = (
                                    current_hands_state != last_sent_hands_state
                                )
                                cooldown_expired = (
                                    current_time - last_sent_time
                                ) >= DEBOUNCE_COOLDOWN_SEC
                                if hands_changed or cooldown_expired:
                                    should_dispatch = True
                                    last_sent_hands_state = current_hands_state
                                    last_sent_time = current_time
                            else:
                                last_sent_hands_state = None
                                if (
                                    current_time - last_sent_time
                                ) >= HEARTBEAT_INTERVAL_SEC:
                                    should_dispatch = True
                                    last_sent_time = current_time

                            if should_dispatch:
                                if self.on_gesture:
                                    payload_dict = {
                                        "hands": detected_hands,
                                        "timestamp": int(current_time),
                                        "gesture": active_gesture,
                                        "confidence": active_confidence,
                                        "telemetry": telemetry_data,
                                    }
                                    with contextlib.suppress(Exception):
                                        self.on_gesture(payload_dict)
                                else:
                                    send_gesture_async(
                                        detected_hands, telemetry=telemetry_data
                                    )

                            # -------------------------------------------------
                            # Visual HUD Overlays (for streaming & preview)
                            # -------------------------------------------------
                            cv2.rectangle(frame, (10, 10), (330, 215), (20, 20, 20), -1)
                            cv2.rectangle(frame, (10, 10), (330, 215), (80, 80, 80), 1)

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
                            conf_color = (
                                (0, 255, 0)
                                if active_confidence == "High"
                                else (0, 200, 255)
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
                            cv2.putText(
                                frame,
                                (
                                    "Press 'Q' to Exit"
                                    if not self.headless
                                    else "Headless AI Service"
                                ),
                                (25, 195),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.55,
                                (180, 180, 180),
                                1,
                                cv2.LINE_AA,
                            )

                            # -------------------------------------------------
                            # Throttled Stream Delivery (10–15 FPS)
                            # -------------------------------------------------
                            stream_interval = 1.0 / max(1.0, self.target_stream_fps)
                            if (
                                current_time - self._last_stream_time
                            ) >= stream_interval:
                                _, buffer = cv2.imencode(
                                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                                )
                                frame_bytes = buffer.tobytes()
                                if self.on_frame:
                                    with contextlib.suppress(Exception):
                                        self.on_frame(frame_bytes)
                                elif video_publisher:
                                    video_publisher.send_frame(frame_bytes)
                                self._last_stream_time = current_time

                            # -------------------------------------------------
                            # Display Window Handling (Only in Preview Mode)
                            # -------------------------------------------------
                            if not self.headless:
                                cv2.imshow("GestureForge Hand Detection", frame)
                                key = cv2.waitKey(1) & 0xFF
                                if key in (ord("q"), ord("Q")):
                                    self._stop_event.set()
                                    break
                            else:
                                # Headless pacing to match target camera FPS if needed
                                frame_elapsed = time.perf_counter() - loop_start
                                min_frame_time = 1.0 / max(1.0, self.target_camera_fps)
                                if frame_elapsed < min_frame_time:
                                    sleep_sec = min_frame_time - frame_elapsed
                                    if sleep_sec > 0.002:
                                        self._stop_event.wait(sleep_sec)
                    finally:
                        cap.release()

        except Exception as exc:
            print(f"[AIWorker Error] Unexpected error in worker thread: {exc}")
            self._worker_status = "failed"
        finally:
            if video_publisher:
                video_publisher.stop()
            if not self.headless:
                cv2.destroyAllWindows()
            self._camera_status = "offline"
            if self._worker_status != "failed":
                self._worker_status = "stopped"


def run_hand_detection(
    headless: bool = True, preview: bool = False, camera_index: int = 0
) -> None:
    """Convenience entrypoint for launching the AI worker."""
    worker = AIWorker(
        camera_index=camera_index,
        headless=(not preview) if preview else headless,
    )
    worker.start()
    try:
        while worker.is_running():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()


def main() -> None:
    """CLI entrypoint for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GestureForge Real-Time Hand Detection Service"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open an OpenCV desktop window for visual debugging",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run completely headless without opening any window (default: True)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam device index (default: 0)",
    )
    args = parser.parse_args()

    # --preview takes precedence over --headless
    is_headless = not args.preview

    print("=" * 65)
    print("GestureForge — Real-Time Hand Detection & Gesture Recognition")
    print(
        f"Mode: {'Preview (Desktop Window)' if not is_headless else 'Headless (No GUI Window)'}"
    )
    print(f"Camera Device Index: {args.camera}")
    print("=" * 65)

    run_hand_detection(
        headless=is_headless,
        preview=args.preview,
        camera_index=args.camera,
    )


if __name__ == "__main__":
    main()
