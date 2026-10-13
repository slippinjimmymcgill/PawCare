"""PawCare — symptom dataset build pipeline (batch 1).

Task: P1-AI-002. Trace: docs/design/symptom-dataset-strategy.md §2, §6, §8.

Ties the batch together and writes the artifacts in ``data/symptom_dataset/batch1``:

1. generate synthetic owner-style text from the KB-derived seed patterns;
2. annotate every example with the rule-based annotator;
3. reserve a hand-authored held-out set (emergency/urgent/routine/low-info);
4. run the annotation quality gate;
5. assign the fixed 70/15/15 split and write ``examples.jsonl`` +
   ``held_out.jsonl`` + ``manifest.json``.

The held-out set is frozen but explicitly marked ``expert_review_status:
pending`` — batch 1 has no veterinary sign-off yet, and the manifest says so
rather than implying validation that did not happen (the same honesty rule the
Safety Layer's rule set uses).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from app.services.symptom_dataset.annotator import annotate_spans, derive_urgency
from app.services.symptom_dataset.generator import generate_examples
from app.services.symptom_dataset.taxonomy import (
    BODY_SYSTEMS,
    CONDITION_BY_ID,
    DURATION_UNITS,
    SEVERITIES,
    SYMPTOM_BY_ID,
    URGENCY_LEVELS,
    Example,
)

# .../app/services/symptom_dataset/pipeline.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "symptom_dataset" / "batch1"

DEFAULT_SEED = 20261013
SPLIT_POLICY = {"train": 0.70, "validation": 0.15, "test": 0.15}

_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://pawcare.local/symptom-dataset")

# Hand-authored held-out examples (strategy §2.1 item 4): a frozen slice that
# deliberately spans emergency / urgent / routine / low-information, so the
# guideline's stability can be measured without touching the training splits.
_HELDOUT_SEEDS: tuple[tuple[str, str, str], ...] = (
    ("My dog ate a whole bar of chocolate an hour ago and now he is vomiting.", "dog", "paraphrased"),
    ("My cat has been straining to urinate for hours and crying in the litter box.", "cat", "paraphrased"),
    ("Rex collapsed in the park and won't wake up.", "dog", "paraphrased"),
    ("She had a seizure this morning and is disoriented.", "dog", "paraphrased"),
    ("My dog's belly looks bloated and hard and he keeps trying to vomit but nothing comes up.", "dog", "paraphrased"),
    ("My cat is open-mouth breathing and gasping for air.", "cat", "paraphrased"),
    ("My dog got hit by a car but seems fine.", "dog", "paraphrased"),
    ("My cat was left in a hot car and is panting nonstop.", "cat", "paraphrased"),
    ("My dog has been vomiting for 3 days and is very weak.", "dog", "paraphrased"),
    ("My dog has been coughing at night for a week.", "dog", "paraphrased"),
    ("My cat has a mild cough for 2 days but is eating normally.", "cat", "paraphrased"),
    ("My dog is limping on the left front leg after the park.", "dog", "paraphrased"),
    ("My cat is scratching constantly and losing hair.", "cat", "paraphrased"),
    ("My dog has watery eyes and is sneezing a lot.", "dog", "paraphrased"),
    ("My cat is hiding under the bed and not eating.", "cat", "paraphrased"),
    ("She seems a bit off today, maybe upset stomach.", "cat", "normalized"),
)


class DatasetError(ValueError):
    """Raised when the built dataset fails the annotation quality gate."""


def _example_id(text: str, species: str, owner_style: str) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, f"example:{species}:{owner_style}:{text}"))


def _split_for(example_id: str) -> str:
    bucket = int(hashlib.sha1(example_id.encode("utf-8")).hexdigest(), 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _build_example(
    text: str,
    species: str,
    owner_style: str,
    *,
    split: str,
    annotation_source: str,
    provenance: dict,
) -> Example:
    spans = annotate_spans(
        text, species, owner_style=owner_style, annotation_source=annotation_source
    )
    urgency, basis = derive_urgency(spans)
    concern_tags = _unique(
        tag
        for span in spans
        for tag in SYMPTOM_BY_ID[span.symptom_label].concern_tags
        if species in CONDITION_BY_ID[tag].species
    ) or ["insufficient_information"]
    red_flag_ids = _unique(
        flag
        for span in spans
        if (flag := SYMPTOM_BY_ID[span.symptom_label].red_flag_id) is not None
    )
    return Example(
        example_id=_example_id(text, species, owner_style),
        text=text,
        species=species,
        spans=spans,
        urgency=urgency,
        urgency_basis=basis,
        concern_tags=concern_tags,
        red_flag_ids=red_flag_ids,
        split=split,
        owner_style=owner_style,
        provenance=provenance,
    )


def build_dataset(
    *,
    seed: int = DEFAULT_SEED,
    red_flag_count: int = 10,
    other_count: int = 5,
) -> list[Example]:
    """Generate + annotate the synthetic batch and append the held-out set."""
    examples: list[Example] = []
    for generated in generate_examples(
        seed=seed, red_flag_count=red_flag_count, other_count=other_count
    ):
        example = _build_example(
            generated.text,
            generated.species,
            "synthetic",
            split="",
            annotation_source="rule",
            provenance={
                "source": "synthetic_augmented",
                "generator": generated.provenance.get("generator", "rule_based_v1"),
                "intended_symptom_id": generated.intended_symptom_id,
                "template_id": generated.template_id,
                "kb_source_ids": generated.provenance.get("kb_source_ids", []),
            },
        )
        example.split = _split_for(example.example_id)
        examples.append(example)

    for text, species, owner_style in _HELDOUT_SEEDS:
        examples.append(
            _build_example(
                text,
                species,
                owner_style,
                split="held_out",
                annotation_source="manual",
                provenance={"source": "handbook_heldout", "review": "pending_expert_review"},
            )
        )
    return examples


def validate(examples: list[Example]) -> dict:
    """Annotation quality gate (strategy §6.2). Raises on any violation."""
    errors: list[str] = []
    for example in examples:
        if example.urgency not in URGENCY_LEVELS:
            errors.append(f"{example.example_id}: bad urgency {example.urgency!r}")
        if example.split not in {"train", "validation", "test", "held_out"}:
            errors.append(f"{example.example_id}: bad split {example.split!r}")
        if not example.spans and example.concern_tags != ["insufficient_information"]:
            errors.append(f"{example.example_id}: no spans and not flagged insufficient_information")
        for span in example.spans:
            concept = SYMPTOM_BY_ID.get(span.symptom_label)
            if concept is None:
                errors.append(f"{example.example_id}: unknown symptom_label {span.symptom_label!r}")
                continue
            if span.body_system not in BODY_SYSTEMS:
                errors.append(f"{example.example_id}: bad body_system {span.body_system!r}")
            if span.severity not in SEVERITIES:
                errors.append(f"{example.example_id}: bad severity {span.severity!r}")
            if span.duration_unit not in DURATION_UNITS:
                errors.append(f"{example.example_id}: bad duration_unit {span.duration_unit!r}")
            if example.text[span.start : span.end] != span.text:
                errors.append(
                    f"{example.example_id}: span offsets {span.start}:{span.end} do not match "
                    f"{span.text!r}"
                )
        if example.red_flag_ids and example.urgency != "emergency":
            errors.append(
                f"{example.example_id}: red flag {example.red_flag_ids} not forced to emergency"
            )
        if len(errors) > 25:
            break
    if errors:
        raise DatasetError("annotation quality gate failed:\n  " + "\n  ".join(errors))
    return summarize(examples)


def summarize(examples: list[Example]) -> dict:
    """Coverage stats the manifest exposes (strategy §6)."""
    by_split: Counter[str] = Counter()
    by_urgency: Counter[str] = Counter()
    by_species: Counter[str] = Counter()
    by_red_flag: Counter[str] = Counter()
    by_concern: Counter[str] = Counter()
    source_mix: Counter[str] = Counter()
    span_total = 0
    for example in examples:
        by_split[example.split] += 1
        by_urgency[example.urgency] += 1
        by_species[example.species] += 1
        source_mix[example.provenance.get("source", "unknown")] += 1
        span_total += len(example.spans)
        for flag in example.red_flag_ids:
            by_red_flag[flag] += 1
        for tag in example.concern_tags:
            by_concern[tag] += 1
    return {
        "example_count": len(examples),
        "span_count": span_total,
        "by_split": dict(sorted(by_split.items())),
        "by_urgency": dict(sorted(by_urgency.items())),
        "by_species": dict(sorted(by_species.items())),
        "red_flag_coverage": dict(sorted(by_red_flag.items())),
        "top_concerns": dict(by_concern.most_common(10)),
        "source_mix": dict(sorted(source_mix.items())),
    }


# Public dataset candidates reviewed for batch 1 (strategy §2.1 item 2). Kept in
# the manifest so the licensing decision is auditable next to the data.
PUBLIC_DATASET_AUDIT = (
    {"dataset": "PetEVAL (Farrell et al., ACL BioNLP 2025)", "license": "access-restricted (real EHRs)", "status": "refused"},
    {"dataset": "karenwky/pet-health-symptoms-dataset (HuggingFace)", "license": "MIT", "status": "cleared_but_deferred"},
    {"dataset": "Kaggle Animal/Veterinary health datasets", "license": "ambiguous / unspecified", "status": "refused"},
    {"dataset": "Zenodo Dog Health Vitals Dataset", "license": "CC BY 4.0", "status": "out_of_scope"},
)


def write_artifacts(examples: Iterable[Example], out_dir: str | Path = DEFAULT_OUT_DIR) -> dict:
    """Write examples.jsonl, held_out.jsonl and manifest.json; return the manifest."""
    examples = list(examples)
    stats = validate(examples)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    primary = [e for e in examples if e.split != "held_out"]
    held_out = [e for e in examples if e.split == "held_out"]

    _write_jsonl(out_dir / "examples.jsonl", (e.to_dict() for e in primary))
    _write_jsonl(out_dir / "held_out.jsonl", (e.to_dict() for e in held_out))

    manifest = {
        "task": "P1-AI-002",
        "artifact_schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "generation": {
            "seed": DEFAULT_SEED,
            "strategy": "knowledge_base_seeds + rule_based_synthetic_augmentation",
        },
        "taxonomy": {
            "symptom_concepts": len(SYMPTOM_BY_ID),
            "urgency_levels": list(URGENCY_LEVELS),
            "body_systems": list(BODY_SYSTEMS),
        },
        "split_policy": SPLIT_POLICY,
        "stats": stats,
        "public_dataset_audit": list(PUBLIC_DATASET_AUDIT),
        "expert_review_status": "pending",
        "expert_review_note": (
            "Held-out examples are frozen but not yet reviewed by the veterinary "
            "advisory contact (requirements.md §7 assumption); do not report "
            "held-out metrics as validated until that review happens."
        ),
        "artifacts": {
            "examples": "examples.jsonl",
            "held_out": "held_out.jsonl",
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict:
    """End-to-end: build, annotate, gate, and write batch-1 artifacts."""
    return write_artifacts(build_dataset(), out_dir)
