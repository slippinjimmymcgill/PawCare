"""
PawCare — shared enum types.

Kept in one file because several models reference the same enum (e.g. both
Feedback and, later, moderation tooling will care about target_type), and
because a single source of truth avoids two models drifting out of sync on
an enum's allowed values.
"""

import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"


class Species(str, enum.Enum):
    DOG = "dog"
    CAT = "cat"
    # Intentionally not extended beyond dog/cat — see specs.md §3.1 and §9.
    # Do not add values here without a scope decision (specs.md §3, plan.md
    # §11 item 7); the app layer should reject anything else at the API
    # boundary, not rely on this enum being incomplete as the only guard.


class Sex(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class HealthRecordType(str, enum.Enum):
    VISIT = "visit"
    WEIGHT_LOG = "weight_log"
    NOTE = "note"
    # Vaccination and Medication are their own entities (vaccination.py,
    # medication.py), not HealthRecordType values — they have their own
    # lifecycle fields (next_due, start/end date) that don't fit this
    # generic record shape. See schema-notes.md §2 for why.


class UrgencyLevel(str, enum.Enum):
    """Matches requirements.md FR-05's four-level triage exactly. This is a
    safety-relevant enum — do not reorder or rename without checking every
    place that compares against UrgencyLevel.EMERGENCY, since the Safety
    Layer (FR-08, plan.md §10) treats that value as a hard override."""

    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    HOME_CARE = "home_care"


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ReminderType(str, enum.Enum):
    VACCINATION = "vaccination"
    DEWORMING = "deworming"
    CHECKUP = "checkup"
    WEIGHT = "weight"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    DISMISSED = "dismissed"


class FeedbackTargetType(str, enum.Enum):
    ASSESSMENT = "assessment"
    MESSAGE = "message"
