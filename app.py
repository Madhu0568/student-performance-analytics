from flask import Flask, request, jsonify
import sqlite3
import os
import random
import uuid
from datetime import datetime

app = Flask(__name__)
DB_PATH = "students.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_status(marks):
    """Classify a student's academic standing based on average marks."""
    if marks < 40:
        return "At Risk"
    elif marks < 55:
        return "Needs Attention"
    elif marks < 70:
        return "Average"
    else:
        return "Good Standing"


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            email TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            credits INTEGER NOT NULL,
            semester INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            marks INTEGER NOT NULL,
            grade TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    departments = ["CSE", "ECE", "ME", "EE", "CE"]
    first_names = ["Aarav", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Divya", "Karan", "Meera",
                   "Arjun", "Kavya", "Aditya", "Pooja", "Nikhil", "Riya", "Siddharth", "Neha", "Manish", "Anjali"]
    last_names = ["Sharma", "Patel", "Kumar", "Singh", "Reddy", "Gupta", "Joshi", "Verma", "Nair", "Iyer",
                  "Das", "Chopra", "Mehta", "Rao", "Mishra", "Bhat", "Saxena", "Chauhan", "Pandey", "Shah"]

    subjects_data = [
        ("Data Structures", "CS101", "CSE", 4, 3), ("Algorithms", "CS102", "CSE", 4, 4),
        ("Database Management", "CS103", "CSE", 3, 4), ("Operating Systems", "CS104", "CSE", 4, 5),
        ("Computer Networks", "CS105", "CSE", 3, 5), ("Machine Learning", "CS106", "CSE", 3, 6),
        ("Signals & Systems", "EC101", "ECE", 4, 3), ("Digital Electronics", "EC102", "ECE", 4, 4),
        ("VLSI Design", "EC103", "ECE", 3, 5), ("Communication Systems", "EC104", "ECE", 4, 5),
        ("Thermodynamics", "ME101", "ME", 4, 3), ("Fluid Mechanics", "ME102", "ME", 3, 4),
        ("Engineering Mathematics", "MA101", "CSE", 4, 1), ("Physics", "PH101", "CSE", 3, 1),
        ("Chemistry", "CH101", "CSE", 3, 1),
    ]

    subject_ids = {}
    for name, code, dept, credits, sem in subjects_data:
        sid = str(uuid.uuid4())[:8]
        cursor.execute("INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?)", (sid, name, code, dept, credits, sem))
        subject_ids[code] = sid

    students = []
    for i in range(1000):
        student_id = str(uuid.uuid4())[:8]
        dept = random.choice(departments)
        sem = random.randint(1, 8)
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        roll = f"{dept[:2]}{2020 + (sem // 2)}{str(i+1).zfill(4)}"
        email = f"{name.lower().replace(' ', '.')}{i}@nit.ac.in"

        cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (student_id, name, roll, dept, sem, email, datetime.utcnow().isoformat()))
        students.append((student_id, dept, sem))

    grade_map = {
        (90, 100): "A+", (80, 89): "A", (70, 79): "B+",
        (60, 69): "B", (50, 59): "C", (40, 49): "D", (0, 39): "F"
    }

    def get_grade(marks):
        for (low, high), grade in grade_map.items():
            if low <= marks <= high:
                return grade
        return "F"

    for student_id, dept, sem in students:
        relevant_subjects = [(code, sid) for code, sid in subject_ids.items()
                             if any(s[2] == dept or s[2] == "CSE" for s in subjects_data if s[1] == code)]
        selected = random.sample(relevant_subjects, min(4, len(relevant_subjects)))

        for code, sid in selected:
            marks = max(0, min(100, int(random.gauss(68, 15))))
            grade = get_grade(marks)
            gid = str(uuid.uuid4())[:8]
            year = f"2023-24"
            cursor.execute("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?)",
                           (gid, student_id, sid, marks, grade, year))

    conn.commit()
    conn.close()


init_db()
seed_data()


@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db()
    dept = request.args.get("department")
    sem = request.args.get("semester")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if dept:
        query += " AND department = ?"
        params.append(dept)
    if sem:
        query += " AND semester = ?"
        params.append(int(sem))
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    students = [dict(row) for row in conn.execute(query, params).fetchall()]
    total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    return jsonify({"total": total, "students": students})


@app.route("/api/students/<student_id>", methods=["GET"])
def get_student(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    grades = conn.execute("""
        SELECT g.*, s.name as subject_name, s.code as subject_code, s.credits
        FROM grades g JOIN subjects s ON g.subject_id = s.id
        WHERE g.student_id = ?
    """, (student_id,)).fetchall()

    conn.close()
    return jsonify({
        "student": dict(student),
        "grades": [dict(g) for g in grades],
    })


@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json()
    required = ["name", "roll_number", "department", "semester"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Required fields: {required}"}), 400

    conn = get_db()
    student_id = str(uuid.uuid4())[:8]
    try:
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (student_id, data["name"], data["roll_number"], data["department"],
                      data["semester"], data.get("email"), datetime.utcnow().isoformat()))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Roll number already exists"}), 409
    conn.close()
    return jsonify({"id": student_id, "message": "Student added"}), 201


@app.route("/api/grades", methods=["POST"])
def add_grade():
    data = request.get_json()
    required = ["student_id", "subject_id", "marks", "academic_year"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Required fields: {required}"}), 400

    marks = data["marks"]
    grade_map = {90: "A+", 80: "A", 70: "B+", 60: "B", 50: "C", 40: "D"}
    grade = "F"
    for threshold, g in sorted(grade_map.items(), reverse=True):
        if marks >= threshold:
            grade = g
            break

    conn = get_db()
    gid = str(uuid.uuid4())[:8]
    conn.execute("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?)",
                 (gid, data["student_id"], data["subject_id"], marks, grade, data["academic_year"]))
    conn.commit()
    conn.close()
    return jsonify({"id": gid, "grade": grade}), 201


@app.route("/api/analytics/gpa-distribution", methods=["GET"])
def gpa_distribution():
    conn = get_db()
    dept = request.args.get("department")

    query = """
        SELECT s.department,
               AVG(g.marks) as avg_marks,
               COUNT(DISTINCT g.student_id) as student_count,
               SUM(CASE WHEN g.grade IN ('A+', 'A') THEN 1 ELSE 0 END) as high_performers,
               SUM(CASE WHEN g.grade = 'F' THEN 1 ELSE 0 END) as failures
        FROM grades g
        JOIN students s ON g.student_id = s.id
    """
    params = []
    if dept:
        query += " WHERE s.department = ?"
        params.append(dept)
    query += " GROUP BY s.department ORDER BY avg_marks DESC"

    results = [dict(row) for row in conn.execute(query, params).fetchall()]
    for r in results:
        r["avg_marks"] = round(r["avg_marks"], 1)

    conn.close()
    return jsonify({"departments": results})


@app.route("/api/analytics/subject-trends", methods=["GET"])
def subject_trends():
    conn = get_db()
    results = conn.execute("""
        SELECT sub.name, sub.code, sub.credits,
               AVG(g.marks) as avg_marks,
               MIN(g.marks) as min_marks,
               MAX(g.marks) as max_marks,
               COUNT(*) as total_students,
               SUM(CASE WHEN g.grade = 'F' THEN 1 ELSE 0 END) as fail_count
        FROM grades g
        JOIN subjects sub ON g.subject_id = sub.id
        GROUP BY sub.id
        ORDER BY avg_marks DESC
    """).fetchall()

    subjects = []
    for r in results:
        d = dict(r)
        d["avg_marks"] = round(d["avg_marks"], 1)
        d["pass_rate"] = round((1 - d["fail_count"] / d["total_students"]) * 100, 1) if d["total_students"] > 0 else 0
        subjects.append(d)

    conn.close()
    return jsonify({"subjects": subjects})


@app.route("/api/analytics/at-risk", methods=["GET"])
def at_risk_students():
    conn = get_db()
    threshold = request.args.get("threshold", 45, type=int)

    results = conn.execute("""
        SELECT s.id, s.name, s.roll_number, s.department, s.semester,
               AVG(g.marks) as avg_marks,
               COUNT(CASE WHEN g.grade = 'F' THEN 1 END) as failed_subjects,
               COUNT(g.id) as total_subjects
        FROM students s
        JOIN grades g ON s.id = g.student_id
        GROUP BY s.id
        HAVING avg_marks < ?
        ORDER BY avg_marks ASC
    """, (threshold,)).fetchall()

    students = []
    for r in results:
        d = dict(r)
        d["avg_marks"] = round(d["avg_marks"], 1)
        d["risk_level"] = "critical" if d["avg_marks"] < 30 else "high" if d["avg_marks"] < 40 else "moderate"
        d["academic_status"] = get_status(d["avg_marks"])
        students.append(d)

    conn.close()
    return jsonify({"threshold": threshold, "count": len(students), "students": students})


@app.route("/api/analytics/dashboard", methods=["GET"])
def dashboard_stats():
    conn = get_db()

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_subjects = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]

    overall = conn.execute("SELECT AVG(marks) as avg, MIN(marks) as min, MAX(marks) as max FROM grades").fetchone()

    dept_stats = conn.execute("""
        SELECT s.department, COUNT(DISTINCT s.id) as students, AVG(g.marks) as avg_marks
        FROM students s LEFT JOIN grades g ON s.id = g.student_id
        GROUP BY s.department
    """).fetchall()

    grade_dist = conn.execute("""
        SELECT grade, COUNT(*) as count FROM grades GROUP BY grade ORDER BY grade
    """).fetchall()

    # High scorers: students with average marks above 75
    high_scorers = conn.execute("""
        SELECT COUNT(DISTINCT student_id) as count
        FROM (
            SELECT student_id, AVG(marks) as avg_marks
            FROM grades
            GROUP BY student_id
            HAVING avg_marks > 75
        )
    """).fetchone()[0]

    # At-risk: students below 45
    at_risk = conn.execute("""
        SELECT COUNT(DISTINCT student_id) as count
        FROM (
            SELECT student_id, AVG(marks) as avg_marks
            FROM grades
            GROUP BY student_id
            HAVING avg_marks < 45
        )
    """).fetchone()[0]

    conn.close()
    return jsonify({
        "total_students": total_students,
        "total_subjects": total_subjects,
        "overall_average": round(overall["avg"], 1) if overall["avg"] else 0,
        "overall_min": overall["min"],
        "overall_max": overall["max"],
        "high_scorers": high_scorers,
        "at_risk_students": at_risk,
        "departments": [{"department": d["department"], "students": d["students"],
                         "avg_marks": round(d["avg_marks"], 1) if d["avg_marks"] else 0,
                         "academic_status": get_status(d["avg_marks"] or 0)} for d in dept_stats],
        "grade_distribution": [dict(g) for g in grade_dist],
    })


@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    conn = get_db()
    subjects = [dict(row) for row in conn.execute("SELECT * FROM subjects ORDER BY department, semester").fetchall()]
    conn.close()
    return jsonify({"subjects": subjects})


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
