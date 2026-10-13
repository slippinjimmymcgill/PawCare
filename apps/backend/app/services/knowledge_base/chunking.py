"""PawCare — document chunking for the knowledge base.

Task: P1-RAG-003. Trace: docs/design/rag-ingestion-pipeline-design.md §3.

Implements the chunking strategy fixed by P1-RAG-002 exactly:

* split on structure first — headings → paragraphs → bullets;
* target 250–350 tokens per chunk;
* paragraphs shorter than 200 tokens merge with their section context;
* paragraphs longer than 300 tokens split at sentence boundaries
  (max 350 tokens, 50-token overlap);
* each substantial bullet is its own chunk;
* no chunk that is pure metadata or a citation line is emitted.

Token counts here are a deterministic approximation (words plus punctuation),
not a specific model's tokenizer. The design only needs *a* consistent token
budget; the embedding model chosen in P1-RAG-004 does not change this contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TARGET_MIN_TOKENS = 250
TARGET_MAX_TOKENS = 350
OVERLAP_TOKENS = 50
SMALL_PARAGRAPH_TOKENS = 200
LARGE_PARAGRAPH_TOKENS = 300
MIN_ACTIONABLE_TOKENS = 8
STANDALONE_BULLET_TOKENS = 60
STANDALONE_BULLET_MIN_WORDS = 8

_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_TABLE_OR_FIGURE_HEADING_RE = re.compile(r"^(table|figure|fig\.?)\s*\d+\b", re.IGNORECASE)
_METADATA_LINE_RE = re.compile(
    r"^(keywords|doi|https?://|www\.|©|copyright|pmid|pmcid|source\s*:)\b",
    re.IGNORECASE,
)


def count_tokens(text: str) -> int:
    """Approximate token count: word runs plus individual punctuation marks."""
    return len(_TOKEN_RE.findall(text))


def count_words(text: str) -> int:
    return len(text.split())


@dataclass
class Block:
    """A single paragraph or bullet at the leaf of the document tree."""

    kind: str  # "paragraph" | "bullet"
    text: str


@dataclass
class SectionChunk:
    """An emitted chunk with the section heading it came from."""

    text: str
    section_heading: str | None


def split_sentences(text: str) -> list[str]:
    """Split prose into sentences, keeping trailing punctuation."""
    parts = [p.strip() for p in _SENTENCE_RE.split(text) if p.strip()]
    return parts or [text.strip()]


def parse_sections(markdown: str) -> list[tuple[str | None, list[Block]]]:
    """Split markdown into ``(heading, blocks)`` sections using ``#`` headings."""
    sections: list[tuple[str | None, list[Block]]] = []
    heading: str | None = None
    blocks: list[Block] = []
    para_lines: list[str] = []

    def flush_paragraph() -> None:
        if para_lines:
            text = " ".join(para_lines).strip()
            if text:
                blocks.append(Block("paragraph", text))
            para_lines.clear()

    def flush_section() -> None:
        flush_paragraph()
        if blocks or heading is not None:
            sections.append((heading, list(blocks)))
            blocks.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            flush_paragraph()
            continue
        if line.lstrip().startswith("#"):
            flush_section()
            heading = line.lstrip("#").strip() or None
            continue
        bullet = _BULLET_RE.match(line)
        if bullet:
            flush_paragraph()
            content = bullet.group(1).strip()
            if content:
                blocks.append(Block("bullet", content))
            continue
        para_lines.append(line.strip())

    flush_section()
    return sections


def _is_standalone_bullet(text: str) -> bool:
    """True if a bullet carries a standalone fact/recommendation (design §3.4.5).

    Product/name list items ("Sugar-free jams, jellies, and nut butters") are not
    standalone facts and are merged with their section context; a full sentence or
    a substantial item stands on its own.
    """
    if count_tokens(text) >= STANDALONE_BULLET_TOKENS:
        return True
    return (
        count_words(text) >= STANDALONE_BULLET_MIN_WORDS and text.rstrip()[-1:] in ".!?:"
    )


def _render_blocks(blocks: list[Block]) -> str:
    """Render buffered blocks, keeping bullets marked and grouped."""
    parts: list[str] = []
    previous_kind: str | None = None
    for block in blocks:
        rendered = f"- {block.text}" if block.kind == "bullet" else block.text
        if previous_kind == "bullet" and block.kind == "bullet":
            parts.append("\n" + rendered)
        elif parts:
            parts.append("\n\n" + rendered)
        else:
            parts.append(rendered)
        previous_kind = block.kind
    return "".join(parts).strip()


def _is_actionable(text: str) -> bool:
    """Reject pure metadata / citation / too-short fragments (design §3.4.6)."""
    stripped = text.strip()
    if not stripped:
        return False
    if count_tokens(stripped) < MIN_ACTIONABLE_TOKENS:
        return False
    if count_words(stripped) < 5:
        return False
    return not _METADATA_LINE_RE.match(stripped)


def _split_long_block(text: str) -> list[str]:
    """Split >300-token prose at sentence boundaries.

    Bounded at :data:`TARGET_MAX_TOKENS` with :data:`OVERLAP_TOKENS` of trailing
    sentence overlap so a fact near a boundary survives into the next chunk.
    """
    sentences = split_sentences(text)
    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        if current and current_tokens + sentence_tokens > TARGET_MAX_TOKENS:
            pieces.append(" ".join(current).strip())
            overlap: list[str] = []
            overlap_tokens = 0
            for previous in reversed(current):
                previous_tokens = count_tokens(previous)
                if overlap_tokens + previous_tokens > OVERLAP_TOKENS:
                    break
                overlap.insert(0, previous)
                overlap_tokens += previous_tokens
            current = overlap
            current_tokens = overlap_tokens
        current.append(sentence)
        current_tokens += sentence_tokens

    if current:
        pieces.append(" ".join(current).strip())
    return [p for p in pieces if p]


def chunk_section(heading: str | None, blocks: list[Block]) -> list[str]:
    """Chunk one section's blocks into actionable text pieces."""
    if heading and _TABLE_OR_FIGURE_HEADING_RE.match(heading.strip()):
        return []

    pieces: list[str] = []
    buffer: list[Block] = []
    buffer_tokens = 0

    def flush() -> None:
        nonlocal buffer, buffer_tokens
        if buffer:
            text = _render_blocks(buffer)
            if _is_actionable(text):
                pieces.append(text)
        buffer = []
        buffer_tokens = 0

    for block in blocks:
        tokens = count_tokens(block.text)

        if tokens > LARGE_PARAGRAPH_TOKENS:
            flush()
            pieces.extend(p for p in _split_long_block(block.text) if _is_actionable(p))
            continue

        if block.kind == "bullet" and _is_standalone_bullet(block.text):
            flush()
            text = _render_blocks([block])
            if _is_actionable(text):
                pieces.append(text)
            continue

        if buffer and buffer_tokens + tokens > TARGET_MAX_TOKENS:
            flush()
        buffer.append(block)
        buffer_tokens += tokens
        if buffer_tokens >= TARGET_MIN_TOKENS:
            flush()

    flush()
    return pieces


def chunk_document(markdown: str) -> list[SectionChunk]:
    """Chunk a normalized markdown document into heading-tagged chunks."""
    chunks: list[SectionChunk] = []
    for heading, blocks in parse_sections(markdown):
        for text in chunk_section(heading, blocks):
            chunks.append(SectionChunk(text=text, section_heading=heading))
    return chunks
