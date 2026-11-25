"""Today's snapshot for the home screen, within the actor's scope."""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core import clock
from apan.core.context import Actor
from apan.modules.classes import service as classes
from apan.modules.dashboard.schemas import AtRiskStudent, DashboardToday, PendingRollCall
from apan.modules.enrollments import service as enrollments
from apan.modules.reports.domain import is_at_risk
from apan.modules.roll_calls import service as roll_calls
from apan.modules.roll_calls.domain import attendance_rate
from apan.modules.roll_calls.schemas import AttendanceQuery
from apan.modules.school_years import service as school_years
from apan.modules.students import service as students
from apan.modules.subjects import service as subjects
from apan.modules.users import service as users

LOW_ATTENDANCE_LIMIT = 10
RECENT_DAYS = 30


def _rate(totals: list[tuple[int, int]]) -> float | None:
    return attendance_rate(sum(p for p, _ in totals), sum(a for _, a in totals))


async def today(session: AsyncSession, actor: Actor) -> DashboardToday:
    day = clock.local_today()
    year = await school_years.current_year(session)
    empty = DashboardToday(
        date=day,
        school_year_id=None,
        school_year_name=None,
        is_school_day=False,
        total_classes=0,
        total_students=0,
        roll_calls_expected=0,
        roll_calls_done=0,
        presence_rate_today=None,
        presence_rate_last_30_days=None,
        pending_roll_calls=[],
        low_attendance_students=[],
    )
    if year is None:
        return empty

    class_list = await classes.active_classes_in_year(session, actor, year.id)
    class_ids = frozenset(c.id for c in class_list)
    class_names = {c.id: c.name for c in class_list}
    is_school_day = day in await school_years.school_days(session, year.id, day, day)

    assignments = await classes.lesson_assignments(session, actor, class_ids)
    done = await roll_calls.taken_on(session, day, class_ids)
    pending = [a for a in assignments if (a[0], a[1]) not in done] if is_school_day else []
    subject_names = {
        s.id: s.name for s in (await subjects.find_many(session, {a[1] for a in pending})).values()
    }
    teacher_names = await users.full_names(session, {a[2] for a in pending})

    start = max(year.starts_on, day - timedelta(days=RECENT_DAYS - 1))
    today_totals = await roll_calls.totals_by_student(
        session, AttendanceQuery(start=day, end=day, class_ids=class_ids)
    )
    recent_totals = await roll_calls.totals_by_student(
        session, AttendanceQuery(start=start, end=day, class_ids=class_ids)
    )
    year_totals = await roll_calls.totals_by_student(
        session, AttendanceQuery(start=year.starts_on, end=day, class_ids=class_ids)
    )

    at_risk = []
    for totals in year_totals:
        rate = attendance_rate(totals.present, totals.absent)
        if rate is not None and is_at_risk(rate):
            at_risk.append((rate, totals))
    at_risk.sort(key=lambda item: item[0])
    at_risk = at_risk[:LOW_ATTENDANCE_LIMIT]
    people = await students.find_many(session, [t.student_id for _, t in at_risk])

    return empty.model_copy(
        update={
            "school_year_id": year.id,
            "school_year_name": year.name,
            "is_school_day": is_school_day,
            "total_classes": len(class_list),
            "total_students": await enrollments.count_active(session, class_ids)
            if class_ids
            else 0,
            "roll_calls_expected": len(assignments) if is_school_day else 0,
            "roll_calls_done": len(done),
            "presence_rate_today": _rate([(t.present, t.absent) for t in today_totals]),
            "presence_rate_last_30_days": _rate([(t.present, t.absent) for t in recent_totals]),
            "pending_roll_calls": sorted(
                (
                    PendingRollCall(
                        class_id=class_id,
                        class_name=class_names[class_id],
                        subject_id=subject_id,
                        subject_name=subject_names.get(subject_id, ""),
                        teacher_id=teacher_id,
                        teacher_name=teacher_names.get(teacher_id, ""),
                    )
                    for class_id, subject_id, teacher_id in pending
                ),
                key=lambda p: (p.class_name.casefold(), p.subject_name.casefold()),
            ),
            "low_attendance_students": [
                AtRiskStudent(
                    student_id=t.student_id,
                    full_name=people[t.student_id].full_name,
                    class_id=t.class_id,
                    class_name=class_names.get(t.class_id, ""),
                    attendance_rate=rate,
                )
                for rate, t in at_risk
                if t.student_id in people
            ],
        }
    )
