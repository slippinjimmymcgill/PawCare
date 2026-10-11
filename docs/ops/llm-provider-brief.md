# PawCare — LLM API Account & Key Provisioning

**Task:** `P0-OPS-004` · **Trace:** `requirements.md` §6, `plan.md` §11 item 2 · **Status:** ⛔ **Blocked**

## Why This Is Blocked

This task requires creating and holding a **billed, credentialed account** with a third-party LLM provider — a real payment method, an account owner's identity, and an API key tied to that account. That's a decision and a financial/legal commitment that has to be made and held by a real person (Ismail, or whoever the project's steering committee designates — `plan.md` §11 item 2 is explicitly listed as an "open decision" for that reason), not something that can be created on someone's behalf. There's also no account to provision the key *into* yet, since provider choice is itself the open decision.

This is not a research gap — the comparison work below is done. It's an account/credential dependency, the same category as `P0-OPS-005` below and distinct from `P0-PD-010` (which is a *relationship* dependency, not a credential one).

**What unblocks it:** a decision on provider (from the list below), then the account owner creating the account and generating a key. Once that happens, provisioning the key into `apps/backend/.env` (already templated in `P0-OPS-003`'s `.env.example` as `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_API_BASE_URL`) is a 5-minute task, not a multi-day one — the actual work here was narrowing the decision, below.

---

## Provider Comparison (to inform the steering-committee decision)

| Provider | Relevant model tier | Notes for PawCare's use case |
|---|---|---|
| **OpenAI API** | GPT-4o / GPT-4o-mini class | Named explicitly as the example provider in `requirements.md` §6 and `specs.md` §8. Mature function-calling/structured-output support, which helps for FR-05's ranked-concern + confidence + urgency schema and FR-07's citation format. Pay-as-you-go billing, no minimum spend. |
| **Anthropic API (Claude)** | Claude Haiku / Sonnet class | Strong instruction-following for the Safety Layer's output constraints (`OC-001`–`OC-006` in `safety-rules-v1.yaml`) — relevant since FR-08 depends on the model actually respecting "never generate a diagnosis/prescription" as a standing instruction, not just a post-hoc filter. Also pay-as-you-go. |
| **Google Gemini API** | Gemini 1.5/2.0 Flash class | Generous free tier historically, useful for an unfunded student project's early iteration (Sprint Block 7–8 prototyping) before committing to paid usage at scale. |
| **Open-weight model via a hosted inference API** (e.g., Groq, Together AI running Llama/Mistral-class models) | Varies | Lower per-token cost, but weaker out-of-the-box grounding/instruction-following for a safety-critical use case — would need more prompt-engineering/evaluation work in `P2-RAG-002`/`P2-RAG-003` to reach the same reliability bar. Worth a line item in `plan.md`'s risk register as a cost-reduction fallback, not a first choice. |

**Decision factors specific to this project** (for whoever makes the call):
- **Cost at FYP scale** is small regardless of provider — the real driver should be instruction-following reliability for the Safety Layer (FR-08) and structured-output quality (FR-05, FR-07), not price, until a post-FYP scale decision (`plan.md` §11 items 5–6) is reached.
- **Data residency / privacy** (also flagged as part of `plan.md` §11 item 2): none of the four options above offer in-Pakistan data residency; this is a known constraint to disclose in the privacy policy (`P0-PD-009` below), not something this brief can resolve.
- **Provider lock-in**: `requirements.md` §6 already calls for a "provider-agnostic abstraction" — recommend `P1-BE-001`'s FastAPI scaffold wrap whichever provider is chosen behind a thin internal interface (e.g., a `LLMClient` protocol) specifically so this decision doesn't have to be revisited at the code level later, only at the `.env` level.

## Supporting Artifact Delivered Now

- `apps/backend/.env.example`'s `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_API_BASE_URL` fields (from `P0-OPS-003`) are already in place and intentionally blank, with a comment pointing back to this blocker, so nothing downstream silently assumes a provider that hasn't been chosen.

## Recorded as Open Risk

Carried forward into the Phase 0 Exit Gate and `plan.md` §11 item 2 — flagged there as unresolved, not silently dropped. Per `plan.md` §12, this is routed to the steering committee, not decided unilaterally here.
