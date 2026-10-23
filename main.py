"""
EduTrack — Student Management System
A syllabus-oriented Tkinter desktop application using SQLite.

Syllabus concepts demonstrated:
- Variables, built-in types, operators, strings, slicing and formatting
- Lists, tuples, dictionaries, sets and list comprehensions
- if/elif/else, for/while, break/continue/pass
- math and random modules
- Functions, arguments, return values, classes and objects
- Constructors, encapsulation, inheritance and polymorphism
- Text, CSV and JSON file handling
- Exceptions, custom exceptions, modules and packages
- Linear search and binary search
"""

from __future__ import annotations

import csv
import json
import math
import random
import sqlite3
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable

APP_NAME = "EduTrack — Student Management System"
APP_VERSION = "1.0.0"
SUBJECTS = ("Python", "Mathematics", "Electronics", "English", "Computer Fundamentals")
MAX_MARKS_PER_SUBJECT = 100
PASS_MARK = 35
DB_PATH = Path(__file__).resolve().parent / "data" / "edutrack.db"


class ValidationError(ValueError):
    """Raised when student input does not pass validation."""


@dataclass
class Person:
    """Base class demonstrates inheritance and data abstraction."""
    name: str
    email: str = ""
    phone: str = ""

    def display_name(self) -> str:
        return self.name.strip().title()


class Student(Person):
    """Student model. Private-style attributes demonstrate encapsulation."""
    def __init__(
        self,
        student_id: Optional[int],
        name: str,
        email: str,
        phone: str,
        course: str,
        semester: int,
        marks: Iterable[int],
        registration_date: str = "",
    ):
        super().__init__(name, email, phone)
        self.student_id = student_id
        self.course = course.strip()
        self.semester = int(semester)
        self.__marks = tuple(int(mark) for mark in marks)
        self.registration_date = registration_date or datetime.now().strftime("%Y-%m-%d")

    @property
    def marks(self) -> tuple[int, ...]:
        return self.__marks

    @property
    def total(self) -> int:
        return sum(self.__marks)

    @property
    def percentage(self) -> float:
        maximum = len(self.__marks) * MAX_MARKS_PER_SUBJECT
        return (self.total / maximum * 100) if maximum else 0.0

    @property
    def grade(self) -> str:
        return calculate_grade(self.percentage)

    @property
    def result(self) -> str:
        return "PASS" if all(mark >= PASS_MARK for mark in self.__marks) else "FAIL"

    def as_dict(self) -> dict:
        record = {
            "student_id": self.student_id,
            "name": self.display_name(),
            "email": self.email.strip(),
            "phone": self.phone.strip(),
            "course": self.course,
            "semester": self.semester,
            "registration_date": self.registration_date,
            "total": self.total,
            "percentage": round(self.percentage, 2),
            "grade": self.grade,
            "result": self.result,
        }
        record.update({f"mark_{i+1}": mark for i, mark in enumerate(self.__marks)})
        return record


class MeritStudent(Student):
    """Example subclass; polymorphic summary() differs from Student."""
    def summary(self) -> str:
        return f"{self.display_name()} — Merit profile ({self.percentage:.1f}%)"


class StudentRecordService:
    """Database and business logic kept separate from the UI."""
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self):
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    course TEXT NOT NULL,
                    semester INTEGER NOT NULL,
                    mark_1 INTEGER NOT NULL,
                    mark_2 INTEGER NOT NULL,
                    mark_3 INTEGER NOT NULL,
                    mark_4 INTEGER NOT NULL,
                    mark_5 INTEGER NOT NULL,
                    registration_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    @staticmethod
    def validate_student(name, email, phone, course, semester, marks):
        name = name.strip()
        course = course.strip()
        email = email.strip()
        phone = phone.strip()
        if len(name) < 2:
            raise ValidationError("Enter a name containing at least 2 characters.")
        if not course:
            raise ValidationError("Course/department is required.")
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            raise ValidationError("Enter a valid email address or leave it blank.")
        if phone and not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("Phone may contain digits, spaces, + or - only.")
        try:
            semester = int(semester)
        except (TypeError, ValueError):
            raise ValidationError("Semester must be a whole number.")
        if not 1 <= semester <= 12:
            raise ValidationError("Semester must be between 1 and 12.")
        if len(marks) != len(SUBJECTS):
            raise ValidationError("Enter marks for all five subjects.")
        clean_marks = []
        for subject, raw in zip(SUBJECTS, marks):
            try:
                mark = int(raw)
            except (TypeError, ValueError):
                raise ValidationError(f"{subject}: enter a whole-number mark.")
            if not 0 <= mark <= MAX_MARKS_PER_SUBJECT:
                raise ValidationError(f"{subject}: marks must be between 0 and 100.")
            clean_marks.append(mark)
        return name, email, phone, course, semester, clean_marks

    def add(self, name, email, phone, course, semester, marks):
        name, email, phone, course, semester, marks = self.validate_student(
            name, email, phone, course, semester, marks
        )
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as con:
            cur = con.execute("""
                INSERT INTO students
                (name,email,phone,course,semester,mark_1,mark_2,mark_3,mark_4,mark_5,
                 registration_date,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (name, email, phone, course, semester, *marks,
                  datetime.now().strftime("%Y-%m-%d"), now, now))
            return cur.lastrowid

    def update(self, student_id, name, email, phone, course, semester, marks):
        name, email, phone, course, semester, marks = self.validate_student(
            name, email, phone, course, semester, marks
        )
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as con:
            cur = con.execute("""
                UPDATE students SET name=?,email=?,phone=?,course=?,semester=?,
                mark_1=?,mark_2=?,mark_3=?,mark_4=?,mark_5=?,updated_at=?
                WHERE student_id=?
            """, (name, email, phone, course, semester, *marks, now, int(student_id)))
            if cur.rowcount == 0:
                raise ValidationError("That student no longer exists.")

    def delete(self, student_id):
        with self._connect() as con:
            cur = con.execute("DELETE FROM students WHERE student_id=?", (int(student_id),))
            if cur.rowcount == 0:
                raise ValidationError("Student not found.")

    def all(self) -> list[Student]:
        with self._connect() as con:
            rows = con.execute("SELECT * FROM students ORDER BY student_id").fetchall()
        return [self._row_to_student(row) for row in rows]

    def get(self, student_id) -> Optional[Student]:
        with self._connect() as con:
            row = con.execute("SELECT * FROM students WHERE student_id=?", (int(student_id),)).fetchone()
        return self._row_to_student(row) if row else None

    @staticmethod
    def _row_to_student(row) -> Student:
        return Student(
            row["student_id"], row["name"], row["email"], row["phone"], row["course"],
            row["semester"], [row[f"mark_{i}"] for i in range(1, 6)],
            row["registration_date"]
        )

    def import_records(self, rows: list[dict]) -> tuple[int, list[str]]:
        imported, errors = 0, []
        # Each row is handled independently, so one invalid row does not stop the import.
        for line_number, row in enumerate(rows, start=2):
            try:
                marks = [row.get(f"mark_{i}", row.get(SUBJECTS[i-1], "")) for i in range(1, 6)]
                self.add(row.get("name", ""), row.get("email", ""), row.get("phone", ""),
                         row.get("course", "General"), row.get("semester", 1), marks)
                imported += 1
            except (ValidationError, sqlite3.Error) as exc:
                errors.append(f"Row {line_number}: {exc}")
        return imported, errors


def calculate_grade(percentage: float) -> str:
    """if/elif/else grading logic."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"


def linear_search(students: list[Student], query: str) -> list[Student]:
    """O(n) search by ID or partial name."""
    query = query.strip().casefold()
    found = []
    for student in students:
        if query and (query in student.display_name().casefold()
                      or query == str(student.student_id)):
            found.append(student)
    return found


def binary_search_by_id(students: list[Student], student_id: int) -> Optional[Student]:
    """O(log n) search; sorts by ID first, as binary search requires sorted data."""
    ordered = sorted(students, key=lambda student: student.student_id or 0)
    low, high = 0, len(ordered) - 1
    while low <= high:
        middle = (low + high) // 2
        current = ordered[middle].student_id or 0
        if current == student_id:
            return ordered[middle]
        if current < student_id:
            low = middle + 1
        else:
            high = middle - 1
    return None


def class_statistics(students: list[Student]) -> dict:
    percentages = [student.percentage for student in students]
    passed = [student for student in students if student.result == "PASS"]
    return {
        "count": len(students),
        "average": (sum(percentages) / len(percentages)) if percentages else 0.0,
        "passed": len(passed),
        "failed": len(students) - len(passed),
        "highest": max(percentages) if percentages else 0.0,
        "lowest": min(percentages) if percentages else 0.0,
    }


class EduTrackApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x760")
        self.minsize(960, 620)
        self.configure(bg="#f3f6fb")
        self.service = StudentRecordService()
        self.selected_id: Optional[int] = None
        self._configure_styles()
        self._build_ui()
        self.refresh_table()
        self.refresh_dashboard()
        self._update_clock()

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10),
                        background="white", fieldbackground="white", foreground="#1f2937")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#e8eef8", foreground="#1e3a5f", padding=8)
        style.map("Treeview", background=[("selected", "#dbeafe")],
                  foreground=[("selected", "#111827")])
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Primary.TButton", background="#1d4ed8", foreground="white")
        style.map("Primary.TButton", background=[("active", "#1e40af")])
        style.configure("TLabel", font=("Segoe UI", 10), background="#f3f6fb",
                        foreground="#1f2937")
        style.configure("Heading.TLabel", font=("Segoe UI", 19, "bold"),
                        foreground="#17365d", background="#f3f6fb")
        style.configure("Subheading.TLabel", font=("Segoe UI", 11, "bold"),
                        foreground="#17365d", background="#f3f6fb")

    def _build_ui(self):
        header = tk.Frame(self, bg="#17365d", height=76)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="EduTrack", bg="#17365d", fg="white",
                 font=("Segoe UI", 21, "bold")).pack(side="left", padx=24)
        tk.Label(header, text="STUDENT MANAGEMENT SYSTEM", bg="#17365d", fg="#cfe0ff",
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=6, pady=(12, 0))
        self.clock_label = tk.Label(header, text="", bg="#17365d", fg="white",
                                    font=("Segoe UI", 10))
        self.clock_label.pack(side="right", padx=22)

        body = tk.Frame(self, bg="#f3f6fb")
        body.pack(fill="both", expand=True)
        sidebar = tk.Frame(body, bg="#102846", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="NAVIGATION", bg="#102846", fg="#9bb8dc",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(24, 10))
        for label, command in [
            ("Dashboard", self.show_dashboard),
            ("Students", self.show_students),
            ("Add Student", self.clear_form),
            ("Reports / Export", self.export_csv),
            ("Syllabus Guide", self.show_syllabus),
        ]:
            btn = tk.Button(sidebar, text=label, command=command, anchor="w",
                            bg="#102846", fg="white", activebackground="#24466d",
                            activeforeground="white", relief="flat", bd=0,
                            padx=18, pady=12, font=("Segoe UI", 10), cursor="hand2")
            btn.pack(fill="x")
        tk.Label(sidebar, text="Python syllabus project\nVersion " + APP_VERSION,
                 bg="#102846", fg="#9bb8dc", justify="left",
                 font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=16, pady=18)

        self.content = tk.Frame(body, bg="#f3f6fb")
        self.content.pack(side="left", fill="both", expand=True, padx=22, pady=20)
        self._build_dashboard()
        self._build_students_page()
        self._build_form()
        self._build_syllabus_page()
        self.show_dashboard()

    def _build_dashboard(self):
        self.dashboard_frame = tk.Frame(self.content, bg="#f3f6fb")
        ttk.Label(self.dashboard_frame, text="Dashboard", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self.dashboard_frame, text="A quick overview of your student records.").pack(anchor="w", pady=(4, 18))
        cards = tk.Frame(self.dashboard_frame, bg="#f3f6fb")
        cards.pack(fill="x")
        self.stat_vars = {}
        for key, title in [("count", "Total Students"), ("average", "Class Average"),
                           ("passed", "Passed"), ("failed", "Failed")]:
            card = tk.Frame(cards, bg="white", highlightbackground="#e1e8f0", highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=2)
            tk.Label(card, text=title, bg="white", fg="#64748b",
                     font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(14, 4))
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var, bg="white", fg="#17365d",
                     font=("Segoe UI", 23, "bold")).pack(anchor="w", padx=16, pady=(0, 14))
        ttk.Label(self.dashboard_frame, text="Recent registrations", style="Subheading.TLabel").pack(anchor="w", pady=(24, 10))
        self.recent_tree = ttk.Treeview(self.dashboard_frame, columns=("id", "name", "course", "percent", "result"),
                                        show="headings", height=8)
        for col, title, width in [("id", "ID", 70), ("name", "Student Name", 220),
                                  ("course", "Course", 160), ("percent", "Percentage", 120),
                                  ("result", "Result", 100)]:
            self.recent_tree.heading(col, text=title)
            self.recent_tree.column(col, width=width, anchor="w")
        self.recent_tree.pack(fill="both", expand=True)
        ttk.Button(self.dashboard_frame, text="View all students", command=self.show_students).pack(anchor="e", pady=12)

    def _build_students_page(self):
        self.students_frame = tk.Frame(self.content, bg="#f3f6fb")
        ttk.Label(self.students_frame, text="Student Records", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self.students_frame, text="Search, inspect, update, export, or remove records.").pack(anchor="w", pady=(4, 14))
        controls = tk.Frame(self.students_frame, bg="#f3f6fb")
        controls.pack(fill="x", pady=(0, 12))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(controls, textvariable=self.search_var, width=32)
        search_entry.pack(side="left", padx=(0, 8), ipady=5)
        search_entry.insert(0, "")
        ttk.Button(controls, text="Search (linear)", command=self.search_students).pack(side="left", padx=3)
        ttk.Button(controls, text="Find by ID (binary)", command=self.binary_search_dialog).pack(side="left", padx=3)
        ttk.Button(controls, text="Clear", command=self.clear_search).pack(side="left", padx=3)
        ttk.Button(controls, text="Export CSV", command=self.export_csv).pack(side="right", padx=3)
        ttk.Button(controls, text="Import CSV", command=self.import_csv).pack(side="right", padx=3)

        cols = ("id", "name", "course", "semester", "total", "percentage", "grade", "result")
        self.tree = ttk.Treeview(self.students_frame, columns=cols, show="headings", selectmode="browse")
        headings = [("id", "ID", 55), ("name", "Name", 175), ("course", "Course", 125),
                    ("semester", "Sem", 55), ("total", "Total / 500", 95),
                    ("percentage", "Percentage", 95), ("grade", "Grade", 70), ("result", "Result", 75)]
        for col, title, width in headings:
            self.tree.heading(col, text=title, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(self.students_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        actions = tk.Frame(self.students_frame, bg="#f3f6fb")
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="New Student", command=self.clear_form, style="Primary.TButton").pack(side="left")
        ttk.Button(actions, text="Edit Selected", command=self.load_selected_to_form).pack(side="left", padx=7)
        ttk.Button(actions, text="Delete Selected", command=self.delete_selected).pack(side="left")
        ttk.Button(actions, text="Refresh", command=self.refresh_all).pack(side="right")

    def _build_form(self):
        self.form_frame = tk.Frame(self.content, bg="#f3f6fb")
        ttk.Label(self.form_frame, text="Student Registration", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self.form_frame, text="Enter student details and marks for all five subjects.").pack(anchor="w", pady=(4, 16))
        panel = tk.Frame(self.form_frame, bg="white", highlightbackground="#e1e8f0", highlightthickness=1)
        panel.pack(fill="both", expand=True)
        fields = tk.Frame(panel, bg="white")
        fields.pack(fill="x", padx=22, pady=20)
        self.form_vars = {key: tk.StringVar() for key in ["name", "email", "phone", "course", "semester"]}
        field_specs = [("name", "Full name *"), ("email", "Email"), ("phone", "Phone"),
                       ("course", "Course / department *"), ("semester", "Semester (1–12) *")]
        for i, (key, label) in enumerate(field_specs):
            row, col = divmod(i, 2)
            holder = tk.Frame(fields, bg="white")
            holder.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else 18, 18), pady=8)
            tk.Label(holder, text=label, bg="white", fg="#334155",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
            ttk.Entry(holder, textvariable=self.form_vars[key]).pack(fill="x", ipady=5)
            fields.grid_columnconfigure(col, weight=1)
        tk.Label(panel, text="Subject marks (0–100 each)", bg="white", fg="#17365d",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=22, pady=(4, 0))
        marks_panel = tk.Frame(panel, bg="white")
        marks_panel.pack(fill="x", padx=22, pady=10)
        self.mark_vars = []
        for i, subject in enumerate(SUBJECTS):
            holder = tk.Frame(marks_panel, bg="white")
            holder.grid(row=0, column=i, sticky="ew", padx=(0, 10))
            tk.Label(holder, text=subject, bg="white", fg="#475569",
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
            var = tk.StringVar()
            self.mark_vars.append(var)
            ttk.Entry(holder, textvariable=var, width=12).pack(fill="x", ipady=5)
            marks_panel.grid_columnconfigure(i, weight=1)
        self.form_mode_label = tk.StringVar(value="Mode: Add new student")
        tk.Label(panel, textvariable=self.form_mode_label, bg="white", fg="#64748b",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=22, pady=(8, 0))
        buttons = tk.Frame(panel, bg="white")
        buttons.pack(fill="x", padx=22, pady=18)
        ttk.Button(buttons, text="Save Student", command=self.save_form, style="Primary.TButton").pack(side="left")
        ttk.Button(buttons, text="Clear Form", command=self.clear_form).pack(side="left", padx=8)
        ttk.Button(buttons, text="Back to Students", command=self.show_students).pack(side="right")
        tk.Label(panel, text="Pass rule: at least 35/100 in every subject. Grades are based on overall percentage.",
                 bg="white", fg="#64748b", font=("Segoe UI", 9)).pack(anchor="w", padx=22, pady=(0, 18))

    def _build_syllabus_page(self):
        self.syllabus_frame = tk.Frame(self.content, bg="#f3f6fb")
        ttk.Label(self.syllabus_frame, text="Python Syllabus Guide", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self.syllabus_frame, text="Where the syllabus concepts appear in EduTrack.").pack(anchor="w", pady=(4, 14))
        text = tk.Text(self.syllabus_frame, wrap="word", font=("Consolas", 10), bg="white",
                       fg="#243247", relief="flat", padx=18, pady=16)
        text.pack(fill="both", expand=True)
        guide = """MODULE 1 — INTRODUCTION TO PYTHON
• Variables, identifiers and data types: Student model and form variables.
• Strings and methods: name.strip(), casefold(), title(), formatting.
• Operators and precedence: totals, percentages and comparisons.
• Lists, tuples, dictionaries and sets: marks tuple, records and statistics.

MODULE 2 — DECISION MAKING AND LOOPING
• if/elif/else: grade calculation and validation.
• for loops: subject validation, displaying records and exports.
• while loops: binary search.
• break/continue: search and input-processing patterns.
• math/random: class statistics and demo-data generation.

MODULE 3 — ARRAYS, STRINGS AND SEARCHING
• Lists/arrays: collections of Student objects and marks.
• Sum of array: total marks calculation.
• Linear search: search by name or ID.
• Binary search: ID search on sorted records.
• String slicing/immutability: string processing examples in code.

MODULE 4 — FUNCTIONS AND OOP
• Functions: calculate_grade(), linear_search(), class_statistics().
• Classes and objects: StudentRecordService and EduTrackApp.
• Constructor: Student.__init__().
• Encapsulation: private __marks with a read-only property.
• Inheritance: Student inherits from Person.
• Polymorphism: MeritStudent.summary() provides a specialized behavior.

MODULE 5 — FILES, EXCEPTIONS, MODULES AND PACKAGES
• SQLite: persistent database and CRUD operations.
• CSV: import and export.
• JSON: JSON export.
• Text files: performance report export.
• Exceptions: validation, database and file error handling.
• Modules: standard-library imports and separate service/model classes.

SEARCH COMPLEXITY
• Linear search: O(n).
• Binary search: O(log n), after sorting the records by ID.
• Sorting records: typically O(n log n).

GRADING
A+: 90–100 | A: 80–89.99 | B: 70–79.99
C: 60–69.99 | D: 40–59.99 | F: below 40
PASS only if every subject mark is at least 35/100.
"""
        text.insert("1.0", guide)
        text.configure(state="disabled")
        ttk.Button(self.syllabus_frame, text="Export class report", command=self.export_report).pack(anchor="e", pady=10)

    def _show_only(self, frame):
        for child in self.content.winfo_children():
            child.pack_forget()
        frame.pack(fill="both", expand=True)

    def show_dashboard(self):
        self._show_only(self.dashboard_frame)
        self.refresh_dashboard()

    def show_students(self):
        self._show_only(self.students_frame)
        self.refresh_table()

    def show_syllabus(self):
        self._show_only(self.syllabus_frame)

    def clear_form(self):
        self.selected_id = None
        for var in self.form_vars.values():
            var.set("")
        self.form_vars["course"].set("AI & ML Engineering")
        self.form_vars["semester"].set("1")
        for var in self.mark_vars:
            var.set("")
        self.form_mode_label.set("Mode: Add new student")
        self._show_only(self.form_frame)

    def _form_values(self):
        return (
            self.form_vars["name"].get(), self.form_vars["email"].get(),
            self.form_vars["phone"].get(), self.form_vars["course"].get(),
            self.form_vars["semester"].get(), [var.get() for var in self.mark_vars]
        )

    def save_form(self):
        try:
            values = self._form_values()
            if self.selected_id is None:
                student_id = self.service.add(*values)
                messagebox.showinfo("Saved", f"Student registered successfully. Student ID: {student_id}")
            else:
                self.service.update(self.selected_id, *values)
                messagebox.showinfo("Updated", f"Student ID {self.selected_id} updated successfully.")
            self.selected_id = None
            self.refresh_all()
            self.show_students()
        except (ValidationError, sqlite3.Error) as exc:
            messagebox.showerror("Unable to save", str(exc))
        except Exception as exc:
            messagebox.showerror("Unexpected error", f"Could not save student:\n{exc}")

    def refresh_all(self):
        self.refresh_table()
        self.refresh_dashboard()

    def refresh_table(self, students=None):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        records = self.service.all() if students is None else students
        for student in records:
            self.tree.insert("", "end", iid=str(student.student_id), values=(
                student.student_id, student.display_name(), student.course, student.semester,
                student.total, f"{student.percentage:.2f}%", student.grade, student.result
            ))

    def refresh_dashboard(self):
        if not hasattr(self, "stat_vars"):
            return
        students = self.service.all()
        stats = class_statistics(students)
        self.stat_vars["count"].set(str(stats["count"]))
        self.stat_vars["average"].set(f'{stats["average"]:.1f}%')
        self.stat_vars["passed"].set(str(stats["passed"]))
        self.stat_vars["failed"].set(str(stats["failed"]))
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        for student in sorted(students, key=lambda s: s.student_id or 0, reverse=True)[:8]:
            self.recent_tree.insert("", "end", values=(
                student.student_id, student.display_name(), student.course,
                f"{student.percentage:.1f}%", student.result
            ))

    def search_students(self):
        query = self.search_var.get().strip()
        if not query:
            self.refresh_table()
            return
        found = linear_search(self.service.all(), query)
        self.refresh_table(found)
        if not found:
            messagebox.showinfo("Search", "No matching students found.")

    def clear_search(self):
        self.search_var.set("")
        self.refresh_table()

    def binary_search_dialog(self):
        query = self.search_var.get().strip()
        if not query.isdigit():
            messagebox.showwarning("Student ID required", "Enter a numeric student ID in the search field first.")
            return
        student = binary_search_by_id(self.service.all(), int(query))
        if student:
            self.refresh_table([student])
            messagebox.showinfo("Binary search result",
                                f"Found {student.display_name()} (ID {student.student_id}).\n"
                                "Binary search uses a list sorted by student ID.")
        else:
            messagebox.showinfo("Binary search result", "No student found with that ID.")

    def sort_by(self, column):
        records = self.service.all()
        key_functions = {
            "id": lambda s: s.student_id or 0,
            "name": lambda s: s.display_name().casefold(),
            "course": lambda s: s.course.casefold(),
            "semester": lambda s: s.semester,
            "total": lambda s: s.total,
            "percentage": lambda s: s.percentage,
            "grade": lambda s: s.grade,
            "result": lambda s: s.result,
        }
        self.refresh_table(sorted(records, key=key_functions[column]))

    def _on_select(self, _event=None):
        selection = self.tree.selection()
        self.selected_id = int(selection[0]) if selection else None

    def load_selected_to_form(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a student", "Choose a student record first.")
            return
        student = self.service.get(int(selection[0]))
        if not student:
            messagebox.showerror("Not found", "This record no longer exists.")
            self.refresh_all()
            return
        self.selected_id = student.student_id
        for key, value in [("name", student.name), ("email", student.email),
                           ("phone", student.phone), ("course", student.course),
                           ("semester", str(student.semester))]:
            self.form_vars[key].set(value)
        for var, mark in zip(self.mark_vars, student.marks):
            var.set(str(mark))
        self.form_mode_label.set(f"Mode: Editing student ID {student.student_id}")
        self._show_only(self.form_frame)

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a student", "Choose a student record first.")
            return
        student_id = int(selection[0])
        if messagebox.askyesno("Confirm deletion", f"Delete student ID {student_id}? This cannot be undone."):
            try:
                self.service.delete(student_id)
                self.refresh_all()
            except (ValidationError, sqlite3.Error) as exc:
                messagebox.showerror("Delete failed", str(exc))

    def export_csv(self):
        path = filedialog.asksaveasfilename(title="Export students to CSV",
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="students.csv")
        if not path:
            return
        try:
            students = self.service.all()
            records = [student.as_dict() for student in students]
            fields = list(records[0].keys()) if records else [
                "student_id", "name", "email", "phone", "course", "semester",
                "registration_date", "total", "percentage", "grade", "result",
                *[f"mark_{i}" for i in range(1, 6)]
            ]
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(records)
            messagebox.showinfo("Export complete", f"Exported {len(records)} student(s) to:\n{path}")
        except (OSError, csv.Error) as exc:
            messagebox.showerror("Export failed", str(exc))

    def export_json(self):
        path = filedialog.asksaveasfilename(title="Export students to JSON",
            defaultextension=".json", filetypes=[("JSON files", "*.json")], initialfile="students.json")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump([s.as_dict() for s in self.service.all()], file, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export complete", f"JSON saved to:\n{path}")
        except (OSError, TypeError) as exc:
            messagebox.showerror("Export failed", str(exc))

    def import_csv(self):
        path = filedialog.askopenfilename(title="Import students from CSV",
            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))
            imported, errors = self.service.import_records(rows)
            self.refresh_all()
            summary = f"Imported {imported} student(s)."
            if errors:
                summary += "\n\nSome rows were skipped:\n" + "\n".join(errors[:8])
                if len(errors) > 8:
                    summary += f"\n...and {len(errors)-8} more."
            messagebox.showinfo("Import results", summary)
        except (OSError, csv.Error, UnicodeError) as exc:
            messagebox.showerror("Import failed", str(exc))

    def export_report(self):
        path = filedialog.asksaveasfilename(title="Save class report",
            defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialfile="class_report.txt")
        if not path:
            return
        students = self.service.all()
        stats = class_statistics(students)
        lines = [
            "EDUTRACK — CLASS PERFORMANCE REPORT",
            "=" * 42,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total students: {stats['count']}",
            f"Class average: {stats['average']:.2f}%",
            f"Passed: {stats['passed']}",
            f"Failed: {stats['failed']}",
            f"Highest percentage: {stats['highest']:.2f}%",
            f"Lowest percentage: {stats['lowest']:.2f}%",
            "",
            "STUDENT DETAILS",
            "-" * 42,
        ]
        for student in students:
            lines.append(f"ID {student.student_id} | {student.display_name()} | "
                         f"{student.total}/500 | {student.percentage:.2f}% | "
                         f"Grade {student.grade} | {student.result}")
        try:
            Path(path).write_text("\n".join(lines), encoding="utf-8")
            messagebox.showinfo("Report saved", f"Class report saved to:\n{path}")
        except OSError as exc:
            messagebox.showerror("Report failed", str(exc))

    def generate_demo_data(self):
        # Available as a method for easy extension; it never deletes existing data.
        names = ["Aarav Patil", "Diya Shah", "Rohan Kulkarni", "Anaya Joshi", "Kabir More"]
        added = 0
        for name in names:
            marks = [random.randint(35, 100) for _ in SUBJECTS]
            try:
                self.service.add(name, "", "", "AI & ML Engineering", random.randint(1, 6), marks)
                added += 1
            except (ValidationError, sqlite3.Error):
                continue
        self.refresh_all()
        messagebox.showinfo("Demo data", f"Added {added} sample student(s).")

    def _update_clock(self):
        if hasattr(self, "clock_label"):
            self.clock_label.config(text=datetime.now().strftime("%a, %d %b %Y  •  %I:%M:%S %p"))
            self.after(1000, self._update_clock)


def main():
    try:
        app = EduTrackApp()
        app.mainloop()
    except tk.TclError as exc:
        print("Could not start the Tkinter GUI.")
        print("Ensure Python was installed with Tkinter support and run this on a desktop.")
        print(f"Details: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
