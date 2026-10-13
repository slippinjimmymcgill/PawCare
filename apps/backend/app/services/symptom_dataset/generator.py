"""PawCare — synthetic owner-style symptom text generator.

Task: P1-AI-002. Trace: docs/design/symptom-dataset-strategy.md §2.1 (item 3).

Generates paraphrased owner statements from the canonical symptom concepts with
controlled, rule-based variation of duration, severity, appetite, behaviour and
location — exactly the modifiers the annotation guideline tags. ``random`` is
always seeded, so a build is byte-for-byte reproducible (the same guarantee
P1-RAG-003's chunking gives).

The generator emits text and provenance only. Labels are produced afterwards by
``annotator.annotate_spans`` so a mismatch between what the generator *intended*
and what the text actually says surfaces as a quality-gate failure rather than
being silently copied through.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.services.symptom_dataset.seeds import kb_sources_for
from app.services.symptom_dataset.taxonomy import SYMPTOM_CONCEPTS, SymptomConcept

_SUBJECTS: dict[str, tuple[str, str]] = {
    "dog": ("My dog", "my dog"),
    "cat": ("My cat", "my cat"),
}

# Duration phrase -> leading form used by the "For the last ..." template.
_DURATION_PHRASES: tuple[str, ...] = (
    "for 2 days",
    "for 3 days",
    "since last night",
    "for a few hours",
    "for a week",
    "for 2 weeks",
    "since yesterday",
    "",
)

_SEVERITY_ADJECTIVES: tuple[str, ...] = ("mild", "moderate", "severe", "really bad", "")
_BEHAVIOR_CLAUSES: tuple[str, ...] = (
    "lethargic",
    "very tired",
    "weak",
    "restless",
    "panting",
    "hiding",
    "",
)
_APPETITE_CLAUSES: tuple[str, ...] = ("not eating", "won't eat", "eating less", "")
_LOCATION_CLAUSES: tuple[str, ...] = (
    "",
    "on the left front leg",
    "on the belly",
    "around the eye",
    "on the paw",
)


@dataclass
class GeneratedText:
    text: str
    species: str
    intended_symptom_id: str
    template_id: int
    owner_style: str = "synthetic"
    provenance: dict = field(default_factory=dict)


def _leading_duration(duration: str) -> str:
    if not duration:
        return "Lately"
    if duration.startswith("for "):
        return "For the last " + duration[4:]
    return duration[0].upper() + duration[1:]


def _render(
    subject: str,
    subject_lower: str,
    symptom: str,
    *,
    duration: str,
    severity: str,
    behavior: str,
    appetite: str,
    location: str,
    template_id: int,
) -> str:
    loc = f" {location}" if location else ""
    dur = f" {duration}" if duration else ""

    def extras(*, behavior_used: bool) -> str:
        clauses: list[str] = []
        if severity:
            clauses.append(f"It's {severity}.")
        if behavior and not behavior_used:
            clauses.append(f"{subject} is {behavior}.")
        if appetite:
            clauses.append(f"{subject} is {appetite}.")
        return (" " + " ".join(clauses)) if clauses else ""

    if template_id == 1 and behavior:
        text = f"{subject} is {behavior} and has been {symptom}{loc}{dur}."
        return text + extras(behavior_used=True)
    if template_id == 2:
        text = f"{_leading_duration(duration)}, {subject_lower} has been {symptom}{loc}."
        return text + extras(behavior_used=False)
    text = f"{subject} has been {symptom}{loc}{dur}."
    return text + extras(behavior_used=False)


def _count_for(concept: SymptomConcept, red_flag_count: int, other_count: int) -> int:
    return red_flag_count if concept.is_red_flag else other_count


def generate_examples(
    *,
    seed: int = 20261013,
    red_flag_count: int = 10,
    other_count: int = 5,
) -> list[GeneratedText]:
    """Deterministically generate synthetic owner text for every concept."""
    rng = random.Random(seed)
    generated: list[GeneratedText] = []
    seen: set[tuple[str, str]] = set()

    for concept in SYMPTOM_CONCEPTS:
        for species in concept.species:
            subject, subject_lower = _SUBJECTS[species]
            target = _count_for(concept, red_flag_count, other_count)
            for _ in range(target):
                surface = rng.choice(concept.surface_forms)
                template_id = rng.randrange(3)
                text = _render(
                    subject,
                    subject_lower,
                    surface,
                    duration=rng.choice(_DURATION_PHRASES),
                    severity=rng.choice(_SEVERITY_ADJECTIVES),
                    behavior=rng.choice(_BEHAVIOR_CLAUSES),
                    appetite=rng.choice(_APPETITE_CLAUSES),
                    location=rng.choice(_LOCATION_CLAUSES),
                    template_id=template_id,
                )
                key = (text, species)
                if key in seen:
                    continue
                seen.add(key)
                generated.append(
                    GeneratedText(
                        text=text,
                        species=species,
                        intended_symptom_id=concept.id,
                        template_id=template_id,
                        provenance={
                            "generator": "rule_based_v1",
                            "intended_symptom_id": concept.id,
                            "red_flag_id": concept.red_flag_id,
                            "kb_source_ids": list(kb_sources_for(concept)),
                        },
                    )
                )
    return generated
