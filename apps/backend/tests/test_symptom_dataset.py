from __future__ import annotations

import json

import pytest

from app.services.symptom_dataset.annotator import annotate_spans, derive_urgency, parse_duration
from app.services.symptom_dataset.generator import generate_examples
from app.services.symptom_dataset.pipeline import (
    DatasetError,
    build_dataset,
    run,
    summarize,
    validate,
    write_artifacts,
)
from app.services.symptom_dataset.seeds import (
    SEED_RELATIONSHIPS,
    build_seed_relationships,
    kb_sources_for,
)
from app.services.symptom_dataset.taxonomy import (
    BODY_SYSTEMS,
    CONDITION_BY_ID,
    RED_FLAG_BY_ID,
    SPECIES,
    SYMPTOM_BY_ID,
    URGENCY_LEVELS,
    Example,
    Span,
)


# ── Taxonomy ─────────────────────────────────────────────────────────────────


def test_taxonomy_ids_and_vocabularies_are_consistent():
    assert len(SYMPTOM_BY_ID) == len({c.id for c in SYMPTOM_BY_ID.values()})
    for concept in SYMPTOM_BY_ID.values():
        assert concept.body_system in BODY_SYSTEMS
        assert set(concept.species) <= set(SPECIES)
        for tag in concept.concern_tags:
            assert tag in CONDITION_BY_ID
        if concept.red_flag_id is not None:
            assert concept.red_flag_id in RED_FLAG_BY_ID


def test_red_flags_match_safety_rules_ids():
    assert set(RED_FLAG_BY_ID) == {f"RF-00{i}" for i in range(1, 10)}


# ── Seeds ────────────────────────────────────────────────────────────────────


def test_seed_relationships_cover_all_red_flags_and_ground_them():
    relationships = build_seed_relationships()
    grounded = {r.red_flag_id for r in relationships if r.grounding == "knowledge_base"}
    assert grounded == set(RED_FLAG_BY_ID)
    for relationship in relationships:
        if relationship.grounding == "knowledge_base":
            assert relationship.kb_source_ids
            assert relationship.urgency_hint == "emergency"


def test_kb_sources_for_heuristic_concept_is_empty():
    concept = next(c for c in SYMPTOM_BY_ID.values() if not c.is_red_flag)
    assert kb_sources_for(concept) == ()
    assert any(r.grounding == "clinical_heuristic" for r in SEED_RELATIONSHIPS)


# ── Annotator ────────────────────────────────────────────────────────────────


def test_annotate_extracts_symptom_and_modifiers():
    text = "My dog has been vomiting for 2 days and is very weak."
    spans = annotate_spans(text, "dog")
    labels = {span.symptom_label for span in spans}
    assert "vomiting" in labels
    vomiting = next(span for span in spans if span.symptom_label == "vomiting")
    assert (vomiting.duration_value, vomiting.duration_unit) == (2, "days")
    assert vomiting.severity == "severe"
    assert vomiting.body_system == "gastrointestinal"
    for span in spans:
        assert text[span.start : span.end] == span.text


def test_annotate_prefers_longest_overlapping_surface():
    spans = annotate_spans("My dog has bloody diarrhea today.", "dog")
    labels = [span.symptom_label for span in spans]
    assert "bloody_diarrhea" in labels
    assert "diarrhea" not in labels


def test_red_flag_precedence_forces_emergency():
    spans = annotate_spans("My dog ate a bar of chocolate.", "dog")
    urgency, basis = derive_urgency(spans)
    assert urgency == "emergency"
    assert basis == "red_flag:RF-005"


def test_derive_urgency_levels():
    no_spans = derive_urgency([])
    assert no_spans == ("routine", "insufficient_information")
    mild = annotate_spans("My dog is scratching constantly.", "dog")
    assert derive_urgency(mild)[0] == "home_care"
    persistent = annotate_spans("My dog has been coughing for 3 days.", "dog")
    assert derive_urgency(persistent) == ("urgent", "duration:persistent")


def test_parse_duration_variants():
    assert parse_duration("vomiting for 2 days") == (2, "days")
    assert parse_duration("sick since last night") == (1, "hours")
    assert parse_duration("for a few hours") == (3, "hours")
    assert parse_duration("no duration here") == (None, "unknown")


# ── Generator ────────────────────────────────────────────────────────────────


def test_generator_is_deterministic_and_contains_surface():
    first = generate_examples(seed=7, red_flag_count=3, other_count=2)
    second = generate_examples(seed=7, red_flag_count=3, other_count=2)
    assert [g.text for g in first] == [g.text for g in second]
    assert first
    for generated in first:
        concept = SYMPTOM_BY_ID[generated.intended_symptom_id]
        assert any(surface.lower() in generated.text.lower() for surface in concept.surface_forms)


def test_generator_different_seed_differs():
    a = [g.text for g in generate_examples(seed=1, red_flag_count=3, other_count=2)]
    b = [g.text for g in generate_examples(seed=2, red_flag_count=3, other_count=2)]
    assert a != b


# ── Pipeline ─────────────────────────────────────────────────────────────────


def test_build_dataset_is_deterministic_and_gated():
    first = build_dataset(seed=99, red_flag_count=3, other_count=2)
    second = build_dataset(seed=99, red_flag_count=3, other_count=2)
    assert [e.example_id for e in first] == [e.example_id for e in second]
    stats = validate(first)
    assert stats["example_count"] == len(first)
    assert set(stats["red_flag_coverage"]) == set(RED_FLAG_BY_ID)


def test_build_dataset_covers_all_urgency_levels_and_splits():
    examples = build_dataset()
    by_urgency = {e.urgency for e in examples}
    assert by_urgency == set(URGENCY_LEVELS)
    by_split = {e.split for e in examples}
    assert {"train", "validation", "test", "held_out"} <= by_split
    assert any(e.provenance["source"] == "handbook_heldout" for e in examples)


def test_validate_rejects_bad_span_offsets():
    bad = Example(
        example_id="bad-1",
        text="hello world",
        species="dog",
        spans=[Span("vomiting", 0, 8, "vomiting", "gastrointestinal")],
        urgency="routine",
        urgency_basis="severity:moderate",
        concern_tags=["gastroenteritis"],
        red_flag_ids=[],
        split="train",
        owner_style="synthetic",
    )
    with pytest.raises(DatasetError):
        validate([bad])


def test_validate_rejects_red_flag_not_emergency():
    examples = build_dataset(seed=5, red_flag_count=1, other_count=1)
    target = next(e for e in examples if e.red_flag_ids)
    target.urgency = "routine"
    with pytest.raises(DatasetError):
        validate(examples)


def test_write_artifacts_writes_expected_files(tmp_path):
    examples = build_dataset(seed=11, red_flag_count=3, other_count=2)
    manifest = write_artifacts(examples, tmp_path)

    primary = [e for e in examples if e.split != "held_out"]
    held_out = [e for e in examples if e.split == "held_out"]
    examples_lines = (tmp_path / "examples.jsonl").read_text(encoding="utf-8").strip().splitlines()
    held_lines = (tmp_path / "held_out.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(examples_lines) == len(primary)
    assert len(held_lines) == len(held_out)

    row = json.loads(examples_lines[0])
    assert {"example_id", "text", "spans", "urgency", "split"} <= set(row)
    assert manifest["expert_review_status"] == "pending"
    assert manifest["task"] == "P1-AI-002"
    assert (tmp_path / "manifest.json").is_file()


def test_summarize_counts_match():
    examples = build_dataset(seed=21, red_flag_count=2, other_count=1)
    stats = summarize(examples)
    assert stats["example_count"] == len(examples)
    assert stats["span_count"] == sum(len(e.spans) for e in examples)
    assert sum(stats["by_split"].values()) == len(examples)


def test_run_end_to_end(tmp_path):
    manifest = run(tmp_path)
    assert manifest["stats"]["example_count"] > 0
    assert manifest["public_dataset_audit"]
    assert manifest["artifacts"]["examples"] == "examples.jsonl"
