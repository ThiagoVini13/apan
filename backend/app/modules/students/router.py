"""FastAPI router for the students module."""

from typing import Optional

from fastapi import APIRouter

from app.modules.students import schemas, service

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=schemas.StudentListOut)
def list_students(
    q: Optional[str] = None,
    class_id: Optional[str] = None,
) -> schemas.StudentListOut:
    """List students with optional search and class filter."""
    return service.list_students(q=q, class_id=class_id)


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: str) -> schemas.StudentOut:
    """Retrieve a single student with their attendance rate."""
    return service.get_student(student_id)


@router.post("", response_model=schemas.StudentOut, status_code=201)
def create_student(body: schemas.StudentCreateIn) -> schemas.StudentOut:
    """Create a new student."""
    return service.create_student(body)


@router.patch("/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: str, body: schemas.StudentUpdateIn
) -> schemas.StudentOut:
    """Partially update an existing student."""
    return service.update_student(student_id, body)
