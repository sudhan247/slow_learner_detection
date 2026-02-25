"""
Model Training Script
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Trains a Random Forest classifier on student data and saves the model artifacts.
"""

import os
import sys
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "data",   "students.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "models")
STATIC_DIR = os.path.join(BASE_DIR, "static")

FEATURE_COLS = [
    'attendance', 'assignment_score', 'internal_marks', 'quiz_score',
    'previous_semester_marks', 'average_score', 'attendance_ratio',
    'performance_drop', 'score_variance'
]


def ensure_dirs():
    for d in [MODEL_DIR, STATIC_DIR]:
        os.makedirs(d, exist_ok=True)


def load_data():
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Dataset not found at {DATA_PATH}")
        print("        Run:  python data/generate_dataset.py")
        sys.exit(1)
    df = pd.read_csv(DATA_PATH)
    print(f"[INFO]  Loaded {len(df)} records from {DATA_PATH}")
    return df


def train_model():
    ensure_dirs()

    # ── Load data ──────────────────────────────────────────────────────────────
    df = load_data()

    X = df[FEATURE_COLS]
    y = df['risk_level']

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # ── Train / test split ─────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
    )

    # ── Train Random Forest ────────────────────────────────────────────────────
    print("[INFO]  Training Random Forest classifier …")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    rf.fit(X_train, y_train)

    # ── Evaluation ─────────────────────────────────────────────────────────────
    y_pred = rf.predict(X_test)

    accuracy  = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall    = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1        = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    cv_scores = cross_val_score(rf, X, y_enc, cv=5, scoring='accuracy')

    print("\n" + "=" * 55)
    print("  MODEL TRAINING RESULTS")
    print("=" * 55)
    print(f"  Accuracy      : {accuracy:.4f}")
    print(f"  Precision     : {precision:.4f}")
    print(f"  Recall        : {recall:.4f}")
    print(f"  F1-Score      : {f1:.4f}")
    print(f"  CV Accuracy   : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # ── Save model artifacts ───────────────────────────────────────────────────
    joblib.dump(rf, os.path.join(MODEL_DIR, "random_forest_model.pkl"))
    joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder.pkl"))

    metrics = {
        'accuracy':      float(accuracy),
        'precision':     float(precision),
        'recall':        float(recall),
        'f1_score':      float(f1),
        'cv_mean':       float(cv_scores.mean()),
        'cv_std':        float(cv_scores.std()),
        'classes':       le.classes_.tolist(),
        'feature_names': FEATURE_COLS,
    }
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # ── Confusion Matrix plot ──────────────────────────────────────────────────
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=le.classes_, yticklabels=le.classes_,
        ax=ax, linewidths=0.5
    )
    ax.set_title('Confusion Matrix — Random Forest', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('True Label', fontsize=11)
    ax.set_xlabel('Predicted Label', fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, "confusion_matrix.png"), dpi=150, bbox_inches='tight')
    plt.close()

    # ── Feature Importance plot ────────────────────────────────────────────────
    feat_imp = pd.DataFrame({
        'feature':    FEATURE_COLS,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=True)

    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(feat_imp)))
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(feat_imp['feature'], feat_imp['importance'], color=colors)
    ax.set_title('Feature Importance — Random Forest', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Importance Score', fontsize=11)
    for bar, val in zip(bars, feat_imp['importance']):
        ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                f'{val:.3f}', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, "feature_importance.png"), dpi=150, bbox_inches='tight')
    plt.close()

    print("\n[DONE]  Artifacts saved:")
    print(f"         Model   -> {MODEL_DIR}/random_forest_model.pkl")
    print(f"         Encoder -> {MODEL_DIR}/label_encoder.pkl")
    print(f"         Metrics -> {MODEL_DIR}/metrics.json")
    print(f"         Plots   -> {STATIC_DIR}/")

    return rf, le, metrics


if __name__ == "__main__":
    train_model()
