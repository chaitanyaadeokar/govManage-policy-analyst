# govManage — AI-Powered GRC Intelligence Platform 🛡️

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![Flask](https://img.shields.io/badge/Flask-Backend-black.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**govManage** is a next-generation Governance, Risk, and Compliance (GRC) platform. It leverages large language models (LLMs), retrieval-augmented generation (RAG), and a multi-agent orchestration pipeline to automate policy generation, conduct real-time risk assessments, and ensure compliance across enterprise operations.

![govManage Dashboard Concept](https://img.shields.io/badge/govManage-Dashboard-4f46e5?style=for-the-badge&logo=react)

---

## ✨ Core Capabilities

- **🧠 Multi-Agent Pipeline:** A 9-stage asynchronous pipeline orchestrated via shared queues (Policy Analysis → Compliance Verification → Risk Assessment → Executive Decision Engine → Audit Logging → Persistence).
- **🛡️ Real-Time Risk Engine:** Evaluates actions instantly using a custom Total Violation Index (TVI) and hard-coded business rules.
- **📑 Automated Policy Generation:** Discovers regulatory frameworks dynamically and generates comprehensive policy packs (Objectives, Scope, Controls) exported as professional PDFs.
- **🔍 Semantic Gap Analysis:** Upload policy documents to cross-reference them against global standards (ISO 27001, NIST AI RMF, GDPR, OECD AI) using ChromaDB vector search.
- **📊 Automated Reporting:** Scheduled weekly executive snapshots generated via APScheduler and dispatched directly to stakeholders' inboxes.

---

## 🏗️ Architecture Overview

The system is designed with a clear separation of concerns, enabling high throughput and easy scalability.

```text
┌─────────────────────────────────────────────────────────┐
│ Frontend (React + Vite + Tailwind CSS)                  │
│  - Interactive Dashboard, Policy Hub, Live Chat         │
└───────────────────┬─────────────────────────────────────┘
                    │ REST API (JSON)
┌───────────────────▼─────────────────────────────────────┐
│ Backend (Flask Application)                             │
│  - Risk Engine (TVI scoring, Rule evaluation)           │
│  - Semantic Search (ChromaDB Vector Store)              │
│  - Report Generation (PDF Export, Email Dispatch)       │
└──────────┬──────────────────────────────────────────────┘
           │ File-based Queues (agents_micro/shared_queues)
┌──────────▼──────────────────────────────────────────────┐
│ Asynchronous Multi-Agent Pipeline                       │
│  Orchestrator → Policy Analyst → Compliance Checker →   │
│  Risk Assessor → Decision Engine → Audit Relay →        │
│  Reporting Agent → Feedback Loop → Persistence          │
└───────────────────┬─────────────────────────────────────┘
                    │ 
┌───────────────────▼─────────────────────────────────────┐
│ Data Persistence Layer                                  │
│  MongoDB Atlas (Document Store)                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- **Python 3.13+**
- **Node.js 18+**
- **MongoDB** (Atlas account or local instance)
- **uv** package manager (`pip install uv`)

### 1. Repository Setup

```bash
git clone https://github.com/your-org/govmanage.git
cd govmanage
```

### 2. Environment Configuration

Copy the example environment file and populate it with your credentials:

```bash
cp .env.example .env
```
*Note: You will need a [Groq API Key](https://console.groq.com/keys) for the LLM features, and a MongoDB connection URI.*

### 3. Install Dependencies

**Backend:**
```bash
uv sync  # Recommended
# OR
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 4. Launch the Platform

**Windows (Automated):**
```bat
launch.bat
```

**Linux/macOS (Manual):**
You must run the backend, the frontend, and the micro-agents concurrently.

```bash
# Terminal 1 — Backend API
FLASK_DEBUG=1 python app.py

# Terminal 2–10 — Multi-Agent Pipeline
python agents_micro/orchestrator/main.py
python agents_micro/policy_analyst/main.py
python agents_micro/compliance/main.py
python agents_micro/risk_assessment/main.py
python agents_micro/decision_engine/main.py
python agents_micro/audit/main.py
python agents_micro/reporting/main.py
python agents_micro/feedback/main.py
python agents_micro/persistence/main.py

# Terminal 11 — Frontend
cd frontend && npm run dev
```

* **Frontend UI:** `http://localhost:5173`
* **Backend API:** `http://localhost:5000`

---

## 🧪 Testing

The platform includes a comprehensive Pytest suite (114+ tests) covering the risk engine, database interactions, and mocked API routes.

```bash
# Run the offline test suite
pytest tests/ -v --tb=short
```

---

## 🌍 Production Deployment

### Important Prerequisites
1. Set `FLASK_DEBUG=0`
2. Set `CORS_ORIGINS` to your exact frontend domain (e.g., `https://govmanage.yourcompany.com`).
3. Define environment variables in your hosting provider's Secrets Manager (do not upload `.env`).

### Option A: PaaS (Render, Railway, Heroku)
The repository includes a `Procfile` configured for Gunicorn.
1. Deploy the backend repository.
2. The platform will automatically execute: `gunicorn wsgi:app --workers 4 --bind 0.0.0.0:$PORT`
3. Deploy the `frontend/` directory to Vercel, Netlify, or Render Static Sites. Make sure to set `VITE_API_URL` to your deployed backend.

### Option B: Linux Server (Gunicorn + Nginx)
```bash
# Install backend requirements
pip install -r requirements.txt

# Start Gunicorn
gunicorn wsgi:app --workers 4 --bind 127.0.0.1:5000 --timeout 120

# Build Frontend
cd frontend
npm run build
# Serve the resulting /dist folder using Nginx
```

*Note: The local file-based micro-agent queue (`agents_micro/shared_queues`) is designed for single-server execution. For multi-server deployment, migrate this queue to Redis or RabbitMQ.*

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|:--------:|
| `GROQ_API_KEY` | LLM inference API key | Yes |
| `MONGO_URI` | MongoDB Atlas Connection String | Yes |
| `CORS_ORIGINS` | Allowed frontend domains | Prod Only |
| `FLASK_DEBUG` | Set to `0` in production | No |
| `SMTP_*` | Credentials for weekly automated reports | No |
| `TAVILY_API_KEY` | Real-time web intelligence capability | No |
| `FIRECRAWL_API_KEY` | Automated regulatory web crawling | No |

*Refer to `.env.production.example` for a complete production configuration template.*

---

## 📂 Project Structure

```text
govManage-policy-analyst/
├── app.py                 # Core REST API Controller
├── database.py            # MongoDB Document Models & Access Layer
├── scheduler.py           # APScheduler background tasks
├── email_service.py       # Modular SMTP & HTML rendering
├── vector_store.py        # ChromaDB bindings for RAG
├── report_pdf.py          # ReportLab PDF generation utilities
├── agents_micro/          # Multi-agent asynchronous pipeline
├── frontend/              # React Vite Application
├── tests/                 # Unit & Integration tests
└── scratch/               # Live system validation scripts
```

---
*Developed by the Advanced Agentic Coding Team.*
