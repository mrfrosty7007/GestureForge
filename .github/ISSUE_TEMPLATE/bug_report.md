---
name: Bug Report
about: Create a structured report to help debug and fix an issue in GestureForge
title: "[BUG] <concise summary>"
labels: ["bug"]
assignees: ""
---

### 🐛 Bug Description
A clear and concise description of the defect encountered.

---

### 🔁 Exact Steps to Reproduce
1. **Pre-conditions**: (e.g. clean virtual environment, Node dependencies installed)
2. **Terminal 1 (Backend)**: Run `uv run uvicorn app:app --reload`
3. **Terminal 2 (Frontend)**: Run `pnpm run dev` or `npm run dev`
4. **Action**: Open browser at `http://localhost:5173` and click [...]
5. **Observed Error**: (e.g. status card shows offline, console shows error 500)

---

### 🎯 Expected Behavior
A clear description of what should have occurred under nominal conditions.

---

### 🔍 Error Logs & Stack Trace
```log
# Paste full terminal traceback, browser DevTools console output, or network response here:

```

---

### 💻 System & Runtime Environment
- **Operating System**: Windows 11 / macOS Sequoia / Ubuntu 22.04
- **Python Version**: `python --version` (e.g., Python 3.11.x)
- **Node.js Version**: `node --version` (e.g., v20.x / v22.x)
- **Package Manager Used**: `uv` / `pip` / `pnpm` / `npm`
- **Browser**: Chrome / Firefox / Safari / Edge (with version)

---

### 👥 Module & Team Ownership
- [ ] Backend & Gateway (Member 1)
- [ ] Computer Vision & MediaPipe (Member 2)
- [ ] ML Model & Datasets (Member 3)
- [ ] Frontend UI & HUD (Member 4)
- [ ] CI/CD & Tooling
