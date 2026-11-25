from dataclasses import dataclass
from uuid import UUID

from httpx import AsyncClient
from polyfactory.factories.pydantic_factory import ModelFactory
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core import security
from apan.core.context import Role
from apan.modules.users import service as users
from apan.modules.users.schemas import UserCreate

DEFAULT_PASSWORD = "correct-horse-battery"
CSRF_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Origin": "http://test"}


class UserCreateFactory(ModelFactory[UserCreate]):
    __check_model__ = False


@dataclass(frozen=True)
class SeededUser:
    id: UUID
    email: str
    password: str
    role: Role


_counter = 0


async def create_user(
    session: AsyncSession,
    *,
    role: Role = Role.TEACHER,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
    full_name: str = "Pessoa de Teste",
    active: bool = True,
    must_change_password: bool = False,
) -> SeededUser:
    global _counter
    _counter += 1
    email = email or f"{role}{_counter}@example.com"
    user = await users.create_account(
        session,
        email=email,
        full_name=full_name,
        role=role,
        password_hash=security.hash_password(password),
        must_change_password=must_change_password,
    )
    user.is_active = active
    await session.commit()
    return SeededUser(id=user.id, email=email, password=password, role=role)


async def login(api: AsyncClient, user: SeededUser) -> str:
    response = await api.post(
        "/api/v1/auth/login", json={"email": user.email, "password": user.password}
    )
    assert response.status_code == 200, response.text
    token: str = response.json()["accessToken"]
    return token


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
