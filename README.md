# govManage — Policy Analyst

> AI-powered Governance, Risk & Compliance (GRC) platform with multi-agent policy generation, real-time risk assessment, and compliance reporting.

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.13+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (`pip install uv`)
- MongoDB Atlas account (or local MongoDB)

### 1. Clone & configure environment

```bash
git clone <repo-url>
cd govManage-policy-analyst

# Copy environment template and fill in your values
cp .env.example .env
```

Edit `.env` with your API keys and database credentials.

### 2. Install Python dependencies

```bash
uv sync
# or
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Launch all services

**Windows:**
```bat
launch.bat
```

**Linux/macOS (manual):**
```bash
# Terminal 1 — Backend API
FLASK_DEBUG=1 python app.py

# Terminal 2–9 — Micro-agents
python agents_micro/orchestrator/main.py
python agents_micro/policy_analyst/main.py
python agents_micro/compliance/main.py
python agents_micro/risk_assessment/main.py
python agents_micro/decision_engine/main.py
python agents_micro/audit/main.py
python agents_micro/reporting/main.py
python agents_micro/feedback/main.py
python agents_micro/persistence/main.py

# Terminal 10 — Frontend
cd frontend && npm run dev
```

Services:
- **Backend API**: `http://localhost:5000`
- **Frontend**: `http://localhost:5173`

---

## Running Tests

```bash
pytest tests/ -v --tb=short
```

---

## Production Deployment

### Option A — Gunicorn (Linux server)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (do NOT use .env in production)
export GROQ_API_KEY=...
export MONGO_URI=...
export CORS_ORIGINS=https://your-domain.com
export FLASK_DEBUG=0

# Start backend
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000 --timeout 120

# Build and serve frontend
cd frontend
npm run build
# Serve /dist with Nginx or upload to Vercel/Netlify
```

### Option B — Railway / Render / Heroku (PaaS)

1. Set all environment variables in the platform dashboard
2. Set `CORS_ORIGINS` to your frontend's production URL
3. The `Procfile` will start Gunicorn automatically

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Frontend (React + Vite)                                 │
│  - Policy Hub, Generator, Library, Reports, Chat        │
└───────────────────┬─────────────────────────────────────┘
                    │ REST API (JSON)
┌───────────────────▼─────────────────────────────────────┐
│ Flask Backend (app.py)                                  │
│  - Risk Engine (TVI scoring, rule evaluation)           │
│  - Compliance mapping (ISO 27001, NIST, GDPR, OECD)    │
│  - Policy generation, PDF export                        │
│  - ChromaDB semantic search                             │
│  - APScheduler weekly email reports                     │
└──────────┬──────────────────────────────────────────────┘
           │ File-based queue (shared_queues/)
┌──────────▼──────────────────────────────────────────────┐
│ Micro-Agent Pipeline                                    │
│  Orchestrator → PolicyAnalyst → Compliance →           │
│  RiskAssessment → DecisionEngine → Audit →             │
│  Reporting → Feedback → Persistence                     │
└──────────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────┐
│ Data Layer                                              │
│  MongoDB Atlas  |  ChromaDB (local vector store)       │
└─────────────────────────────────────────────────────────┘
```

---

## Key Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | LLM API key (Groq) |
| `MONGO_URI` | Yes | MongoDB connection string |
| `MONGO_DB_NAME` | No | Database name (default: `govmanage`) |
| `CORS_ORIGINS` | Yes (prod) | Comma-separated allowed origins |
| `FLASK_DEBUG` | No | `1` for dev, `0` for prod |
| `SMTP_*` | No | Email settings for weekly reports |
| `TAVILY_API_KEY` | No | Web intelligence (optional) |
| `FIRECRAWL_API_KEY` | No | Web crawling (optional) |

---

## Project Structure

```
govManage-policy-analyst/
├── app.py              # Main Flask application (3000+ lines)
├── wsgi.py             # Gunicorn WSGI entrypoint
├── database.py         # MongoDB data layer
├── scheduler.py        # APScheduler weekly email job
├── email_service.py    # Email dispatch
├── crawler.py          # Web crawler for regulatory sources
├── vector_store.py     # ChromaDB wrapper
├── file_parser.py      # PDF/DOCX text extraction
├── report_pdf.py       # PDF report generation
├── agents_micro/       # 9 micro-agent processes
│   ├── orchestrator/
│   ├── policy_analyst/
│   ├── compliance/
│   ├── risk_assessment/
│   ├── decision_engine/
│   ├── audit/
│   ├── reporting/
│   ├── feedback/
│   └── persistence/
├── frontend/           # React + Vite + Tailwind
│   └── src/
├── tests/              # Pytest test suite
├── requirements.txt
├── pyproject.toml
├── Procfile
└── .env.example
```
