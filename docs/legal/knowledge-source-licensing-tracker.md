# PawCare — Knowledge-Source Licensing Tracking Sheet

**Task:** `P0-RAG-002` · **Trace:** `specs.md` §8 · **Status:** ✅ Complete
**Purpose:** One row per candidate veterinary knowledge source, with license type, attribution requirement, and redistribution/derivative-use permission — verified by reading each source's actual terms of use/copyright policy (live web research, dated below), not assumed from reputation or apparent public availability. "Found on the internet" is explicitly not a license (per this task's Do NOT clause and `P1-RAG-001`'s gate).

This sheet feeds `P1-RAG-001` (Knowledge-source identification & licensing audit), which will expand it with the specific symptom/condition coverage each cleared source provides.

---

## 1. How to Read This Sheet

- **Status:**
  - 🟢 **Cleared** — openly licensed, redistribution/derivative use permitted under stated terms (attribution honored).
  - 🔴 **Restricted** — all-rights-reserved or permission-gated; reuse requires a case-by-case request that has not been made/granted. Do not ingest until/unless that permission is obtained and recorded here.
  - 🟡 **Ambiguous** — conflicting or unclear terms on the source's own site. Flagged per this task's explicit instruction not to guess in PawCare's favor. Do not ingest until clarified.
- **Verified:** date this row's license info was actually checked against the source's live terms-of-use/copyright page (not the project's general knowledge), so staleness is visible at a glance.

---

## 2. Tracking Sheet

| # | Source | License Type | Attribution Required? | Redistribution / Derivative Use Permitted? | Status | Verified | Link |
|---|---|---|---|---|---|---|---|
| 1 | Merck/MSD Veterinary Manual (professional & owner editions) | All rights reserved; site is for "personal, non-commercial use" | Yes, if permission granted | No — anything beyond personal non-commercial use requires a formal permissions request to Merck | 🔴 Restricted | 2026-10-06 | [merckvetmanual.com](https://www.merckvetmanual.com) |
| 2 | WSAVA Global Nutrition Guidelines (and other WSAVA guideline documents) | Copyrighted; WSAVA "welcomes reproduction" for education but requires following their SOP | Yes | Conditional — requires submitting WSAVA's own reuse-request form per their SOP; not a standing open license | 🔴 Restricted | 2026-10-06 | [wsava.org](https://wsava.org) |
| 3 | AAHA Guidelines (vaccination, senior care, etc.) | Copyrighted, no open license | Yes, if permission granted | No — requires direct email contact with AAHA for any reuse | 🔴 Restricted | 2026-10-06 | [aaha.org](https://www.aaha.org) |
| 4 | ASPCA website content, incl. Animal Poison Control summaries | All rights reserved; site is for "educational, informational, personal, noncommercial purposes" | Yes, if permission granted (exact notice text specified) | No — requires submitting ASPCA's Website Reprint Request form, case-by-case approval, no content alteration | 🔴 Restricted | 2026-10-08 | [aspca.org copyright policy](https://aspca.org/node/548) |
| 5 | PetMD articles | "Owned and copyrighted by PetMD unless otherwise noted" | Yes, if permission granted | No — modifying, copying, distributing, or republishing requires PetMD's prior approval; commercial use of PetMD content is explicitly "STRICTLY PROHIBITED" | 🔴 Restricted | 2026-10-08 | [petmd.com/legal-notices](https://petmd.com/legal-notices) |
| 6 | VCA Animal Hospitals articles | All rights reserved | Not applicable (reuse not permitted) | No — personal use only; modification, redistribution, or reposting for public/commercial purposes is "strictly prohibited" without express written permission | 🔴 Restricted | 2026-10-08 | [vcahospitals.com/terms-and-conditions](https://vcahospitals.com/terms-and-conditions) |
| 7 | WikiVet (veterinary education wiki, Royal Veterinary College / RCVS-affiliated) | Conflicting on the source's own site — main text claims CC BY 3.0 (commercial use allowed), modified-reuse clause requires CC BY-SA 3.0+, but the site footer claims CC BY-NC-ND (non-commercial, no derivatives) | Yes, under any of the cited licenses | **Unresolved by the source itself** — the three license statements on WikiVet's own Terms of Service page contradict each other on whether commercial/derivative use is allowed | 🟡 Ambiguous | 2026-10-08 | [en.wikivet.net Terms of Service](https://en.wikivet.net/WikiVet:Terms_of_Service) |
| 8 | Open Veterinary Journal (OVJ) | Creative Commons **CC BY-NC 4.0** | Yes (attribution) | Yes, for non-commercial use; derivatives permitted with attribution | 🟢 Cleared (non-commercial use only — see §3 note below) | 2026-10-06 | [openveterinaryjournal.com](https://openveterinaryjournal.com) |
| 9 | Journal of Veterinary Research (Polish NIVR) | Creative Commons **CC BY 4.0** | Yes (attribution) | Yes, including commercial use and derivatives | 🟢 Cleared | 2026-10-06 | [jvetres.com](https://jvetres.com) |
| 10 | Veterinary Record Open (BVA/BMJ) | Creative Commons **CC BY 4.0** (per BMJ open-access policy) | Yes (attribution) | Yes, including commercial use and derivatives | 🟢 Cleared | 2026-10-06 | [bvajournals.onlinelibrary.wiley.com](https://bvajournals.onlinelibrary.wiley.com) |
| 11 | Journal of Veterinary Internal Medicine (JVIM) | Open access since 2015; individual articles carry their own CC license (commonly CC BY or CC BY-NC, varies per article) | Yes (attribution) | Varies per article — **must be checked per article, not assumed at journal level** | 🟢 Cleared, per-article check required | 2026-10-06 | [onlinelibrary.wiley.com/journal/19391676](https://onlinelibrary.wiley.com/journal/19391676) |
| 12 | MDPI *Animals* (veterinary/animal-science open-access journal) | Creative Commons **CC BY 4.0** (MDPI's standard license for all published articles) | Yes (attribution) | Yes, including commercial use and derivatives | 🟢 Cleared | 2026-10-08 | [mdpi.com/journal/animals](https://www.mdpi.com/journal/animals) |

---

## 3. Notes & Flags Carried to `P1-RAG-001`

- **Pattern observed:** every major consumer-facing / clinical-brand veterinary reference site checked (Merck/MSD, WSAVA, AAHA, ASPCA, PetMD, VCA) is **all-rights-reserved or permission-gated** — none grant a standing open license for redistribution, regardless of how freely the content reads on the page. This confirms the project's working assumption that "freely readable" and "freely reusable" are different things, and that the viable path for PawCare's knowledge base is **open-access veterinary journal literature**, not consumer health-content brands.
- **OVJ (row 8) is non-commercial only (CC BY-NC).** PawCare is an academic FYP today, but if a post-FYP commercial track (`plan.md` §8, `plan.md` §11 item 6) is pursued, OVJ-derived chunks would need to be re-flagged or excluded at that point — tagged here now so `PX-RAG-ONGOING-001` catches it later rather than this being rediscovered the hard way.
- **WikiVet (row 7) is flagged ambiguous, not excluded or included.** Per this task's explicit instruction, ambiguous licensing is reported as ambiguous rather than resolved optimistically. If WikiVet content is wanted later, the concrete next step is emailing WikiVet to ask which of their three conflicting license statements actually governs reuse — not inferring the most permissive one.
- **JVIM (row 11) requires per-article checking.** Journal-level "open access since 2015" does not mean every individual article carries the same license; `P1-RAG-001` should record the license actually printed on each article page it draws from, not the journal's general policy.
- **Coverage gap to flag for `P1-RAG-001`:** the cleared sources (rows 8–12) are academic journal articles — rigorous, but not written as owner-facing symptom/triage material, and not indexed by common-symptom the way a clinical manual is. `P1-RAG-001`'s 3-day audit should explicitly search for further CC-licensed, owner-facing veterinary content (e.g., university extension-service pet-health pages, government/public-health animal-health pages, open courseware) rather than assuming journal articles alone are sufficient to cover the red-flag symptom categories in `P0-RAG-001`'s rule set — this sheet's Acceptance Criteria depends on that coverage existing, and right now it's not yet demonstrated.
- **None of the cleared sources were ingested as part of this task.** This task is the licensing sheet only (per its Do NOT clause carried over from `P1-RAG-001`'s own scope note) — no chunking, no content pulled, nothing beyond recording what's legally usable.
