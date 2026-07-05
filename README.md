# MCP Workspace Assistant

Local AI assistant for developers. Read local project files, search code, summarize codebases, and (later) call GitHub tools — powered by FastAPI, LangGraph, and React.

## Project structure

```
mcp-workspace-assistant/
├── backend/           # FastAPI + LangGraph agent
├── frontend/          # React + TypeScript + Tailwind
├── sample-workspace/  # Demo project for file tools
└── README.md
```

## Prerequisites

- **Node.js** 18+
- **Python** 3.11+

## Quick start

### 1. Environment

```bash
cp .env.example .env
```

Edit `.env` and set `WORKSPACE_PATH` (default: `./sample-workspace`).

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Frontend

From the repo root:

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Scripts (repo root)

| Command               | Description                   |
| --------------------- | ----------------------------- |
| `npm run dev`         | Start frontend dev server     |
| `npm run dev:backend` | Start FastAPI with reload     |
| `npm run build`       | Build frontend for production |

## Status

- [x] **Step 1** — Monorepo scaffold (FastAPI + React)
- [x] **Step 2** — Workspace config & settings API
- [x] **Step 3** — Path safety layer
- [ ] Step 4 — Filesystem tools
- [ ] Step 5–6 — LangGraph agent
- [ ] Step 7–9 — Chat UI
- [ ] Step 10–11 — MCP & GitHub tools
