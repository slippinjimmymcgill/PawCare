# PawCare — Database Schema Notes (P0-BE-001)

**Status:** Phase 0 design draft — not yet migrated (`P1-BE-002` does that once this is reviewed).
**Trace:** `requirements.md` §5 (Data Requirements), FR-02, FR-03, FR-05, FR-07, FR-09, FR-11.
**Artifacts in this folder:** `er-diagram.png` (visual, v1.1), `models/` (first-pass SQLAlchemy 2.0 model stubs, one file per entity, importable and smoke-tested against SQLite — see §6).

---

## 1. What changed from the preliminary entity list

`requirements.md` §5 listed ten entities at a one-line-per-field level. This draft keeps all ten, resolves the modeling questions that list left open, and adds the fields needed to actually implement each FR's acceptance criteria. Nothing here removes or renames an entity from §5.

## 2. Modeling decision: HealthRecord vs. Vaccination vs. Medication

`requirements.md` lists `HealthRecord` with a generic `type` field alongside separate `Vaccination` and `Medication` entities — it doesn't say why both exist. Decision: they're kept separate on purpose.

- **Vaccination** and **Medication** have their own lifecycle fields (`next_due`, `start_date`/`end_date`) that the Reminder Service (`P2-BE-003`, FR-09) and the dashboard (FR-10) query against directly. Burying `next_due` inside a generic record's free-text description would make reminders unreliable.
- **HealthRecord** stays generic for the three things that genuinely don't need specialized lifecycle fields: vet visits, weight logs, and notes. `weight_kg` is nullable on this table rather than a separate `WeightLog` entity, since it's a single extra column, not a distinct lifecycle.

If a fourth specialized type turns up later (e.g. lab results with their own due-for-recheck logic), the same reasoning says give it its own table rather than overloading `HealthRecord.type` further.

## 3. Modeling decision: Pet deletion — soft-delete, not hard cascade

FR-02's acceptance criteria explicitly left this open ("deleting a pet cascades or archives its dependent records per a documented policy"). Decision: **soft-delete by default.**

- `Pet.deleted_at` (nullable timestamp) marks a pet as archived. `NULL` = active.
- Dependent tables (`HealthRecord`, `Vaccination`, `Medication`, `SymptomAssessment`, `ChatSession`, `Reminder`) are **not** deleted when a pet is archived — they're just excluded from default queries once their parent `Pet.deleted_at` is set (enforce this filter at the service layer in `P1-BE-004`, not just in the frontend).
- **Why not hard delete by default:** a pet's vaccination and visit history has real value even after the pet is no longer active in the app (a second pet later, a vet visit referencing history, etc.), and FR-02's "cascades or archives" framing doesn't force irreversibility. Defaulting to reversible is the safer choice when the alternative is silent, permanent data loss from a single misclick.
- **Hard delete still exists**, just not as the default path: every dependent table's foreign key is declared `ondelete="CASCADE"` at the database level (see any `models/*.py` file). This is for a separate, explicit, account-level erasure action — not triggered by the normal "delete my pet" button. `FR-11`'s user-controlled deletion of assessment/chat *history* is a different, narrower action (clearing history for an active pet) and is unaffected by this decision either way.
- **Open follow-up for `P1-BE-004`:** decide whether archived pets are ever shown in the UI at all (e.g. a "restore" affordance) or purely invisible until a real erasure/export feature exists. Not resolved here — flagged so it doesn't get decided by accident in the UI layer.

## 4. Modeling decision: Feedback's polymorphic target

`Feedback.target_id` can point at either a `SymptomAssessment` or a `Message`, and `requirements.md` §5 doesn't specify how. Decision: **one `target_id` column, no database-level foreign key constraint**, with `target_type` disambiguating which table it refers to. This is enforced at the application layer (validate `target_id` exists in the right table before insert), not the database.

**Trade-off, stated plainly:** Postgres can't express "this UUID exists in table A or table B" as a single FK. The alternative — two nullable FK columns (`assessment_id`, `message_id`) with a `CHECK` constraint that exactly one is set — is more defensible at the database level and is the standard fix if orphaned feedback rows ever become a real problem. Noted here as the fallback, not implemented now, since it adds complexity for a feature (`FR-13`) marked **Low** priority in `requirements.md` §8.

## 5. Other notable choices

- **UUID primary keys everywhere**, not auto-increment integers — IDs stay non-guessable and stable once the AI/RAG services and the API are split across the layered architecture in `plan.md` §2.
- **`Chunk.embedding` is a placeholder `TEXT` column**, not a real `pgvector` column yet — it's commented with the exact swap needed once `P1-BE-002` confirms pgvector is viable on the chosen hosting provider (`plan.md` §11 item 3). Everything else in the schema is independent of that decision; if pgvector turns out not to be viable, only this one column/table relationship needs to move to a separate vector store.
- **`metadata_json`, not `metadata`**, on `Chunk` — `metadata` is reserved by SQLAlchemy's declarative `Base` and would silently collide with it.
- **`Medication.notes` is owner/vet-entered only** — flagged explicitly in the model's docstring so nobody wires the AI/RAG services to write to this table later without noticing it would cross the hard "no prescription/dosage output" constraint in `requirements.md` §7.
- **`UrgencyLevel` enum values are safety-relevant**, not just display labels — the Safety Layer (`FR-08`, built in `P2-RAG-004`) checks against `UrgencyLevel.EMERGENCY` specifically. Flagged in the enum's docstring so a future rename doesn't quietly break a safety check.

## 6. Verification done on this draft

- All 12 models import cleanly as a package (`models/__init__.py` exposes every entity + enum).
- `Base.metadata.create_all()` was smoke-tested against an in-memory SQLite database — all 12 tables create without error. This confirms the schema's structure (columns, FKs, relationships) is internally consistent; it does **not** validate Postgres- or pgvector-specific behavior, which needs `P1-BE-002`'s real database.
- Cross-checked against every FR this schema touches (FR-02, FR-03, FR-05, FR-07, FR-09, FR-11) per this task's own gate — no required field from those FRs' acceptance criteria is missing. **Note:** this check missed one field on first pass — see §8.

## 7. What's deliberately NOT done here

Per `P0-BE-001`'s own scope (see `task_backlog.md`):
- No Alembic setup, no live database, no migration run — that's `P1-BE-002`.
- No real pgvector column — placeholder only, pending the provider check.
- No application code (routers, services) reads or writes these models yet — that starts with `P1-BE-001`'s FastAPI scaffold.

## 8. Amendment (v1.1) — found during `P0-PD-007` consolidation

While cross-referencing this schema against the wireframes (`P0-FE-001`) during design-document consolidation, the Pet edit form wireframe was found to include a **"Medical history"** field with no matching column here. Re-checking against `requirements.md` FR-02's literal text — *"pet profiles (species, breed, age, sex, weight, **medical history**, allergies, medications)"* — confirms this was a genuine gap in v1, not a wireframe getting ahead of the schema: FR-02 names it explicitly, and §6's "cross-checked against every FR" claim was wrong on this one point.

**Fix:** added `Pet.medical_history` (nullable `Text`) — a free-text, owner-entered summary (e.g. "history of hip dysplasia, TPLO surgery 2023"), distinct from the itemized, time-series `HealthRecord`/`Vaccination`/`Medication` tables. `medications` from FR-02's list is still intentionally **not** a Pet column — that's the existing `Medication` entity (§2), unaffected by this amendment.

Updated: `er-diagram.png` (now v1.1, Pet box includes `medical_history : text`), `models/pet.py`. No other entity or decision in this document changed. This is exactly the kind of cross-artifact inconsistency `P0-PD-007`'s consolidation pass exists to catch — noted here rather than quietly folded into §5 as if it had always been correct.
