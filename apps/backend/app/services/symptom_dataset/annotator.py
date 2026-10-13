"""PawCare — rule-based symptom span annotator.

Task: P1-AI-002. Trace: docs/design/symptom-dataset-strategy.md §3–§4.

Applies the annotation guideline deterministically: it finds symptom spans,
attaches duration/severity/behaviour/appetite modifiers found in the same
sentence, and derives a triage urgency. It is intentionally a *separate* pass
from the generator — the generator only writes owner-style text, and the
annotator re-derives the labels from the text using the taxonomy and lexicons,
so the batch is a genuine (rule-based) annotation rather than a restatement of
the generator's intent. Any disagreement shows up as a quality-gate failure.

This is a baseline annotator, not the eventual model: it is the "rule" source
in `annotation_source`. Hand-authored held-out examples go through the same
function so their labels are produced the same way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.symptom_dataset.taxonomy import (
    APPETITE_PHRASES,
    BEHAVIOR_PHRASES,
    SEVERITY_PHRASES,
    SYMPTOM_BY_ID,
    SYMPTOM_CONCEPTS,
    SymptomConcept,
    Span,
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_BOUNDARY_RE = re.compile(r"[a-z0-9]")

_DURATION_RE = re.compile(
    r"\bfor\s+(?P<count>\d+|a\s+few|a|an|two|three|couple\s+of)\s+"
    r"(?P<unit>hour|hours|day|days|week|weeks)\b"
    r"|\bsince\s+last\s+night\b"
    r"|\bsince\s+yesterday\b",
    re.IGNORECASE,
)

_COUNT_WORDS = {"a few": 3, "two": 2, "three": 3, "couple of": 2, "a": 1, "an": 1}


@dataclass
class _Match:
    start: int
    end: int
    concept: SymptomConcept
    surface: str


def _is_word_boundary(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start > 0 else " "
    after = text[end] if end < len(text) else " "
    return not _BOUNDARY_RE.match(before) and not _BOUNDARY_RE.match(after)


def find_symptom_matches(text: str, species: str) -> list[_Match]:
    """All non-overlapping symptom surface matches (longest match wins)."""
    lowered = text.lower()
    candidates: list[_Match] = []
    for concept in SYMPTOM_CONCEPTS:
        if species not in concept.species:
            continue
        for surface in concept.surface_forms:
            needle = surface.lower()
            cursor = 0
            while True:
                index = lowered.find(needle, cursor)
                if index == -1:
                    break
                end = index + len(needle)
                if _is_word_boundary(lowered, index, end):
                    candidates.append(_Match(index, end, concept, text[index:end]))
                cursor = index + 1
    # Earliest start first, then longest, so "bloody diarrhea" beats "diarrhea".
    candidates.sort(key=lambda m: (m.start, -(m.end - m.start)))
    chosen: list[_Match] = []
    for match in candidates:
        if any(match.start < other.end and other.start < match.end for other in chosen):
            continue
        chosen.append(match)
    return sorted(chosen, key=lambda m: m.start)


def _sentence_for(text: str, start: int, end: int) -> str:
    offset = 0
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        sentence_start = offset
        sentence_end = offset + len(sentence)
        if sentence_start <= start and end <= sentence_end + 1:
            return sentence
        offset = sentence_end + 1
    return text


def _find_phrase(sentence: str, phrases: tuple[tuple[str, str], ...]) -> str | None:
    """First (longest) phrase from ``phrases`` present in ``sentence``."""
    lowered = sentence.lower()
    for phrase, value in sorted(phrases, key=lambda p: -len(p[0])):
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            return value
    return None


def parse_duration(sentence: str) -> tuple[int | None, str]:
    match = _DURATION_RE.search(sentence)
    if not match:
        return None, "unknown"
    if match.group("unit") is None:
        lowered = match.group(0).lower()
        if "last night" in lowered:
            return 1, "hours"
        return 1, "days"
    raw_count = re.sub(r"\s+", " ", match.group("count").strip().lower())
    value = _COUNT_WORDS.get(raw_count)
    if value is None:
        value = int(raw_count)
    unit = match.group("unit").lower().rstrip("s") + "s"
    return value, unit


def annotate_spans(
    text: str,
    species: str,
    *,
    owner_style: str = "synthetic",
    annotation_source: str = "rule",
) -> list[Span]:
    """Annotate every symptom span in ``text`` per the guideline."""
    spans: list[Span] = []
    for match in find_symptom_matches(text, species):
        sentence = _sentence_for(text, match.start, match.end)
        severity = _find_phrase(sentence, SEVERITY_PHRASES) or "unknown"
        if severity == "unknown":
            # No explicit severity wording: fall back to the concept's clinical
            # default rather than under-triaging a moderately serious sign
            # (Safety Layer over-referral bias, safety-rules-v1.yaml).
            severity = match.concept.severity_default
        duration_value, duration_unit = parse_duration(sentence)
        spans.append(
            Span(
                text=match.surface,
                start=match.start,
                end=match.end,
                symptom_label=match.concept.id,
                body_system=match.concept.body_system,
                severity=severity,
                duration_value=duration_value,
                duration_unit=duration_unit,
                behavior_modifier=_find_phrase(sentence, BEHAVIOR_PHRASES),
                appetite_modifier=_find_phrase(sentence, APPETITE_PHRASES),
                owner_style=owner_style,
                annotation_source=annotation_source,
            )
        )
    return spans


_SEVERITY_RANK = {"unknown": 0, "mild": 1, "moderate": 2, "severe": 3}


def derive_urgency(spans: list[Span]) -> tuple[str, str]:
    """Map annotated spans to a triage level + the rule that decided it.

    Red-flag precedence (safety-rules-v1.yaml) is applied first and cannot be
    downgraded; otherwise a deliberately conservative severity/duration rule
    set assigns urgent / routine / home_care. This mirrors the Safety Layer's
    over-referral bias — when in doubt, the more urgent level wins.
    """
    red_flag_spans = [s for s in spans if SYMPTOM_BY_ID[s.symptom_label].is_red_flag]
    if red_flag_spans:
        return "emergency", f"red_flag:{SYMPTOM_BY_ID[red_flag_spans[0].symptom_label].red_flag_id}"

    if not spans:
        return "routine", "insufficient_information"

    max_severity = max(_SEVERITY_RANK[s.severity] for s in spans)
    if max_severity >= _SEVERITY_RANK["severe"]:
        return "urgent", "severity:severe"

    persistent = any(
        (s.duration_unit == "days" and (s.duration_value or 0) >= 3)
        or (s.duration_unit == "weeks" and (s.duration_value or 0) >= 1)
        for s in spans
    )
    if persistent:
        return "urgent", "duration:persistent"

    if max_severity >= _SEVERITY_RANK["moderate"]:
        return "routine", "severity:moderate"

    return "home_care", "low_severity"
