"""PawCare — Knowledge base ingestion, embedding and retrieval.

Tasks: P1-RAG-003 (collection + chunking), P1-RAG-004 (embedding + indexing).
Trace: plan.md §3, requirements.md FR-07 / §6,
       docs/design/rag-ingestion-pipeline-design.md.

The package implements the design's operational pipeline:

1. source validation — ``source_registry`` (cleared-license gate);
2. document normalization + 3. chunking + 4. metadata enrichment — ``loader``,
   ``chunking``, ``pipeline`` (P1-RAG-003);
5. embedding + 6. indexing — ``embeddings``, ``indexer`` (P1-RAG-004);
7. retrieval smoke test — ``indexer.semantic_search`` (P1-RAG-004).

Design decisions fixed by P1-RAG-002 and treated as contract here:

* chunk target 250–350 tokens, 40–80 token overlap;
* split on document structure (headings → paragraphs → bullets);
* paragraphs shorter than 200 tokens merge with their section context;
* paragraphs longer than 300 tokens split at sentence boundaries
  (max 350 tokens, 50-token overlap);
* no chunk may be pure metadata / a citation line;
* every chunk is traceable to a source + license (nothing anonymous);
* embeddings come from a swappable provider; the metadata contract is unchanged
  by the model choice.
"""

from app.services.knowledge_base.embeddings import (
    EmbeddingError,
    EmbeddingProvider,
    HashingEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    build_embedding_provider,
    cosine_similarity,
)
from app.services.knowledge_base.indexer import (
    IndexReport,
    IndexingError,
    SearchHit,
    index_batch,
    load_batch_artifacts,
    semantic_search,
)
from app.services.knowledge_base.source_registry import (
    CLEARED_SOURCES,
    LicenseError,
    get_source,
    require_cleared,
)
from app.services.knowledge_base.types import (
    Chunk,
    Document,
    SourceRecord,
)

__all__ = [
    "CLEARED_SOURCES",
    "Chunk",
    "Document",
    "EmbeddingError",
    "EmbeddingProvider",
    "HashingEmbeddingProvider",
    "IndexReport",
    "IndexingError",
    "LicenseError",
    "SearchHit",
    "SentenceTransformerEmbeddingProvider",
    "SourceRecord",
    "build_embedding_provider",
    "cosine_similarity",
    "get_source",
    "index_batch",
    "load_batch_artifacts",
    "require_cleared",
    "semantic_search",
]
