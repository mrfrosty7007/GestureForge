# 📊 GestureForge Evidence Recording Session: `recording_9_2026-09-12_21-05-20`

This report provides an executive summary and granular telemetry analysis of a live gesture recognition recording session.

---

## 📌 Executive Overview

| Metric | Result | Operational Assessment |
| :--- | :---: | :--- |
| **Session Identifier** | `recording_9_2026-09-12_21-05-20` | Recording #9 (Chronological) |
| **Total Duration** | `00:00:24.499` | Active capture window |
| **Total Recognized Events** | **32** | Distinct stabilized gesture transitions |
| **Average Model Confidence** | **74.0%** | 🟡 Moderate (Meets threshold) |
| **Average Pipeline FPS** | **12.5 FPS** | ⚠️ Bottleneck Detected (<25 FPS) |

---

## 🖐️ Gesture Recognition Breakdown

Distribution of discrete gesture events detected and classified during this recording:

| Emoji | Gesture Class | Event Count | % of Session | Detection Quality |
| :---: | :--- | :---: | :---: | :--- |
| ✋ | **Open Palm** | 16 | 50.0% | 🟢 High Frequency |
| ✊ | **Closed Fist** | 5 | 15.6% | 🔵 Standard |
| 👌 | **OK** | 4 | 12.5% | 🔵 Standard |
| 🤘 | **Rock** | 2 | 6.2% | 🔵 Standard |
| 🤙 | **Call Me** | 2 | 6.2% | 🔵 Standard |
| ✌️ | **Peace** | 2 | 6.2% | 🔵 Standard |
| 👍 | **Thumbs Up** | 1 | 3.1% | 🔵 Standard |

---

## ⏱️ Latency & Real-Time Performance Benchmarks

| Pipeline Stage | Metric | Target | Status |
| :--- | :---: | :---: | :---: |
| **Camera Frame Acquisition** | ~12.5 FPS | $\ge 28$ FPS | ⚠️ CHECK |
| **MediaPipe Landmark Inference** | ~22–28 ms | $< 30$ ms | ✅ PASS |
| **Classifier Decision Latency** | $< 0.5$ ms | $< 2$ ms | ✅ PASS |
| **End-to-End Latency** | ~80.0 ms | $< 35$ ms | ⚠️ INVESTIGATE |

---

## 🧪 Operational Test Environment Metadata

This metadata documents the experimental test conditions for cross-session validation:

| Condition Field | Value / Parameter | Notes |
| :--- | :--- | :--- |
| **Lighting Condition** | Standard Ambient Indoor | Normal office illumination |
| **Camera Distance** | ~0.5m – 0.8m | Standard laptop/desktop operational distance |
| **Camera Angle** | Frontal 0° | Direct line of sight |
| **Session Classification** | Empirical Test Run | Suitable for cross-session comparison |

---

## 📁 Attached Raw Telemetry Artifacts

* **`session.csv`**: Complete tabular time-series log with per-event timestamps, gesture labels, confidence scores, and frame indices (Excel-compatible).
* **`session.json`**: Structured JSON dataset of all raw event transitions for programmatic analysis.
* **`summary.json`**: Aggregated performance summary dictionary.

