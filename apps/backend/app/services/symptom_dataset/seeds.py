"""PawCare — knowledge-base-derived seed relationships for the symptom dataset.

Task: P1-AI-002. Trace: docs/design/symptom-dataset-strategy.md §2.1 (item 1).

The dataset strategy anchors the label schema in the cleared knowledge base
rather than in vague public text: symptom → condition → urgency relationships
extracted from the batch-1 sources. This module is the machine-readable form of
that anchoring. It does **not** copy KB prose — it records which cleared source
grounds each red-flag relationship, so a generated example can name its KB
provenance and the downstream classifier (P1-AI-004) has clinically-grounded
seed pairs.

Routine (non-red-flag) symptom concepts have no batch-1 KB source yet; they are
labelled ``clinical_heuristic`` and their provenance says so rather than
pretending to a citation that batch 1 did not collect.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.symptom_dataset.taxonomy import (
    RED_FLAG_BY_ID,
    SYMPTOM_CONCEPTS,
    SymptomConcept,
)

# Red-flag id -> cleared batch-1 source id(s) that ground it. Mirrors
# data/knowledge_base/batch1/manifest.json's source list.
RF_SOURCE_MAP: dict[str, tuple[str, ...]] = {
    "RF-001": ("mdpi-emergency-dyspnea-cats",),
    "RF-002": ("mdpi-acute-seizures",),
    "RF-003": ("mdpi-acute-seizures",),
    "RF-004": ("frontiers-hemorrhage",),
    "RF-005": ("fda-xylitol", "frontiers-household-toxins"),
    "RF-006": ("mdpi-gdv",),
    "RF-007": ("jvim-feline-urethral-obstruction",),
    "RF-008": ("mdpi-trauma-att",),
    "RF-009": ("mdpi-heat-illness",),
}


@dataclass(frozen=True)
class SeedRelationship:
    symptom_id: str
    condition_id: str
    urgency_hint: str | None
    red_flag_id: str | None
    kb_source_ids: tuple[str, ...]
    grounding: str  # "knowledge_base" | "clinical_heuristic"


def build_seed_relationships() -> tuple[SeedRelationship, ...]:
    """Expand the taxonomy into (symptom, condition, urgency) seed triples."""
    relationships: list[SeedRelationship] = []
    for concept in SYMPTOM_CONCEPTS:
        for condition_id in concept.concern_tags:
            if concept.is_red_flag:
                urgency = "emergency"
                sources = RF_SOURCE_MAP.get(concept.red_flag_id or "", ())
                grounding = "knowledge_base"
            else:
                urgency = None
                sources = ()
                grounding = "clinical_heuristic"
            relationships.append(
                SeedRelationship(
                    symptom_id=concept.id,
                    condition_id=condition_id,
                    urgency_hint=urgency,
                    red_flag_id=concept.red_flag_id,
                    kb_source_ids=sources,
                    grounding=grounding,
                )
            )
    return tuple(relationships)


SEED_RELATIONSHIPS: tuple[SeedRelationship, ...] = build_seed_relationships()


def kb_sources_for(concept: SymptomConcept) -> tuple[str, ...]:
    """Cleared KB source ids grounding a symptom concept (empty if heuristic)."""
    if not concept.red_flag_id:
        return ()
    return RF_SOURCE_MAP.get(concept.red_flag_id, ())


def red_flag_label(red_flag_id: str) -> str:
    flag = RED_FLAG_BY_ID.get(red_flag_id)
    return flag.label if flag else red_flag_id
