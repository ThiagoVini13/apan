"""FastAPI router for the roll_calls module."""

from datetime import date
from typing import Optional

from fastapi import APIRouter

from app.modules.roll_calls import schemas, service

router = APIRouter(prefix="/roll-calls", tags=["roll-calls"])


@router.get("", response_model=schemas.RollCallListOut)
def list_roll_calls(
    class_id: Optional[str] = None,
    date: Optional[date] = None,
) -> schemas.RollCallListOut:
    """List roll calls with optional filters by class and date."""
    return service.list_roll_calls(class_id=class_id, lesson_date=date)


@router.put("", response_model=schemas.RollCallOut)
def upsert_roll_call(body: schemas.RollCallUpsertIn) -> schemas.RollCallOut:
    """Create or update a roll call (upsert by classId + subjectId + date)."""
    return service.upsert_roll_call(body)


@router.get("/{roll_call_id}", response_model=schemas.RollCallOut)
def get_roll_call(roll_call_id: str) -> schemas.RollCallOut:
    """Get a single roll call with all attendance records."""
    return service.get_roll_call(roll_call_id)
