# Student Analytics Platform — Performance Tracking System

> This project demonstrates backend system design concepts including APIs, data processing, and asynchronous workflows.

## Overview

Built a full-stack web app to store and analyze student performance data for 1,000+ students. Implemented SQL queries to compute average scores and identify at-risk students. Designed a dynamic UI to display analytics and insights loaded asynchronously with no page reloads.

The platform uses a normalized 3-table SQL schema across 5 departments and surfaces performance trends through a real-time dashboard.

## Features

- Ingests and stores academic records for **1,000+ students** across departments (CSE, ECE, ME, EE, CE)
- Normalized SQL schema with 3 tables: `students`, `subjects`, `grades` — with foreign keys and proper indexing
- **GPA distribution by department** — multi-table JOIN with aggregations
- **Subject-level trend analysis** — average marks, pass rates, difficulty ranking
- **At-risk student detection** — flags students below a configurable marks threshold with risk levels (critical / high / moderate)
- **Dynamic dashboard** loaded via JavaScript Fetch API — zero page reloads, async data pipelines
- SQL queries with multi-table joins, GROUP BY, HAVING, and CASE expressions

## Tech Stack

Python · Flask · SQLite · JavaScript (Fetch API) · HTML5 · CSS3

## How to Run

```bash
pip install -r requirements.txt
python app.py
```

The database is created and seeded automatically on first run with 1,000 students. Opens at `http://localhost:5003`.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/dashboard` | Summary stats: total students, avg marks, grade distribution |
| GET | `/api/analytics/gpa-distribution` | Avg marks and performance by department |
| GET | `/api/analytics/subject-trends` | Per-subject avg, pass rate, difficulty |
| GET | `/api/analytics/at-risk` | Students below threshold (`?threshold=45`) |
| GET | `/api/students` | List students (filter: `?department=`, `?semester=`) |
| GET | `/api/students/<id>` | Student detail with all grade records |
| POST | `/api/students` | Add a student |
| POST | `/api/grades` | Add a grade record |
| GET | `/api/subjects` | List all subjects |

## Example SQL Query (At-Risk Detection)

```sql
SELECT s.name, s.department, AVG(g.marks) as avg_marks,
       COUNT(CASE WHEN g.grade = 'F' THEN 1 END) as failed_subjects
FROM students s
JOIN grades g ON s.id = g.student_id
GROUP BY s.id
HAVING avg_marks < 45
ORDER BY avg_marks ASC;
```

## Example API Response

```json
{
  "threshold": 45,
  "count": 87,
  "students": [
    {
      "name": "Rohan Sharma",
      "roll_number": "CS20210042",
      "department": "CSE",
      "avg_marks": 31.2,
      "failed_subjects": 2,
      "risk_level": "critical"
    }
  ]
}
```

## Database Schema

```
students (id, name, roll_number, department, semester, email)
    │
    └── grades (id, student_id, subject_id, marks, grade, academic_year)
                         │
subjects (id, name, code, department, credits, semester)
```

## Architecture

- **MVC structure**: routes handle HTTP, SQL queries live in dedicated functions, dashboard renders from Fetch API responses
- **Async data loading**: JavaScript Fetch API pulls each analytics endpoint independently — dashboard sections load in parallel
- **Seeded with 1,000 students** across 5 departments and 15 subjects on first run

## Output

See [sample_output.txt](sample_output.txt) for real API request/response examples including dashboard summary, at-risk student detection, student detail breakdown, and top performer listing.
