"""PawCare — raw-document loader for the knowledge base.

Task: P1-RAG-003.

Raw knowledge-base documents are UTF-8 markdown files with a TOML front-matter
fence delimited by ``+++`` lines (mirroring Hugo/Zola). The front matter is
parsed with the stdlib ``tomllib`` (Python 3.11+), so the ingestion pipeline has
no third-party parsing dependency.

Example::

    +++
    source_id = "fda-xylitol"
    retrieved_at = "2026-10-13"
    published_date = "2022-12-09"
    author = "..."
    symptom_tags = ["vomiting", "collapse"]
    condition_tags = ["xylitol toxicity"]
    is_red_flag_relevant = true
    +++

    ## Signs of xylitol poisoning
    ...
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

FRONT_MATTER_FENCE = "+++"


class FrontMatterError(ValueError):
    """Raised when a raw document's front matter is missing or malformed."""


@dataclass
class RawDocument:
    """A parsed raw document: front matter + normalized markdown body."""

    path: Path
    metadata: dict
    body: str

    def require(self, key: str) -> object:
        if key not in self.metadata:
            raise FrontMatterError(f"{self.path.name}: missing required front matter key {key!r}")
        return self.metadata[key]


def parse_front_matter(text: str, *, source_name: str = "<text>") -> tuple[dict, str]:
    """Split a ``+++`` TOML front-matter block from the markdown body."""
    stripped = text.lstrip("\ufeff")  # tolerate a UTF-8 BOM
    if not stripped.startswith(FRONT_MATTER_FENCE):
        raise FrontMatterError(f"{source_name}: document must start with a {FRONT_MATTER_FENCE} fence")

    lines = stripped.splitlines()
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONT_MATTER_FENCE:
            closing_index = index
            break
    if closing_index is None:
        raise FrontMatterError(f"{source_name}: unterminated {FRONT_MATTER_FENCE} front matter")

    toml_text = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :]).strip()
    try:
        metadata = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as exc:  # pragma: no cover - surfaces as a clear error
        raise FrontMatterError(f"{source_name}: invalid TOML front matter: {exc}") from exc
    if not isinstance(metadata, dict):  # pragma: no cover - tomllib always returns a dict
        raise FrontMatterError(f"{source_name}: front matter must be a TOML table")
    return metadata, body


def load_raw_document(path: str | Path) -> RawDocument:
    """Load and parse a single raw ``.md`` document from disk."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_front_matter(text, source_name=path.name)
    return RawDocument(path=path, metadata=metadata, body=body)
