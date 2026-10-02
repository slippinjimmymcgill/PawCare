# PawCare

**An AI-Powered Pet Health Assistant for Intelligent Symptom Assessment, Health Monitoring, and Preventive Pet Care**

Final Year Design Project — Department of Computer Science, NUST
Author: Ismail Jamal Tariq (480321) · Supervisor: Dr. Shah Khalid · Co-supervisor: Mr. Muhammad Daud Abdullah Asif

---

## What this is

PawCare is a web-based, AI-powered pet-health assistance platform. Owners keep structured pet profiles and health records, describe symptoms in natural language, and receive a structured assessment (possible concerns, confidence, urgency level, guidance). A RAG-grounded conversational assistant answers general pet-health questions with citations, and a preventive-care engine generates personalized reminders. A dedicated **Veterinary Safety Layer** enforces red-flag rules, communicates uncertainty, and always directs owners to a veterinarian when a case is serious or unclear.

PawCare is positioned strictly as **decision support and education — never a diagnosis, prescription, or replacement for a veterinarian.**

## Planning documents

Full project documentation lives in [`docs/`](./docs):

| Document | What it covers |
|---|---|
| [`docs/requirements.md`](./docs/requirements.md) | Formal, testable requirements catalog (FR/NFR, data model, interfaces) |
| [`docs/specs.md`](./docs/specs.md) | Product scope — in scope, out of scope, future work, glossary |
| [`docs/plan.md`](./docs/plan.md) | Architecture, roadmap, team, timeline, QA/security plan, go-to-market, risk register, KPI gates, open decisions |
| [`docs/task_backlog.md`](./docs/task_backlog.md) | Sprint-by-sprint execution backlog, traced to the documents above |

Start with `specs.md` for the one-paragraph pitch and scope boundary, then `plan.md` for how it gets built, then `task_backlog.md` for what's being worked on right now.

## Planned stack

- **Frontend:** Next.js, React, Tailwind CSS
- **Backend:** FastAPI, Pydantic, PostgreSQL + SQLAlchemy, pgvector
- **AI/ML:** scikit-learn, PyTorch/TensorFlow, Transformers, an external LLM API (RAG)
- **Deployment:** Vercel (frontend), Render (backend), GitHub Actions (CI/CD)

## Repository structure

```
PawCare/
├── docs/                # Requirements, specs, plan, task backlog
├── apps/
│   ├── backend/         # FastAPI service (scaffolded in Sprint Block 2)
│   └── frontend/        # Next.js app (scaffolded in Sprint Block 2)
└── .github/workflows/   # CI
```

## Status

Pre-build — planning and design phase (Sprint Block 1 of 8). See `docs/task_backlog.md` §10 for the current progress log.

## Safety note

This project does not provide veterinary diagnoses, prescriptions, or dosages, and is not a substitute for professional veterinary care. See `docs/specs.md` §2 for the full non-goals.
