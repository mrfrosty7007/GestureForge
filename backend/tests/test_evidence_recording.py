"""Unit Tests for Evidence Recording Mode in GestureForge.

Validates:
- RecordingSession state management and variable initialization
- start_recording creates timestamped directory and activates session
- log_event filtering: threshold, invalid gestures, duplicate spam prevention, 500ms persistence
- save_session generation of session.json, session.csv, and summary.json
- stop_recording auto-save behavior
- _draw_recording_hud and _draw_shortcut_hints rendering safety
"""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

# Ensure ai-model directory is in python path
_ai_model_path = str(Path(__file__).resolve().parent.parent.parent / "ai-model")
if _ai_model_path not in sys.path:
    sys.path.insert(0, _ai_model_path)

from hand_detection import (  # noqa: E402
    RecordingSession,
    _draw_recording_hud,
    _draw_shortcut_hints,
    _format_relative_time,
    log_event,
    save_session,
    start_recording,
    stop_recording,
)


def test_recording_session_state_variables():
    """Verify all required state variables exist and have correct initial values."""
    session = RecordingSession()
    assert hasattr(session, "recording")
    assert hasattr(session, "record_start_time")
    assert hasattr(session, "session_events")
    assert hasattr(session, "last_logged_gesture")
    assert hasattr(session, "last_log_time")
    assert hasattr(session, "gesture_counter")
    assert hasattr(session, "confidence_samples")
    assert hasattr(session, "fps_samples")

    assert session.recording is False
    assert session.record_start_time is None
    assert session.session_events == []
    assert session.last_logged_gesture is None
    assert session.last_log_time == 0.0
    assert len(session.gesture_counter) == 0
    assert session.confidence_samples == []
    assert session.fps_samples == []


def test_format_relative_time():
    """Verify relative time formatting produces HH:MM:SS.mmm format."""
    assert _format_relative_time(0.0) == "00:00:00.000"
    assert _format_relative_time(1.240) == "00:00:01.240"
    assert _format_relative_time(65.500) == "00:01:05.500"
    assert _format_relative_time(3661.123) == "01:01:01.123"


def test_start_and_stop_recording(tmp_path: Path):
    """Verify starting and stopping a recording session creates files and updates state."""
    session = RecordingSession(output_root=tmp_path)
    started = start_recording(session, output_root=tmp_path)

    assert started.recording is True
    assert started.record_start_time is not None
    assert started.session_folder is not None
    assert started.session_folder.exists()

    saved_dir = stop_recording(started)
    assert started.recording is False
    assert saved_dir is not None
    assert (saved_dir / "session.json").exists()
    assert (saved_dir / "session.csv").exists()
    assert (saved_dir / "summary.json").exists()


def test_log_event_filtering_and_persistence(tmp_path: Path):
    """Verify log_event filters invalid events, blocks duplicate spam, and handles persistence."""
    session = RecordingSession(output_root=tmp_path)
    start_recording(session, output_root=tmp_path)

    # 1. Reject invalid gestures
    assert not log_event(session, gesture="", confidence=90.0)
    assert not log_event(session, gesture="None", confidence=90.0)
    assert not log_event(session, gesture="Unknown", confidence=90.0)

    # 2. Reject below-threshold confidence
    assert not log_event(session, gesture="Open Palm", confidence=50.0, threshold=55.0)

    # 3. Log initial valid event
    assert log_event(
        session, gesture="Open Palm", confidence=98.7, frame_number=1, fps=30.0
    )
    assert len(session.session_events) == 1
    assert session.last_logged_gesture == "Open Palm"
    assert session.gesture_counter["Open Palm"] == 1

    # 4. Immediate duplicate frame within 500 ms must NOT log (duplicate spam prevention)
    assert not log_event(
        session, gesture="Open Palm", confidence=99.0, frame_number=2, fps=30.0
    )
    assert len(session.session_events) == 1

    # 5. Gesture change logs immediately even if < 500 ms
    assert log_event(
        session, gesture="Closed Fist", confidence=96.5, frame_number=3, fps=29.5
    )
    assert len(session.session_events) == 2
    assert session.last_logged_gesture == "Closed Fist"
    assert session.gesture_counter["Closed Fist"] == 1

    # 6. Persistence: same gesture logs after simulated 500 ms
    session.last_log_time = time.perf_counter() - 0.6  # simulate 600 ms elapsed
    assert log_event(
        session, gesture="Closed Fist", confidence=97.0, frame_number=20, fps=30.0
    )
    assert len(session.session_events) == 3
    assert session.gesture_counter["Closed Fist"] == 2


def test_session_file_formats(tmp_path: Path):
    """Verify session.json, session.csv, and summary.json adhere strictly to specifications."""
    session = RecordingSession(output_root=tmp_path)
    start_recording(session, output_root=tmp_path)

    log_event(session, gesture="Open Palm", confidence=98.7, frame_number=142, fps=29.5)
    saved_path = save_session(session)
    assert saved_path is not None
    folder = session.session_folder
    assert folder is not None

    # Check session.json
    session_json_path = folder / "session.json"
    with open(session_json_path, encoding="utf-8") as f:
        events = json.load(f)
    assert isinstance(events, list)
    assert len(events) == 1
    ev = events[0]
    assert ev["gesture"] == "Open Palm"
    assert ev["confidence"] == 98.7
    assert ev["frame"] == 142
    assert "timestamp" in ev

    # Check session.csv
    session_csv_path = folder / "session.csv"
    with open(session_csv_path, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    assert reader[0] == ["Time", "Gesture", "Confidence", "Frame"]
    assert len(reader) == 2
    row = reader[1]
    assert row[1] == "Open Palm"
    assert row[2] == "98.7"
    assert row[3] == "142"

    # Check summary.json
    summary_json_path = folder / "summary.json"
    with open(summary_json_path, encoding="utf-8") as f:
        summary = json.load(f)
    assert "session duration" in summary
    assert "total events" in summary
    assert summary["total events"] == 1
    assert summary["gesture counts"]["Open Palm"] == 1
    assert summary["average confidence"] == 98.7
    assert summary["average FPS"] == 29.5


def test_hud_rendering_safety(tmp_path: Path):
    """Verify HUD overlays render safely onto canvas without errors."""
    session = RecordingSession(output_root=tmp_path)
    start_recording(session, output_root=tmp_path)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Should not raise exception
    _draw_recording_hud(
        frame, session, current_gesture="Open Palm", current_confidence=98.7
    )
    _draw_shortcut_hints(frame, is_recording=True)
    _draw_shortcut_hints(frame, is_recording=False)

    stop_recording(session)


def test_sequential_recording_indexing(tmp_path: Path):
    """Verify recording sessions are sequentially ordered (recording_1, recording_2, recording_3)."""
    # First recording
    s1 = RecordingSession(output_root=tmp_path)
    start_recording(s1, output_root=tmp_path)
    assert s1.session_folder is not None
    assert s1.session_folder.name.startswith("recording_1_")
    stop_recording(s1)

    # Second recording
    s2 = RecordingSession(output_root=tmp_path)
    start_recording(s2, output_root=tmp_path)
    assert s2.session_folder is not None
    assert s2.session_folder.name.startswith("recording_2_")
    stop_recording(s2)

    # Third recording
    s3 = RecordingSession(output_root=tmp_path)
    start_recording(s3, output_root=tmp_path)
    assert s3.session_folder is not None
    assert s3.session_folder.name.startswith("recording_3_")
    stop_recording(s3)
