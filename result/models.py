from decimal import Decimal
from django.conf import settings
from django.db import models

from accounts.models import Student
from course.models import Course


# =======================
# CONSTANTS
# =======================
A_PLUS = "A+"
A = "A"
A_MINUS = "A-"
B_PLUS = "B+"
B = "B"
B_MINUS = "B-"
C_PLUS = "C+"
C = "C"
C_MINUS = "C-"
D = "D"
F = "F"
NG = "NG"

GRADE_CHOICES = (
    (A_PLUS, "A+"), (A, "A"), (A_MINUS, "A-"),
    (B_PLUS, "B+"), (B, "B"), (B_MINUS, "B-"),
    (C_PLUS, "C+"), (C, "C"), (C_MINUS, "C-"),
    (D, "D"), (F, "F"), (NG, "NG"),
)

PASS = "PASS"
FAIL = "FAIL"

COMMENT_CHOICES = (
    (PASS, "PASS"),
    (FAIL, "FAIL"),
)

GRADE_POINT_MAPPING = {
    A_PLUS: 4.0, A: 4.0, A_MINUS: 3.75,
    B_PLUS: 3.5, B: 3.0, B_MINUS: 2.75,
    C_PLUS: 2.5, C: 2.0, C_MINUS: 1.75,
    D: 1.0, F: 0.0, NG: 0.0,
}


# =======================
# TAKEN COURSE MODEL
# =======================
class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="taken_courses")

    assignment = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    mid_exam = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    quiz = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    attendance = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    # NEW MARKS
    in_mark = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    ex_mark = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    third_mark = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    final_exam = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    total = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True, editable=False)
    point = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False)
    comment = models.CharField(max_length=10, choices=COMMENT_CHOICES, blank=True, editable=False)

    def __str__(self):
        return f"{self.course.title} ({self.course.code})"

    # =======================
    # FINAL EXAM LOGIC (FIXED SAFE VERSION)
    # =======================
    def get_final_exam(self):
        marks = [
            float(self.in_mark or 0),
            float(self.ex_mark or 0)
        ]

        if self.third_mark not in [None, ""]:
            marks.append(float(self.third_mark))

        if len(marks) == 2:
            return Decimal(str(sum(marks) / 2))

        if len(marks) < 3:
            return Decimal(str(marks[0] if marks else 0))

        a, b, c = marks

        diffs = {
            "ab": abs(a - b),
            "ac": abs(a - c),
            "bc": abs(b - c),
        }

        if diffs["ab"] <= diffs["ac"] and diffs["ab"] <= diffs["bc"]:
            selected = [a, b]
        elif diffs["ac"] <= diffs["ab"] and diffs["ac"] <= diffs["bc"]:
            selected = [a, c]
        else:
            selected = [b, c]

        return Decimal(str(sum(selected) / 2))

    # =======================
    # TOTAL
    # =======================
    def get_total(self):
        return sum([
            Decimal(self.assignment),
            Decimal(self.mid_exam),
            Decimal(self.quiz),
            Decimal(self.attendance),
            Decimal(self.final_exam),
        ])

    # =======================
    # GRADE
    # =======================
    def get_grade(self):
        for boundary, grade in [
            (80, A_PLUS), (75, A), (70, A_MINUS),
            (65, B_PLUS), (60, B), (55, B_MINUS),
            (50, C_PLUS), (45, C), (40, C_MINUS),
            (35, D), (0, F),
        ]:
            if self.total >= boundary:
                return grade
        return NG

    def get_comment(self):
        return FAIL if self.grade in [F, NG] else PASS

    def get_point(self):
        return Decimal(self.course.credit) * Decimal(str(GRADE_POINT_MAPPING.get(self.grade, 0.0)))

    # =======================
    # SAVE (AUTO CALCULATION SAFE)
    # =======================
    def save(self, *args, **kwargs):
        self.final_exam = self.get_final_exam()
        self.total = self.get_total()
        self.grade = self.get_grade()
        self.point = self.get_point()
        self.comment = self.get_comment()
        super().save(*args, **kwargs)


# =======================
# RESULT MODEL
# =======================
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    gpa = models.FloatField(null=True, blank=True)
    cgpa = models.FloatField(null=True, blank=True)
    semester = models.CharField(max_length=100, choices=settings.SEMESTER_CHOICES)
    session = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=25, choices=settings.LEVEL_CHOICES, null=True)

    def __str__(self):
        return f"{self.student} - {self.semester} - {self.level}"