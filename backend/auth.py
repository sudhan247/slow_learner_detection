"""
Authentication Module — JWT-based
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Handles token generation, verification, and route protection decorators.
"""

from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, g

SECRET_KEY     = os.environ.get("JWT_SECRET", "eduai-slow-learner-jwt-secret-2024")
TOKEN_HOURS    = 8
ALGORITHM      = "HS256"


# ── Token helpers ──────────────────────────────────────────────────────────────
def generate_token(user: dict) -> str:
    """Create a signed JWT for the authenticated user."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id":           user["id"],
        "username":          user["username"],
        "role":              user["role"],
        "linked_student_id": user.get("linked_student_id"),
        "linked_faculty_id": user.get("linked_faculty_id"),
        "iat":               now,
        "exp":               now + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns the payload dict or None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _extract_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


# ── Decorators ─────────────────────────────────────────────────────────────────
def login_required(f):
    """Allow any authenticated user."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token   = _extract_token()
        if not token:
            return jsonify({"error": "Authentication required", "code": "MISSING_TOKEN"}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token", "code": "INVALID_TOKEN"}), 401
        g.current_user = payload
        return f(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles: str):
    """Allow only users whose role is in allowed_roles."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token   = _extract_token()
            if not token:
                return jsonify({"error": "Authentication required"}), 401
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            if payload["role"] not in allowed_roles:
                return jsonify({
                    "error": f"Access denied. Allowed roles: {list(allowed_roles)}"
                }), 403
            g.current_user = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator
