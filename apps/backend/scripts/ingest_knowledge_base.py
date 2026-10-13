"""CLI: ingest the raw knowledge base corpus into batch artifacts.

Task: P1-RAG-003.

Usage (from ``apps/backend``)::

    python scripts/ingest_knowledge_base.py
    python scripts/ingest_knowledge_base.py --raw-dir data/... --out-dir data/...

Exits non-zero with a clear message if any raw document is missing, malformed,
or its source is not cleared for ingestion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.knowledge_base.loader import FrontMatterError  # noqa: E402
from app.services.knowledge_base.pipeline import (  # noqa: E402
    DEFAULT_OUT_DIR,
    DEFAULT_RAW_DIR,
    IngestionError,
    run,
)
from app.services.knowledge_base.source_registry import LicenseError  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest raw knowledge base docs into chunked JSONL artifacts.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help=f"raw corpus dir (default: {DEFAULT_RAW_DIR})")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help=f"artifact output dir (default: {DEFAULT_OUT_DIR})")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        manifest = run(args.raw_dir, args.out_dir)
    except (FrontMatterError, LicenseError, IngestionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"raw dir:     {args.raw_dir}")
    print(f"out dir:     {args.out_dir}")
    print(f"documents:   {manifest['document_count']}")
    print(f"chunks:      {manifest['chunk_count']}")
    print(f"total tokens: {manifest['total_tokens']} (avg {manifest['avg_chunk_tokens']}/chunk)")
    for source in manifest["sources"]:
        print(f"  - {source['source_id']}: {source['chunk_count']} chunks ({source['license']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
