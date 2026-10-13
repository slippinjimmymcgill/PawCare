"""PawCare — Knowledge base ingestion (collection, licensing gate, chunking).

Task: P1-RAG-003.
Trace: plan.md §3, requirements.md FR-07,
       docs/design/rag-ingestion-pipeline-design.md.

This package implements pipeline steps 1–4 of the design (source validation,
document normalization, chunking, metadata enrichment) for batch 1. Steps 5–7
(embedding, pgvector indexing, retrieval smoke test) are P1-RAG-004 — nothing
here talks to a database, pgvector, or an embedding model. The output is a set
of JSONL artifacts plus a manifest, which P1-RAG-004 consumes.

Design decisions that were fixed by P1-RAG-002 and are treated as contract here:

* chunk target 250–350 tokens, 40–80 token overlap;
* split on document structure (headings → paragraphs → bullets);
* paragraphs shorter than 200 tokens merge with their section context;
* paragraphs longer than 300 tokens split at sentence boundaries
  (max 350 tokens, 50-token overlap);
* no chunk may be pure metadata / a citation line;
* every chunk is traceable to a source + license (nothing anonymous).
"""

from app.services.knowledge_base.source_registry import (
    CLEARED_SOURCES,
    LicenseError,
    get_source,
    require_cleared,
)
from app.services.knowledge_base.types import (
    Chunk,
    Document,
    SourceRecord,
)

__all__ = [
    "CLEARED_SOURCES",
    "Chunk",
    "Document",
    "LicenseError",
    "SourceRecord",
    "get_source",
    "require_cleared",
]
