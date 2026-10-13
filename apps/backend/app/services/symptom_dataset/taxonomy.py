"""PawCare — symptom dataset taxonomy and annotation dataclasses.

Task: P1-AI-002. Trace: docs/design/symptom-dataset-strategy.md §3–§4,
requirements.md FR-04/FR-05, docs/design/safety/safety-rules-v1.yaml.

This module fixes the label schema the annotation batch is validated against:

* canonical **symptom concepts** (the `symptom_label` field),
* **body systems**, **severity**, **duration** and **owner style** vocabularies,
* the **red-flag** categories, mirrored from safety-rules-v1.yaml so a generated
  example's urgency can be checked against the same RF-001..RF-009 ids the
  Safety Layer (P2-RAG-004) will enforce.

It is deliberately plain data + dataclasses (no Pydantic, no ORM): batch 1 emits
JSONL artifacts, and the eventual ORM/Pydantic shapes land with P2-BE-001.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ── Controlled vocabularies (strategy §3) ────────────────────────────────────

URGENCY_LEVELS = ("emergency", "urgent", "routine", "home_care")
SEVERITIES = ("mild", "moderate", "severe", "unknown")
DURATION_UNITS = ("hours", "days", "weeks", "unknown")
OWNER_STYLES = ("synthetic", "paraphrased", "normalized")
SPECIES = ("dog", "cat")

# The guideline's seven systems, plus the additional systems the red-flag rules
# need (toxicology/trauma/environmental) and two common clinical ones.
BODY_SYSTEMS = (
    "gastrointestinal",
    "respiratory",
    "urinary",
    "neurologic",
    "dermal",
    "musculoskeletal",
    "ophthalmic",
    "hematologic",
    "cardiovascular",
    "toxicology",
    "trauma",
    "environmental",
    "general",
)

# Annotation provenance: was the chunk surfaced by a human, a rule, or the model?
ANNOTATION_SOURCES = ("manual", "rule", "synthetic")


# ── Red flags (mirrors docs/design/safety/safety-rules-v1.yaml v1) ───────────


@dataclass(frozen=True)
class RedFlag:
    id: str
    category: str
    label: str
    body_system: str
    trigger_terms: tuple[str, ...]


RED_FLAGS: tuple[RedFlag, ...] = (
    RedFlag(
        id="RF-001",
        category="respiratory",
        label="Difficulty breathing / labored or rapid breathing",
        body_system="respiratory",
        trigger_terms=(
            "can't breathe",
            "gasping",
            "struggling to breathe",
            "blue gums",
            "open-mouth breathing",
            "labored breathing",
            "breathing hard",
        ),
    ),
    RedFlag(
        id="RF-002",
        category="neurological",
        label="Collapse or unresponsiveness",
        body_system="neurologic",
        trigger_terms=("collapsed", "won't wake up", "unresponsive", "passed out"),
    ),
    RedFlag(
        id="RF-003",
        category="neurological",
        label="Seizure activity",
        body_system="neurologic",
        trigger_terms=("seizure", "convulsing", "fitting", "seizing"),
    ),
    RedFlag(
        id="RF-004",
        category="hemorrhage",
        label="Uncontrolled bleeding",
        body_system="hematologic",
        trigger_terms=("won't stop bleeding", "heavy bleeding", "blood everywhere"),
    ),
    RedFlag(
        id="RF-005",
        category="toxin_ingestion",
        label="Suspected poisoning or toxin ingestion",
        body_system="toxicology",
        trigger_terms=(
            "ate chocolate",
            "ate xylitol",
            "ate grapes",
            "ate raisins",
            "rat poison",
            "ate a lily",
            "ate human medication",
            "antifreeze",
        ),
    ),
    RedFlag(
        id="RF-006",
        category="gastrointestinal",
        label="Distended/painful abdomen with unproductive retching (suspected GDV/bloat)",
        body_system="gastrointestinal",
        trigger_terms=(
            "bloated stomach",
            "swollen belly",
            "trying to vomit but nothing comes up",
            "hard stomach",
        ),
    ),
    RedFlag(
        id="RF-007",
        category="urinary",
        label="Straining to urinate or unable to urinate",
        body_system="urinary",
        trigger_terms=("can't pee", "straining to urinate", "no urine", "crying when trying to urinate"),
    ),
    RedFlag(
        id="RF-008",
        category="trauma",
        label="Severe trauma (vehicle strike, fall, major wound)",
        body_system="trauma",
        trigger_terms=("hit by a car", "fell from", "deep wound", "puncture wound"),
    ),
    RedFlag(
        id="RF-009",
        category="environmental",
        label="Heatstroke signs",
        body_system="environmental",
        trigger_terms=(
            "heavy panting",
            "collapsed in the heat",
            "bright red gums",
            "left in a hot car",
        ),
    ),
)

RED_FLAG_BY_ID: dict[str, RedFlag] = {flag.id: flag for flag in RED_FLAGS}


# ── Condition concepts (classifier targets for P1-AI-004) ────────────────────


@dataclass(frozen=True)
class ConditionConcept:
    id: str
    label: str
    body_system: str
    species: tuple[str, ...]


CONDITION_CONCEPTS: tuple[ConditionConcept, ...] = (
    ConditionConcept("xylitol_toxicity", "Xylitol toxicity", "toxicology", ("dog",)),
    ConditionConcept("chocolate_toxicity", "Chocolate toxicity", "toxicology", ("dog", "cat")),
    ConditionConcept("grape_toxicity", "Grape/raisin toxicity", "toxicology", ("dog",)),
    ConditionConcept("rodenticide_toxicity", "Rodenticide poisoning", "toxicology", ("dog", "cat")),
    ConditionConcept("lily_toxicity", "Lily toxicity", "toxicology", ("cat",)),
    ConditionConcept("antifreeze_toxicity", "Antifreeze (ethylene glycol) poisoning", "toxicology", ("dog", "cat")),
    ConditionConcept("gastric_dilatation_volvulus", "GDV / bloat", "gastrointestinal", ("dog",)),
    ConditionConcept("urethral_obstruction", "Urethral obstruction", "urinary", ("cat", "dog")),
    ConditionConcept("urinary_tract_infection", "Urinary tract infection", "urinary", ("dog", "cat")),
    ConditionConcept("heatstroke", "Heatstroke", "environmental", ("dog", "cat")),
    ConditionConcept("seizure_disorder", "Seizure disorder", "neurologic", ("dog", "cat")),
    ConditionConcept("respiratory_distress", "Respiratory distress", "respiratory", ("dog", "cat")),
    ConditionConcept("internal_injury", "Internal injury / trauma", "trauma", ("dog", "cat")),
    ConditionConcept("gastroenteritis", "Gastroenteritis", "gastrointestinal", ("dog", "cat")),
    ConditionConcept("pancreatitis", "Pancreatitis", "gastrointestinal", ("dog", "cat")),
    ConditionConcept("foreign_body_ingestion", "Foreign body ingestion", "gastrointestinal", ("dog", "cat")),
    ConditionConcept("osteoarthritis", "Osteoarthritis", "musculoskeletal", ("dog", "cat")),
    ConditionConcept("fracture", "Fracture", "musculoskeletal", ("dog", "cat")),
    ConditionConcept("flea_allergy_dermatitis", "Flea allergy dermatitis", "dermal", ("dog", "cat")),
    ConditionConcept("skin_infection", "Skin infection", "dermal", ("dog", "cat")),
    ConditionConcept("conjunctivitis", "Conjunctivitis", "ophthalmic", ("dog", "cat")),
    ConditionConcept("kennel_cough", "Kennel cough / infectious tracheobronchitis", "respiratory", ("dog",)),
    ConditionConcept("feline_upper_respiratory", "Feline upper respiratory infection", "respiratory", ("cat",)),
    ConditionConcept("dental_disease", "Dental disease", "gastrointestinal", ("dog", "cat")),
    ConditionConcept("ear_infection", "Ear infection / otitis", "general", ("dog", "cat")),
    ConditionConcept("insufficient_information", "Insufficient information", "general", ("dog", "cat")),
)

CONDITION_BY_ID: dict[str, ConditionConcept] = {c.id: c for c in CONDITION_CONCEPTS}


# ── Symptom concepts (the annotation labels) ─────────────────────────────────


@dataclass(frozen=True)
class SymptomConcept:
    id: str
    canonical_label: str
    body_system: str
    surface_forms: tuple[str, ...]
    species: tuple[str, ...]
    concern_tags: tuple[str, ...]
    red_flag_id: str | None = None
    severity_default: str = "unknown"

    @property
    def is_red_flag(self) -> bool:
        return self.red_flag_id is not None


SYMPTOM_CONCEPTS: tuple[SymptomConcept, ...] = (
    # ── Red-flag symptoms (all forced to emergency downstream) ──
    SymptomConcept(
        "difficulty_breathing", "difficulty breathing", "respiratory",
        ("difficulty breathing", "having trouble breathing", "struggling to breathe",
         "breathing hard", "labored breathing", "gasping for air", "open-mouth breathing"),
        ("dog", "cat"), ("respiratory_distress",), red_flag_id="RF-001", severity_default="severe",
    ),
    SymptomConcept(
        "collapse", "collapse", "neurologic",
        ("collapsed", "collapsed and won't wake up", "passed out", "unresponsive", "fainted"),
        ("dog", "cat"), ("insufficient_information",), red_flag_id="RF-002", severity_default="severe",
    ),
    SymptomConcept(
        "seizure", "seizure", "neurologic",
        ("seizure", "seizing", "had a seizure", "convulsing", "fitting", "shaking uncontrollably"),
        ("dog", "cat"), ("seizure_disorder",), red_flag_id="RF-003", severity_default="severe",
    ),
    SymptomConcept(
        "uncontrolled_bleeding", "uncontrolled bleeding", "hematologic",
        ("won't stop bleeding", "heavy bleeding", "bleeding a lot", "blood everywhere"),
        ("dog", "cat"), ("insufficient_information",), red_flag_id="RF-004", severity_default="severe",
    ),
    SymptomConcept(
        "toxin_ingestion", "toxin ingestion", "toxicology",
        ("ate chocolate", "ate a bar of chocolate", "ate a whole bar of chocolate",
         "ate some chocolate", "ate xylitol", "ate grapes", "ate raisins",
         "got into rat poison", "ate a lily", "ate human medication", "drank antifreeze"),
        ("dog", "cat"), ("chocolate_toxicity", "xylitol_toxicity", "grape_toxicity",
                          "rodenticide_toxicity", "lily_toxicity", "antifreeze_toxicity"),
        red_flag_id="RF-005", severity_default="severe",
    ),
    SymptomConcept(
        "bloated_abdomen", "distended abdomen with unproductive retching", "gastrointestinal",
        ("bloated stomach", "swollen belly", "hard stomach", "trying to vomit but nothing comes up",
         "retching with nothing coming up"),
        ("dog", "cat"), ("gastric_dilatation_volvulus",), red_flag_id="RF-006", severity_default="severe",
    ),
    SymptomConcept(
        "straining_to_urinate", "straining to urinate", "urinary",
        ("straining to urinate", "can't pee", "trying to pee but nothing comes out",
         "crying when trying to urinate", "no urine for a day"),
        ("dog", "cat"), ("urethral_obstruction",), red_flag_id="RF-007", severity_default="severe",
    ),
    SymptomConcept(
        "severe_trauma", "severe trauma", "trauma",
        ("hit by a car", "fell from a height", "deep wound", "puncture wound", "got hit by a bike"),
        ("dog", "cat"), ("internal_injury", "fracture"), red_flag_id="RF-008", severity_default="severe",
    ),
    SymptomConcept(
        "heatstroke_signs", "heatstroke signs", "environmental",
        ("heavy panting and won't stop", "collapsed in the heat", "bright red gums",
         "left in a hot car", "panting nonstop in the heat"),
        ("dog", "cat"), ("heatstroke",), red_flag_id="RF-009", severity_default="severe",
    ),
    # ── Gastrointestinal ──
    SymptomConcept(
        "vomiting", "vomiting", "gastrointestinal",
        ("vomiting", "throwing up", "been sick", "vomited"), ("dog", "cat"),
        ("gastroenteritis", "foreign_body_ingestion", "pancreatitis"), severity_default="moderate",
    ),
    SymptomConcept(
        "diarrhea", "diarrhea", "gastrointestinal",
        ("diarrhea", "loose stool", "watery poop", "runny stool"), ("dog", "cat"),
        ("gastroenteritis",), severity_default="moderate",
    ),
    SymptomConcept(
        "bloody_diarrhea", "bloody diarrhea", "gastrointestinal",
        ("bloody diarrhea", "blood in the stool", "bloody stool"), ("dog", "cat"),
        ("gastroenteritis",), severity_default="severe",
    ),
    SymptomConcept(
        "not_eating", "appetite loss", "gastrointestinal",
        ("not eating", "won't eat", "refusing food", "eating less", "lost appetite"), ("dog", "cat"),
        ("gastroenteritis", "dental_disease"), severity_default="moderate",
    ),
    SymptomConcept(
        "abdominal_pain", "abdominal pain", "gastrointestinal",
        ("painful belly", "abdominal pain", "tender stomach", "yelping when touched on the belly"),
        ("dog", "cat"), ("pancreatitis", "gastroenteritis"), severity_default="moderate",
    ),
    SymptomConcept(
        "weight_loss", "weight loss", "gastrointestinal",
        ("losing weight", "weight loss", "getting thin"), ("dog", "cat"),
        ("dental_disease", "pancreatitis"), severity_default="moderate",
    ),
    # ── Respiratory ──
    SymptomConcept(
        "coughing", "coughing", "respiratory",
        ("coughing", "a cough", "cough", "hacking", "coughing at night"), ("dog", "cat"),
        ("kennel_cough", "feline_upper_respiratory"), severity_default="mild",
    ),
    SymptomConcept(
        "sneezing", "sneezing", "respiratory",
        ("sneezing", "sneezing a lot", "sneezing fits"), ("dog", "cat"),
        ("feline_upper_respiratory",), severity_default="mild",
    ),
    SymptomConcept(
        "nasal_discharge", "nasal discharge", "respiratory",
        ("runny nose", "nasal discharge", "green snot", "discharge from the nose"), ("dog", "cat"),
        ("feline_upper_respiratory",), severity_default="mild",
    ),
    # ── Urinary ──
    SymptomConcept(
        "blood_in_urine", "blood in urine", "urinary",
        ("blood in the urine", "bloody pee", "pink urine"), ("dog", "cat"),
        ("urinary_tract_infection",), severity_default="moderate",
    ),
    SymptomConcept(
        "frequent_urination", "frequent urination", "urinary",
        ("peeing more often", "frequent urination", "asking to go out constantly"), ("dog", "cat"),
        ("urinary_tract_infection",), severity_default="mild",
    ),
    # ── Neurologic ──
    SymptomConcept(
        "lethargy", "lethargy", "general",
        ("lethargic", "very tired", "low energy", "not himself", "seems weak"), ("dog", "cat"),
        ("insufficient_information",), severity_default="moderate",
    ),
    SymptomConcept(
        "head_tilt", "head tilt", "neurologic",
        ("head tilt", "tilted head", "holding his head to one side"), ("dog", "cat"),
        ("insufficient_information",), severity_default="moderate",
    ),
    SymptomConcept(
        "disorientation", "disorientation", "neurologic",
        ("disoriented", "seems confused", "wandering in circles", "unsteady"), ("dog", "cat"),
        ("insufficient_information",), severity_default="moderate",
    ),
    # ── Dermal ──
    SymptomConcept(
        "itching", "itching", "dermal",
        ("itching", "scratching constantly", "very itchy", "scratching himself raw"), ("dog", "cat"),
        ("flea_allergy_dermatitis", "skin_infection"), severity_default="mild",
    ),
    SymptomConcept(
        "hair_loss", "hair loss", "dermal",
        ("losing hair", "bald patches", "hair loss"), ("dog", "cat"),
        ("flea_allergy_dermatitis",), severity_default="mild",
    ),
    SymptomConcept(
        "rash", "rash", "dermal",
        ("a rash", "red patches", "skin rash", "bumps on the skin"), ("dog", "cat"),
        ("skin_infection",), severity_default="mild",
    ),
    SymptomConcept(
        "lump", "lump", "dermal",
        ("a lump", "a bump under the skin", "swelling on the leg"), ("dog", "cat"),
        ("skin_infection",), severity_default="moderate",
    ),
    # ── Musculoskeletal ──
    SymptomConcept(
        "limping", "limping", "musculoskeletal",
        ("limping", "walking with a limp", "favoring one leg"), ("dog", "cat"),
        ("osteoarthritis", "fracture"), severity_default="moderate",
    ),
    SymptomConcept(
        "stiffness", "stiffness", "musculoskeletal",
        ("stiff", "stiff in the mornings", "slow to get up"), ("dog", "cat"),
        ("osteoarthritis",), severity_default="mild",
    ),
    # ── Ophthalmic ──
    SymptomConcept(
        "watery_eyes", "watery eyes", "ophthalmic",
        ("watery eyes", "runny eyes", "discharge from the eye"), ("dog", "cat"),
        ("conjunctivitis",), severity_default="mild",
    ),
    SymptomConcept(
        "squinting", "squinting", "ophthalmic",
        ("squinting", "keeping the eye closed", "holding the eye shut"), ("dog", "cat"),
        ("conjunctivitis",), severity_default="moderate",
    ),
    # ── General behaviour observations ──
    SymptomConcept(
        "hiding", "hiding", "general",
        ("hiding", "hiding under the bed", "hiding away"), ("dog", "cat"),
        ("insufficient_information",), severity_default="unknown",
    ),
    SymptomConcept(
        "panting", "panting", "general",
        ("panting", "panting a lot", "breathing fast"), ("dog", "cat"),
        ("insufficient_information",), severity_default="unknown",
    ),
    SymptomConcept(
        "restlessness", "restlessness", "general",
        ("restless", "can't settle", "pacing"), ("dog", "cat"),
        ("insufficient_information",), severity_default="unknown",
    ),
    SymptomConcept(
        "vocalizing", "vocalizing", "general",
        ("crying", "whining", "yelping", "yowling"), ("dog", "cat"),
        ("insufficient_information",), severity_default="unknown",
    ),
    # Vague / ambiguous phrases used by the held-out low-information set
    # (guideline §4.4). Deliberately low-confidence: no confident concern label.
    SymptomConcept(
        "gi_upset", "stomach upset", "gastrointestinal",
        ("upset stomach", "stomach issue", "tummy trouble", "sore stomach"), ("dog", "cat"),
        ("insufficient_information",), severity_default="unknown",
    ),
    SymptomConcept(
        "vague_illness", "vague unwellness", "general",
        ("a bit off", "seems off", "not right", "something's wrong", "not herself", "not his usual self"),
        ("dog", "cat"), ("insufficient_information",), severity_default="unknown",
    ),
)

SYMPTOM_BY_ID: dict[str, SymptomConcept] = {s.id: s for s in SYMPTOM_CONCEPTS}


# ── Lexicons for the (rule-based) annotator ──────────────────────────────────

# Modifier phrase -> normalized value. Longest phrases are matched first so
# "very weak" beats "weak".
SEVERITY_PHRASES: tuple[tuple[str, str], ...] = (
    ("a little", "mild"),
    ("slightly", "mild"),
    ("mild", "mild"),
    ("moderate", "moderate"),
    ("very weak", "severe"),
    ("extremely", "severe"),
    ("really bad", "severe"),
    ("severe", "severe"),
    ("worse than yesterday", "severe"),
)

BEHAVIOR_PHRASES: tuple[tuple[str, str], ...] = (
    ("lethargic", "lethargic"),
    ("very tired", "lethargic"),
    ("low energy", "lethargic"),
    ("seems weak", "weak"),
    ("weak", "weak"),
    ("restless", "restless"),
    ("can't settle", "restless"),
    ("pacing", "restless"),
    ("panting", "panting"),
    ("hiding", "hiding"),
    ("crying", "vocalizing"),
    ("whining", "vocalizing"),
    ("yelping", "vocalizing"),
    ("yowling", "vocalizing"),
)

APPETITE_PHRASES: tuple[tuple[str, str], ...] = (
    ("not eating", "no_appetite"),
    ("won't eat", "no_appetite"),
    ("refusing food", "no_appetite"),
    ("eating less", "reduced_appetite"),
    ("lost appetite", "no_appetite"),
    ("off his food", "reduced_appetite"),
)


# ── Annotation dataclasses ───────────────────────────────────────────────────


@dataclass
class Span:
    """One annotated symptom span (strategy §3)."""

    text: str
    start: int
    end: int
    symptom_label: str
    body_system: str
    severity: str = "unknown"
    duration_value: int | None = None
    duration_unit: str = "unknown"
    behavior_modifier: str | None = None
    appetite_modifier: str | None = None
    owner_style: str = "synthetic"
    annotation_source: str = "rule"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Example:
    """One owner-style symptom description plus its full annotation."""

    example_id: str
    text: str
    species: str
    spans: list[Span]
    urgency: str
    urgency_basis: str
    concern_tags: list[str]
    red_flag_ids: list[str]
    split: str
    owner_style: str
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["spans"] = [span.to_dict() for span in self.spans]
        return data
