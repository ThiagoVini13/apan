from httpx import AsyncClient

from tests.factories.registries import Seed

DASHBOARD = "/api/v1/dashboard/today"
TODAY = "2026-11-24"


async def test_dashboard_without_school_year(api: AsyncClient, seed: Seed) -> None:
    response = await api.get(DASHBOARD, headers=seed.headers)

    assert response.status_code == 200
    assert response.json()["schoolYearId"] is None
    assert response.json()["pendingRollCalls"] == []


async def test_teacher_dashboard_shows_own_pending_roll_calls(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    mine = await seed.school_class(year["id"], name="5º Ano A")
    other = await seed.school_class(year["id"], name="6º Ano B")
    math = await seed.subject(name="Matemática")
    portuguese = await seed.subject(name="Português")
    teacher, headers = await seed.teacher_in_class(mine["id"], math["id"])
    await seed.assign(mine["id"], [(math["id"], teacher.id), (portuguese["id"], teacher.id)])
    await seed.teacher_in_class(other["id"], math["id"])
    ana = await seed.student(mine["id"], full_name="Ana", enrolled_on="2026-03-02")
    await seed.student(other["id"], enrolled_on="2026-03-02")

    before = (await api.get(DASHBOARD, headers=headers)).json()
    await api.put(
        "/api/v1/roll-calls",
        json={
            "classId": mine["id"],
            "subjectId": math["id"],
            "lessonDate": TODAY,
            "attendances": [{"studentId": ana["id"], "status": "absent"}],
        },
        headers=headers,
    )
    after = (await api.get(DASHBOARD, headers=headers)).json()
    admin = (await api.get(DASHBOARD, headers=seed.headers)).json()

    assert before["isSchoolDay"] is True
    assert (before["totalClasses"], before["totalStudents"]) == (1, 1)
    assert before["rollCallsExpected"] == 2
    assert [p["subjectName"] for p in before["pendingRollCalls"]] == ["Matemática", "Português"]
    assert [p["subjectName"] for p in after["pendingRollCalls"]] == ["Português"]
    assert after["rollCallsDone"] == 1
    assert after["presenceRateToday"] == 0.0
    assert [s["fullName"] for s in after["lowAttendanceStudents"]] == ["Ana"]
    assert (admin["totalClasses"], admin["totalStudents"], admin["rollCallsExpected"]) == (2, 2, 3)
