# PawCare — Veterinary Safety Layer Rule Set v1 (P0-RAG-001)

**Status:** Phase 0 design draft — **specification only**, not implemented in code. `P2-RAG-004` (Phase 2, Sprint Block 9–10) builds the actual override engine against this file.
**Review status:** **UNREVIEWED.** `safety-rules-v1.yaml`'s `meta.reviewed_by` / `meta.last_reviewed` are `null` until the veterinary advisory contact (`P0-PD-010`) has actually looked at this. Treat v1 as sufficient for development and testing only, not as a cleared safety artifact.
**Trace:** `requirements.md` FR-08, `requirements.md` §7 (hard constraints), `plan.md` §10.
**Companion file:** `safety-rules-v1.yaml` — the machine-readable rule set this document explains and governs.

---

## 1. Why this is a separate file from the prompt/code

The whole point of the Safety Layer, per `requirements.md` FR-08 and `plan.md` §2's architecture, is that it sits **after** the classifier/LLM output and **before** the user, and can override both — independently of whatever the AI components decided. If the red-flag list and output constraints lived only inside a prompt string, "independently" wouldn't be true: a prompt is something the LLM can be talked around, mis-weighted against other instructions, or silently drift from as the prompt gets edited for unrelated reasons. A versioned, reviewed, structured file that `P2-RAG-004` loads and checks against deterministically is what makes the override real rather than aspirational.

## 2. What v1 covers

- **9 red-flag categories** (`safety-rules-v1.yaml` → `red_flags`), each forcing `urgency: emergency` regardless of model confidence — respiratory distress, collapse/unresponsiveness, seizures, uncontrolled bleeding, suspected toxin ingestion, GDV/bloat presentation, urinary obstruction, severe trauma, and heatstroke. This list matches the categories named in the source proposal's Safety Layer section; nothing was added or dropped, only structured and given rationale per category.
- **A confidence/uncertainty policy** — a placeholder threshold (0.50, explicitly marked as untuned), an over-referral bias stated as a *permanent design decision* rather than a temporary default, and an explicit statement that red-flag rules take precedence over the classifier no matter how confident the model is.
- **Four disclaimer templates** — standard, emergency, uncertainty, and toxin-exposure-specific — covering every case `requirements.md` FR-06/FR-08 requires a disclaimer for.
- **6 output constraints** (`OC-001`–`OC-006`) — the hard "never state a diagnosis / never give a dosage / always cite sources / red flags can't be bypassed" rules from `requirements.md` §7, written as checkable statements rather than prose.

## 3. Deliberate scope decisions

- **`trigger_terms` are illustrative, not exhaustive.** They're a starting point for whatever matching approach `P2-RAG-004` ends up using (keyword matching, embedding similarity, or the NLP pipeline from `P1-AI-003`) — they are explicitly not a claim that this is a complete list of how owners phrase these symptoms. The annotated dataset from `P1-AI-002` is the real source of coverage; this file seeds it, it doesn't replace it.
- **The toxin-ingestion category is intentionally broad.** Real owner behavior under-reports urgency here ("she only had a little chocolate") — the rule is written to trigger on a plausible mention, not a confirmed large exposure, because the failure mode of triggering Emergency on a small, harmless exposure (a mildly annoyed owner) is far cheaper than the failure mode of not triggering it on a genuinely dangerous one.
- **Urinary obstruction is not narrowed to "male cats only"**, even though that's the textbook highest-risk group, because other presentations (severe UTIs, other species/sexes) are also time-sensitive and a narrower rule risks under-triaging them. This is flagged explicitly in the YAML (`species_note`) so a future "optimization" doesn't quietly narrow it without realizing why it was broad.
- **No home first-aid instructions for any red-flag category.** This was a close call for bleeding and heatstroke, where some home action is genuinely often appropriate (apply pressure; move to shade) — v1 draws the line at one short, generic action folded into the disclaimer itself ("move to shade/AC and offer water on the way to a vet") rather than step-by-step first-aid instructions, because step-by-step guidance is exactly the kind of substance- and situation-specific content `requirements.md` §7 asks the system to stay out of. This line is worth the veterinary reviewer's explicit attention — it's a judgment call, not a clear-cut rule.

## 4. What's explicitly out of this file's scope

- **Non-emergency home-care guidance content** (what FR-06 allows for Routine/Home-care cases) isn't specified here — that's general wellness content sourced from the knowledge base (`P1-RAG-001` onward), not a safety override rule. This file only governs the emergency/uncertainty/constraint side.
- **The actual NLP/matching implementation** — how `trigger_terms` become real detection logic — is `P2-RAG-004`'s job, not this task's.
- **Prompt text for the LLM** — `P2-RAG-002` (prompt engineering) consumes `output_constraints` and `disclaimers` as requirements the prompt must satisfy, but the prompt wording itself isn't written here.

## 5. Governance — how this file changes

Per `safety-rules-v1.yaml`'s own `meta.change_policy`:

- Any edit to `red_flags`, `confidence_policy`, or `output_constraints` requires a **version bump** (v2, v3, …), not an in-place edit — once `P2-RAG-004` is built against v1, silently changing v1 underneath it is how a safety regression ships unnoticed.
- **Adding** a red flag later (e.g. from real evaluation data surfacing a missed category) goes through the same veterinary review as the original set. "It's just an addition" is not a lighter bar — an addition can still be wrong (overly broad, overly narrow, or categorized incorrectly).
- The **over-referral bias is marked as permanent**, specifically to pre-empt a plausible future "optimization": tightening it to reduce false-positive referrals without a matching improvement in model confidence would be a safety regression dressed up as a UX improvement. Any change to this specific policy should get veterinary sign-off, not just an engineering review.

## 6. Immediate next step

This file is the input to `P0-PD-010` (confirm veterinary advisory relationship) having something concrete to review, rather than an abstract request for "general veterinary input." Once that review happens, `meta.reviewed_by` / `meta.last_reviewed` in the YAML get filled in — that's the signal `P2-RAG-004` should check before treating this as more than a development-time default.
