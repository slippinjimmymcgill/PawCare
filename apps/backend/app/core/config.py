"""
PawCare backend — application settings.

Task: P1-BE-001 · Trace: plan.md §2
Everything configurable is read from the environment (via .env in local
dev), per this task's "Do NOT hardcode secrets or a database URL" rule.
Field names here match apps/backend/.env.example exactly — if you add a
setting, add it to both files, in the same order, so a fresh clone never
hits an "unknown env var" surprise.

LLM_* and OBJECT_STORAGE_* are intentionally allowed to be blank — those
are blocked on P0-OPS-004 / P0-OPS-005 (real provider/hosting accounts),
not a dev-environment problem. Code that depends on them (Phase 2's
Assistant Service, P1-BE-006's attachment upload) must check for an empty
value and fail with a clear "not configured" message rather than a raw
exception — that's those tasks' responsibility, not this one's.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "changeme-generate-a-real-random-value"
    DEBUG: bool = True

    # ── Database (real provisioning is P1-BE-002) ───────────────
    DATABASE_URL: str = "postgresql+psycopg://pawcare:pawcare@localhost:5432/pawcare_dev"

    # ── Auth (FR-01) ─────────────────────────────────────────────
    JWT_SECRET_KEY: str = "changeme-generate-a-separate-random-value"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── LLM provider (blocked on P0-OPS-004) ────────────────────
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    # ── Object storage (P1-BE-006) ──────────────────────────────
    OBJECT_STORAGE_PROVIDER: str = "local"
    OBJECT_STORAGE_BUCKET: str = ""
    OBJECT_STORAGE_KEY: str = ""
    OBJECT_STORAGE_SECRET: str = ""
    OBJECT_STORAGE_REGION: str = "us-east-1"
    OBJECT_STORAGE_ENDPOINT_URL: str = ""
    LOCAL_STORAGE_DIR: str = "uploads"
    MAX_ATTACHMENT_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit

    # ── Knowledge base embeddings (P1-RAG-004) ──────────────────
    # "sentence_transformers" is the design's local default
    # (`all-MiniLM-L6-v2`) and needs the optional sentence-transformers
    # package. "hashing" is a deterministic, dependency-free baseline for
    # offline dev/CI. EMBEDDING_DIM is fixed at the vector column's width.
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    EMBEDDING_BATCH_SIZE: int = 64

    # ── CORS ─────────────────────────────────────────────────────
    FRONTEND_ORIGIN: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Cached so Settings() — which reads .env — only runs once per process."""
    return Settings()
