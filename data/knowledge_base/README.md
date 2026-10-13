# PawCare Knowledge Base — Batch 1

**Tasks:** `P1-RAG-003` (collection & chunking) · `P1-RAG-004` (embedding & indexing)
**Trace:** `docs/design/rag-ingestion-pipeline-design.md` · `docs/task_backlog.md`
**Generated:** 2026-10-13 · **Status:** collection + chunking + indexing complete

This directory holds the batch-1 knowledge corpus: nine openly licensed
veterinary documents, the chunks derived from them, and the manifest that
records exactly what was produced.

## Layout

```
raw/                 # source markdown with TOML front matter (input, committed)
  <source_id>.md
batch1/              # generated artifacts (output)
  documents.jsonl    # one normalized document per line
  chunks.jsonl       # one retrievable, citable chunk per line
  manifest.json      # run summary: counts, chunking params, source list
```

## Licensing rule

Every document here comes from a source cleared by `P1-RAG-001` and recorded in
`docs/legal/knowledge-source-licensing-tracker.md`. The pipeline refuses
(`LicenseError`) any `source_id` that is not in
`app/services/knowledge_base/source_registry.py` with a concrete license and
`redistribution_permitted = true`. All nine sources are CC BY 4.0 or U.S.
public domain; attribution remains a UI obligation and is carried per chunk in
`citation_text` / `author` / `license`.

## Sources (batch 1)

| `source_id` | Red-flag | Species | License |
|---|---|---|---|
| `fda-xylitol` | RF-005 toxin ingestion | dog | Public domain (US Gov work) |
| `frontiers-household-toxins` | RF-005 | dog, cat | CC BY 4.0 |
| `frontiers-hemorrhage` | RF-004 bleeding | dog, cat | CC BY 4.0 |
| `mdpi-gdv` | RF-006 bloat/GDV | dog | CC BY 4.0 |
| `mdpi-heat-illness` | RF-009 heatstroke | dog | CC BY 4.0 |
| `mdpi-acute-seizures` | RF-003 seizures, RF-002 collapse | dog, cat | CC BY 4.0 |
| `mdpi-emergency-dyspnea-cats` | RF-001 respiratory distress | cat | CC BY 4.0 |
| `mdpi-trauma-att` | RF-008 trauma | dog, cat | CC BY 4.0 |
| `jvim-feline-urethral-obstruction` | RF-007 urinary obstruction | cat | CC BY 4.0 (per-article) |

Known coverage gaps carried into later batches: **RF-001 (respiratory distress)
is covered for cats only**, and RF-005 is covered by two overlapping documents.
Owner-facing, non-journal material is still thin (the `P1-RAG-001` coverage-gap
flag).

## Chunking

Fixed by `P1-RAG-002`; implemented in
`app/services/knowledge_base/chunking.py`:

- target 250–350 tokens/chunk, 50-token overlap on splits;
- paragraphs < 200 tokens merge with their section context;
- paragraphs > 300 tokens split at sentence boundaries (max 350);
- a bullet becomes its own chunk only when it is a standalone fact or
  recommendation, otherwise it merges with the section;
- table/figure sections and pure-metadata lines are dropped.

Token counts use a deterministic word+punctuation approximation (no model
tokenizer), so they are stable across machines.

## Regenerate

```bash
cd apps/backend
python scripts/ingest_knowledge_base.py
```

This rewrites `batch1/`. Document and chunk ids are deterministic UUIDv5 values
derived from `source_id` + index, so re-running produces byte-identical
`documents.jsonl` / `chunks.jsonl` (only `manifest.json`'s `generated_at`
changes).

## Index (embed + load into the database)

`P1-RAG-004` consumes `batch1/chunks.jsonl`, embeds each chunk and upserts the
documents + vectors into the `knowledge_documents` / `chunks` tables:

```bash
cd apps/backend
python scripts/index_knowledge_base.py            # Postgres + pgvector (default)
```

Offline smoke test without Postgres or model weights (uses the deterministic
`hashing` provider and a throwaway SQLite file):

```bash
cd apps/backend
python scripts/index_knowledge_base.py \
  --database-url sqlite:///kb_smoke.db --create-tables --provider hashing \
  --search "dog ate chocolate xylitol" --species dog --red-flag-only
```

Indexing is idempotent (chunk ids are deterministic), re-embedding only when the
embedding model changed or `--force` is passed. On PostgreSQL the `embedding`
column is a native pgvector `vector(384)` with an HNSW cosine index; on other
dialects it degrades to JSON. The `sentence-transformers` embedding model is an
optional dependency — the `hashing` provider needs nothing beyond the standard
library.

## Next

`P2-RAG-001` (retrieval pipeline) builds on `app/services/knowledge_base/indexer.py`'s
`semantic_search`, moving the cosine scan into native pgvector ANN queries on
Postgres. The chunk metadata contract emitted here is unchanged by the embedding
model choice.
