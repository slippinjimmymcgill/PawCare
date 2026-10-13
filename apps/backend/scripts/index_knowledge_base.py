"""CLI: embed + index the knowledge base, then optionally run a search smoke test.

Task: P1-RAG-004.

Usage (from ``apps/backend``)::

    # Index into the configured Postgres database
    python scripts/index_knowledge_base.py

    # Offline smoke test on a throwaway SQLite file
    python scripts/index_knowledge_base.py --database-url sqlite:///kb_smoke.db \\
        --create-tables --provider hashing --search "dog ate chocolate"

The command is idempotent: chunk ids are deterministic, so re-running updates
rows in place (re-embedding only when the model changed or ``--force`` is given).
Exits non-zero with a clear message on any indexing/search error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.models  # noqa: E402,F401  (register models on Base.metadata)
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.services.knowledge_base.embeddings import (  # noqa: E402
    EmbeddingError,
    HashingEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from app.services.knowledge_base.indexer import (  # noqa: E402
    IndexingError,
    index_batch,
    semantic_search,
)
from app.services.knowledge_base.pipeline import DEFAULT_OUT_DIR  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed and index knowledge base chunks into the database."
    )
    parser.add_argument(
        "--batch-dir", type=Path, default=DEFAULT_OUT_DIR,
        help=f"batch artifacts dir (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument("--provider", default=None, help="embedding provider (overrides EMBEDDING_PROVIDER)")
    parser.add_argument("--model", default=None, help="sentence-transformers model name")
    parser.add_argument("--dim", type=int, default=None, help="hashing provider dimension")
    parser.add_argument("--force", action="store_true", help="re-embed chunks even if unchanged")
    parser.add_argument("--database-url", default=None, help="override DATABASE_URL")
    parser.add_argument(
        "--create-tables", action="store_true",
        help="create tables before indexing (for a fresh SQLite smoke DB)",
    )
    parser.add_argument("--search", default=None, help="run a retrieval smoke query after indexing")
    parser.add_argument("--top-k", type=int, default=5, help="number of search hits to show")
    parser.add_argument("--species", default=None, help="restrict search to a species (dog/cat)")
    parser.add_argument("--body-system", default=None, help="restrict search to a body system")
    parser.add_argument("--red-flag-only", action="store_true", help="restrict search to red-flag chunks")
    return parser.parse_args(argv)


def _build_provider(args: argparse.Namespace):
    settings = get_settings()
    provider_id = (args.provider or settings.EMBEDDING_PROVIDER or "").strip().lower()
    if provider_id in {"hashing", "hash", "baseline"}:
        return HashingEmbeddingProvider(args.dim or settings.EMBEDDING_DIM)
    if provider_id in {"sentence_transformers", "sentence-transformers", "st"}:
        return SentenceTransformerEmbeddingProvider(args.model or settings.EMBEDDING_MODEL)
    raise EmbeddingError(
        f"unknown provider {provider_id!r}; expected 'sentence_transformers' or 'hashing'"
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = get_settings()

    engine = create_engine(args.database_url or settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    try:
        provider = _build_provider(args)
        if args.create_tables:
            Base.metadata.create_all(bind=engine)

        db = session_factory()
        try:
            report = index_batch(db, args.batch_dir, provider, force=args.force)
            print(f"batch dir:    {report.batch_dir}")
            print(f"provider:     {report.provider} (dim {report.dim})")
            print(f"documents:    {report.documents_indexed}")
            print(f"chunks:       {report.chunks_total} ({report.chunks_embedded} embedded, {report.chunks_reused} reused)")

            if args.search is not None:
                hits = semantic_search(
                    db,
                    args.search,
                    provider,
                    top_k=args.top_k,
                    species=args.species,
                    body_system=args.body_system,
                    red_flag_only=args.red_flag_only,
                )
                print(f"\nsearch: {args.search!r}")
                if not hits:
                    print("  (no matches)")
                for hit in hits:
                    snippet = " ".join(hit.chunk.chunk_text.split())[:160]
                    print(f"  [{hit.score:.4f}] {hit.chunk.citation_text}")
                    print(f"      {snippet}")
        finally:
            db.close()
    except (EmbeddingError, IndexingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
