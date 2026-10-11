"""
PawCare — Chat session/message Pydantic schemas.
Trace: FR-07, FR-11, requirements.md §5.

Placeholder only — real schemas (ChatSession, Message, with source
citations per FR-07's acceptance criteria) land with P2-BE-002 (Phase 2),
matching docs/design/models/chat_session.py and message.py. One file for
both entities here since they're always read/written together (a message
never exists without its session) — matches how P1-FE-001's Assistant
Chat wireframe treats them as a single screen, not two.
"""

from pydantic import BaseModel


class ChatSessionBase(BaseModel):
    """Placeholder — fields added in P2-BE-002."""


class MessageBase(BaseModel):
    """Placeholder — fields added in P2-BE-002."""
