# Resume Deep Interview Agent

A system that extracts technical claims from resumes and conducts deep-dive interview sessions using a LangGraph state machine and LLM (Agnes API).

Frontend: React 19 + TypeScript + Vite + TanStack Query + Zustand
Backend: FastAPI + SQLAlchemy 2.0 async + PostgreSQL + LangGraph

## Architecture

```
PDF / TXT / TEX → Parser Registry → ResumeDocument → Profile Builder → Claims
    → LangGraph Interview (question → answer → analyze → score → decide)
    → Coaching + Final Report
```

## Project Structure

```
app/
├── api/v1/           # FastAPI endpoints — health, resumes, interviews, reports,
│                     #   dashboard, analytics, auth (placeholder), SSE manager
├── core/             # Config, enums, IDs, exceptions, security
├── parsers/          # PDF, TXT, LaTeX parsers + normalizer + quality
├── resume/           # Profile builder, claim extractor, claim ranker
├── interview/        # LangGraph state machine (11 nodes), rules, routing
├── llm/              # Agnes API gateway, model router, retry, token budget
├── persistence/      # SQLAlchemy models (14 tables), repositories, checkpoint
└── observability/    # structlog logging, metrics, tracing

frontend-react/       # React 19 + TypeScript + Tailwind CSS
└── src/
    ├── app/          # App entry, router (13 routes, lazy-loaded), query client
    ├── lib/          # Axios client, query keys, env validation, utilities
    ├── stores/       # Zustand — UI, interview drafts, preferences
    ├── styles/       # Tailwind globals + CSS custom properties
    ├── components/   # Layout (AppLayout, InterviewLayout, Sidebar, Topbar)
    └── features/
        ├── resumes/     # Upload, list, review, profile, claims pages
        ├── interviews/  # List, create, live room (SSE), hooks, event runtime
        ├── reports/     # Interview report (5-tab view)
        ├── dashboard/   # Landing page with stats
        ├── analytics/   # Score distribution, abilities, trends
        ├── settings/    # Interview preferences
        └── auth/        # Login placeholder

frontend-vue-archive/ # Original Vue 3 frontend (archived)
```

## Quick Start

### Prerequisites

- Python 3.12+ (conda recommended)
- Node.js 22+
- PostgreSQL 16 (optional, dev uses SQLAlchemy without DB requirement for tests)

### Backend Setup

```bash
# Create conda environment
conda create -n resume-interview python=3.12 -y
conda activate resume-interview

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp config.env .env
# Edit .env with your Agnes API key
```

### Frontend Setup

```bash
cd frontend-react
pnpm install
```

### Configuration

Edit `config.env`:

```env
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://apihub.agnes-ai.com/v1
LLM_MODEL_FAST=agnes-2.5-flash
LLM_MODEL_BALANCED=agnes-2.5-flash
LLM_MODEL_JUDGE=agnes-2.5-flash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resume_interview
```

### Run

```bash
# Terminal 1 — Start the API server
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Start the frontend dev server (proxies /api to :8000)
cd frontend-react
pnpm dev
```

Open http://localhost:5174 in your browser.

### Tests

```bash
# Backend tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app

# Frontend type check
cd frontend-react && pnpm type-check

# Frontend build
cd frontend-react && pnpm build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/me` | Current user (placeholder, returns anon) |
| **Resumes** | | |
| GET | `/api/v1/resumes` | List resumes (pagination, search, status filter, sort) |
| POST | `/api/v1/resumes` | Upload resume file (PDF/TXT/TEX) |
| POST | `/api/v1/resumes/text` | Upload resume as text |
| GET | `/api/v1/resumes/{id}` | Get resume details |
| GET | `/api/v1/resumes/{id}/claims` | Get extracted claims |
| PATCH | `/api/v1/resumes/{id}/claims/{claim_id}` | Update claim (enabled, priority) |
| GET | `/api/v1/resumes/{id}/revisions` | Revision history |
| PATCH | `/api/v1/resumes/{id}/revisions/{rev}` | Update revision (rebuilds blocks) |
| POST | `/api/v1/resumes/{id}/revisions/{rev}/confirm` | Confirm revision (builds profile + claims) |
| DELETE | `/api/v1/resumes/{id}` | Delete resume and related data |
| **Interviews** | | |
| GET | `/api/v1/interviews` | List interviews (pagination, status/mode filter) |
| POST | `/api/v1/interviews` | Create interview |
| GET | `/api/v1/interviews/{id}` | Get interview state |
| GET | `/api/v1/interviews/{id}/events` | SSE event stream (real-time) |
| POST | `/api/v1/interviews/{id}/answers` | Submit answer |
| POST | `/api/v1/interviews/{id}/finish` | Force finish (generates report) |
| GET | `/api/v1/interviews/{id}/report` | Get final report |
| POST | `/api/v1/interviews/{id}/report/export` | Export report (JSON/Markdown) |
| **Dashboard & Analytics** | | |
| GET | `/api/v1/dashboard/summary` | Aggregated dashboard stats |
| GET | `/api/v1/analytics/summary` | Score distribution, abilities, verification rate |
| GET | `/api/v1/analytics/trends` | Weekly interview counts, score trends |

## SSE Event Types

The interview SSE stream (`GET /interviews/{id}/events`) emits these event types:

| Event | Description |
|-------|-------------|
| `interview.initialized` | Interview started, graph built |
| `question.ready` | New question available |
| `answer.accepted` | Answer received, analysis begins |
| `analysis.completed` | Answer analysis finished |
| `scoring.completed` | 6-dimension scoring done |
| `coaching.ready` | Coaching feedback available |
| `interview.finished` | Interview ended |
| `report.ready` | Final report generated |

Events include `sequence`, `event_id`, and `payload` fields. The frontend SSE client supports exponential backoff reconnection (1s–15s, max 10 retries) with sequence-based deduplication.

## Interview Flow (LangGraph)

11-node state machine with 2 conditional routing points:

```
START → initialize → build_plan → select_target
                                       │
                          ┌────────────┴────────────┐
                          ▼                         ▼
                   generate_question         generate_report (all claims done)
                          │
                          ▼
                   wait_for_answer  ←── interrupt, resume via Command(resume=)
                          │
                          ▼
                   analyze_answer → score_answer → update_evidence → decide_next
                                                                        │
                                      ┌─────────────────┬───────────────┴───────────────┐
                                      ▼                 ▼                               ▼
                              generate_question   select_target (switch claim)   generate_report
                                                                                      │
                                                                                 generate_coaching
```

- Checkpointer: MemorySaver (dev) / PostgresSaver (production)
- Decision routing is code-controlled (rule engine), not LLM-dependent
- 6-dimension scoring with rubric-defined weights

## 7-Level Depth Model

| Depth | Focus | Example |
|-------|-------|---------|
| 1 | Background & responsibilities | What problem, your role |
| 2 | Execution flow | Request lifecycle |
| 3 | Code, interfaces, data structures | State fields, contracts |
| 4 | Principles & design reasons | Why this split |
| 5 | Edge cases & failures | Timeout, retry, concurrency |
| 6 | Alternatives & tradeoffs | Why not other approaches |
| 7 | Counterfactuals & evolution | What would you change |

## Scoring Dimensions

| Dimension | Weight |
|-----------|--------|
| Technical Correctness | 25% |
| Implementation Depth | 20% |
| Architecture & Tradeoffs | 15% |
| Personal Contribution | 15% |
| Production Awareness | 15% |
| Clarity | 10% |

Scoring uses weighted calculation (not simple average) per architecture requirements.
