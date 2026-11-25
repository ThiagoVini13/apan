"""Attendance reports for a period, scoped to the classes the actor may reach."""

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.constants import MIN_ATTENDANCE_RATE
from apan.core.context import Actor, ClientInfo
from apan.core.errors import FieldError, ValidationError
from apan.core.pagination import ItemList
from apan.modules.audit import service as audit
from apan.modules.classes import service as classes
from apan.modules.reports import domain, export
from apan.modules.reports.schemas import (
    AttendanceSummary,
    ClassReportRow,
    ExportFormat,
    ReportParams,
    StudentReportRow,
)
from apan.modules.roll_calls import service as roll_calls
from apan.modules.roll_calls.domain import attendance_rate
from apan.modules.roll_calls.schemas import AttendanceQuery
from apan.modules.school_years import service as school_years
from apan.modules.students import service as students
from apan.modules.subjects import service as subjects
from apan.modules.users import service as users

MEDIA_TYPES = {
    ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ExportFormat.CSV: "text/csv; charset=utf-8",
}


@dataclass(frozen=True, slots=True)
class ExportFile:
    filename: str
    media_type: str
    content: bytes


async def _query(session: AsyncSession, actor: Actor, params: ReportParams) -> AttendanceQuery:
    problem = domain.range_problem(params.date_from, params.date_to)
    if problem:
        raise ValidationError(code=problem, field_errors=[FieldError("to", problem)])
    if params.class_id is not None:
        await classes.require_class(session, actor, params.class_id)
    scope = await classes.scope_for(session, actor)
    return AttendanceQuery(
        start=params.date_from,
        end=params.date_to,
        class_ids=scope.class_ids,
        class_id=params.class_id,
        subject_id=params.subject_id,
        student_id=params.student_id,
    )


async def _student_rows(session: AsyncSession, query: AttendanceQuery) -> list[StudentReportRow]:
    totals = await roll_calls.totals_by_student(session, query)
    people = await students.find_many(session, list({t.student_id for t in totals}))
    class_info = await classes.find_many(session, {t.class_id for t in totals})
    rows = []
    for t in totals:
        rate = attendance_rate(t.present, t.absent)
        person = people[t.student_id]
        rows.append(
            StudentReportRow(
                student_id=t.student_id,
                full_name=person.full_name,
                enrollment_number=person.enrollment_number,
                class_id=t.class_id,
                class_name=class_info[t.class_id].name,
                present=t.present,
                absent=t.absent,
                total=t.present + t.absent,
                attendance_rate=rate,
                at_risk=domain.is_at_risk(rate),
            )
        )
    rows.sort(key=lambda r: (r.class_name.casefold(), r.full_name.casefold()))
    return rows


def _class_rows(
    student_rows: list[StudentReportRow], lessons_per_class: dict[UUID, int], names: dict[UUID, str]
) -> list[ClassReportRow]:
    grouped: dict[UUID, list[StudentReportRow]] = defaultdict(list)
    for row in student_rows:
        grouped[row.class_id].append(row)
    result = []
    for class_id in set(grouped) | set(lessons_per_class):
        rows = grouped.get(class_id, [])
        present = sum(r.present for r in rows)
        absent = sum(r.absent for r in rows)
        result.append(
            ClassReportRow(
                class_id=class_id,
                class_name=names.get(class_id, ""),
                lessons=lessons_per_class.get(class_id, 0),
                students=len(rows),
                present=present,
                absent=absent,
                attendance_rate=attendance_rate(present, absent),
                at_risk_students=sum(1 for r in rows if r.at_risk),
            )
        )
    result.sort(key=lambda r: r.class_name.casefold())
    return result


async def _school_days(session: AsyncSession, params: ReportParams) -> int | None:
    if params.class_id is not None:
        school_class = await classes.find_class(session, params.class_id)
        year_id = school_class.school_year_id if school_class else None
    else:
        year = await school_years.current_year(session)
        year_id = year.id if year else None
    if year_id is None:
        return None
    return len(await school_years.school_days(session, year_id, params.date_from, params.date_to))


def _summary(
    params: ReportParams, school_days: int | None, rows: list[StudentReportRow], lessons: int
) -> AttendanceSummary:
    present = sum(r.present for r in rows)
    absent = sum(r.absent for r in rows)
    return AttendanceSummary(
        date_from=params.date_from,
        date_to=params.date_to,
        school_days=school_days,
        lessons=lessons,
        students=len({r.student_id for r in rows}),
        present=present,
        absent=absent,
        attendance_rate=attendance_rate(present, absent),
        at_risk_students=sum(1 for r in rows if r.at_risk),
        min_attendance_rate=MIN_ATTENDANCE_RATE,
    )


# --------------------------------------------------------------------------- endpoints


async def by_student(
    session: AsyncSession, actor: Actor, params: ReportParams
) -> ItemList[StudentReportRow]:
    query = await _query(session, actor, params)
    return ItemList[StudentReportRow].of(await _student_rows(session, query))


async def low_attendance(
    session: AsyncSession, actor: Actor, params: ReportParams
) -> ItemList[StudentReportRow]:
    query = await _query(session, actor, params)
    rows = [r for r in await _student_rows(session, query) if r.at_risk]
    rows.sort(key=lambda r: (r.attendance_rate or 0.0, r.full_name.casefold()))
    return ItemList[StudentReportRow].of(rows)


async def by_class(
    session: AsyncSession, actor: Actor, params: ReportParams
) -> ItemList[ClassReportRow]:
    query = await _query(session, actor, params)
    rows = await _student_rows(session, query)
    lessons = await roll_calls.lessons(session, query)
    per_class: dict[UUID, int] = defaultdict(int)
    for lesson in lessons:
        per_class[lesson.class_id] += 1
    names = {c.id: c.name for c in (await classes.find_many(session, per_class.keys())).values()}
    names.update({r.class_id: r.class_name for r in rows})
    return ItemList[ClassReportRow].of(_class_rows(rows, per_class, names))


async def summary(session: AsyncSession, actor: Actor, params: ReportParams) -> AttendanceSummary:
    query = await _query(session, actor, params)
    rows = await _student_rows(session, query)
    lessons = await roll_calls.lessons(session, query)
    return _summary(params, await _school_days(session, params), rows, len(lessons))


async def export_report(
    session: AsyncSession,
    actor: Actor,
    params: ReportParams,
    fmt: ExportFormat,
    client: ClientInfo,
) -> ExportFile:
    query = await _query(session, actor, params)
    student_rows = await _student_rows(session, query)
    lessons = await roll_calls.lessons(session, query)
    records = await roll_calls.records(session, query) if fmt is ExportFormat.XLSX else []

    class_ids = {lesson.class_id for lesson in lessons} | {r.class_id for r in student_rows}
    class_names = {c.id: c.name for c in (await classes.find_many(session, class_ids)).values()}
    subject_names = {
        s.id: s.name
        for s in (
            await subjects.find_many(session, {lesson.subject_id for lesson in lessons})
        ).values()
    }
    teacher_names = await users.full_names(session, {lesson.taken_by_id for lesson in lessons})
    people = await students.find_many(session, list({r.student_id for r in records}))

    per_class: dict[UUID, int] = defaultdict(int)
    for lesson in lessons:
        per_class[lesson.class_id] += 1

    filters: list[tuple[str, str]] = []
    if params.class_id:
        filters.append(("Turma", class_names.get(params.class_id, "")))
    if params.subject_id:
        found = await subjects.find_many(session, [params.subject_id])
        filters.append(("Disciplina", found[params.subject_id].name if found else ""))
    if params.student_id:
        found_students = await students.find_many(session, [params.student_id])
        if params.student_id in found_students:
            filters.append(("Aluno", found_students[params.student_id].full_name))

    data = export.ReportData(
        summary=_summary(params, await _school_days(session, params), student_rows, len(lessons)),
        filters=filters,
        students=student_rows,
        classes=_class_rows(student_rows, per_class, class_names),
        lessons=[
            export.LessonLine(
                lesson_date=lesson.lesson_date,
                class_name=class_names.get(lesson.class_id, ""),
                subject_name=subject_names.get(lesson.subject_id, ""),
                teacher_name=teacher_names.get(lesson.taken_by_id, ""),
                present=lesson.present,
                absent=lesson.absent,
                notes=lesson.notes or "",
            )
            for lesson in lessons
        ],
        records=[
            export.RecordLine(
                lesson_date=record.lesson_date,
                class_name=class_names.get(record.class_id, ""),
                subject_name=subject_names.get(record.subject_id, ""),
                enrollment_number=people[record.student_id].enrollment_number,
                student_name=people[record.student_id].full_name,
                status=record.status.value,
            )
            for record in records
            if record.student_id in people
        ],
    )
    content = export.to_xlsx(data) if fmt is ExportFormat.XLSX else export.to_csv(data)

    audit.record(
        session,
        "reports.exported",
        client=client,
        actor_id=actor.user_id,
        entity_type="report",
        details={
            "format": fmt.value,
            "from": params.date_from.isoformat(),
            "to": params.date_to.isoformat(),
            "classId": str(params.class_id) if params.class_id else None,
            "rows": len(student_rows),
        },
    )
    await session.commit()
    filename = f"frequencia_{params.date_from.isoformat()}_{params.date_to.isoformat()}.{fmt.value}"
    return ExportFile(filename=filename, media_type=MEDIA_TYPES[fmt], content=content)
