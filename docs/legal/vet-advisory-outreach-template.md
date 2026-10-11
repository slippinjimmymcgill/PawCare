# PawCare — Veterinary Advisory Relationship

**Task:** `P0-PD-010` · **Trace:** `plan.md` §11 item 4 · **Status:** ⛔ **Blocked**

## Why This Is Blocked

This task requires a **real, named, human veterinary professional** who agrees to review PawCare's knowledge-base content and sampled outputs. That's a relationship Ismail has to form himself — it can't be simulated, assumed, or stood in for by research, since the entire point (per `task_backlog.md` §2.5) is that it be "a real person, confirmed, not an assumption carried forward silently." Nothing here is a knowledge gap the agent could close through research the way `P0-RAG-002` was.

**This is the one blocker with the widest blast radius** — the backlog is explicit that if it's still open by Sprint Block 9–10, that sprint block's exit gate does not clear (`P2-QA-001`'s expert-review gate and `P3-QA-003`'s post-integration expert review both assume this relationship exists), and `safety-rules-v1.yaml`'s `meta.reviewed_by`/`meta.last_reviewed` stay `null` — meaning the Safety Layer rule set stays formally "development/testing-only" — until this happens.

**What unblocks it:** Ismail (or the steering committee) identifies and confirms a willing veterinary contact — a practicing vet, a veterinary academic, or a vet-med student in an advanced/clinical year, per `plan.md`'s explicit allowance for "voluntary/academic consultation." Given the market context already researched for the proposal (`plan.md` §8 — Islamabad/Rawalpindi's existing clinic network, the Chubby Meows precedent), a local clinic or a NUST/veterinary-program academic contact are both plausible starting points, but who to actually approach is a judgment call this document isn't positioned to make on Ismail's behalf.

---

## Outreach Template (ready to send once a contact is identified)

*Use as a starting point — adjust tone/length for whether this goes to an unfamiliar clinic by email vs. a warmer personal/academic contact.*

> Subject: Volunteer veterinary advisor for a university AI/pet-health final-year project
>
> Hi [Name],
>
> I'm a final-year Computer Science student at NUST, building **PawCare** — an AI-assisted pet-health information and record-keeping tool for dog and cat owners, as my final-year design project under Dr. Shah Khalid and Mr. Muhammad Daud Abdullah Asif.
>
> PawCare is explicitly designed as decision-support and education, never diagnosis or prescription — it helps owners understand how urgent a symptom might be and always directs them to a real veterinarian for anything serious. To make sure that's actually true in practice, not just in intent, I'd like to ask for a small amount of your time as a volunteer veterinary advisor on the project. Specifically:
>
> 1. **A review of our rule-based "Safety Layer"** (the list of symptom red-flags that always trigger an emergency recommendation, plus our disclaimers) — about 30–45 minutes, reviewing a written document, no software involved.
> 2. **Later in the project** (around month 5–6), a short review of a sample of the system's actual outputs for dogs/cats, to flag anything that reads as unsafe, overconfident, or medically off.
>
> This is entirely voluntary/informal — not a contract, not paid work — and I'm happy to work around your schedule, over email or in person, whichever is easier. I can share the specific document (a few pages) whenever convenient.
>
> Would you be open to this? Happy to answer any questions first.
>
> Thanks,
> Ismail Jamal Tariq
> NUST, Department of Computer Science

---

## What Happens Once This Unblocks

1. Record the confirmed contact's name/affiliation here (replacing this task's ⛔ status with ✅), without needing to publish sensitive personal contact details in the repo — a first-name/affiliation reference is enough for traceability.
2. Send `safety-rules-v1.yaml` + `safety-rules-v1.md` for the first review (closes the `P0-RAG-001` loose end: `meta.reviewed_by`/`meta.last_reviewed` get filled in, and the open judgment call flagged in that task — whether the bleeding/heatstroke disclaimers' home-action lines cross into first-aid territory — gets an actual answer instead of sitting as a flagged question).
3. Note the relationship's confirmed cadence (one-off vs. ongoing through Sprint Block 9–10 and Phase 3) in `task_backlog.md`'s Progress Log, so later phases know what's actually been committed to versus hoped for.

## Recorded as Open Risk

This is the Phase 0 Exit Gate line item most likely to still be open when Phase 1 starts, and the backlog already accounts for that (Phase 1 doesn't depend on it; Sprint Block 9–10 does). Carried forward explicitly rather than quietly dropped — consistent with how `P0-OPS-004`/`P0-OPS-005` are handled above.
