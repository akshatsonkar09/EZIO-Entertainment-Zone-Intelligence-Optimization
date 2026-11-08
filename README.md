# 🎬 Project Black Knight — Production Application & Deployment Repository

An AI-powered Entertainment Discovery & Cross-Domain Retrieval Engine connecting **Movies**, **Anime**, and **Books** based on semantic taste profiling, lexical matching, and neural reranking.

---

## 🏗 Architecture Overview

- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS SPA.
- **Backend API:** FastAPI RESTful service with async endpoints (`/api/search`, `/api/items/{id}`, `/api/random`, `/api/metadata/categories`, `/api/browse`).
- **Retrieval Pipeline:**
  - **Dense Semantic Retrieval:** `SentenceTransformer` (`all-MiniLM-L6-v2`) querying persistent ChromaDB vector collections.
  - **Lexical Retrieval:** BM25Okapi over rich document tags.
  - **Fusion:** Reciprocal Rank Fusion (RRF) with deterministic tie-breaking.
  - **Neural Reranking:** CrossEncoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
  - **Metadata Hard Filtering:** Exact boundary enforcement for genres, years, authors, and directors.
  - **Query Understanding:** Zero-shot query parser via Groq LLM with resilient heuristic fallback.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ (Python 3.13 recommended)
- Node.js 20+ and npm

### 2. Environment Setup
Copy the environment template and insert your API keys:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Backend Setup & Run
Create and activate a virtual environment, install dependencies, bootstrap the vector database, and launch FastAPI:

```bash
# Create virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Or on Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Bootstrap ChromaDB vector index from precomputed embeddings (takes ~18s)
python scripts/build_chroma_index.py

# Launch FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend Swagger documentation will be available at: `http://localhost:8000/docs`

### 4. Frontend Setup & Run
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```

Frontend web app will be available at: `http://localhost:5173`

---

## 🧪 Testing

Project Black Knight includes a comprehensive 139-test regression and parity test suite:

```bash
# Run backend and retrieval test suite
pytest tests

# Run frontend production build & typecheck
cd frontend
npm run build
```

---

## 🌐 Production Deployment

### Frontend (Vercel)
1. Import repository on [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Set Framework to `Vite`.
4. Configure Environment Variable:
   - `VITE_API_BASE_URL`: URL of deployed FastAPI backend (e.g., `https://your-backend.onrender.com`).
5. Deploy.

### Backend (Render / Docker)
Deploy as a Docker Web Service on [Render](https://render.com) or [Railway](https://railway.app):
- Python runtime or Dockerfile.
- Recommended RAM: 2 GB (standard plan).
- Start command:
  ```bash
  python scripts/build_chroma_index.py && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```
- Environment variables:
  - `GROQ_API_KEY`: Your Groq API key.

