"""CLI: build the batch-1 symptom dataset (generate + annotate + split + gate).

Task: P1-AI-002.

Usage (from ``apps/backend``)::

    python scripts/build_symptom_dataset.py
    python scripts/build_symptom_dataset.py --out-dir data/symptom_dataset/batch1

Reproducible: the seed is fixed, so re-running produces byte-identical
``examples.jsonl`` / ``held_out.jsonl`` (only ``manifest.json``'s
``generated_at`` changes). Exits non-zero if the annotation quality gate fails.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.symptom_dataset.pipeline import (  # noqa: E402
    DEFAULT_OUT_DIR,
    DEFAULT_SEED,
    DatasetError,
    build_dataset,
    write_artifacts,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build + annotate the batch-1 symptom dataset.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help=f"artifact output dir (default: {DEFAULT_OUT_DIR})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="generation seed (default: %(default)s)")
    parser.add_argument("--red-flag-count", type=int, default=10, help="examples per red-flag concept/species")
    parser.add_argument("--other-count", type=int, default=5, help="examples per routine concept/species")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        examples = build_dataset(
            seed=args.seed,
            red_flag_count=args.red_flag_count,
            other_count=args.other_count,
        )
        manifest = write_artifacts(examples, args.out_dir)
    except DatasetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    stats = manifest["stats"]
    print(f"out dir:      {args.out_dir}")
    print(f"examples:     {stats['example_count']}")
    print(f"spans:        {stats['span_count']}")
    print(f"by split:     {stats['by_split']}")
    print(f"by urgency:   {stats['by_urgency']}")
    print(f"by species:   {stats['by_species']}")
    print(f"red flags:    {stats['red_flag_coverage']}")
    print(f"source mix:   {stats['source_mix']}")
    print(f"expert review: {manifest['expert_review_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
