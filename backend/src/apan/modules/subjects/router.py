from fastapi import APIRouter

from apan.core.schemas import ApiModel
from apan.core.store import store
from apan.modules.classes.schemas import SubjectOut


class SubjectListOut(ApiModel):
    items: list[SubjectOut]
    total: int


router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=SubjectListOut)
def list_subjects() -> SubjectListOut:
    """List all available subjects."""
    items = [SubjectOut.model_validate(s) for s in store.subjects.values()]
    return SubjectListOut(items=items, total=len(items))
