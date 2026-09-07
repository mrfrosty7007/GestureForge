# GestureForge Copilot Instructions

## Project shape

GestureForge is a local real-time hand-gesture pipeline with three cooperating parts:

- `ai-model/` owns webcam capture, MediaPipe Hands landmark extraction, gesture classification, telemetry generation, and JPEG frame publishing.
- `backend/` is the FastAPI gateway. It starts the headless `AIWorker` during the application lifespan, stores the latest prediction in thread-safe memory, and broadcasts telemetry and video to clients.
- `frontend/` is a React/Vite operations dashboard. It consumes `/ws/telemetry` for gesture and hardware data and `/ws/video` for binary JPEG frames; it does not request browser camera access.

The normal flow is webcam -> MediaPipe (up to two hands, 21 landmarks each) -> hybrid classifier -> FastAPI callbacks/storage -> React HUD. The backend also retains REST compatibility through `POST /gesture` and `GET /gesture/latest`. The video stream is intentionally coalesced to the newest frame so slow clients do not build a stale queue.

The root Python project is managed by `uv` and `uv.lock`; frontend dependencies are managed separately by `pnpm` and `frontend/pnpm-lock.yaml`. Use the root environment for backend and AI commands so the configured `pythonpath` can resolve `backend`, `ai-model`, and `ai-model/scripts`.

## Setup and commands

Prerequisites are Python 3.11+, Node.js 20+, `uv`, and `pnpm`.

```bash
uv sync
pnpm --dir frontend install
```

Copy `backend/.env.example` to `backend/.env` for local overrides. Do not commit `.env` files.

### Run the services

Start the backend before the camera worker or dashboard:

```bash
uv run uvicorn backend.main:app --reload
pnpm --dir frontend dev
```

The backend is at `http://127.0.0.1:8000` (`/health`, `/docs`); Vite is at `http://localhost:5173`. The standalone AI command is headless by default. Use `python ai-model/hand_detection.py --preview` only when a local OpenCV window is needed; `Q` exits preview mode.

The backend owns the single headless AI worker and webcam in the normal integrated flow. Use the standalone AI script only for explicit preview/debug work, and stop or disable the backend worker first to avoid duplicate camera ownership.

The dashboard uses `WS /ws/video` as the primary latest-frame video stream and `WS /ws/telemetry` for separate JSON telemetry. `GET /video/feed` is retained as a documented MJPEG fallback only.

Set `GESTUREFORGE_DISABLE_AI_WORKER=1` when starting the backend to prevent its lifespan from opening a physical camera (useful for API/UI tests or machines without a webcam).

### Backend quality and tests

These are the checks used by CI:

```bash
uv run ruff check .
uv run black --check backend ai-model
uv run pytest
```

Run one test module, test function, or keyword selection with pytest selectors:

```bash
uv run pytest backend/tests/test_health.py
uv run pytest backend/tests/test_health.py::test_post_gesture_and_retrieve_latest
uv run pytest -k "websocket and video"
```

### Frontend quality, build, and E2E tests

Run frontend commands from the root with `--dir`, or from `frontend/` after changing directory:

```bash
pnpm --dir frontend run format:check
pnpm --dir frontend run lint
pnpm --dir frontend run build
pnpm --dir frontend run test:e2e
```

Playwright starts the FastAPI backend and Vite dev server from `frontend/playwright.config.js`, installs/uses Chromium, and uses fake media flags. Run a single file or test title with:

```bash
pnpm --dir frontend exec playwright test tests/e2e/dashboard.spec.js
pnpm --dir frontend exec playwright test tests/e2e/gestures.spec.js -g "dual-hand updates"
```

## Key implementation conventions

- Keep backend imports package-qualified (`backend.main`, `backend.routes`, etc.) when running from the repository root. The AI modules are deliberately made importable through the pytest `pythonpath` and the small `sys.path` bridges in `ai-model/`.
- Pydantic models in `backend/models.py` are the protocol boundary. `GesturePrediction` normalizes both the current multi-hand `hands` payload and the legacy `gesture`/`confidence` shape; telemetry-only payloads represent a heartbeat with zero hands. Preserve this compatibility when changing API payloads.
- `backend.storage.storage`, `backend.routes.manager`, `backend.routes.video_manager`, and `backend.worker.ai_worker` are process-local singletons. Tests explicitly clear their state; new tests should do the same rather than relying on test order.
- FastAPI lifespan callbacks connect worker-thread events to the async WebSocket managers with `asyncio.run_coroutine_threadsafe`. Worker callbacks must remain non-blocking and should not directly await or manipulate the event loop.
- `/ws/telemetry` sends the current state immediately, then accepts `ping` and replies `pong`. `/ws/video` carries binary JPEG frames and also accepts `ping`, `frame`, and `refresh`. Keep stale-client cleanup and frame coalescing behavior intact.
- The worker is headless by default and owns camera acquisition/retry, MediaPipe processing, status transitions (`active`, `degraded`, `offline`), telemetry, and stream throttling. GUI calls are only valid in `--preview` mode. Gesture dispatch is debounced on state changes/cooldowns, with heartbeat payloads when no hands are detected.
- `GestureClassifier` first uses `ai-model/models/gesture_model.joblib` on wrist-relative, scale-normalized 63-value landmark features. Low-confidence, missing, or invalid models fall back to geometric rules. Classification has two-frame hysteresis independently per `hand_id`; preserve that smoothing when modifying gesture rules.
- Frontend state is driven by WebSocket messages in `frontend/src/App.jsx`. It keeps a REST `/gesture/latest` fallback for telemetry, reconnects automatically, and maintains only the latest video frame for canvas rendering. Do not reintroduce `getUserMedia` into the browser dashboard; camera access belongs to the Python worker.
- Match the configured formatters: Python uses Ruff/Black with 88 columns; JavaScript/JSX uses Prettier with semicolons, single quotes, two-space indentation, ES5 trailing commas, and 100-column print width. ESLint warnings are currently allowed, but errors fail the lint command.
- Dataset preprocessing lives in `ai-model/scripts/`; processed features must retain 21 landmarks × 3 coordinates and gesture labels expected by the serialized model. Large/raw dataset artifacts are intentionally excluded from normal Git tracking.

## API and UI integration points

When changing a telemetry field or gesture representation, update the Pydantic schema, both backend broadcast paths (REST ingestion and in-process worker dispatch), the frontend message handling, and the relevant backend/Playwright tests together. The primary browser-visible endpoints are:

- `GET /health`
- `POST /gesture`
- `GET /gesture/latest`
- `WS /ws/telemetry`
- `WS /ws/video`
- `GET /video/feed`

## Permanent project rules

- Never search outside the current Git repository.
- Preserve the existing MJPEG video pipeline and separate WebSocket telemetry pipeline.
- Never replace latest-frame buffering with queued frames.
- Always read affected files before proposing edits.
- For UI changes, prefer Playwright validation before claiming success.
- Never commit automatically unless explicitly instructed.
- At the end of every completed task, always provide:
  - Changes made
  - Files modified
  - Tests run and results
  - Git diff summary
  - Commit hash
  - Remaining risks or follow-up work

## Git Workflow

- Never switch branches unless instructed.
- Never merge branches automatically.
- Never rewrite Git history.
- Never modify unrelated files.

## Performance Rules

GestureForge prioritizes latency over throughput.

Always prefer:

- latest-frame replacement
- frame dropping over queue growth
- non-blocking async operations
- browser rendering synchronized to the display refresh rate

Never introduce:

- frame queues
- blocking sleeps in request handlers
- duplicate camera ownership

## AI Worker Rules

The headless AI worker is the single owner of the webcam.

Frontend must consume streamed frames only.

Never reopen the webcam from React.

## Manual Validation

Before claiming camera-related work is complete, remind the user to verify:

- browser minimize/restore
- rapid hand movement
- dual-hand tracking
- FPS stability
- latency feeling in real time
