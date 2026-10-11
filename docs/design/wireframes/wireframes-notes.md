# PawCare — UI/UX Wireframes Notes (P0-FE-001)

**Status:** Phase 0 design draft — low/mid-fidelity, greyscale, structure only. No final visual design (colors, typography, branding) yet, per this task's own scope.
**Trace:** `specs.md` §6, and every FR listed per screen below.
**Artifacts in this folder:** `wireframes/01-auth.png` … `wireframes/07-admin.png`, plus the generating scripts (`build_wireframes.py`, `wireframe_lib.py`) so a screen can be regenerated or tweaked without redrawing from scratch.

---

## 1. Screens covered

| # | Screen | Covers |
|---|---|---|
| 01 | Auth — Login & Register | FR-01 |
| 02 | Pet Profile — list & create/edit | FR-02 |
| 03 | Health Records — timeline & add-record | FR-03 |
| 04 | Symptom Checker — submission & results | FR-04, FR-05, FR-06, FR-08 |
| 05 | AI Assistant Chat | FR-07, FR-08 |
| 06 | Health Monitoring Dashboard | FR-09, FR-10 |
| 07 | Admin — users & knowledge-base documents | FR-12 |

(FR-11 — history/deletion — isn't a standalone screen; it's the delete action on the records/assessments already shown in 02/03/06, flagged as a `P1-FE-xxx` detail once that module is actually built, not a separate wireframe.)

## 2. Gate: cross-checked against each FR's acceptance criteria

Per `task_backlog.md`'s own gate for this task — every wireframe reviewed against the FR it covers:

- **FR-01 (Auth):** email/password fields, a password-confirmation field on register, and a forgot-password link are present. The wireframe doesn't show hashing/JWT mechanics (correctly — that's backend, not UI), but the note under "Create Account" exists as a reminder for whoever builds `P1-FE-002`.
- **FR-02 (Pet Profile):** every field `requirements.md` §5 lists for `Pet` has an input in the edit form (name, species, breed, sex, DOB, weight, allergies — plus a medical-history field). The "Archive pet" button is labeled explicitly as soft-delete, matching the Phase 0 schema decision in `schema-notes.md` §3, not a plain "Delete" that would misrepresent what the button does.
- **FR-03 (Health Records):** record types (visit/weight/note) match `HealthRecordType` in the schema; a weight field is conditionally relevant per type; attachment upload is present.
- **FR-04/05/06 (Symptom Checker) — the one with the most riding on it:** free-text input is primary and required; structured fields are explicitly marked optional (matching FR-04's acceptance criteria that empty free-text *and* no structured input gets rejected, not "all fields required"); the results panel shows, in order: an urgency banner, ranked concerns with confidence, home-care guidance, an explicit "when to see a vet" box, sources, and the disclaimer — all four of FR-05/FR-06's required elements are present and none of them are hideable or collapsed by default in this layout. The urgency banner and "when to see a vet" box are visually flagged (heavier red outline) as safety-critical, not decorative — intentional, not an accident of the wireframe tool's styling.
- **FR-07/FR-08 (Assistant Chat):** every assistant message shows a sources row; the disclaimer sits directly under the message it qualifies, not buried in a footer; a dedicated callout documents that the Safety Layer can interrupt the conversation with an Emergency banner — this is shown as a *behavior* note rather than a static element, since it only appears when triggered, and that distinction matters for whoever builds `P2-FE-002` off this wireframe.
- **FR-09/FR-10 (Dashboard):** all four required widgets (weight trend, reminders, assessments, record summary) are present, each with an explicit empty-state note — `requirements.md`'s acceptance criteria for FR-10 specifically calls out graceful empty states for new pets, so this isn't an afterthought.
- **FR-12 (Admin):** user list and knowledge-base document list are both present; the upload action is explicitly labeled as triggering re-indexing (matching FR-12's acceptance criteria) rather than a generic "Upload" button that hides what it does; a note ties the license field requirement back to `schema-notes.md` §5 (KnowledgeDocument's license is non-optional) so the admin UI and the schema decision stay consistent.

## 3. Gap found here — resolved during `P0-PD-007` consolidation

~~The Pet edit form includes a "Medical history" field that isn't a distinct column in the `requirements.md` §5 entity table or the `P0-BE-001` schema.~~ **Resolved.** Cross-checking against `requirements.md` FR-02's literal text confirmed the schema was missing this field, not the wireframe getting ahead of it — FR-02 lists "medical history" explicitly as a pet-profile attribute. `Pet.medical_history` (nullable text) was added to the schema; see `schema-notes.md` §8 for the full amendment note. The wireframe needed no change — it was correct as drawn.

## 4. What's deliberately NOT done here

Per this task's own scope (see `task_backlog.md`):
- No final visual design — colors, typography, spacing system, iconography are all a later pass, not this one.
- No interaction/prototype flow (click-through) — these are static layouts per screen.
- No mobile-specific layouts beyond the Symptom Checker screen's device label — responsive behavior is a frontend-build concern (`P1-FE-001` onward), not a wireframe concern.
