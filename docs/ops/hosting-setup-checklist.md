# PawCare — Hosting Accounts Provisioning

**Task:** `P0-OPS-005` · **Depends on:** `P0-OPS-001` · **Trace:** `requirements.md` §6 · **Status:** ⛔ **Blocked**

## Why This Is Blocked

Like `P0-OPS-004`, this requires creating and holding real accounts on third-party platforms (Vercel, Render, a managed PostgreSQL provider) — tied to a real identity/email, and in most cases a payment method even on free tiers. That has to be the account owner (Ismail), not something done on his behalf. Nothing below is a research gap; it's a credential dependency.

**What unblocks it:** the account owner creates the three accounts below (free tiers are sufficient at this stage per `requirements.md` §6 — no paid tier is required to clear this task), then this checklist is walked through in under a day, matching the original 0.5d estimate.

---

## Setup Checklist (to run once accounts exist)

### 1. Vercel (Frontend hosting)
- [ ] Create account at vercel.com, connect to the `slippinjimmymcgill/PawCare` GitHub repo.
- [ ] Set project root to `apps/frontend` (per the repo layout in `P0-OPS-003`).
- [ ] Add environment variables matching `apps/frontend/.env.local.example`: `NEXT_PUBLIC_API_BASE_URL` (pointed at the Render backend URL once that exists), `NEXT_PUBLIC_APP_NAME`.
- [ ] Confirm preview deployments trigger on PRs, production deploy on merge to `main` — matches the CI/CD intent in `plan.md` §2.

### 2. Render (Backend hosting)
- [ ] Create account at render.com, connect to the same repo.
- [ ] Create a Web Service with root `apps/backend`, build command and start command matching `P1-BE-001`'s eventual scaffold (`uvicorn app.main:app`).
- [ ] Add environment variables matching `apps/backend/.env.example` — critically, do **not** copy real secrets into this checklist file or into the repo; set them directly in Render's dashboard.
- [ ] Confirm a `/health` health-check endpoint is configured once `P1-BE-001` exists (Render's own health-check config, not just the app route).

### 3. Managed PostgreSQL
- [ ] Choose a managed Postgres provider — Render's own managed Postgres add-on is the simplest (same platform, same billing, easiest networking to the Render-hosted backend), but a dedicated provider (e.g., Supabase, Neon) is worth comparing specifically for **pgvector support**, since `P1-BE-002` needs to confirm pgvector availability on whichever provider is chosen — check that before committing, not after.
- [ ] Create a dev-tier (or free-tier) instance.
- [ ] Record the connection string into Render's environment variables as `DATABASE_URL` (not into this file, and not into source control).

### 4. Object Storage (for health-record attachments, FR-03)
- [ ] Not explicitly named as a separate account in `plan.md` §11, but `requirements.md` §6 calls for object storage for attachments/model artifacts. Cheapest path: many managed-Postgres/hosting providers bundle S3-compatible storage, or Render/Vercel both integrate cleanly with Cloudflare R2's free tier. Decide alongside the Postgres provider choice above rather than as a fourth separate account if a bundled option exists.

---

## Config Stubs Delivered Now

- `docker-compose.dev.yml` (from `P0-OPS-003`) — local Postgres, so Sprint Block 1–2 isn't blocked on this task even before hosting accounts exist.
- `apps/backend/.env.example` — `DATABASE_URL`, `OBJECT_STORAGE_*` fields already present and blank, with comments pointing back to this blocker.

## Recorded as Open Risk

Carried forward into the Phase 0 Exit Gate. Note that `P1-BE-002` (PostgreSQL provisioning & Alembic setup, Sprint Block 1–2) and `P1-OPS-001` (staging deployment, Sprint Block 5–6) both depend on this — so while this task doesn't block Phase 1 from *starting* (scaffolding work doesn't need live hosting), it does block those two specific downstream tasks if left open past Sprint Block 1–2.
