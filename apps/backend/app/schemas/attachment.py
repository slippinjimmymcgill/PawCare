from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AttachmentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=500)
    mime_type: str = Field(..., max_length=100)
    size_bytes: int = Field(..., ge=0)


class AttachmentUploadResponse(AttachmentBase):
    pass


class AttachmentRead(AttachmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    record_id: str | None = None
