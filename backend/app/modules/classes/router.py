"""FastAPI router for the classes module."""

from fastapi import APIRouter

from app.modules.classes import schemas, service
from app.modules.students.schemas import StudentListOut

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=schemas.SchoolClassListOut)
def list_classes() -> schemas.SchoolClassListOut:
    """List all school classes with student counts."""
    return service.list_classes()


@router.get("/{class_id}", response_model=schemas.SchoolClassOut)
def get_class(class_id: str) -> schemas.SchoolClassOut:
    """Get details for a single class."""
    return service.get_class(class_id)


@router.get("/{class_id}/students", response_model=StudentListOut)
def get_class_students(class_id: str) -> StudentListOut:
    """List all students enrolled in a class."""
    return service.get_class_students(class_id)
