"""
API Routes Blueprint
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
All REST endpoint definitions with role-based access control.
"""

from __future__ import annotations
import os
import sys
import traceback

from flask import Blueprint, request, jsonify, g

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.auth            import login_required, role_required, generate_token
from backend.database        import (
    verify_user, get_all_users,
    get_all_students, get_student_by_id, get_students_by_faculty,
    update_student_prediction, get_analytics_summary,
    add_improvement_record, get_improvement_history, load_csv_to_db,
)
from backend.model_handler   import predict_risk, get_model_metrics, engineer_features
from backend.recommendation  import get_recommendations
from backend.external_db     import (
    test_connection as ext_test_connection,
    get_tables as ext_get_tables,
    get_columns as ext_get_columns,
    load_data as ext_load_data,
)

api = Blueprint("api", __name__)


# ── Health ─────────────────────────────────────────────────────────────────────
@api.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Slow Learner Detection API is running"}), 200


# ── Auth ───────────────────────────────────────────────────────────────────────
@api.route("/login", methods=["POST"])
def login():
    """
    POST /login
    Body: { username, password }
    Returns: { token, role, username, user_id, linked_student_id, linked_faculty_id }
    """
    data     = request.get_json(force=True, silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = verify_user(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    token = generate_token(user)
    return jsonify({
        "success":           True,
        "token":             token,
        "role":              user["role"],
        "username":          user["username"],
        "user_id":           user["id"],
        "linked_student_id": user["linked_student_id"],
        "linked_faculty_id": user["linked_faculty_id"],
    }), 200


@api.route("/logout", methods=["POST"])
@login_required
def logout():
    # Stateless JWT — client simply discards the token
    return jsonify({"success": True, "message": "Logged out"}), 200


@api.route("/current_user", methods=["GET"])
@login_required
def current_user():
    return jsonify({"success": True, "user": g.current_user}), 200


# ── Predict ────────────────────────────────────────────────────────────────────
@api.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        data     = request.get_json(force=True, silent=True) or {}
        required = ["attendance", "assignment_score", "internal_marks",
                    "quiz_score", "previous_semester_marks"]
        missing  = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        for field in required:
            try:
                val = float(data[field])
                if not (0 <= val <= 100):
                    return jsonify({"error": f"'{field}' must be between 0 and 100"}), 400
                data[field] = val
            except (TypeError, ValueError):
                return jsonify({"error": f"'{field}' must be numeric"}), 400

        # Students can only predict for themselves
        user = g.current_user
        if user["role"] == "student":
            data["student_id"] = user["linked_student_id"]

        prediction = predict_risk(data)
        merged     = {**data, **prediction["engineered_features"]}
        recs       = get_recommendations(merged, prediction["risk_level"])

        if "student_id" in data and data["student_id"]:
            update_student_prediction(
                data["student_id"],
                prediction["risk_level"],
                prediction["confidence"],
                ", ".join(recs["difficulty_types"]),
            )

        return jsonify({
            "success":         True,
            "prediction":      prediction,
            "recommendations": recs,
        }), 200

    except FileNotFoundError as exc:
        return jsonify({"error": str(exc), "hint": "Run: python ml/train_model.py"}), 503
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Prediction failed"}), 500


# ── Students ───────────────────────────────────────────────────────────────────
@api.route("/students", methods=["GET"])
@login_required
def students():
    try:
        user = g.current_user
        if user["role"] == "admin":
            df = get_all_students()
        elif user["role"] == "faculty":
            df = get_students_by_faculty(user["linked_faculty_id"])
        else:
            df = get_student_by_id(user["linked_student_id"])

        return jsonify({"success": True, "count": len(df),
                        "students": df.to_dict("records")}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch students"}), 500


@api.route("/students/<student_id>", methods=["GET"])
@login_required
def student_detail(student_id: str):
    try:
        user = g.current_user
        if user["role"] == "student" and user["linked_student_id"] != student_id:
            return jsonify({"error": "Access denied"}), 403

        df = get_student_by_id(student_id)
        if df.empty:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({"success": True, "student": df.to_dict("records")[0]}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch student"}), 500


# ── Upload ─────────────────────────────────────────────────────────────────────
@api.route("/upload_data", methods=["POST"])
@role_required("admin")
def upload_data():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename.lower().endswith(".csv"):
            return jsonify({"error": "Only .csv files accepted"}), 400

        path = os.path.join(ROOT, "data", "uploaded_students.csv")
        file.save(path)
        success = load_csv_to_db(path)
        if success:
            return jsonify({"success": True, "message": "Data uploaded and loaded"}), 200
        return jsonify({"error": "Failed to load data into database"}), 500
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Upload failed"}), 500


# ── Analytics ──────────────────────────────────────────────────────────────────
@api.route("/analytics", methods=["GET"])
@role_required("admin", "faculty")
def analytics():
    try:
        import pandas as pd
        user = g.current_user
        if user["role"] == "faculty":
            df    = get_students_by_faculty(user["linked_faculty_id"])
            total = len(df)
            vc    = df["risk_level"].value_counts() if "risk_level" in df.columns else pd.Series()
            summary = {
                "total_students":    total,
                "risk_distribution": [{"risk_level": k, "count": int(v)} for k, v in vc.items()],
                "avg_attendance":    round(float(df["attendance"].mean()), 2) if total else 0,
                "avg_score":         round(float(df["average_score"].mean()), 2) if total else 0,
            }
        else:
            summary = get_analytics_summary()

        return jsonify({
            "success":       True,
            "analytics":     summary,
            "model_metrics": get_model_metrics(),
        }), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch analytics"}), 500


# ── Improvement tracking ───────────────────────────────────────────────────────
@api.route("/track_improvement", methods=["POST"])
@login_required
def track_improvement():
    try:
        data     = request.get_json(force=True, silent=True) or {}
        required = ["student_id", "attendance", "average_score", "risk_level"]
        missing  = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        user = g.current_user
        if user["role"] == "student" and user["linked_student_id"] != data["student_id"]:
            return jsonify({"error": "Access denied"}), 403

        add_improvement_record(
            data["student_id"], float(data["attendance"]),
            float(data["average_score"]), data["risk_level"],
        )
        return jsonify({"success": True}), 201
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to record improvement"}), 500


@api.route("/improvement_history/<student_id>", methods=["GET"])
@login_required
def improvement_history(student_id: str):
    try:
        user = g.current_user
        if user["role"] == "student" and user["linked_student_id"] != student_id:
            return jsonify({"error": "Access denied"}), 403
        df = get_improvement_history(student_id)
        return jsonify({"success": True, "history": df.to_dict("records")}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch history"}), 500


# ── Admin-only ─────────────────────────────────────────────────────────────────
@api.route("/users", methods=["GET"])
@role_required("admin")
def list_users():
    try:
        users = get_all_users()
        return jsonify({"success": True, "count": len(users), "users": users}), 200
    except Exception:
        return jsonify({"error": "Failed to fetch users"}), 500


@api.route("/retrain", methods=["POST"])
@role_required("admin")
def retrain():
    try:
        sys.path.insert(0, ROOT)
        from ml.train_model import train_model
        _, _, metrics = train_model()
        return jsonify({
            "success": True,
            "message": "Model retrained successfully",
            "metrics": metrics,
        }), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Retraining failed"}), 500


# ── External Database ─────────────────────────────────────────────────────────
@api.route("/external_db/test", methods=["POST"])
@role_required("admin")
def external_db_test():
    """
    POST /external_db/test
    Body: { connection_string }
    Returns: { success, message, tables }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        conn_string = str(data.get("connection_string", "")).strip()

        if not conn_string:
            return jsonify({"error": "Connection string is required"}), 400

        result = ext_test_connection(conn_string)
        return jsonify(result), 200 if result["success"] else 400

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Connection test failed"}), 500


@api.route("/external_db/tables", methods=["POST"])
@role_required("admin")
def external_db_tables():
    """
    POST /external_db/tables
    Body: { connection_string, table (optional) }
    Returns: { success, tables } or { success, columns } if table specified
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        conn_string = str(data.get("connection_string", "")).strip()
        table = data.get("table")

        if not conn_string:
            return jsonify({"error": "Connection string is required"}), 400

        if table:
            # Get columns for specific table
            result = ext_get_columns(conn_string, table)
        else:
            # Get list of tables
            result = ext_get_tables(conn_string)

        return jsonify(result), 200 if result["success"] else 400

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch tables/columns"}), 500


@api.route("/external_db/load", methods=["POST"])
@role_required("admin")
def external_db_load():
    """
    POST /external_db/load
    Body: { connection_string, table }
    Returns: { success, message, rows_loaded }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        conn_string = str(data.get("connection_string", "")).strip()
        table = str(data.get("table", "")).strip()

        if not conn_string:
            return jsonify({"error": "Connection string is required"}), 400
        if not table:
            return jsonify({"error": "Table name is required"}), 400

        result = ext_load_data(conn_string, table)
        return jsonify(result), 200 if result["success"] else 400

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Failed to load data"}), 500
