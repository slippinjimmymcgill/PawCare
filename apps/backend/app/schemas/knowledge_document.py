"""
PawCare — Knowledge document / chunk Pydantic schemas.
Trace: FR-07, FR-12, requirements.md §5.

Placeholder only — real schemas (admin-facing document upload/management,
FR-12; chunk retrieval metadata feeding FR-07's citations) land with
P1-RAG-002/P2-BE-005, matching docs/design/models/knowledge_document.py
and chunk.py. Chunk.embedding is itself a placeholder at the model layer
(pending P1-BE-002's pgvector confirmation) — this schema inherits that
same "not yet real" status, not a separate decision.
"""

from pydantic import BaseModel


class KnowledgeDocumentBase(BaseModel):
    """Placeholder — fields added in P2-BE-005 (admin endpoints)."""


class ChunkBase(BaseModel):
    """Placeholder — fields added in P1-RAG-002/P2-RAG-001 (retrieval)."""
