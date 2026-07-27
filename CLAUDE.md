# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

A LangGraph state machine that extracts technical claims from resumes and conducts deep-dive interview sessions using the Agnes API (OpenAI-compatible). The backend runs on FastAPI + SQLAlchemy 2.0 async + PostgreSQL; the frontend is React 19 + TypeScript + Vite + TanStack Query + Zustand.

### Data Flow

```
Upload (PDF/TXT/TEX) → Parser Registry → ResumeDocument → Profile Builder
    → Claim Extractor → Claim Ranker → LangGraph Interview (11 nodes)
    → Coaching + Final Report
```

### Pipeline Phases

1. **Parsing** — Text/PDF/LaTeX parsers produce `ResumeDocument` (normalized blocks with quality score)
2. **Profile Building** — Section classifier + LLM extraction → `ResumeProfile` (sectioned entries)
3. **Claim Extraction** — LLM extracts tech claims from entries → `ResumeClaim[]` with risk flags
4. **Claim Ranking** — Priority formula: `0.30*role_relevance + 0.20*prominence + 0.20*level_score + 0.15*verification_value + 0.15*risk`
5. **Interview** — LangGraph workflow with 11 nodes (see below), answers collected via `interrupt()`
6. **Scoring** — 6-dimension evaluation with weighted rubric
7. **Coaching** — Per-answer feedback with expert reference answers

### Interview Graph (11 Nodes)

```
START → initialize → build_plan → select_target ─┬─→ generate_question → wait_for_answer
                                                   │                           ↓
                                                   └─→ generate_report    analyze_answer → score_answer
                                                        ↑                      ↓
                                                   generate_coaching ← decide_next ← update_evidence
```

- `select_target` has conditional edge: `route_after_select` → `generate_question` or `generate_report`
- `decide_next` has conditional edge: `route_after_decide` → `generate_question / select_target / generate_coaching / generate_report`
- `wait_for_answer` is the `interrupt()` point — the graph pauses for user input
- After `wait_for_answer`, the graph resumes via `Command(resume={"answer_text": "..."})`

### 7-Level Depth Model

| Depth | Focus |
|-------|-------|
| 1 | Background & responsibilities |
| 2 | Execution flow |
| 3 | Code, interfaces, data structures |
| 4 | Principles & design reasons |
| 5 | Edge cases & failures |
| 6 | Alternatives & tradeoffs |
| 7 | Counterfactuals & evolution |

### Scoring Dimensions (100 pts total)

- Technical Correctness (25%), Implementation Depth (20%), Architecture/Tradeoffs (15%)
- Personal Contribution (15%), Production Awareness (15%), Clarity (10%)

## Project Structure

```
app/
├── api/v1/           # FastAPI routers — health, resumes, interviews, reports,
│                     #   dashboard, analytics, auth (placeholder), SSE manager
├── core/             # Settings, enums, ID generation, exceptions, security
├── parsers/          # ParserRegistry → PdfParser/TextParser/LatexParser, normalizer, quality
├── resume/           # ProfileBuilder, ClaimExtractor, ClaimRanker, section classifier
├── interview/        # InterviewState (TypedDict), graph builder, 11 node functions, rules, routing, rubrics
├── llm/              # AgnesGateway (httpx → Agnes API), model router, retry, token budget
├── persistence/      # SQLAlchemy async models (14 tables), repositories, checkpoint saver
└── observability/    # structlog logging, metrics, tracing placeholders

frontend-react/       # React 19 + TypeScript strict + Tailwind CSS 4
└── src/
    ├── app/          # App entry, router (14 routes, lazy-loaded), query client, error boundary
    ├── lib/          # Axios client, query keys, env validation (Zod), utilities
    ├── stores/       # Zustand — ui-store, interview-draft-store, preference-store (all persisted)
    ├── styles/       # Tailwind globals + CSS custom properties
    ├── components/   # Layout (AppLayout, InterviewLayout, Sidebar, Topbar)
    └── features/
        ├── resumes/     # Upload, list, review, profile, claims pages + hooks + API layer
        ├── interviews/  # List, create, live room (SSE), hooks, event runtime, SSE client
        ├── reports/     # Interview report (5-tab view)
        ├── dashboard/   # Landing page with stats
        ├── analytics/   # Score distribution, abilities, trends
        ├── settings/    # Interview preferences
        └── auth/        # Login placeholder

frontend-vue-archive/ # Original Vue 3 frontend (archived)
```

## Key Design Decisions

### Backend

- **Code-controlled decisions**: `decide_next` uses a rule engine (not LLM) — LLM only *suggests* via `model_recommended_action`. The Decision class in `rules.py` carries action/reason/target/depth.
- **Prompt injection defense**: `wrap_user_data()` wraps resume content with Chinese-language boundary markers; `detect_injection_signal()` checks for instruction override patterns.
- **Async everywhere**: All parsing, LLM calls, and DB operations use `async/await`.
- **Single LLM provider**: Agnes API (OpenAI-compatible) via `AgnesGateway` — no provider abstraction beyond `LLMGateway` protocol.
- **Model tier routing**: `model_router.py` maps task names to fast/balanced/judge tiers (all same model in development).
- **No ORM commits in repos**: Repositories use `add_*` patterns; transactions managed at the API router level.
- **SSE via asyncio.Queue**: `SSEManager` in `sse_manager.py` maintains per-interview subscriber sets. Publishers push events to all subscribers' queues; each subscriber gets a dedicated `asyncio.Queue`.

### Frontend

- **Feature-based directory structure**: Each domain (resumes, interviews, reports, dashboard, analytics, settings, auth) is self-contained with its own `api/`, `hooks/`, `pages/`, and optionally `components/`.
- **All inline CSS**: Uses `React.CSSProperties` objects declared at file bottom. No CSS modules, no styled-components, no Tailwind classes in JSX. Global styles in `globals.css`.
- **Lazy-loaded routes**: All 14 page components are `React.lazy(() => import(...))` with a `<Suspense>` wrapper.
- **TanStack Query key factory**: `queryKeys` in `lib/query-keys.ts` — structured, hierarchical keys (`resumes.list(filters)`, `interviews.detail(id)`, etc.). Filter params use `Record<string, any>` to accept typed parameter objects.
- **Zustand with persist**: All 3 stores (`ui-store`, `interview-draft-store`, `preference-store`) use `persist` middleware with localStorage. Draft store keys are composite: `${interviewId}_${questionId}`.
- **SSE client**: Uses `fetch` + `ReadableStream.getReader()` (not `EventSource`) for fine-grained control. Exponential backoff reconnection (1s→15s, max 10 retries). Connection state machine: idle → connecting → connected → reconnecting → disconnected → failed.
- **Event reducer**: `eventReducer` (useReducer-based) handles 9 SSE event types + internal `_connection_change`. Connection events bypass sequence-based deduplication. Interview stage state machine: loading → waiting_for_question → answering → analyzing → finished.
- **Idempotent answer submission**: `useSubmitAnswer` generates idempotency keys via `${interviewId}_${questionId}_${Date.now()}`.
- **Answer drafts persisted**: `useInterviewDraftStore` saves partial answers to localStorage, keyed by interview+question.
- **Axios with ApiError**: Request interceptor injects `X-Request-ID` (first 12 chars of UUID). Response interceptor normalizes backend error shape `{error: {code, message, request_id, field_errors}}` into `ApiError` class.

## Commands

### Backend

```bash
# Install
pip install -e ".[dev]"

# Run API server
uvicorn app.main:app --reload --port 8000

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_parsers.py -v

# Run single test
pytest tests/test_normalizer.py::TestNormalizer::test_broken_line_merging -v

# Run with coverage
pytest tests/ --cov=app

# Lint
ruff check app/ tests/
```

### Frontend

```bash
cd frontend-react

# Install
pnpm install

# Dev server (proxies /api → localhost:8000)
pnpm dev                    # → http://localhost:5174

# Type check (TypeScript strict, zero errors required)
pnpm type-check

# Production build
pnpm build

# Lint
pnpm lint

# Generate API types from running backend
pnpm api:generate
```

### Run Both

```bash
# Terminal 1
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend-react && pnpm dev
```

## Important Constraints

- Python 3.12+ required
- Node.js 22+ with pnpm
- config.env must have `LLM_API_KEY` set
- Database: PostgreSQL 16 with asyncpg
- Tests use `pytest-asyncio` with `asyncio_mode = auto`
- LangGraph 0.2+ with `Command(resume=...)` syntax for resuming after interrupts
- PyMuPDF 1.24+ for PDF extraction; pylatexenc 2.10 for LaTeX (static parsing only, no `\input`/`\include`)
- TypeScript `strict: true` + `noUncheckedIndexedAccess: true` + `verbatimModuleSyntax: true`
- Path alias `@/` maps to `src/` (configured in both tsconfig and vite.config)
- Vite dev server runs on port 5174 with `/api` proxy to `localhost:8000`
- Frontend uses no component library — all components are hand-built with inline styles
- Auth is placeholder-only (`GET /api/v1/me` returns anon user, `LoginPage` is a stub, API client has auth interceptor comment for future token injection)
- See `persistence/models.py` for all 14 DB tables (includes `llm_calls` and `prompt_versions` audit tables)
