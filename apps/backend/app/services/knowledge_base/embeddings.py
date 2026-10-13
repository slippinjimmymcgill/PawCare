"""PawCare — embedding providers for the knowledge base.

Task: P1-RAG-004. Trace: docs/design/rag-ingestion-pipeline-design.md §5.

The design fixes a *local sentence-transformer* as the default embedding model
(`all-MiniLM-L6-v2` / `bge-small-en-v1.5`) with a hosted API as the later
fallback if a retrieval benchmark shows it is needed. This module expresses that
as a small provider interface so `P1-RAG-004`'s indexing code (and P2-RAG-001's
retrieval code) never hard-codes a model:

* :class:`SentenceTransformerEmbeddingProvider` — the design default. Lazy
  import; raises a clear :class:`EmbeddingError` if the optional package is not
  installed, rather than an ImportError deep in the stack.
* :class:`HashingEmbeddingProvider` — a deterministic, dependency-free baseline
  used for offline dev and tests. It is a feature-hashing bag-of-words vector,
  **not** a semantic model; it exists so the pipeline is runnable and its
  behavior reproducible without downloading model weights.

Swapping providers changes vectors but not the chunk metadata contract, exactly
as the design intends.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from app.core.config import Settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingError(RuntimeError):
    """Raised when no usable embedding provider can be constructed."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Minimal contract the indexing/retrieval code depends on."""

    name: str
    dim: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one L2-normalized vector per input text."""
        ...


class HashingEmbeddingProvider:
    """Deterministic feature-hashing baseline (unigrams + bigrams).

    Reproducible across machines and versions (blake2b, not Python's salted
    ``hash``), so re-indexing yields identical vectors. Good enough to make a
    smoke test meaningful — an owner query like ``"vomiting in a dog"`` scores
    higher against chunks that share those terms — but it captures lexical, not
    semantic, similarity. Not a substitute for the real model in production.
    """

    name = "hashing"

    def __init__(self, dim: int = 384) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = int(dim)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = _TOKEN_RE.findall(text.lower())
        features: list[tuple[str, float]] = [(token, 1.0) for token in tokens]
        features += [(f"{tokens[i]} {tokens[i + 1]}", 0.5) for i in range(len(tokens) - 1)]
        for feature, weight in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dim
            sign = 1.0 if (value >> 63) & 1 else -1.0
            vector[index] += sign * weight
        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0.0:
            return vector
        return [component / norm for component in vector]


class SentenceTransformerEmbeddingProvider:
    """Local sentence-transformers provider (the design's default)."""

    name = "sentence_transformers"

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise EmbeddingError(
                "sentence-transformers is not installed. Install it "
                "(`pip install sentence-transformers`) or use the offline "
                "baseline with EMBEDDING_PROVIDER=hashing."
            ) from exc
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> list[list[float]]:  # pragma: no cover - needs weights
        if not texts:
            return []
        vectors = self._model.encode(list(texts), normalize_embeddings=True)
        return [[float(component) for component in vector] for vector in vectors]


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Construct the provider named by ``settings.EMBEDDING_PROVIDER``."""
    provider_id = (settings.EMBEDDING_PROVIDER or "").strip().lower()
    if provider_id in {"hashing", "hash", "baseline"}:
        return HashingEmbeddingProvider(settings.EMBEDDING_DIM)
    if provider_id in {"sentence_transformers", "sentence-transformers", "st"}:
        return SentenceTransformerEmbeddingProvider(settings.EMBEDDING_MODEL)
    raise EmbeddingError(
        f"unknown EMBEDDING_PROVIDER {settings.EMBEDDING_PROVIDER!r}; "
        "expected 'sentence_transformers' or 'hashing'"
    )


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors; 0.0 for a zero/degenerate vector."""
    if len(a) != len(b):
        raise ValueError(f"vector length mismatch: {len(a)} != {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
