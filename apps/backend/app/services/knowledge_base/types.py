"""PawCare — data structures for the knowledge base ingestion pipeline.

Task: P1-RAG-003. Trace: docs/design/rag-ingestion-pipeline-design.md §2–§4.

These are plain dataclasses, deliberately not Pydantic models and not ORM
models. The DB-backed ``KnowledgeDocument`` / ``Chunk`` entities land with
P1-RAG-004; batch 1 only needs in-memory structures that serialize cleanly to
the JSONL artifacts. Field names track the design doc's metadata contract
(§3.5 and §4) so the mapping to the eventual ORM models stays mechanical.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# A source that was cleared by the licensing audit. ``status`` is one of
# ``cleared`` / ``restricted`` / ``ambiguous``; only ``cleared`` is ingestable.
VALID_STATUSES = ("cleared", "restricted", "ambiguous")

VALID_CONTENT_TYPES = (
    "journal_article",
    "guide",
    "public_health_resource",
    "vet_school_page",
)


@dataclass(frozen=True)
class SourceRecord:
    """One cleared (or explicitly refused) knowledge source.

    Mirrors a row of ``docs/legal/knowledge-source-licensing-tracker.md`` so the
    registry and the human-readable sheet stay reconcilable. ``license`` is the
    exact license string copied from the source's own copyright notice — never
    inferred from the publisher's general policy.
    """

    source_id: str
    title: str
    publisher: str
    source_url: str
    license: str
    license_url: str | None
    attribution_required: bool
    redistribution_permitted: bool
    status: str
    verified: str
    species_applicability: tuple[str, ...]
    body_system_tags: tuple[str, ...]
    content_type: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"source {self.source_id!r}: status must be one of {VALID_STATUSES}, "
                f"got {self.status!r}"
            )
        if self.content_type not in VALID_CONTENT_TYPES:
            raise ValueError(
                f"source {self.source_id!r}: content_type must be one of "
                f"{VALID_CONTENT_TYPES}, got {self.content_type!r}"
            )


@dataclass
class Chunk:
    """A single retrievable, citable unit of knowledge base text.

    Field names match the metadata contract in
    ``docs/design/rag-ingestion-pipeline-design.md`` §3.5 / §4. ``is_red_flag_relevant``
    is carried so the Safety Layer (P2-RAG-004) can prioritise grounding text
    for the red-flag categories in ``docs/design/safety/safety-rules-v1.yaml``.
    """

    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    section_heading: str | None
    token_count: int
    word_count: int
    source_id: str
    source_title: str
    source_url: str
    author: str | None
    license: str
    species_applicability: list[str]
    body_system: str | None
    symptom_tags: list[str]
    condition_tags: list[str]
    published_date: str | None
    retrieved_date: str
    citation_text: str
    is_red_flag_relevant: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Document:
    """A normalized source document plus the chunks derived from it."""

    document_id: str
    source_id: str
    title: str
    source: str
    source_url: str
    license: str
    license_url: str | None
    author: str | None
    published_at: str | None
    retrieved_at: str
    species_applicability: list[str]
    body_system_tags: list[str]
    content_type: str
    status: str
    notes: str
    source_text_path: str
    chunks: list[Chunk] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize without the chunk list — chunks get their own JSONL file."""
        data = asdict(self)
        data.pop("chunks", None)
        return data
