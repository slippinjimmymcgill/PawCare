"""PawCare — symptom dataset collection, augmentation & annotation.

Task: P1-AI-002 (Sprint Block 3–4). Trace: requirements.md §7,
docs/design/symptom-dataset-strategy.md (the P1-AI-001 guideline).

Batch 1 is built from the strategy's hybrid design:

* KB-derived seed relationships (``seeds``) anchor the schema in cleared sources;
* rule-based synthetic augmentation (``generator``) produces owner-style text;
* a deterministic annotator (``annotator``) labels symptom spans + modifiers and
  derives triage urgency with red-flag precedence;
* a frozen, hand-authored held-out set covers emergency/urgent/routine/low-info;
* ``pipeline`` runs the quality gate and writes the batch artifacts.

No public dataset was folded into batch 1: the one license-clear candidate
(MIT) has a label schema incompatible with the red-flag taxonomy, and the
EHR-derived candidate is access-restricted. That decision is recorded in the
manifest's ``public_dataset_audit`` and in
``docs/legal/symptom-dataset-licensing-audit.md``.
"""

from app.services.symptom_dataset.annotator import annotate_spans, derive_urgency
from app.services.symptom_dataset.generator import GeneratedText, generate_examples
from app.services.symptom_dataset.pipeline import (
    DEFAULT_OUT_DIR,
    PUBLIC_DATASET_AUDIT,
    DatasetError,
    build_dataset,
    run,
    summarize,
    validate,
    write_artifacts,
)
from app.services.symptom_dataset.seeds import SEED_RELATIONSHIPS, SeedRelationship
from app.services.symptom_dataset.taxonomy import (
    BODY_SYSTEMS,
    CONDITION_BY_ID,
    RED_FLAGS,
    SYMPTOM_BY_ID,
    URGENCY_LEVELS,
    Example,
    Span,
)

__all__ = [
    "BODY_SYSTEMS",
    "CONDITION_BY_ID",
    "DEFAULT_OUT_DIR",
    "DatasetError",
    "Example",
    "GeneratedText",
    "PUBLIC_DATASET_AUDIT",
    "RED_FLAGS",
    "SEED_RELATIONSHIPS",
    "SYMPTOM_BY_ID",
    "Span",
    "SeedRelationship",
    "URGENCY_LEVELS",
    "annotate_spans",
    "build_dataset",
    "derive_urgency",
    "generate_examples",
    "run",
    "summarize",
    "validate",
    "write_artifacts",
]
