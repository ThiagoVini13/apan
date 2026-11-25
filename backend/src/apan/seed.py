"""Synthetic demo data for development (never real people: LGPD)."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core import clock, security
from apan.core.config import get_settings
from apan.core.context import Actor, ClientInfo, Role
from apan.core.errors import ConflictError
from apan.core.pagination import PageParams
from apan.modules.classes import service as classes
from apan.modules.classes.schemas import (
    SchoolClassCreate,
    Shift,
    SubjectTeacherAssignment,
    SubjectTeachersReplace,
)
from apan.modules.roll_calls import service as roll_calls
from apan.modules.roll_calls.schemas import AttendanceIn, AttendanceStatus, RollCallUpsert
from apan.modules.school_years import service as school_years
from apan.modules.school_years.schemas import (
    CalendarDayCreate,
    CalendarDayKind,
    SchoolYearCreate,
    TermCreate,
)
from apan.modules.students import service as students
from apan.modules.students.schemas import GuardianCreate, Relationship, StudentCreate
from apan.modules.subjects import service as subjects
from apan.modules.subjects.schemas import SubjectCreate
from apan.modules.users import service as users
from apan.modules.users.schemas import UserFilters

CLIENT = ClientInfo(ip=None, user_agent="apan-cli seed-demo")
TEACHER_EMAIL = "professora.demo@example.com"

CLASSES = [
    (
        "5º Ano A",
        "5",
        Shift.MORNING,
        ["Alice Souza", "Bruno Martins", "Carla Ferreira", "Daniel Oliveira", "Eduarda Lima"],
        2016,
    ),
    (
        "6º Ano B",
        "6",
        Shift.AFTERNOON,
        ["Felipe Costa", "Gabriela Nunes", "Henrique Alves", "Isabela Rocha", "João Pereira"],
        2015,
    ),
    (
        "7º Ano C",
        "7",
        Shift.MORNING,
        ["Karen Ramos", "Lucas Barbosa", "Mariana Carvalho", "Nicolas Gomes", "Olivia Santos"],
        2014,
    ),
]


HISTORY_DAYS = 14
CHRONIC_ABSENTEE = 3


@dataclass(frozen=True)
class SeedResult:
    school_year: str
    teacher_email: str
    students: int
    roll_calls: int


async def _admin_actor(session: AsyncSession) -> Actor:
    page = await users.list_users(
        session, UserFilters(role=Role.ADMIN, is_active=True), PageParams(page=1, page_size=1)
    )
    if not page.items:
        raise ConflictError("Create an administrator first (apan create-admin).", code="no_admin")
    return Actor(user_id=page.items[0].id, role=Role.ADMIN, session_id=uuid4())


async def seed_demo(session: AsyncSession, teacher_password: str) -> SeedResult:
    actor = await _admin_actor(session)
    year_number = clock.local_today().year

    year = await school_years.create_year(
        session,
        actor,
        SchoolYearCreate(
            name=f"{year_number} (demo)",
            starts_on=date(year_number, 2, 2),
            ends_on=date(year_number, 12, 15),
            is_current=True,
        ),
        CLIENT,
    )
    for name, start, end in [
        ("1º bimestre", (2, 2), (4, 17)),
        ("2º bimestre", (4, 20), (7, 3)),
        ("3º bimestre", (7, 27), (10, 2)),
        ("4º bimestre", (10, 5), (12, 15)),
    ]:
        await school_years.create_term(
            session,
            actor,
            year.id,
            TermCreate(
                name=name, starts_on=date(year_number, *start), ends_on=date(year_number, *end)
            ),
            CLIENT,
        )
    for day, description in [
        ((4, 21), "Tiradentes"),
        ((9, 7), "Independência"),
        ((11, 20), "Consciência Negra"),
    ]:
        await school_years.create_calendar_day(
            session,
            actor,
            year.id,
            CalendarDayCreate(
                day=date(year_number, *day), kind=CalendarDayKind.HOLIDAY, description=description
            ),
            CLIENT,
        )

    subject_ids = {}
    for code, name in [("MAT", "Matemática"), ("POR", "Português"), ("CIE", "Ciências")]:
        subject_ids[code] = (
            await subjects.create_subject(
                session, actor, SubjectCreate(code=code, name=name), CLIENT
            )
        ).id

    teacher = await users.find_by_email(session, TEACHER_EMAIL)
    if teacher is None:
        teacher = await users.create_account(
            session,
            email=TEACHER_EMAIL,
            full_name="Professora Demonstração",
            role=Role.TEACHER,
            password_hash=security.hash_password(teacher_password),
            must_change_password=False,
        )
        await session.commit()

    count = 0
    lessons = 0
    for index, (name, grade, shift, names, birth_year) in enumerate(CLASSES):
        school_class = await classes.create_class(
            session,
            actor,
            SchoolClassCreate(
                school_year_id=year.id,
                name=name,
                grade=grade,
                shift=shift,
                room=f"Sala {index + 1}",
                capacity=30,
            ),
            CLIENT,
        )
        # The demo teacher teaches the first two classes; the third stays outside her scope.
        if index < 2:
            await classes.replace_subject_teachers(
                session,
                actor,
                school_class.id,
                SubjectTeachersReplace(
                    items=[
                        SubjectTeacherAssignment(
                            subject_id=subject_ids["MAT"], teacher_id=teacher.id
                        ),
                        SubjectTeacherAssignment(
                            subject_id=subject_ids["POR"], teacher_id=teacher.id
                        ),
                    ]
                ),
                CLIENT,
            )
        roster: list[UUID] = []
        for offset, full_name in enumerate(names):
            surname = full_name.split()[-1]
            created = await students.create_student(
                session,
                actor,
                StudentCreate(
                    full_name=full_name,
                    birth_date=date(birth_year, 1 + offset * 2, 10 + offset),
                    class_id=school_class.id,
                    enrolled_on=year.starts_on,
                    guardians=[
                        GuardianCreate(
                            full_name=f"Responsável {surname}",
                            phone=f"(92) 99{offset:03d}-{index:04d}",
                            relationship=Relationship.MOTHER,
                        )
                    ],
                ),
                CLIENT,
            )
            roster.append(created.id)
            count += 1
        lesson_subjects = (
            [subject_ids["MAT"], subject_ids["POR"]] if index < 2 else [subject_ids["MAT"]]
        )
        lessons += await _roll_call_history(
            session, actor, year.id, school_class.id, lesson_subjects, roster
        )

    return SeedResult(
        school_year=year.name, teacher_email=TEACHER_EMAIL, students=count, roll_calls=lessons
    )


async def _roll_call_history(
    session: AsyncSession,
    actor: Actor,
    year_id: UUID,
    class_id: UUID,
    subject_ids: list[UUID],
    roster: list[UUID],
) -> int:
    """Two weeks of past lessons (today stays pending for the dashboard)."""
    today = clock.local_today()
    days = await school_years.school_days(
        session, year_id, today - timedelta(days=HISTORY_DAYS), today - timedelta(days=1)
    )
    settings = get_settings()
    taken = 0
    for day in days:
        for subject_id in subject_ids:
            marks = [
                AttendanceIn(student_id=student_id, status=_demo_status(position, day))
                for position, student_id in enumerate(roster)
            ]
            await roll_calls.upsert(
                session,
                settings,
                actor,
                RollCallUpsert(
                    class_id=class_id,
                    subject_id=subject_id,
                    lesson_date=day,
                    notes="Aula de demonstração.",
                    attendances=marks,
                ),
                CLIENT,
            )
            taken += 1
    return taken


def _demo_status(position: int, day: date) -> AttendanceStatus:
    """Deterministic absences; the fourth student of each class is often absent."""
    if position == CHRONIC_ABSENTEE:
        absent = day.toordinal() % 3 != 0
    else:
        absent = (day.toordinal() + position * 3) % 7 == 0
    return AttendanceStatus.ABSENT if absent else AttendanceStatus.PRESENT
