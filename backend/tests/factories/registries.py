"""Creates registry data through the API, as an administrator."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from tests.factories.users import SeededUser, bearer, create_user, login

DEFAULT_GUARDIAN = {
    "fullName": "Maria Responsável",
    "phone": "(92) 99123-4567",
    "relationship": "mother",
}

Json = dict[str, Any]


def _ok(response: Any, status: int = 201) -> Json:
    assert response.status_code == status, response.text
    body: Json = response.json()
    return body


@dataclass
class Seed:
    api: AsyncClient
    session: AsyncSession
    admin: SeededUser
    headers: dict[str, str]
    _counter: int = field(default=0)

    def _next(self) -> int:
        self._counter += 1
        return self._counter

    async def year(
        self,
        name: str | None = None,
        starts_on: str = "2026-02-01",
        ends_on: str = "2026-12-15",
        is_current: bool = True,
    ) -> Json:
        body = {
            "name": name or f"Ano {self._next()}",
            "startsOn": starts_on,
            "endsOn": ends_on,
            "isCurrent": is_current,
        }
        return _ok(await self.api.post("/api/v1/school-years", json=body, headers=self.headers))

    async def subject(self, code: str | None = None, name: str = "Matemática") -> Json:
        body = {"code": code or f"SUB{self._next()}", "name": name}
        return _ok(await self.api.post("/api/v1/subjects", json=body, headers=self.headers))

    async def school_class(
        self,
        school_year_id: str,
        name: str | None = None,
        shift: str = "morning",
        capacity: int | None = None,
    ) -> Json:
        body: Json = {
            "schoolYearId": school_year_id,
            "name": name or f"Turma {self._next()}",
            "grade": "5",
            "shift": shift,
        }
        if capacity is not None:
            body["capacity"] = capacity
        return _ok(await self.api.post("/api/v1/classes", json=body, headers=self.headers))

    async def assign(self, class_id: str, pairs: list[tuple[str, UUID | str]]) -> Json:
        body = {"items": [{"subjectId": s, "teacherId": str(t)} for s, t in pairs]}
        return _ok(
            await self.api.put(
                f"/api/v1/classes/{class_id}/subject-teachers", json=body, headers=self.headers
            ),
            200,
        )

    async def student(
        self,
        class_id: str | None = None,
        *,
        full_name: str | None = None,
        birth_date: str = "2016-03-14",
        guardians: list[Json] | None = None,
        enrolled_on: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> Json:
        body: Json = {
            "fullName": full_name or f"Aluno {self._next()}",
            "birthDate": birth_date,
            "guardians": [DEFAULT_GUARDIAN] if guardians is None else guardians,
        }
        if class_id is not None:
            body["classId"] = class_id
        if enrolled_on is not None:
            body["enrolledOn"] = enrolled_on
        return _ok(
            await self.api.post("/api/v1/students", json=body, headers=headers or self.headers)
        )

    async def teacher_in_class(
        self, class_id: str, subject_id: str
    ) -> tuple[SeededUser, dict[str, str]]:
        teacher = await create_user(self.session, role=Role.TEACHER)
        await self.assign(class_id, [(subject_id, teacher.id)])
        return teacher, bearer(await login(self.api, teacher))


async def make_seed(api: AsyncClient, session: AsyncSession) -> Seed:
    admin = await create_user(session, role=Role.ADMIN)
    return Seed(api=api, session=session, admin=admin, headers=bearer(await login(api, admin)))
