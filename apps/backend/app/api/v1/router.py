"""
PawCare — API v1 router aggregation.

Collects every module router under app/api/v1/ into one APIRouter so
app/main.py only needs one include_router() call. Adding a new v1 router
means: create the file, define `router = APIRouter(...)`, import and
include it here — nothing in main.py should need to change.
"""

from fastapi import APIRouter

from app.api.v1 import admin, assessments, assistant, auth, pets, records, reminders

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(pets.router)
api_router.include_router(records.router)
api_router.include_router(assessments.router)
api_router.include_router(assistant.router)
api_router.include_router(reminders.router)
api_router.include_router(admin.router)
