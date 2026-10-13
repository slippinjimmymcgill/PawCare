# PawCare — Symptom Dataset, Batch 1

**Task:** `P1-AI-002` (symptom dataset collection/augmentation + annotation)
**Trace:** `docs/design/symptom-dataset-strategy.md` (P1-AI-001) ·
`docs/design/symptom-dataset-batch1.md` · `docs/task_backlog.md`
**Generated:** 2026-10-13 · **Status:** complete; held-out set frozen, expert review pending

Batch 1 of the symptom dataset for the triage/assessment pipeline. It is built
from (a) knowledge-base-derived seed relationships and (b) rule-based synthetic
augmentation of owner-style text, annotated with the P1-AI-001 guideline. No
public dataset is folded in (see the licensing audit).

## Layout

```
batch1/
  examples.jsonl    # train + validation + test examples, one JSON object per line
  held_out.jsonl    # frozen held-out slice (emergency/urgent/routine/low-info)
  manifest.json     # counts, taxonomy version, split policy, public-dataset audit
```

Each example:

```json
{
  "example_id": "uuid5",
  "text": "My dog has been vomiting for 2 days and is very weak.",
  "species": "dog",
  "spans": [
    {"text": "vomiting", "start": 16, "end": 24, "symptom_label": "vomiting",
     "body_system": "gastrointestinal", "severity": "severe",
     "duration_value": 2, "duration_unit": "days",
     "behavior_modifier": "weak", "appetite_modifier": null,
     "owner_style": "synthetic", "annotation_source": "rule"}
  ],
  "urgency": "urgent",
  "urgency_basis": "severity:severe",
  "concern_tags": ["gastroenteritis"],
  "red_flag_ids": [],
  "split": "train",
  "owner_style": "synthetic",
  "provenance": {"source": "synthetic_augmented", "intended_symptom_id": "vomiting"}
}
```

## Licensing

Every knowledge-base seed cites a cleared batch-1 KB source
(`data/knowledge_base/batch1/manifest.json`). Public-dataset candidates were
audited against the same licensing gate as `P1-RAG-001`; results are in the
manifest and `docs/legal/symptom-dataset-licensing-audit.md`. The one
license-clear candidate (MIT) was deferred for label-schema mismatch, not
refused for licensing.

## Provenance & honesty

`provenance.source` is one of `synthetic_augmented` or `handbook_heldout`.
Batch 1's training labels are synthetic (rule generator + rule annotator); they
validate the pipeline, not real-world accuracy. The held-out examples are frozen
but **not yet expert-validated** — the manifest says `expert_review_status:
pending`, and held-out metrics must not be reported as validated until the
veterinary advisory contact reviews them.

## Regenerate

```bash
cd apps/backend
python scripts/build_symptom_dataset.py
```

The seed is fixed, so a re-run is byte-identical except for `manifest.json`'s
`generated_at`.

## Next

`P1-AI-003` (NLP symptom-extraction pipeline) trains/evaluates against
`examples.jsonl`; `P1-AI-004` (symptom→condition classifier) uses
`concern_tags`; `P1-AI-005` (urgency triage) uses `urgency`. `P2-AI-001`
iterates on the held-out set once it has been expert-validated.
