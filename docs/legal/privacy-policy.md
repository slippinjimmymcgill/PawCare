# PawCare — Data Protection / Privacy Policy (Draft)

**Task:** `P0-PD-009` · **Trace:** `plan.md` §7 · **Status:** ✅ Complete (draft — academic-project scope, not a formal regulatory filing)
**Scope note:** Written at the scope stated in the task description — an academic FYP's privacy policy, covering what data PawCare actually collects and how it's handled during the project, not a GDPR/formal-regulator filing. If a post-FYP track is pursued (`plan.md` §11 items 5–6), this needs a real legal/compliance review against whatever jurisdiction(s) that track targets — flagged, not resolved, here.

---

## PawCare — Privacy Policy (Draft)

*Last updated: [date of actual publication] · Version 0.1 (FYP demo scope)*

### 1. What Data PawCare Collects

| Category | Examples | Why it's collected |
|---|---|---|
| Account data | Email, hashed password | Authentication (FR-01). Passwords are hashed (bcrypt/argon2 per `requirements.md` §4) — PawCare never stores or can recover your plaintext password. |
| Pet profile data | Species, breed, age, sex, weight, medical history, allergies, medications | Core functionality (FR-02) — personalizes assessments and reminders to the specific pet. |
| Health records | Vaccinations, medications, vet visits, weight logs, notes, attached documents/images | Core functionality (FR-03) — context the AI components read from. |
| Symptom assessments & chat history | Free-text symptom descriptions, structured inputs, assistant conversations | Core functionality (FR-04–FR-07); retained per-pet so you can review past assessments (FR-11), deletable by you at any time. |
| Feedback | Ratings on assessments/assistant answers | FR-13 — used to evaluate and improve the system during the project. |
| Technical/usage data | Login timestamps, basic request logs | Security (detecting abuse) and debugging during development; not used for profiling or advertising — PawCare has no advertising. |

**What PawCare does not collect:** payment information (no payment is taken in the FYP demo scope), precise device location, or any data not listed above. If a future version collects additional categories, this policy will be updated and users notified — not silently expanded.

### 2. How Data Is Used

- To provide the service itself: storing your pet's records, running symptom assessments, powering the assistant, generating reminders, showing your dashboard.
- To evaluate the system as part of the FYP's own evaluation plan (`plan.md` §9/§11) — e.g., aggregate, where feasible de-identified, usage patterns to measure things like assessment accuracy or usability study results (`requirements.md` §4, `P3-QA-004`'s SUS study). Where the usability study or expert review (`P3-QA-003`) needs identifiable session data rather than aggregate patterns, participants are informed and asked for separate, explicit consent as part of that study — not assumed under this general policy.
- **Not** used to train or fine-tune any third-party LLM provider's foundation models — per `requirements.md` §7's explicit assumption that no real personal user data is used for model training without explicit consent. Any future change to this (e.g., building a PawCare-specific fine-tuned model) would need that consent sought directly, not retrofitted into this policy's general language.

### 3. Third Parties Data Is Shared With

PawCare's architecture (`plan.md` §2, `requirements.md` §6) depends on a small number of external services, so data necessarily passes through them:

| Third party | What it sees | Why |
|---|---|---|
| LLM provider (blocked on `P0-OPS-004` — provider not yet chosen) | The text of your symptom descriptions and assistant chat messages, and pet-profile context relevant to the request, sent as part of generating a response | Required for FR-04–FR-07 to function at all — no on-device/local alternative is in scope for this project. |
| Hosting providers (Vercel, Render, managed PostgreSQL — blocked on `P0-OPS-005`) | All stored data, as the infrastructure it physically runs on | Standard hosting dependency; these providers do not use PawCare's data for their own purposes beyond providing the hosting service, per their own terms. |
| Object storage provider (for attachments, FR-03) | Uploaded documents/images | Required to store and retrieve health-record attachments. |

**No data is sold, and no data is shared for advertising purposes** — PawCare has no advertising/monetization in the FYP scope, and any future monetization decision (`plan.md` §11 item 5) would need this policy revisited explicitly, not assumed to already permit it.

**Data residency note (consistent with `P0-OPS-004`'s LLM provider brief):** none of the LLM providers under consideration currently offer in-Pakistan data residency. This is disclosed here as a known limitation of the FYP-scope architecture, not something this policy resolves — a real deployment serving Pakistani users at scale would need this revisited as part of the `plan.md` §11 item 6 legal-review trigger.

### 4. Data Retention & Deletion

- Health records and pet profiles are retained for as long as your account exists.
- Symptom-assessment and chat history can be deleted by you at any time (FR-11); deletion is irreversible once confirmed, consistent with `requirements.md` FR-11's acceptance criteria.
- Deleting your pet's profile follows the documented soft-delete policy from `docs/design/schema-notes.md` (§2 of that document) — records are archived, not immediately hard-deleted, except via an explicit separate erasure action. This policy should be read alongside that document rather than restating its mechanics independently, so the two don't drift.
- On account deletion, all associated pet profiles, records, and history are scheduled for erasure; the exact timeline (immediate vs. a short grace period) is an implementation decision for `P1-BE-003`, not fixed by this policy yet.

### 5. Security Measures

Matching `requirements.md` §4's NFR table: hashed passwords (bcrypt/argon2), JWT-based sessions with expiry, HTTPS for all traffic, role-based access control (owner vs. admin), input validation, and secrets kept out of source control (enforced structurally — see `P0-OPS-003`'s `.env.example` pattern, where real secrets never enter the repo).

### 6. Your Rights

- Access: you can view all your stored pet/health data through the dashboard and records UI.
- Correction: you can edit pet profiles and records directly (FR-02, FR-03).
- Deletion: per §4 above.
- Questions: [project contact — to be filled in before any user-facing deployment beyond the FYP demo].

### 7. Children's Data

PawCare's Terms of Use (`P0-PD-008`) require users to be at least 18 (or the local age of majority). PawCare does not knowingly collect data from minors; if this is discovered, the account and associated data are removed.

### 8. Changes to This Policy

As with the Terms of Use, material changes are surfaced to users at next login rather than applied silently — consistent with `requirements.md` §9's change-control principle of amendments over silent edits.

---

## Consistency Check Performed As Part of This Task

Read `requirements.md` §4 (NFR table), §7 (constraints/assumptions), and FR-11 to confirm this policy doesn't promise anything the system doesn't actually do (e.g., doesn't claim a specific deletion timeline the schema doesn't yet enforce) and doesn't omit anything those sections require (e.g., the no-training-without-consent assumption is reflected in §2 above, not left out). Also cross-checked against `docs/design/schema-notes.md`'s soft-delete design so §4 above describes the real mechanism rather than an idealized one.

## What's Deliberately Not Decided Here

- Exact account-deletion grace period (implementation decision, `P1-BE-003`).
- Formal regulatory classification (GDPR/local data-protection-law applicability) — out of scope at FYP scale per this task's own scope note; a real trigger for revisiting this is `plan.md` §11 item 6.
- Cookie/analytics-specific disclosures — not yet applicable since no analytics/tracking tooling has been chosen; add when one is.
