"""Spreadsheet rendering. Headers are in pt-BR: the file is read by people, not code."""

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import xlsxwriter

from apan.core.constants import MIN_ATTENDANCE_RATE
from apan.modules.reports.domain import format_rate, safe_cell
from apan.modules.reports.schemas import AttendanceSummary, ClassReportRow, StudentReportRow

STATUS_LABELS = {"present": "Presente", "absent": "Ausente"}


@dataclass(frozen=True, slots=True)
class LessonLine:
    lesson_date: date
    class_name: str
    subject_name: str
    teacher_name: str
    present: int
    absent: int
    notes: str


@dataclass(frozen=True, slots=True)
class RecordLine:
    lesson_date: date
    class_name: str
    subject_name: str
    enrollment_number: str
    student_name: str
    status: str


@dataclass(frozen=True, slots=True)
class ReportData:
    summary: AttendanceSummary
    filters: Sequence[tuple[str, str]]
    students: Sequence[StudentReportRow]
    classes: Sequence[ClassReportRow]
    lessons: Sequence[LessonLine]
    records: Sequence[RecordLine]


STUDENT_HEADERS = [
    "Matrícula",
    "Aluno",
    "Turma",
    "Presenças",
    "Faltas",
    "Total de aulas",
    "Frequência (%)",
    "Situação",
]


def _situation(row: StudentReportRow) -> str:
    if row.attendance_rate is None:
        return "Sem aulas"
    return f"Abaixo de {MIN_ATTENDANCE_RATE:.0f}%" if row.at_risk else "Regular"


def to_csv(data: ReportData) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(STUDENT_HEADERS)
    for row in data.students:
        writer.writerow(
            [
                safe_cell(row.enrollment_number),
                safe_cell(row.full_name),
                safe_cell(row.class_name),
                row.present,
                row.absent,
                row.total,
                format_rate(row.attendance_rate),
                _situation(row),
            ]
        )
    # BOM so Excel opens the accents correctly.
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def to_xlsx(data: ReportData) -> bytes:
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True, "strings_to_formulas": False})
    bold = workbook.add_format({"bold": True})
    header = workbook.add_format({"bold": True, "bg_color": "#1A56DB", "font_color": "#FFFFFF"})
    date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})
    percent = workbook.add_format({"num_format": "0.0"})
    risk = workbook.add_format({"font_color": "#B91C1C", "bold": True})

    def table(name: str, headers: list[str], widths: list[int]) -> xlsxwriter.worksheet.Worksheet:
        sheet = workbook.add_worksheet(name)
        for col, (title, width) in enumerate(zip(headers, widths, strict=True)):
            sheet.write_string(0, col, title, header)
            sheet.set_column(col, col, width)
        sheet.freeze_panes(1, 0)
        return sheet

    # Summary
    summary = workbook.add_worksheet("Resumo")
    summary.set_column(0, 0, 32)
    summary.set_column(1, 1, 40)
    s = data.summary
    lines: list[tuple[str, object]] = [
        ("Relatório de frequência", ""),
        ("Período", f"{s.date_from:%d/%m/%Y} a {s.date_to:%d/%m/%Y}"),
        *[(label, value) for label, value in data.filters],
        ("Dias letivos no período", s.school_days if s.school_days is not None else "—"),
        ("Aulas registradas", s.lessons),
        ("Alunos", s.students),
        ("Presenças", s.present),
        ("Faltas", s.absent),
        ("Frequência geral (%)", s.attendance_rate if s.attendance_rate is not None else "—"),
        (f"Alunos abaixo de {MIN_ATTENDANCE_RATE:.0f}%", s.at_risk_students),
    ]
    for line_no, (label, value) in enumerate(lines):
        summary.write_string(line_no, 0, label, bold)
        if isinstance(value, int | float):
            summary.write_number(line_no, 1, value)
        else:
            summary.write_string(line_no, 1, str(value))

    # Per student
    sheet = table("Por aluno", STUDENT_HEADERS, [12, 36, 18, 11, 9, 14, 15, 18])
    for r, student in enumerate(data.students, start=1):
        sheet.write_string(r, 0, student.enrollment_number)
        sheet.write_string(r, 1, student.full_name)
        sheet.write_string(r, 2, student.class_name)
        sheet.write_number(r, 3, student.present)
        sheet.write_number(r, 4, student.absent)
        sheet.write_number(r, 5, student.total)
        if student.attendance_rate is not None:
            sheet.write_number(r, 6, student.attendance_rate, percent)
        sheet.write_string(r, 7, _situation(student), risk if student.at_risk else None)
    if data.students:
        sheet.autofilter(0, 0, len(data.students), len(STUDENT_HEADERS) - 1)

    # Per class
    sheet = table(
        "Por turma",
        ["Turma", "Aulas", "Alunos", "Presenças", "Faltas", "Frequência (%)", "Alunos em risco"],
        [18, 8, 8, 11, 9, 15, 15],
    )
    for r, group in enumerate(data.classes, start=1):
        sheet.write_string(r, 0, group.class_name)
        sheet.write_number(r, 1, group.lessons)
        sheet.write_number(r, 2, group.students)
        sheet.write_number(r, 3, group.present)
        sheet.write_number(r, 4, group.absent)
        if group.attendance_rate is not None:
            sheet.write_number(r, 5, group.attendance_rate, percent)
        sheet.write_number(r, 6, group.at_risk_students)

    # Lessons with the teacher's notes
    sheet = table(
        "Aulas",
        ["Data", "Turma", "Disciplina", "Professor(a)", "Presentes", "Ausentes", "Anotações"],
        [12, 18, 18, 26, 10, 10, 60],
    )
    for r, lesson in enumerate(data.lessons, start=1):
        sheet.write_datetime(r, 0, lesson.lesson_date, date_format)
        sheet.write_string(r, 1, lesson.class_name)
        sheet.write_string(r, 2, lesson.subject_name)
        sheet.write_string(r, 3, lesson.teacher_name)
        sheet.write_number(r, 4, lesson.present)
        sheet.write_number(r, 5, lesson.absent)
        sheet.write_string(r, 6, lesson.notes)

    # Every mark
    sheet = table(
        "Registros",
        ["Data", "Turma", "Disciplina", "Matrícula", "Aluno", "Situação"],
        [12, 18, 18, 12, 36, 10],
    )
    for r, record in enumerate(data.records, start=1):
        sheet.write_datetime(r, 0, record.lesson_date, date_format)
        sheet.write_string(r, 1, record.class_name)
        sheet.write_string(r, 2, record.subject_name)
        sheet.write_string(r, 3, record.enrollment_number)
        sheet.write_string(r, 4, record.student_name)
        sheet.write_string(r, 5, STATUS_LABELS.get(record.status, record.status))

    workbook.close()
    return buffer.getvalue()
