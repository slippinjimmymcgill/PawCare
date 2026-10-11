# PawCare — Design Document (P0-PD-007)

**Status:** Phase 0 design draft — consolidation of everything produced in `docs/design/` so far.
**Trace:** `plan.md` §2 (architecture), `requirements.md` §5 (data), `specs.md` §6 (functional spec).
**This document consolidates, it does not replace:** `schema-notes.md`, `wireframes/wireframes-notes.md`, and `safety/safety-rules-v1.md` remain the source of truth for the reasoning behind each decision. This document's job is to tie them together, show how they agree with each other, and surface where they didn't (yet) — see §5.

---

## 1. Overview

PawCare is a web-based, AI-powered pet-health assistance platform: structured pet profiles and health records, an AI symptom-assessment pipeline with explicit urgency triage, a RAG-grounded conversational assistant, preventive-care reminders, and a Veterinary Safety Layer that can override any of the above when a case looks serious or uncertain. Full product framing is in `specs.md` §1; this document covers how it's built, not why it exists.

## 2. System Architecture

Layered, service-oriented design (`plan.md` §2):

```
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER — Next.js / React / Tailwind CSS              │
│ Pet Profiles & Records · Symptom Checker · AI Assistant (Chat)   │
│ Health Dashboard · Reminders & Recommendations                   │
└─────────────────────────────────────────────────────────────────┘
                              ▲  REST/HTTPS
┌─────────────────────────────────────────────────────────────────┐
│ API LAYER — FastAPI / Pydantic / JWT / OAuth 2.0                 │
│ Auth & User Service · Pet & Records Service · Assessment Service │
│ Assistant Service · Reminder Service                             │
└─────────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────────┐
│ AI / INTELLIGENCE LAYER — Python, scikit-learn, PyTorch,         │
│ Transformers                                                     │
│ NLP Pipeline · Symptom-Condition Classifier & Triage Model       │
│ RAG Engine (embeddings + vector search + LLM)                    │
│ Veterinary Safety Layer (red-flag rules) · Recommendation Engine │
└─────────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                       │
│ PostgreSQL + SQLAlchemy · Vector Store (pgvector)                │
│ Object Storage · Curated Veterinary Knowledge Base               │
└─────────────────────────────────────────────────────────────────┘
```

**The one architectural property every other artifact in this folder is built to respect:** the Veterinary Safety Layer sits in the AI/Intelligence layer but acts on output from both the Assessment Service and the Assistant Service *before* it reaches the Presentation layer — it's drawn as a peer of the NLP/classifier/RAG components, not because it's equally "just another model," but because it's the one component with override authority over the other three. The wireframes (§4) and the safety rule set (§5) are both built around that asymmetry; losing it in a future refactor would be a regression, not a simplification.

Full component responsibilities: `plan.md` §2–§3.

## 3. Data Model

See `er-diagram.png` (v1.1) and `schema-notes.md` for the full reasoning. Summary of the four modeling decisions made beyond what `requirements.md` §5 specified:

| Decision | Resolution | Why (short) |
|---|---|---|
| Pet deletion policy | Soft-delete (`deleted_at`); hard `ON DELETE CASCADE` reserved for a separate erasure action | Years of vaccination/visit history shouldn't vanish on a misclick |
| HealthRecord vs. Vaccination vs. Medication | Three separate tables, not one generic one | `next_due`/`start–end date` need to be queryable columns for the Reminder Service, not buried in free text |
| Feedback's polymorphic target | One `target_id` + `target_type`, app-level validated, not a DB FK | Postgres can't express "exists in table A or B" as a single FK; the two-nullable-FK fallback is noted if this ever causes real problems |
| `Chunk.embedding` | Placeholder `TEXT` column, pgvector swap commented in | Depends on `P1-BE-002` confirming pgvector is viable on the chosen host |

**12 entities, all smoke-tested** against an in-memory SQLite database (`schema-notes.md` §6) — confirms structural consistency, not Postgres/pgvector-specific behavior.

## 4. UI/UX Design

Seven low-fidelity wireframes (`wireframes/01-auth.png` … `07-admin.png`), each cross-checked against the FR it implements — full gate review in `wireframes/wireframes-notes.md` §2. Two screens carry the project's safety requirements directly in their layout, not as an afterthought:

- **Symptom Checker** (`04-symptom-checker.png`): urgency banner, ranked concerns with confidence, home-care guidance, an explicit "when to see a vet" box, sources, and the disclaimer — all fixed, non-collapsible elements.
- **Assistant Chat** (`05-assistant-chat.png`): every assistant message carries a sources row and a disclaimer; a documented (not drawn) behavior shows where the Safety Layer can interrupt with an Emergency banner mid-conversation.

## 5. Safety Layer

`safety/safety-rules-v1.yaml` + `safety-rules-v1.md` — 9 red-flag categories forcing `urgency: emergency`, a confidence/uncertainty policy with over-referral treated as a permanent design bias, 4 disclaimer templates, 6 output constraints. **Still unreviewed** by the veterinary advisory contact (`P0-PD-010`) — treat as development/testing-only until that review happens; `meta.reviewed_by` in the YAML is the field to check.

## 6. Cross-Artifact Consistency Review

This is the actual point of a consolidation pass — checking the artifacts against each other, not just re-listing them. One real inconsistency was found and fixed while producing this document:

> **Pet.medical_history was missing from the schema.** The wireframe for the Pet edit screen (`P0-FE-001`) included a "Medical history" field; the schema (`P0-BE-001`) didn't have a matching column. Re-checking against `requirements.md` FR-02's literal text confirmed the wireframe was right and the schema had a genuine gap — FR-02 names "medical history" explicitly as a profile attribute. **Fixed:** `Pet.medical_history` (nullable text) added to `models/pet.py` and `er-diagram.png` (now v1.1); full amendment note in `schema-notes.md` §8.

Everything else cross-checked clean:
- Every entity the wireframes imply (pets, records, vaccinations, medications, assessments, chat, reminders, admin/KB docs) has a matching table in the schema.
- Every red-flag category in the Safety Layer rule set has a corresponding visual treatment in the Symptom Checker / Chat wireframes (the heavier red outline convention).
- The architecture's "Safety Layer overrides the classifier and the LLM" property (§2) matches what the Safety Layer rule set's `red_flag_precedence` policy actually states (`safety-rules-v1.yaml`) — no drift between the two.

## 7. Open Items Carried Forward

Not this task's job to resolve, but worth listing in one place so nothing is quietly assumed:

- **Veterinary review of the Safety Layer** (`P0-PD-010`) — blocks treating `safety-rules-v1` as more than a development default.
- **pgvector viability on the chosen host** (`P1-BE-002`) — the one schema decision (`Chunk.embedding`) that isn't fully settled yet.
- **Archived-pet UI behavior** (`schema-notes.md` §3) — whether a soft-deleted pet is ever shown with a "restore" option, deferred to `P1-BE-004`.
- **Final visual design** (colors, typography, branding) — explicitly out of scope for every wireframe in this folder; a later, separate pass.

## 8. Phase 0 Exit — Design Theme Status

With this document, `task_backlog.md` §2.2 ("Architecture & Design") is feature-complete: architecture finalized, ER diagram + schema notes done (and now internally consistent with the wireframes), wireframes + notes done, Safety Layer rule set v1 done (pending vet review), and this consolidation written. The Phase 0 exit gate's remaining open items live in §2.3–§2.5 (environments, legal/ethics, veterinary advisory) — outside this task's scope, tracked in `task_backlog.md` directly.
