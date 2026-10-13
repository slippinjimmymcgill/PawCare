"""Tests for the knowledge base ingestion pipeline (P1-RAG-003).

Covers the chunking algorithm (``chunking.py``), the raw TOML front-matter
loader (``loader.py``), the license gate (``source_registry.py``) and the
end-to-end pipeline (``pipeline.py``).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from app.services.knowledge_base import chunking
from app.services.knowledge_base.chunking import (
    Block,
    chunk_document,
    chunk_section,
    count_tokens,
    count_words,
    parse_sections,
    split_sentences,
)
from app.services.knowledge_base.loader import (
    FrontMatterError,
    load_raw_document,
    parse_front_matter,
)
from app.services.knowledge_base.pipeline import (
    DEFAULT_RAW_DIR,
    IngestionError,
    build_document,
    ingest_directory,
    ingest_file,
    run,
    write_artifacts,
)
from app.services.knowledge_base.source_registry import (
    CLEARED_SOURCES,
    LicenseError,
    get_source,
    require_cleared,
)


def _raw_markdown(source_id: str, body: str, **front_matter: object) -> str:
    fields = {"source_id": source_id, "retrieved_at": "2026-10-13", **front_matter}
    lines = ["+++"]
    for key, value in fields.items():
        if isinstance(value, list):
            rendered = "[" + ", ".join(json.dumps(v) for v in value) + "]"
        elif isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = json.dumps(str(value))
        lines.append(f"{key} = {rendered}")
    lines.append("+++")
    return "\n".join(lines) + "\n\n" + body + "\n"


def _write_raw(directory: Path, filename: str, source_id: str, body: str, **front: object) -> Path:
    path = directory / filename
    path.write_text(_raw_markdown(source_id, body, **front), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Token accounting
# --------------------------------------------------------------------------- #


def test_count_tokens_counts_words_and_punctuation() -> None:
    assert count_tokens("Hello world.") == 3  # Hello, world, .
    assert count_tokens("") == 0
    assert count_tokens("a, b, c") == 5  # a , b , c


def test_count_words_ignores_punctuation_only() -> None:
    assert count_words("Hello world.") == 2


def test_split_sentences_keeps_terminators() -> None:
    assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]


def test_split_sentences_falls_back_to_whole_text() -> None:
    assert split_sentences("no terminator here") == ["no terminator here"]


# --------------------------------------------------------------------------- #
# Section parsing
# --------------------------------------------------------------------------- #


def test_parse_sections_splits_headings_paragraphs_and_bullets() -> None:
    markdown = (
        "## Signs\n\n"
        "Vomiting and lethargy are common.\n\n"
        "- Collapse\n"
        "- Difficulty walking\n\n"
        "## Next\n\n"
        "More text here."
    )
    sections = parse_sections(markdown)
    assert [heading for heading, _ in sections] == ["Signs", "Next"]
    signs_blocks = sections[0][1]
    assert [b.kind for b in signs_blocks] == ["paragraph", "bullet", "bullet"]
    assert signs_blocks[1].text == "Collapse"


# --------------------------------------------------------------------------- #
# Chunk assembly rules
# --------------------------------------------------------------------------- #


def test_short_paragraphs_merge_up_to_target() -> None:
    short = "This sentence adds a modest number of tokens to the buffer."
    blocks = [Block("paragraph", " ".join([short] * 8)) for _ in range(3)]
    pieces = chunk_section("Overview", blocks)
    assert len(pieces) == 1, "short paragraphs should merge into one chunk"
    assert count_tokens(pieces[0]) >= chunking.TARGET_MIN_TOKENS
    assert pieces[0].count(short) == 24


def test_long_paragraph_splits_with_overlap_and_max_size() -> None:
    sentences = [
        f"This is sentence number {i} and it carries enough words to count as several tokens here."
        for i in range(30)
    ]
    paragraph = " ".join(sentences)
    assert count_tokens(paragraph) > chunking.LARGE_PARAGRAPH_TOKENS

    pieces = chunk_section("Long", [Block("paragraph", paragraph)])
    assert len(pieces) >= 2
    assert all(count_tokens(p) <= chunking.TARGET_MAX_TOKENS for p in pieces)
    # The last sentence of one piece is carried into the next (overlap).
    last_sentence = split_sentences(pieces[0])[-1]
    assert last_sentence in pieces[1]


def test_short_bullet_list_items_merge_but_recommendations_stand_alone() -> None:
    blocks = [
        Block("bullet", "Sugar-free jams, jellies, and nut butters"),
        Block("bullet", "Cough syrups and liquid medicines for adults and children"),
        Block("bullet", "Take your dog to a veterinarian immediately if poisoning is suspected."),
    ]
    pieces = chunk_section("About xylitol", blocks)
    assert len(pieces) == 2
    assert "Sugar-free jams" in pieces[0]
    assert pieces[1].startswith("- Take your dog")


def test_table_and_figure_sections_are_skipped() -> None:
    assert chunk_section("Table 1", [Block("paragraph", "Mean age and weight of the cohort are reported.")]) == []
    assert chunk_section("Figure 2", [Block("paragraph", "Survival curve by triage score.")]) == []


def test_metadata_only_text_is_not_a_chunk() -> None:
    assert chunk_section(None, [Block("paragraph", "doi: 10.3390/vetsci11060277")]) == []
    assert chunk_section(None, [Block("paragraph", "Keywords: sepsis, shock, trauma, emergency")]) == []


def test_chunk_document_tags_every_chunk_with_its_heading() -> None:
    markdown = "## Signs\n\nVomiting and lethargy are the most common owner-reported signs.\n"
    chunks = chunk_document(markdown)
    assert chunks
    assert all(chunk.section_heading == "Signs" for chunk in chunks)


# --------------------------------------------------------------------------- #
# Front-matter loader
# --------------------------------------------------------------------------- #


def test_parse_front_matter_reads_toml_and_body() -> None:
    text = '+++\nsource_id = "demo"\nretrieved_at = "2026-10-13"\nis_red_flag_relevant = true\n+++\n\n# Heading\n\nBody text.'
    metadata, body = parse_front_matter(text)
    assert metadata["source_id"] == "demo"
    assert metadata["is_red_flag_relevant"] is True
    assert body.startswith("# Heading")


def test_parse_front_matter_requires_fence() -> None:
    with pytest.raises(FrontMatterError):
        parse_front_matter("no front matter here")


def test_parse_front_matter_rejects_unterminated_block() -> None:
    with pytest.raises(FrontMatterError):
        parse_front_matter('+++\nsource_id = "demo"\n\nbody with no close')


def test_load_raw_document_round_trips(tmp_path: Path) -> None:
    path = _write_raw(tmp_path, "demo.md", "fda-xylitol", "## Signs\n\nSomething actionable here.")
    raw = load_raw_document(path)
    assert raw.metadata["source_id"] == "fda-xylitol"
    assert raw.require("retrieved_at") == "2026-10-13"


def test_load_raw_document_requires_source_id(tmp_path: Path) -> None:
    path = tmp_path / "missing.md"
    path.write_text("+++\nretrieved_at = \"2026-10-13\"\n+++\n\nbody", encoding="utf-8")
    raw = load_raw_document(path)
    with pytest.raises(FrontMatterError):
        raw.require("source_id")


# --------------------------------------------------------------------------- #
# License gate
# --------------------------------------------------------------------------- #


def test_require_cleared_returns_registered_source() -> None:
    record = require_cleared("fda-xylitol")
    assert record.source_id == "fda-xylitol"
    assert record.status == "cleared"


def test_require_cleared_rejects_unknown_source() -> None:
    with pytest.raises(LicenseError):
        require_cleared("not-in-the-registry")


def test_require_cleared_rejects_license_mismatch() -> None:
    with pytest.raises(LicenseError):
        require_cleared("fda-xylitol", license="CC BY 4.0")


def test_get_source_returns_none_for_unknown() -> None:
    assert get_source("does-not-exist") is None


def test_registry_only_contains_cleared_redistributable_sources() -> None:
    for record in CLEARED_SOURCES.values():
        assert record.status == "cleared"
        assert record.redistribution_permitted is True
        assert record.license.strip()


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #


def test_ingest_file_builds_chunks_with_full_metadata() -> None:
    document = ingest_file(DEFAULT_RAW_DIR / "fda-xylitol.md")
    assert document.source_id == "fda-xylitol"
    assert document.chunks, "expected at least one chunk"
    for chunk in document.chunks:
        assert chunk.species_applicability == ["dog"]
        assert chunk.is_red_flag_relevant is True
        assert chunk.body_system
        assert chunk.citation_text.startswith("U.S. Food and Drug Administration")
        assert uuid.UUID(chunk.chunk_id)  # valid, deterministic id
    assert [c.chunk_index for c in document.chunks] == list(range(len(document.chunks)))


def test_pipeline_ids_are_deterministic() -> None:
    first = ingest_file(DEFAULT_RAW_DIR / "mdpi-gdv.md")
    second = ingest_file(DEFAULT_RAW_DIR / "mdpi-gdv.md")
    assert first.document_id == second.document_id
    assert [c.chunk_id for c in first.chunks] == [c.chunk_id for c in second.chunks]


def test_ingest_file_rejects_uncleared_source(tmp_path: Path) -> None:
    path = _write_raw(tmp_path, "bad.md", "some-random-blog", "## Signs\n\nNot licensed for ingestion.")
    with pytest.raises(LicenseError):
        ingest_file(path)


def test_ingest_directory_rejects_empty_dir(tmp_path: Path) -> None:
    with pytest.raises(IngestionError):
        ingest_directory(tmp_path)


def test_build_document_reports_front_matter_mismatch(tmp_path: Path) -> None:
    raw = load_raw_document(
        _write_raw(tmp_path, "mismatch.md", "frontiers-household-toxins", "## Signs\n\nBody text here.")
    )
    source = require_cleared("fda-xylitol")
    with pytest.raises(IngestionError):
        build_document(raw, source)


def test_run_writes_matching_jsonl_artifacts(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "out"
    raw_dir.mkdir()
    _write_raw(raw_dir, "a.md", "fda-xylitol", "## Signs\n\nVomiting and weakness are common signs of poisoning.")
    _write_raw(
        raw_dir,
        "b.md",
        "mdpi-heat-illness",
        "## Risk\n\nBrachycephalic dogs are at higher risk of heat-related illness in summer.",
        is_red_flag_relevant="true",
    )

    manifest = run(raw_dir, out_dir)

    assert (out_dir / "documents.jsonl").exists()
    assert (out_dir / "chunks.jsonl").exists()
    assert (out_dir / "manifest.json").exists()

    documents = [json.loads(line) for line in (out_dir / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert manifest["document_count"] == len(documents) == 2
    assert manifest["chunk_count"] == len(chunks)
    assert {d["source_id"] for d in documents} == {"fda-xylitol", "mdpi-heat-illness"}
    assert all("chunks" not in doc for doc in documents)  # chunk list lives in its own file
    assert {c["source_id"] for c in chunks} <= {"fda-xylitol", "mdpi-heat-illness"}


def test_write_artifacts_is_deterministic(tmp_path: Path) -> None:
    documents = ingest_directory(DEFAULT_RAW_DIR)
    write_artifacts(documents, tmp_path)
    first_chunks = (tmp_path / "chunks.jsonl").read_text(encoding="utf-8")
    write_artifacts(documents, tmp_path)
    second_chunks = (tmp_path / "chunks.jsonl").read_text(encoding="utf-8")
    assert first_chunks == second_chunks


# --------------------------------------------------------------------------- #
# Batch-1 corpus integration
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not DEFAULT_RAW_DIR.is_dir(), reason="raw corpus not present")
def test_batch1_corpus_covers_every_red_flag_source() -> None:
    documents = ingest_directory(DEFAULT_RAW_DIR)
    assert len(documents) == len(CLEARED_SOURCES) == 9
    source_ids = {doc.source_id for doc in documents}
    assert source_ids == set(CLEARED_SOURCES)
    # Every batch-1 document is red-flag relevant and produces actionable chunks.
    for document in documents:
        assert document.chunks
        assert all(chunk.is_red_flag_relevant for chunk in document.chunks)
        assert all(chunk.token_count <= chunking.TARGET_MAX_TOKENS for chunk in document.chunks)
