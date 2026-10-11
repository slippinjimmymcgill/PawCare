# PawCare — RAG Ingestion Pipeline Design (P1-RAG-002)

**Status:** Design draft complete — not implemented yet; this is the specification for Sprint Block 3–4 (`P1-RAG-003` / `P1-RAG-004`).
**Trace:** `plan.md` §3, `requirements.md` §5, `requirements.md` §4 (RAG Recall@5), `specs.md` §8, `docs/legal/knowledge-source-licensing-tracker.md`

## 1. Goal and constraints

This design defines the ingestion contract for the knowledge base that grounds PawCare's assistant and assessment explanations. It is intentionally constrained by the project safety/legal rules:

- Only sources cleared by `P1-RAG-001` may be ingested.
- Every ingested document must carry a license and a source link.
- A citation must be traceable to a retrievable chunk, not just to a model answer.
- The system must allow filtering by species, body system, and source license without losing the citation trail.

The design below assumes the vector capability confirmed in `P1-BE-002` is viable. If pgvector is not viable on the final host, the model `Chunk.embedding` still moves to a separate vector store, but the ingestion metadata and citation fields stay identical.

## 2. Source intake policy

### 2.1 Eligible sources

Only document sources with a recorded license and no unresolved ambiguity are eligible.

- Preferred: open-access veterinary journals with explicit CC BY / CC BY-NC terms.
- Acceptable fallback: public veterinary-school or public-health pages with explicit permission and attribution terms.
- Blocked: all-rights-reserved medical-brand sites, ambiguous wiki terms, or any source with missing licensing metadata.

### 2.2 Source metadata captured at document level

Each source document is ingested as a `KnowledgeDocument` with the following fields:

- `document_id` (UUID)
- `title`
- `source` (publisher / domain / institution)
- `source_url`
- `license`
- `license_url` (if available)
- `published_at` (date or null)
- `retrieved_at`
- `species_applicability` (dog, cat, both, unspecified)
- `body_system_tags` (e.g. GI, respiratory, urinary, dermatologic)
- `content_type` (journal_article, guide, public_health_resource, vet_school_page)
- `status` (`active`, `archived`, `excluded`)
- `notes` (optional explanation for edge cases)

This matches the project’s `KnowledgeDocument` model and supports admin review.

## 3. Chunking strategy

### 3.1 Design goal

Chunks must be:

- large enough to preserve the factual context needed for a correct answer,
- small enough to retrieve highly relevant content with low noise,
- easy to cite by source and heading,
- safe to filter by species and body system.

### 3.2 Chunk unit

Use the natural document structure as the first split boundary:

1. Heading / section title
2. Paragraphs
3. Bullet lists or clinical notices

Do not split mid-sentence unless the paragraph is extremely long.

### 3.3 Target size

Recommended target:

- 250–350 tokens per chunk
- 40–80 token overlap between adjacent chunks

Reasoning:

- For veterinary source material, a chunk needs enough surrounding context to explain how a symptom maps to a body system, risk level, or home-care warning.
- The chunk should still be small enough to stay semantically tight and be retrievable without pulling in a whole article.
- The overlap ensures that a meaningful sentence near the edge of one chunk is still available in the next chunk for retrieval continuity.

### 3.4 Chunking algorithm

1. Parse the document and keep section headings.
2. Split by headings and paragraphs.
3. If a paragraph is shorter than 200 tokens, keep it with the previous section context.
4. If a paragraph is longer than 300 tokens, split at sentence boundaries using a max of 350 tokens and 50-token overlap.
5. If there are bullets or tables, treat the list item as a separate chunk whenever it contains a standalone fact or recommendation.
6. Do not create a chunk that is pure metadata or only the citation line; every chunk must contain actionable text.

### 3.5 Chunk content contract

Each emitted chunk should carry:

- `chunk_id`
- `document_id`
- `chunk_index`
- `chunk_text`
- `section_heading`
- `word_count` / `token_count`
- `source_title`
- `source_url`
- `author` (if available)
- `license`
- `species_applicability`
- `body_system`
- `symptom_tags` / `condition_tags`
- `published_date`
- `retrieved_date`
- `citation_text` (the source short label used in UI)

This design keeps the chunk itself both retrieval-ready and user-visible.

## 4. Metadata schema per chunk

The `Chunk` model already reserves a flexible `metadata_json` field. This is the correct place for the bulk of chunk-specific metadata, while the core columns remain lean and query-friendly.

Recommended schema:

```json
{
  "document_id": "uuid",
  "section_heading": "Vomiting in dogs",
  "chunk_index": 3,
  "token_count": 286,
  "species": ["dog"],
  "body_system": "gastrointestinal",
  "symptom_tags": ["vomiting", "dehydration"],
  "condition_tags": ["gastroenteritis", "obstruction"],
  "source": "Open Veterinary Journal",
  "source_url": "https://example.org/article",
  "license": "CC BY-NC 4.0",
  "published_date": "2023-06-14",
  "retrieved_at": "2026-10-11T22:00:00Z",
  "citation_label": "Open Veterinary Journal, 2023",
  "is_red_flag_relevant": true,
  "confidence_note": "derived from a clinically specific section"
}
```

### 4.1 Query filter fields

These fields are required for the retrieval pipeline and admin UI:

- `species`
- `body_system`
- `source`
- `license`
- `published_date`
- `section_heading`
- `symptom_tags`

These are the fields that should be queryable in SQL and vector retrieval filters, so the retrieval layer can support both semantic similarity and hard filters.

### 4.2 Why this schema satisfies FR-07

`requirements.md` FR-07 requires that every substantive assistant claim is traceable to a retrieved knowledge-base chunk and that sources are shown to the user.

This schema satisfies that requirement because each chunk has:

- a source and license,
- a citation label,
- a section heading and date,
- a living retrieval path back to the original document.

No answer should be rendered without at least one source-backed chunk being retrieved, and no chunk should be anonymous or untraceable.

## 5. Embedding model choice

### 5.1 Decision: use a local sentence-transformer model for the first implementation

Recommended default:

- `sentence-transformers/all-MiniLM-L6-v2` or `BAAI/bge-small-en-v1.5`
- Use a local embedding model in the first version of the ingestion pipeline.

### 5.2 Why this is the right default for PawCare

- Lower cost: no per-request API billing during prototyping and early benchmark runs.
- Faster iteration: the team can run re-indexing locally without external vendor dependencies.
- Easier to keep licenses and model provenance in a reproducible pipeline.
- Good quality for short-to-medium veterinary passages if the chunks are tightly constructed.
- Keeps the project independent of a single hosted AI provider during the design and early validation phase.

### 5.3 Hosted embedding alternative

A hosted embedding model is still a valid future option when the project grows or if evaluation shows that local embeddings underperform on retrieval recall.

Trade-off:

- Hosted embedding API: higher quality in some tasks, simpler scaling, but recurring cost and vendor dependency.
- Local embedding model: lower cost and more control, but requires local storage and more inference work on project infrastructure.

### 5.4 Decision gate for later re-evaluation

Re-evaluate the embedding model once recall targets are measured against the held-out retrieval benchmark (`requirements.md` §4 / `plan.md` §11). If local embeddings fail the RAG Recall@5 gate, switch to a hosted model without changing the metadata contract.

## 6. Retrieval contract that the ingestion design must enable

The ingestion design must support the later retrieval pipeline (`P2-RAG-001`) and the assistant UI.

At retrieval time, the system should be able to:

- retrieve top-k semantically relevant chunks,
- filter by `species` and `body_system`,
- surface a source citation and visible license,
- rank alternative chunks by relevance without hiding the source provenance.

This contract matters because the design goal is not just a vector index — it is a evidence-backed assistant that can answer with traceable veterinarian-safe citations.

## 7. Operational pipeline steps

1. Source validation
   - confirm the source is on the cleared list and is not ambiguous
2. Document normalization
   - strip boilerplate, preserve headings, store source metadata
3. Chunking
   - paragraph/section-based splitting with bounded token size and overlap
4. Metadata enrichment
   - species, body system, symptom tags, source details, license, date
5. Embedding
   - compute embeddings for each chunk and save to the vector store
6. Indexing
   - store chunk + metadata + embedding in the vector database
7. Validation
   - run a small retrieval smoke test to confirm citations show source info and filters work

## 8. Acceptance criteria for this design

This task is considered complete when the project has a written, concrete design that:

- defines token/overlap boundaries for chunking,
- defines the per-chunk metadata fields needed for filters and citations,
- chooses an embedding approach with an explicit cost/latency/quality trade-off,
- does not leave the license/source provenance unspecified,
- is specific enough that `P1-RAG-003` and `P1-RAG-004` do not need to rediscover the same design choices in code.

That is the threshold the backlog item is meant to satisfy.
