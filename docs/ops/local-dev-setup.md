# PawCare — Local Development Environment Setup

**Task:** `P0-OPS-003` · **Depends on:** `P0-OPS-001` · **Trace:** `plan.md` §2 · **Status:** ✅ Complete
**Purpose:** Let anyone (including a future teammate, or the examiner's panel reproducing the demo) go from a clean `git clone` of `https://github.com/slippinjimmymcgill/PawCare` to a running backend + frontend with no undocumented manual steps.

This does not require any billed account or credential the agent can't produce — it's pinned versions, `.env` templates, and instructions. It's the one task in this group of 7 that is fully and immediately completable without a human-held account (unlike `P0-OPS-004`/`P0-OPS-005`, which are blocked for that reason — see below).

---

## 1. Toolchain Versions (Pinned)

| Tool | Version | Why this version |
|---|---|---|
| Python | 3.11.x | FastAPI + SQLAlchemy 2.0's `Mapped`/`mapped_column` style (already used in `docs/design/models/`) is fully supported from 3.10+; 3.11 picked for its performance improvements and current Debian/Ubuntu LTS availability. |
| Node.js | 20.x (LTS) | Next.js 14+ requires Node 18.17+; 20.x LTS gives the longest support window for an 8-month project. |
| PostgreSQL | 16.x | Current stable major version with mature `pgvector` extension support (pgvector availability itself is a `P1-BE-002` open question, not assumed here). |
| Docker / Docker Compose | Docker Engine 24+, Compose v2 | For a local Postgres container — avoids requiring a local Postgres install for dev. |
| npm | bundled with Node 20 | No separate pin; `package-lock.json` governs exact dependency versions once `P1-FE-001` scaffolds the frontend. |
| pip / venv | bundled with Python 3.11 | `requirements.txt` (or `pyproject.toml`, decided in `P1-BE-001`) governs exact dependency versions. |

**Note:** these are the versions a clean setup should target; they are not yet enforced by any automated check. `P0-OPS-002`'s CI skeleton is a placeholder lint/typecheck workflow only — pinning these in CI (e.g., a `.python-version` / `.nvmrc` file read by the workflow) is explicitly carried into `P1-BE-001`/`P1-FE-001`'s scaffolding tasks, since there's no real app code yet for CI to check against.

---

## 2. Repository Layout Assumed

```
PawCare/
├── apps/
│   ├── backend/       # FastAPI app (scaffolded in P1-BE-001)
│   └── frontend/      # Next.js app (scaffolded in P1-FE-001)
├── docs/
│   ├── design/         # P0-BE-001, P0-FE-001, P0-RAG-001, P0-PD-007 deliverables
│   ├── legal/           # P0-PD-008, P0-PD-009, P0-RAG-002 deliverables
│   └── ops/              # this file, plus P0-OPS-004/005 supporting docs
├── .github/workflows/   # P0-OPS-002 CI skeleton
├── .gitignore
└── README.md
```

This matches the scaffold already pushed to `D:\PawCare` — this task adds the setup instructions and `.env` templates into `docs/ops/` and the two `apps/*` folders, not a new layout.

---

## 3. `.env` Templates

Neither `apps/backend/.env` nor `apps/frontend/.env.local` should ever be committed (already covered by the repo's `.gitignore` from `P0-OPS-001`). The templates below are what gets committed instead, so a clean clone knows exactly what to fill in.

### 3.1 `apps/backend/.env.example`

```bash
# ── App ──────────────────────────────────────────────────────────
APP_ENV=development
APP_SECRET_KEY=changeme-generate-a-real-random-value   # used for JWT signing (FR-01)

# ── Database ─────────────────────────────────────────────────────
# Local dev default assumes the docker-compose Postgres service below.
DATABASE_URL=postgresql+psycopg://pawcare:pawcare@localhost:5432/pawcare_dev

# ── JWT / Auth (FR-01) ───────────────────────────────────────────
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# ── LLM Provider (FR-07) ─────────────────────────────────────────
# BLOCKED on P0-OPS-004 — provider not yet selected, no real key exists.
# Leave blank in dev; AI assistant / RAG endpoints should no-op or
# return a clear "not configured" response rather than failing silently
# when this is empty, once those endpoints exist (Phase 2).
LLM_PROVIDER=
LLM_API_KEY=
LLM_API_BASE_URL=

# ── Object Storage (FR-03 attachments) ───────────────────────────
# BLOCKED on P0-OPS-005 — no hosting/storage account provisioned yet.
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=

# ── CORS ─────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 3.2 `apps/frontend/.env.local.example`

```bash
# ── API ──────────────────────────────────────────────────────────
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# ── App ──────────────────────────────────────────────────────────
NEXT_PUBLIC_APP_NAME=PawCare
```

### 3.3 `docker-compose.dev.yml` (repo root)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: pawcare
      POSTGRES_PASSWORD: pawcare
      POSTGRES_DB: pawcare_dev
    ports:
      - "5432:5432"
    volumes:
      - pawcare_pg_data:/var/lib/postgresql/data

volumes:
  pawcare_pg_data:
```

`pgvector` is **not** added to this image yet — confirming pgvector support is explicitly `P1-BE-002`'s job (per `task_backlog.md` §3.1a), not assumed here. If `P1-BE-002` confirms it's needed locally, the fix is switching this image to `pgvector/pgvector:pg16` and re-running migrations, not something this task should pre-decide.

---

## 4. Setup Instructions (for `README.md`'s "Getting Started" section)

```markdown
## Getting Started (Local Development)

### Prerequisites
- Python 3.11.x
- Node.js 20.x (LTS)
- Docker + Docker Compose (for local Postgres)
- Git

### 1. Clone and configure
\`\`\`bash
git clone https://github.com/slippinjimmymcgill/PawCare.git
cd PawCare
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local
# Edit apps/backend/.env: set a real APP_SECRET_KEY.
# Leave LLM_* and OBJECT_STORAGE_* blank until P0-OPS-004/005 are unblocked.
\`\`\`

### 2. Start the database
\`\`\`bash
docker compose -f docker-compose.dev.yml up -d
\`\`\`

### 3. Backend
\`\`\`bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate   # .venv\\Scripts\\activate on Windows
pip install -r requirements.txt
alembic upgrade head          # once P1-BE-002 exists
uvicorn app.main:app --reload --port 8000
\`\`\`

### 4. Frontend
\`\`\`bash
cd apps/frontend
npm install
npm run dev
\`\`\`

### 5. Verify
- Backend health check: http://localhost:8000/health → \`{"status": "ok"}\`
- Frontend: http://localhost:3000
```

This is written now, ahead of `P1-BE-001`/`P1-FE-001` actually scaffolding the apps, so those tasks implement *against* a documented contract (specific env var names, specific ports, specific commands) instead of inventing one ad hoc mid-implementation.

---

## 5. What This Task Does Not Cover

- Does not provision any real database, LLM account, or hosting account — see `P0-OPS-004`/`P0-OPS-005` below, both blocked.
- Does not pin dependency versions inside `requirements.txt`/`package.json` — those files don't exist yet (created in `P1-BE-001`/`P1-FE-001`); this task pins the *toolchain* (language/runtime/DB engine), not the eventual library versions.
- Does not set up the CI pipeline to actually enforce these versions — flagged above as carried into `P1-BE-001`/`P1-FE-001`.
