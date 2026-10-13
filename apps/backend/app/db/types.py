"""PawCare — SQLAlchemy custom types.

Task: P1-RAG-004. Trace: requirements.md §6, plan.md §11 item 3,
docs/design/models/chunk.py.

`Vector` is the one dialect-sensitive column in the schema. On PostgreSQL it
maps to pgvector's native ``vector(dim)`` type (ANN-searchable via an HNSW
index — see the ``knowledge_base_tables`` migration); everywhere else — SQLite
tests, or Postgres where the ``vector`` extension is not available — it stores
the embedding as a JSON array of floats. Both shapes round-trip as
``list[float]``, so the embedding pipeline and retrieval code are dialect
agnostic.

This is how PawCare honours plan.md §11 item 3 ("pgvector inside the primary
Postgres instance vs. a dedicated vector database") without blocking on the
decision: the default is pgvector-in-Postgres as requirements.md §6 specifies,
and the portable JSON fallback keeps local dev, CI and any non-pgvector host
working while that decision is still open.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

#: Default embedding dimension — matches `all-MiniLM-L6-v2` / `bge-small-en-v1.5`
#: (the design's local sentence-transformer default). A different model/dim is a
#: schema change (the `vector(n)` column is fixed-width), so it requires a new
#: migration.
DEFAULT_EMBEDDING_DIM = 384


class Vector(TypeDecorator):
    """Embedding column: pgvector ``vector(n)`` on Postgres, JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIM) -> None:
        self.dim = int(dim)
        super().__init__()

    def copy(self, **kw: Any) -> Vector:
        return Vector(self.dim)

    def load_dialect_impl(self, dialect):  # noqa: ANN001 - SQLAlchemy Dialect
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector as PgVector
            except ImportError:  # pgvector not installed on this deployment
                return dialect.type_descriptor(JSON())
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):  # noqa: ANN001
        if value is None:
            return None
        return [float(component) for component in value]

    def process_result_value(self, value: Any, dialect):  # noqa: ANN001
        if value is None:
            return None
        return [float(component) for component in value]

    def __repr__(self) -> str:
        return f"Vector({self.dim})"
