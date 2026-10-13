# PawCare — Symptom Dataset Batch 1 (As-Built)

**Task:** `P1-AI-002` · **Depends on:** `P1-AI-001` (✅)
**Trace:** `docs/design/symptom-dataset-strategy.md`, `requirements.md` §7, FR-04/FR-05,
`docs/design/safety/safety-rules-v1.yaml`
**Status:** Batch 1 collected/augmented, annotated, gated. Held-out set frozen
but `expert_review_status: pending`.

This document records what batch 1 actually is, as distinct from the `P1-AI-001`
strategy that specifies how it should be built. Code lives in
`apps/backend/app/services/symptom_dataset/`; artifacts in
`data/symptom_dataset/batch1/`.

## 1. What was built

| Source (strategy §2.1) | Batch-1 status |
|---|---|
| 1. KB-derived seed relationships | ✅ all 9 red flags grounded in cleared batch-1 KB sources (`seeds.py`) |
| 2. Public datasets | ⛔ none folded in — see `docs/legal/symptom-dataset-licensing-audit.md` (1 cleared-but-deferred, rest refused/out-of-scope) |
| 3. Synthetic owner-style augmentation | ✅ rule-based, seeded, 460 examples |
| 4. Expert-validated held-out set | ⚠ 16 hand-authored held-out examples, frozen, **expert review pending** |

## 2. Label schema (implemented)

Controlled vocabularies in `taxonomy.py`:

- **urgency** — `emergency` / `urgent` / `routine` / `home_care`
- **severity** — `mild` / `moderate` / `severe` / `unknown`
- **duration unit** — `hours` / `days` / `weeks` / `unknown`
- **body system** — the guideline's 7 (gastrointestinal, respiratory, urinary,
  neurologic, dermal, musculoskeletal, general) plus ophthalmic, hematologic,
  cardiovascular, toxicology, trauma, environmental
- **owner style** — `synthetic` / `paraphrased` / `normalized`

37 canonical **symptom concepts** (the `symptom_label` values), each with surface
forms, species applicability, candidate **concern tags**, and — for the 9
red-flag concepts — a `red_flag_id` copied from `safety-rules-v1.yaml`
(RF-001..RF-009). 26 **condition concepts** are the classifier targets for
`P1-AI-004`.

A **`Span`** carries: `text`, `start`, `end`, `symptom_label`, `body_system`,
`severity`, `duration_value`/`duration_unit`, `behavior_modifier`,
`appetite_modifier`, `owner_style`, `annotation_source`. An **`Example`** carries
the text, species, spans, derived `urgency` + `urgency_basis`, `concern_tags`,
`red_flag_ids`, `split`, and provenance.

## 3. How examples are produced and annotated

1. **Generate** (`generator.py`) — seeded (`random.Random(seed)`) text from each
   concept × species, varying duration, severity, appetite, behaviour and
   location, across three sentence frames. Generator writes text + provenance
   only.
2. **Annotate** (`annotator.py`) — a *separate* rule pass finds symptom spans by
   longest-match surface form, attaches modifiers found in the same sentence,
   parses durations by regex, and derives urgency. Because annotation re-derives
   labels from the text, a generator/annotator mismatch fails the gate instead of
   passing silently.
3. **Urgency** — red-flag precedence first (`emergency`, basis
   `red_flag:RF-00x`), then a conservative over-referral rule set:
   `severe → urgent`, persistent (≥3 days / ≥1 week) → `urgent`,
   `moderate → routine`, else `home_care`.

## 4. Split policy and quality gate

- Fixed deterministic split by a hash of `example_id`: **70 / 15 / 15**
  train / validation / test.
- The **held-out** set is separate (`held_out.jsonl`), never mixed into a
  training split, and covers emergency/urgent/routine/low-information.
- Quality gate (`validate`) refuses to write artifacts unless: every span label
  is in the taxonomy, body-system/severity/duration values are valid, span
  offsets match the text, every example is either labelled or explicitly
  `insufficient_information`, and every red-flag example is `emergency`.

## 5. Batch-1 numbers (seed 20261013)

**476 examples · 1,155 spans.**

| split | n |
|---|---|
| train | 311 |
| validation | 64 |
| test | 85 |
| held-out | 16 |

| urgency | n |  | species | n |
|---|---|---|---|---|
| emergency | 188 |  | dog | 239 |
| urgent | 74 |  | cat | 237 |
| routine | 190 | | | |
| home_care | 24 | | | |

Red-flag coverage: RF-001…RF-009 each ≥ 20 examples. Source mix: 460 synthetic,
16 handbook held-out. Full numbers in `manifest.json`.

## 6. Known limitations (carried forward, not hidden)

- **Synthetic-only training data.** Batch 1's training labels come from a rule
  generator + rule annotator, so they measure pipeline mechanics, not real
  owner-language distribution. Real owner text (consented) is required before
  any accuracy claim.
- **Held-out is not expert-validated.** `expert_review_status: pending`; do not
  report held-out metrics as validated until the veterinary advisory contact
  (`P0-PD-010`) reviews it.
- **Rule annotator, not the model.** `P1-AI-003` replaces this with the NER
  pipeline; this annotator is the baseline and the gate.
- **English owner-idiom coverage is template-limited.**

## 7. Regenerate

```bash
cd apps/backend
python scripts/build_symptom_dataset.py
```

Byte-identical `examples.jsonl` / `held_out.jsonl` for a fixed seed (only
`manifest.json`'s `generated_at` changes).
