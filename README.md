# EduTrack — Student Management System

A Python Tkinter desktop application designed to demonstrate concepts from an introductory Python syllabus.

## Requirements
- Python 3.10 or newer recommended
- Tkinter (usually included with Python on Windows and macOS)
- SQLite (included with Python)

No third-party packages are required.

## Run
From the `EduTrack_Student_Management_System` folder:

```bash
python main.py
```

The SQLite database is created automatically at `data/edutrack.db`.

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Features
- Add, edit, delete, search, and sort student records
- Five subject marks, total, percentage, grade, and pass/fail
- SQLite persistence
- CSV import/export, JSON export, text class report
- Dashboard statistics
- Linear and binary search
- Syllabus guide inside the application

## Grade rules
A+ >= 90; A >= 80; B >= 70; C >= 60; D >= 40; F < 40.
A student passes only when each subject has at least 35/100.

## Syllabus mapping
- Data types/operators: Student model, marks calculations and form values
- Strings: `display_name`, `linear_search`, input validation
- Lists/tuples/dictionaries: marks, student collections and exported records
- Conditions and loops: validation, grade rules, search and table population
- `math`/`random`: imported for syllabus demonstration and sample data extension
- Functions: `calculate_grade`, `linear_search`, `binary_search_by_id`, `class_statistics`
- OOP: `Person`, `Student`, `MeritStudent`, `StudentRecordService`, `EduTrackApp`
- Encapsulation: private `Student.__marks` and `marks` property
- Inheritance: `Student(Person)` and `MeritStudent(Student)`
- Files: CSV, JSON and text report output
- Exceptions: `ValidationError`, file/database exception handling
- Modules: built-in modules and separated tests

## Notes
- Student information is stored locally. Do not use real sensitive data for demonstrations.
- CSV import expects columns such as `name`, `course`, `semester`, and `mark_1` through `mark_5`.
- Binary search sorts records by student ID before searching.
