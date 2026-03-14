"""
External Database Connector
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Handles connections to external databases (PostgreSQL, MySQL, SQLite, etc.) via SQLAlchemy.
"""

from __future__ import annotations
import os
import sqlite3
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "students.db")

# Required fields for student data
REQUIRED_FIELDS = [
    "student_id",
    "attendance",
    "assignment_score",
    "internal_marks",
    "quiz_score",
    "previous_semester_marks",
]


def test_connection(conn_string: str) -> dict[str, Any]:
    """
    Test if a connection string is valid and return available tables.

    Args:
        conn_string: SQLAlchemy connection string

    Returns:
        dict with 'success', 'message', and 'tables' keys
    """
    try:
        engine = create_engine(conn_string, connect_args=_get_connect_args(conn_string))
        with engine.connect() as conn:
            # Test the connection by executing a simple query
            conn.execute(text("SELECT 1"))

        # Get available tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        engine.dispose()

        return {
            "success": True,
            "message": "Connection successful",
            "tables": tables,
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "tables": [],
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "tables": [],
        }


def get_tables(conn_string: str) -> dict[str, Any]:
    """
    Get list of tables in the external database.

    Args:
        conn_string: SQLAlchemy connection string

    Returns:
        dict with 'success', 'tables', and optional 'error' keys
    """
    try:
        engine = create_engine(conn_string, connect_args=_get_connect_args(conn_string))
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()

        return {
            "success": True,
            "tables": tables,
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "tables": [],
            "error": str(e),
        }


def get_columns(conn_string: str, table: str) -> dict[str, Any]:
    """
    Get column names for a specific table.

    Args:
        conn_string: SQLAlchemy connection string
        table: Name of the table

    Returns:
        dict with 'success', 'columns', and optional 'error' keys
    """
    try:
        engine = create_engine(conn_string, connect_args=_get_connect_args(conn_string))
        inspector = inspect(engine)

        # Check if table exists
        tables = inspector.get_table_names()
        if table not in tables:
            engine.dispose()
            return {
                "success": False,
                "columns": [],
                "error": f"Table '{table}' not found",
            }

        columns = [col["name"] for col in inspector.get_columns(table)]
        engine.dispose()

        return {
            "success": True,
            "columns": columns,
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "columns": [],
            "error": str(e),
        }


def load_data(conn_string: str, table: str) -> dict[str, Any]:
    """
    Load data from external database into the local SQLite database.
    Expects standard column names: student_id, attendance, assignment_score,
    internal_marks, quiz_score, previous_semester_marks

    Args:
        conn_string: SQLAlchemy connection string
        table: Name of the source table

    Returns:
        dict with 'success', 'message', 'rows_loaded', and optional 'error' keys
    """
    try:
        engine = create_engine(conn_string, connect_args=_get_connect_args(conn_string))

        # Load all data from table
        query = f'SELECT * FROM `{table}`'
        df = pd.read_sql_query(query, engine)
        engine.dispose()

        if df.empty:
            return {
                "success": False,
                "message": "No data found in the source table",
                "rows_loaded": 0,
            }

        # Validate required columns exist
        missing = set(REQUIRED_FIELDS) - set(df.columns)
        if missing:
            return {
                "success": False,
                "message": f"Missing required columns: {', '.join(missing)}",
                "rows_loaded": 0,
            }

        # Calculate derived fields if not provided
        df = _calculate_derived_fields(df)

        # Load into local SQLite database
        rows_loaded = _insert_into_local_db(df)

        return {
            "success": True,
            "message": f"Successfully loaded {rows_loaded} records",
            "rows_loaded": rows_loaded,
        }

    except SQLAlchemyError as e:
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "rows_loaded": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error loading data: {str(e)}",
            "rows_loaded": 0,
        }


def _get_connect_args(conn_string: str) -> dict:
    """Get connection arguments based on database type."""
    if conn_string.startswith("sqlite"):
        return {}
    elif "postgresql" in conn_string or "postgres" in conn_string:
        return {"connect_timeout": 10}
    elif "mysql" in conn_string or "mariadb" in conn_string:
        # TiDB Cloud and other cloud MySQL services require SSL
        if "tidbcloud.com" in conn_string:
            return {"connect_timeout": 10, "ssl": {"ssl_mode": "REQUIRED"}}
        return {"connect_timeout": 10}
    return {}


def _calculate_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate auto-derived fields if not present."""

    # Set default faculty_id if not present
    if "faculty_id" not in df.columns:
        df["faculty_id"] = "FAC001"

    # Calculate average_score if not present
    if "average_score" not in df.columns:
        score_cols = ["assignment_score", "internal_marks", "quiz_score"]
        available_cols = [c for c in score_cols if c in df.columns]
        if available_cols:
            df["average_score"] = df[available_cols].mean(axis=1).round(2)
        else:
            df["average_score"] = 0.0

    # Calculate attendance_ratio if not present
    if "attendance_ratio" not in df.columns and "attendance" in df.columns:
        df["attendance_ratio"] = (df["attendance"] / 100).round(4)

    # Calculate performance_drop if not present
    if "performance_drop" not in df.columns:
        if "previous_semester_marks" in df.columns and "average_score" in df.columns:
            df["performance_drop"] = (
                df["previous_semester_marks"] - df["average_score"]
            ).round(2)
        else:
            df["performance_drop"] = 0.0

    # Calculate score_variance if not present
    if "score_variance" not in df.columns:
        score_cols = ["assignment_score", "internal_marks", "quiz_score"]
        available_cols = [c for c in score_cols if c in df.columns]
        if len(available_cols) >= 2:
            df["score_variance"] = df[available_cols].var(axis=1).round(2)
        else:
            df["score_variance"] = 0.0

    # Calculate risk_level based on performance metrics
    if "risk_level" not in df.columns:
        def calculate_risk(row):
            avg_score = row.get("average_score", 0) or 0
            attendance = row.get("attendance", 0) or 0

            if attendance >= 85 and avg_score >= 75:
                return "Low Risk"
            elif attendance >= 70 and avg_score >= 55:
                return "Medium Risk"
            else:
                return "High Risk"

        df["risk_level"] = df.apply(calculate_risk, axis=1)

    return df


def _insert_into_local_db(df: pd.DataFrame) -> int:
    """Insert dataframe into local SQLite students table. Clears existing data first."""
    conn = sqlite3.connect(DB_PATH)

    # Clear existing student data before loading new data
    conn.execute("DELETE FROM students")

    sql = """
        INSERT OR REPLACE INTO students
        (student_id, faculty_id, attendance, assignment_score, internal_marks,
         quiz_score, previous_semester_marks, average_score, attendance_ratio,
         performance_drop, score_variance, risk_level)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """

    rows = []
    for _, row in df.iterrows():
        rows.append((
            row.get("student_id"),
            row.get("faculty_id", "FAC001"),
            row.get("attendance"),
            row.get("assignment_score"),
            row.get("internal_marks"),
            row.get("quiz_score"),
            row.get("previous_semester_marks"),
            row.get("average_score"),
            row.get("attendance_ratio"),
            row.get("performance_drop"),
            row.get("score_variance"),
            row.get("risk_level"),
        ))

    conn.executemany(sql, rows)
    conn.commit()
    rows_affected = len(rows)
    conn.close()

    return rows_affected
