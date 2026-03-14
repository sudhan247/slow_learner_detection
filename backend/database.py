"""
Database Handler — SQLite
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Manages users (role-based auth), students, and improvement tracking.
"""

from __future__ import annotations
import os
import sqlite3

import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "students.db")


# ── Connection helper ──────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Schema ─────────────────────────────────────────────────────────────────────
def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            username            TEXT    UNIQUE NOT NULL,
            password_hash       TEXT    NOT NULL,
            role                TEXT    NOT NULL
                            CHECK(role IN ('admin','faculty','student')),
            linked_student_id   TEXT    DEFAULT NULL,
            linked_faculty_id   TEXT    DEFAULT NULL,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id              TEXT    UNIQUE NOT NULL,
            faculty_id              TEXT    DEFAULT 'FAC001',
            attendance              REAL,
            assignment_score        REAL,
            internal_marks          REAL,
            quiz_score              REAL,
            previous_semester_marks REAL,
            average_score           REAL,
            attendance_ratio        REAL,
            performance_drop        REAL,
            score_variance          REAL,
            risk_level              TEXT,
            predicted_risk          TEXT,
            confidence              REAL,
            difficulty_type         TEXT,
            created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS improvement_tracking (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    TEXT    NOT NULL,
            timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            attendance    REAL,
            average_score REAL,
            risk_level    TEXT
        );
    """)
    conn.commit()
    conn.close()


# ── Default user seeding ───────────────────────────────────────────────────────
def create_default_users() -> None:
    """Insert admin and faculty accounts (idempotent)."""
    conn = _conn()
    defaults = [
        ("admin",    "admin123",    "admin",   None,      None),
        ("faculty1", "faculty123",  "faculty", None,      "FAC001"),
        ("faculty2", "faculty123",  "faculty", None,      "FAC002"),
    ]
    for username, password, role, sid, fid in defaults:
        try:
            conn.execute(
                "INSERT INTO users (username,password_hash,role,linked_student_id,linked_faculty_id)"
                " VALUES (?,?,?,?,?)",
                (username, generate_password_hash(password), role, sid, fid),
            )
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()


def create_student_users() -> int:
    """Create one login account per student (username = student_id lowercase)."""
    conn = _conn()
    students = conn.execute("SELECT student_id FROM students").fetchall()
    created = 0
    for row in students:
        sid = row["student_id"]
        try:
            conn.execute(
                "INSERT INTO users (username,password_hash,role,linked_student_id)"
                " VALUES (?,?,?,?)",
                (sid.lower(), generate_password_hash("student123"), "student", sid),
            )
            created += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return created


# ── Auth queries ───────────────────────────────────────────────────────────────
def get_user_by_username(username: str) -> dict | None:
    conn = _conn()
    row  = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def verify_user(username: str, password: str) -> dict | None:
    """Return user dict if credentials are valid, else None."""
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def get_all_users() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT id, username, role, linked_student_id, linked_faculty_id, created_at"
        " FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Student data loading ───────────────────────────────────────────────────────
def load_csv_to_db(csv_path: str | None = None) -> bool:
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, "data", "students.csv")
    if not os.path.exists(csv_path):
        return False

    df = pd.read_csv(csv_path)

    # Calculate derived fields if missing
    if "faculty_id" not in df.columns:
        df["faculty_id"] = "FAC001"

    if "average_score" not in df.columns:
        score_cols = ["assignment_score", "internal_marks", "quiz_score"]
        available = [c for c in score_cols if c in df.columns]
        if available:
            df["average_score"] = df[available].mean(axis=1).round(2)

    if "attendance_ratio" not in df.columns and "attendance" in df.columns:
        df["attendance_ratio"] = (df["attendance"] / 100).round(4)

    if "performance_drop" not in df.columns:
        if "previous_semester_marks" in df.columns and "average_score" in df.columns:
            df["performance_drop"] = (df["previous_semester_marks"] - df["average_score"]).round(2)

    if "score_variance" not in df.columns:
        score_cols = ["assignment_score", "internal_marks", "quiz_score"]
        available = [c for c in score_cols if c in df.columns]
        if len(available) >= 2:
            df["score_variance"] = df[available].var(axis=1).round(2)

    # Calculate risk_level if missing
    if "risk_level" not in df.columns:
        def calc_risk(row):
            avg = row.get("average_score", 0) or 0
            att = row.get("attendance", 0) or 0
            if att >= 85 and avg >= 75:
                return "Low Risk"
            elif att >= 70 and avg >= 55:
                return "Medium Risk"
            else:
                return "High Risk"
        df["risk_level"] = df.apply(calc_risk, axis=1)

    conn = _conn()

    # Clear existing data before loading new data
    conn.execute("DELETE FROM students")

    sql = (
        "INSERT INTO students"
        " (student_id, faculty_id, attendance, assignment_score, internal_marks,"
        "  quiz_score, previous_semester_marks, average_score, attendance_ratio,"
        "  performance_drop, score_variance, risk_level)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    rows = [
        (
            row.get("student_id"), row.get("faculty_id", "FAC001"),
            row.get("attendance"), row.get("assignment_score"),
            row.get("internal_marks"), row.get("quiz_score"),
            row.get("previous_semester_marks"), row.get("average_score"),
            row.get("attendance_ratio"), row.get("performance_drop"),
            row.get("score_variance"), row.get("risk_level"),
        )
        for _, row in df.iterrows()
    ]
    conn.executemany(sql, rows)
    conn.commit()
    conn.close()
    return True


# ── Student queries ────────────────────────────────────────────────────────────
def get_all_students() -> pd.DataFrame:
    conn = _conn()
    df   = pd.read_sql_query("SELECT * FROM students ORDER BY student_id", conn)
    conn.close()
    return df


def get_student_by_id(student_id: str) -> pd.DataFrame:
    conn = _conn()
    df   = pd.read_sql_query(
        "SELECT * FROM students WHERE student_id = ?", conn, params=(student_id,)
    )
    conn.close()
    return df


def get_students_by_faculty(faculty_id: str) -> pd.DataFrame:
    conn = _conn()
    df   = pd.read_sql_query(
        "SELECT * FROM students WHERE faculty_id = ? ORDER BY student_id",
        conn, params=(faculty_id,),
    )
    conn.close()
    return df


def update_student_prediction(
    student_id: str,
    predicted_risk: str,
    confidence: float,
    difficulty_type: str,
) -> None:
    conn = _conn()
    conn.execute(
        "UPDATE students SET predicted_risk=?, confidence=?, difficulty_type=?"
        " WHERE student_id=?",
        (predicted_risk, confidence, difficulty_type, student_id),
    )
    conn.commit()
    conn.close()


def add_improvement_record(
    student_id: str,
    attendance: float,
    average_score: float,
    risk_level: str,
) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO improvement_tracking (student_id, attendance, average_score, risk_level)"
        " VALUES (?,?,?,?)",
        (student_id, attendance, average_score, risk_level),
    )
    conn.commit()
    conn.close()


def get_improvement_history(student_id: str) -> pd.DataFrame:
    conn = _conn()
    df   = pd.read_sql_query(
        "SELECT * FROM improvement_tracking WHERE student_id = ? ORDER BY timestamp",
        conn, params=(student_id,),
    )
    conn.close()
    return df


def get_analytics_summary() -> dict:
    conn      = _conn()
    total     = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    risk_dist = pd.read_sql_query(
        "SELECT risk_level, COUNT(*) AS count FROM students GROUP BY risk_level", conn
    )
    avg_att   = conn.execute("SELECT AVG(attendance)    FROM students").fetchone()[0] or 0
    avg_scr   = conn.execute("SELECT AVG(average_score) FROM students").fetchone()[0] or 0
    conn.close()
    return {
        "total_students":    int(total),
        "risk_distribution": risk_dist.to_dict("records"),
        "avg_attendance":    round(float(avg_att), 2),
        "avg_score":         round(float(avg_scr), 2),
    }
