"""
Model Handler
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Loads the trained Random Forest and runs predictions with confidence scores.
"""

from __future__ import annotations
import json
import os
from typing import Any

import joblib
import numpy as np
import pandas as pd

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH   = os.path.join(BASE_DIR, "models", "random_forest_model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "models", "label_encoder.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "models", "metrics.json")

FEATURE_COLS = [
    "attendance", "assignment_score", "internal_marks", "quiz_score",
    "previous_semester_marks", "average_score", "attendance_ratio",
    "performance_drop", "score_variance",
]


def load_model() -> tuple:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at '{MODEL_PATH}'. Run: python ml/train_model.py"
        )
    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)


def engineer_features(data: dict[str, Any]) -> dict[str, Any]:
    att  = float(data.get("attendance", 0))
    asgn = float(data.get("assignment_score", 0))
    intm = float(data.get("internal_marks", 0))
    quiz = float(data.get("quiz_score", 0))
    prev = float(data.get("previous_semester_marks", 0))

    avg_score        = (asgn + intm + quiz) / 3
    attendance_ratio = att / 100
    perf_drop        = prev - avg_score
    score_variance   = float(np.var([asgn, intm, quiz]))

    return {
        **data,
        "average_score":    round(avg_score, 2),
        "attendance_ratio": round(attendance_ratio, 4),
        "performance_drop": round(perf_drop, 2),
        "score_variance":   round(score_variance, 2),
    }


def predict_risk(student_data: dict[str, Any]) -> dict[str, Any]:
    model, encoder = load_model()
    features = engineer_features(student_data)
    X = pd.DataFrame(
        [[features.get(col, 0.0) for col in FEATURE_COLS]],
        columns=FEATURE_COLS,
    )
    pred_enc     = model.predict(X)[0]
    probs        = model.predict_proba(X)[0]
    confidence   = float(np.max(probs))
    risk_level   = encoder.inverse_transform([pred_enc])[0]
    class_probs  = {
        cls: round(float(p), 4)
        for cls, p in zip(encoder.classes_, probs)
    }
    return {
        "risk_level":          risk_level,
        "confidence":          round(confidence, 4),
        "class_probabilities": class_probs,
        "engineered_features": {
            "average_score":    features["average_score"],
            "attendance_ratio": features["attendance_ratio"],
            "performance_drop": features["performance_drop"],
            "score_variance":   features["score_variance"],
        },
    }


def get_model_metrics() -> dict | None:
    if not os.path.exists(METRICS_PATH):
        return None
    with open(METRICS_PATH) as f:
        return json.load(f)
