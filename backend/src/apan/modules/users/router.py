from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from apan.core.constants import API_PREFIX
from apan.core.context import Role
from apan.core.dependencies import (
    ClientInfoDep,
    MailerDep,
    PageParamsDep,
    SessionDep,
    SettingsDep,
)
from apan.core.pagination import Page
from apan.modules.auth import service as auth
from apan.modules.auth.dependencies import AdminActor, CurrentActor, get_actor
from apan.modules.users import service
from apan.modules.users.schemas import UserCreate, UserFilters, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_actor)])


def _filters(
    q: Annotated[str | None, Query(max_length=100)] = None,
    role: Role | None = None,
    is_active: Annotated[bool | None, Query(alias="isActive")] = None,
) -> UserFilters:
    return UserFilters(q=q, role=role, is_active=is_active)


@router.get("", response_model=Page[UserRead], operation_id="users_list")
async def list_users(
    session: SessionDep,
    _: AdminActor,
    page: PageParamsDep,
    filters: Annotated[UserFilters, Depends(_filters)],
) -> Page[UserRead]:
    return await service.list_users(session, filters, page)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="users_create",
)
async def create_user(
    body: UserCreate,
    response: Response,
    session: SessionDep,
    mailer: MailerDep,
    settings: SettingsDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> UserRead:
    user = await auth.invite_user(session, mailer, settings, actor, client, body)
    response.headers["Location"] = f"{API_PREFIX}/users/{user.id}"
    return user


@router.get("/{user_id}", response_model=UserRead, operation_id="users_get")
async def get_user(user_id: UUID, session: SessionDep, actor: CurrentActor) -> UserRead:
    return await service.get_user(session, actor, user_id)


@router.patch("/{user_id}", response_model=UserRead, operation_id="users_update")
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    session: SessionDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> UserRead:
    return await service.update_user(session, actor, user_id, body, client)


@router.post("/{user_id}/deactivate", response_model=UserRead, operation_id="users_deactivate")
async def deactivate_user(
    user_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> UserRead:
    return await service.set_active(session, actor, user_id, active=False, client=client)


@router.post("/{user_id}/activate", response_model=UserRead, operation_id="users_activate")
async def activate_user(
    user_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> UserRead:
    return await service.set_active(session, actor, user_id, active=True, client=client)
