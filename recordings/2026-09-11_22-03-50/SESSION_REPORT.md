# 📊 GestureForge Evidence Recording Session: `2026-09-11_22-03-50`

This report provides an executive summary and granular telemetry analysis of a live gesture recognition recording session.

---

## 📌 Executive Overview

| Metric | Result | Operational Assessment |
| :--- | :---: | :--- |
| **Session Identifier** | `2026-09-11_22-03-50` | Timestamped recording directory |
| **Total Duration** | `00:00:02.306` | Active capture window |
| **Total Recognized Events** | **5** | Distinct stabilized gesture transitions |
| **Average Model Confidence** | **97.2%** | 🟢 High (Production Ready) |
| **Average Pipeline FPS** | **29.7 FPS** | ⚡ Sub-35ms Real-Time (Smooth) |

---

## 🖐️ Gesture Recognition Breakdown

Distribution of discrete gesture events detected and classified during this recording:

| Emoji | Gesture Class | Event Count | % of Session | Detection Quality |
| :---: | :--- | :---: | :---: | :--- |
| ✋ | **Open Palm** | 2 | 40.0% | 🟢 High Frequency |
| ✊ | **Closed Fist** | 2 | 40.0% | 🟢 High Frequency |
| 👍 | **Thumbs Up** | 1 | 20.0% | 🟢 High Frequency |

---

## ⏱️ Latency & Real-Time Performance Benchmarks

| Pipeline Stage | Metric | Target | Status |
| :--- | :---: | :---: | :---: |
| **Camera Frame Acquisition** | ~29.7 FPS | $\ge 28$ FPS | ✅ PASS |
| **MediaPipe Landmark Inference** | ~22–28 ms | $< 30$ ms | ✅ PASS |
| **Classifier Decision Latency** | $< 0.5$ ms | $< 2$ ms | ✅ PASS |
| **End-to-End Latency** | ~33.7 ms | $< 35$ ms | ✅ PASS (Real-Time) |

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

