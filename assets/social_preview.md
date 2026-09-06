# 🎨 GestureForge GitHub Social Preview Specification

This document defines the exact visual specification, color palette, typography, and layout for the official **GitHub Social Preview** image (recommended resolution: **1280 × 640 px**, 2:1 aspect ratio, `< 1 MB` PNG/JPEG).

---

## 🎯 Visual Theme & Concept

- **Art Direction**: High-tech Cyberpunk HUD / Deep Space Minimalist.
- **Hero Element**: A glowing neon-cyan holographic human hand with all **21 Google MediaPipe 3D landmark joints** distinctly highlighted with glowing nodes and connecting coordinate vectors.
- **Centerpiece**: The bold typography **GestureForge** with a subtle electric gradient.
- **Tech Stack Badges**: `FastAPI` • `React` • `MediaPipe` • `OpenCV`.

---

## 📐 Layout & Dimensions

| Parameter | Specification |
|:---|:---|
| **Canvas Dimensions** | `1280 × 640 px` (Standard GitHub OpenGraph banner) |
| **Aspect Ratio** | `2:1` |
| **Format** | Optimized PNG or high-quality JPEG (`< 1 MB`) |
| **Safe Margins** | 64px padding on all sides to prevent edge clipping across mobile views |
| **Focal Point** | Left: Cybernetic hand with 21 landmarks; Right: Brand title & stack chips |

---

## 🎨 Color Palette & Hex Tokens

```
Background:
  --bg-deep-space:   #07090e  (Deepest black/blue canvas)
  --bg-grid-overlay: rgba(6, 182, 212, 0.05) (HUD radar grid)

Hand & Vision Elements:
  --hand-cyan-glow:  #06b6d4  (Neon blue MediaPipe hand skeleton)
  --node-accent:     #67e8f9  (3D landmark keypoint dots)
  --wrist-anchor:    #10b981  (Emerald green wrist base coordinate)

Typography & Brand:
  --brand-white:     #ffffff  (Primary bold text)
  --brand-indigo:    #818cf8  (Gradient midtone)
  --text-muted:      #94a3b8  (Subtitle and telemetry indicators)
```

---

## 🖐️ Hand Landmark Structure (21 MediaPipe Nodes)

The hand visualization must show all 21 anatomical landmarks:
1. **Wrist Anchor**: Landmark 0 (green anchor node)
2. **Thumb**: Landmarks 1-4 (CMC, MCP, IP, TIP)
3. **Index Finger**: Landmarks 5-8 (MCP, PIP, DIP, TIP) - pointing upward
4. **Middle Finger**: Landmarks 9-12 (MCP, PIP, DIP, TIP)
5. **Ring Finger**: Landmarks 13-16 (MCP, PIP, DIP, TIP)
6. **Pinky Finger**: Landmarks 17-20 (MCP, PIP, DIP, TIP)

All connected by glowing vector beams with radar distance scanlines.

---

## 🤖 Image Generation Prompt (for DALL-E / Midjourney / Flux)

If generating via an AI image model, use the following tested prompt:

```text
A sleek, ultra-detailed GitHub social preview banner, 1280x640 resolution, 2:1 aspect ratio. 
Dark cyberpunk aesthetic with deep navy and obsidian background (#07090e). 
On the left side: a futuristic holographic wireframe human hand glowing in electric neon cyan and azure blue, showing 21 geometric glowing joint nodes (Google MediaPipe hand tracking style) connected by clean thin laser lines and subtle digital coordinate data. 
On the right side: glowing sleek typography reading "GestureForge" in modern geometric sans-serif font with a cyan-indigo gradient. 
Underneath the title: clean minimalist tech pills reading "FastAPI • React • MediaPipe • OpenCV". 
Subtle isometric HUD grid overlay in the background, cinematic rim lighting, 8k render, minimalist UI design, clean professional open-source flagship showcase.
```

---

## 📤 GitHub Upload Checklist

1. Export final artwork as `social_preview.png` to `assets/`.
2. Navigate to repository: **Settings -> General -> Social preview**.
3. Click **Edit -> Upload an image**.
4. Select `assets/social_preview.png`.
5. Preview link card generation at [opengraph.xyz](https://www.opengraph.xyz).
