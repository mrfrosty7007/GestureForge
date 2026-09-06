# GestureForge Dataset Repository

This directory manages the raw and processed training data for hand gesture recognition.

## 📂 Directory Layout

```
dataset/
├── raw/                    # Raw webcam frames, video clips (.mp4, .avi)
│   └── .gitkeep
├── processed/              # Extracted normalized landmark coordinates (.csv, .npy)
│   └── .gitkeep
└── README.md               # Dataset taxonomy, collection instructions, and schema
```

> [!NOTE]
> All binary video files (`*.mp4`, `*.avi`, `*.mov`) and large serialized arrays (`*.npy`, `*.npz`) in this folder are excluded from Git version control via `.gitignore`.

---

## 🎯 Target Gesture Classes (Phase 1 & 2)

| Class ID | Gesture Label | Description | Landmark Key Characteristics |
|:---|:---|:---|:---|
| `0` | **Thumbs Up** | Thumb extended vertically upward, all 4 fingers curled into fist | Thumb TIP higher than IP, MCP; Fingers closed |
| `1` | **Thumbs Down** | Thumb pointed downward, all 4 fingers curled into fist | Thumb TIP lower than IP, MCP; Fingers closed |
| `2` | **Peace / Victory** | Index and middle fingers extended in 'V' shape, ring/pinky curled | Index & Middle PIP-TIP extended; Ring & Pinky closed |
| `3` | **Open Palm** | All 5 fingers extended outward, hand facing camera | All 5 finger tips extended beyond PIP joints |
| `4` | **Fist** | All fingers curled tightly into palm, thumb over fingers | All tips curled towards wrist/palm center |
| `5` | **Pointing Up** | Index finger extended upward, other 3 fingers and thumb curled | Only index finger tip extended |
| `6` | **OK Sign** | Thumb tip touching index finger tip forming circle; 3 fingers extended | Thumb TIP distance to Index TIP < threshold |
| `7` | **Rock On** | Index and pinky fingers extended, middle and ring curled | Index & Pinky extended; Middle & Ring curled |

---

## 📊 Landmark Coordinate Format (`dataset/processed/gestures.csv`)

Each row represents one recorded frame's hand landmark detection:

```csv
label,wrist_x,wrist_y,wrist_z,thumb_cmc_x,thumb_cmc_y,thumb_cmc_z,...,pinky_tip_x,pinky_tip_y,pinky_tip_z
0,0.512,0.823,-0.002,0.485,0.762,-0.015,...,0.621,0.510,0.045
```

- Total columns: `1 (label) + 21 landmarks * 3 coordinates (x, y, z) = 64 columns`.
- All `(x, y, z)` values are normalized relative to image width/height and wrist anchor.
