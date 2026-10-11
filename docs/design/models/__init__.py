"""
PawCare — model package.

Phase 0 design draft (P0-BE-001). These stubs are meant to be copied into
apps/backend/app/models/ once the FastAPI scaffold exists (P1-BE-001) —
they are not wired into a running app yet, and no migration has been run
against them. See ../schema-notes.md for the design decisions behind this
package, and ../er-diagram.png for the visual.
"""

from .base import Base, TimestampMixin, UUIDPKMixin, utcnow
from .chat_session import ChatSession
from .chunk import Chunk
from .enums import (
    ChatRole,
    FeedbackTargetType,
    HealthRecordType,
    ReminderStatus,
    ReminderType,
    Sex,
    Species,
    UrgencyLevel,
    UserRole,
)
from .feedback import Feedback
from .health_record import HealthRecord
from .knowledge_document import KnowledgeDocument
from .medication import Medication
from .message import Message
from .pet import Pet
from .reminder import Reminder
from .symptom_assessment import SymptomAssessment
from .user import User
from .vaccination import Vaccination

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPKMixin",
    "utcnow",
    "User",
    "Pet",
    "HealthRecord",
    "Vaccination",
    "Medication",
    "SymptomAssessment",
    "ChatSession",
    "Message",
    "Reminder",
    "KnowledgeDocument",
    "Chunk",
    "Feedback",
    "UserRole",
    "Species",
    "Sex",
    "HealthRecordType",
    "UrgencyLevel",
    "ChatRole",
    "ReminderType",
    "ReminderStatus",
    "FeedbackTargetType",
]
