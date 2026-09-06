# GestureForge Backend

FastAPI backend for GestureForge. Handles webcam frame ingestion, hand landmark detection, and real-time gesture classification.

## 🚀 Setup & Execution

### 1. Activate the Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI Server

```bash
uvicorn main:app --reload
```

- **API Base URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
