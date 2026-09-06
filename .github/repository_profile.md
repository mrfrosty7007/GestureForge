# 📋 GestureForge GitHub Repository Profile & Settings Checklist

This checklist documents the recommended GitHub configuration settings to optimize GestureForge as a flagship public repository for university club selection and portfolio presentation.

---

## 📌 1. Repository Description & About Section

Configure via the **"About"** section (gear icon on the right sidebar of the repo home):

- **Description**:
  > Real-time AI-powered hand gesture recognition system built with MediaPipe, FastAPI, and React.
- **Website**:
  > `http://localhost:5173` *(or production deployment URL once hosted)*
- **Include in home page**:
  - [x] Releases
  - [x] Packages
  - [x] Environments

---

## 🏷️ 2. Recommended GitHub Topics (Tags)

Paste the following comma-separated tags into the **Topics** field:

```
computer-vision, gesture-recognition, mediapipe, fastapi, react, opencv, machine-learning, hackathon
```

| Topic | Purpose |
|:---|:---|
| `computer-vision` | Categorizes repo under CV exploration |
| `gesture-recognition` | Core project domain identifier |
| `mediapipe` | Primary perception engine keyword |
| `fastapi` | Modern asynchronous Python backend framework |
| `react` | Modern frontend reactive HUD |
| `opencv` | Frame ingestion and computer vision processing |
| `machine-learning` | Landmark classification keyword |
| `hackathon` | Highlights hackathon/club team engineering |

---

## 👁️ 3. Repository Visibility & Pinned Recommendation

- **Visibility**: **Public** (Ensure all reviewers and university club committee members can view without authentication).
- **Suggested Pinned Repository**:
  - In your GitHub Profile (**Customize your pins**):
  - **Unpin**: `abode-adobe_but_free-`
  - **Pin**: `GestureForge` as **Pin #1 (Top Flagship Position)**

---

## 🖼️ 4. Social Preview Card

- **Settings -> General -> Features -> Social preview**:
- Upload the social preview banner specified in [`assets/social_preview.md`](../assets/social_preview.md).
- Preview vector placeholder available at [`assets/logo_placeholder.svg`](../assets/logo_placeholder.svg).

---

## ⚙️ 5. GitHub Repository Features & Tabs

- [x] **Issues**: Enabled (using templates in `.github/ISSUE_TEMPLATE/`)
- [x] **Pull Requests**: Enabled (using `.github/PULL_REQUEST_TEMPLATE.md`)
- [x] **Actions**: Enabled (workflow active at `.github/workflows/ci.yml`)
- [x] **Discussions**: Enabled (optional for community / team Q&A)
- [ ] **Wikis**: Disabled (all documentation is centralized in version-controlled `docs/`)
- [x] **Projects**: Enabled (for Kanban task tracking)
