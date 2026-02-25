"""
Flask Application Factory
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
"""

from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask
from flask_cors import CORS

from backend.database import init_db, load_csv_to_db, create_default_users
from backend.routes   import api


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "eduai-flask-secret-2024")
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.register_blueprint(api)
    return app


# ── One-time initialisation on import ─────────────────────────────────────────
init_db()
create_default_users()
load_csv_to_db(os.path.join(ROOT, "data", "students.csv"))

app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting Flask API on http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
