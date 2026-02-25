# IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS

> **Final Year Engineering Project** — AI-powered Educational Analytics Platform

---

## Project Overview

This system uses **Machine Learning (Random Forest)** and a **rule-based Recommendation Engine** to:

- **Identify slow learners** from student assessment data
- **Classify students** into High Risk / Medium Risk / Low Risk
- **Detect learning difficulty types**: Attendance Issue, Conceptual Weakness, Practice Inconsistency, Performance Fluctuation
- **Recommend personalised remedial strategies** and innovative teaching methods
- **Track improvement** over time
- Provide an **interactive analytics dashboard** with professional charts

---

## Project Structure

```
slow_learner_detection/
│
├── backend/
│   ├── __init__.py          # Package init
│   ├── app.py               # Flask REST API (5 endpoints)
│   ├── model_handler.py     # ML model loading & prediction
│   ├── recommendation.py    # Rule-based recommendation engine
│   └── database.py          # SQLite persistence layer
│
├── frontend/
│   └── dashboard.py         # Streamlit dashboard (5 pages)
│
├── ml/
│   └── train_model.py       # Model training + evaluation + plots
│
├── data/
│   ├── generate_dataset.py  # Synthetic dataset generator
│   └── students.csv         # Generated after setup
│
├── models/                  # Auto-created after training
│   ├── random_forest_model.pkl
│   ├── label_encoder.pkl
│   └── metrics.json
│
├── static/                  # Auto-created after training
│   ├── confusion_matrix.png
│   └── feature_importance.png
│
├── setup.py                 # One-shot: generate data + train model
├── run_backend.py           # Flask API launcher
├── requirements.txt
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### Step 1 — Clone / Navigate to project

```bash
cd slow_learner_detection
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — One-shot setup (generate data + train model)

```bash
python setup.py
```

This will:
1. Generate `data/students.csv` with 500 synthetic student records
2. Train the Random Forest classifier
3. Save model artifacts in `models/`
4. Save evaluation plots in `static/`

### Step 4 — Start the Flask API (Terminal 1)

```bash
python run_backend.py
```

API will be available at: **http://localhost:5000**

### Step 5 — Start the Streamlit Dashboard (Terminal 2)

```bash
streamlit run frontend/dashboard.py
```

Dashboard will open at: **http://localhost:8501**

---

## Dataset

The synthetic dataset (`data/students.csv`) contains **500 student records** with:

| Column | Description |
|---|---|
| `student_id` | Unique identifier (STU0001 … STU0500) |
| `attendance` | Attendance percentage (%) |
| `assignment_score` | Average assignment score (0–100) |
| `internal_marks` | Internal examination marks (0–100) |
| `quiz_score` | Average quiz score (0–100) |
| `previous_semester_marks` | Previous semester marks (0–100) |
| `average_score` | *(engineered)* Mean of assignment, internal, quiz |
| `attendance_ratio` | *(engineered)* attendance / 100 |
| `performance_drop` | *(engineered)* previous_sem − average_score |
| `score_variance` | *(engineered)* variance of [assignment, internal, quiz] |
| `risk_level` | **Target**: High Risk / Medium Risk / Low Risk |

---

## Flask API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/predict` | Predict risk level for one student |
| `GET` | `/students` | Get all student records |
| `GET` | `/students/<id>` | Get a specific student |
| `POST` | `/upload_data` | Upload a CSV file |
| `GET` | `/analytics` | Analytics summary + model metrics |
| `POST` | `/track_improvement` | Log an improvement record |
| `GET` | `/improvement_history/<id>` | Get improvement timeline |

### Example `/predict` request

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "attendance": 55,
    "assignment_score": 42,
    "internal_marks": 38,
    "quiz_score": 45,
    "previous_semester_marks": 60
  }'
```

---

## Dashboard Pages

| Page | Description |
|---|---|
| 📊 **Dashboard** | Animated metric cards, risk pie chart, score comparison, scatter + histogram |
| 👨‍🎓 **Student Analysis** | Individual radar chart, score breakdown, filterable data table |
| 📈 **Analytics** | Model metrics, feature importance, confusion matrix, correlation heatmap |
| 📋 **Reports** | Class summary, improvement trend, high-risk priority list, CSV export |
| 🤖 **AI Prediction** | Live prediction with sliders, confidence bars, recommendations, innovative methods |

---

## Machine Learning

- **Algorithm**: Random Forest Classifier (200 estimators)
- **Features**: 9 (5 raw + 4 engineered)
- **Train/Test Split**: 80% / 20% (stratified)
- **Cross-Validation**: 5-fold
- **Output**: Risk level + confidence score + class probabilities
- **Artifacts**: `.pkl` model + `.json` metrics + PNG plots

---

## Recommendation Engine (Rule-Based)

| Condition | Difficulty Type | Remedial Action |
|---|---|---|
| Attendance < 60% | Attendance Issue | Attendance improvement plan, counselling |
| Internal / Quiz < 50 | Conceptual Weakness | Tutoring, micro-learning, concept maps |
| Assignment < 50 | Practice Inconsistency | Daily tracking, gamified challenges |
| Score variance > 300 or drop > 15 | Performance Fluctuation | Mock tests, stress management |
| High Risk overall | — | Intensive remedial programme, dedicated mentor |

---

## Technologies Used

| Category | Technology |
|---|---|
| Language | Python 3.10+ |
| Data | Pandas, NumPy |
| ML | Scikit-learn (Random Forest), Joblib |
| Backend API | Flask, Flask-CORS |
| Frontend | Streamlit |
| Charts | Plotly |
| Database | SQLite |
| Visualisation | Matplotlib, Seaborn |

---

*Final Year Project — AI-Powered Educational Analytics Platform*
