"""
Dataset Generator
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Generates a realistic synthetic student dataset with faculty_id assignment.
"""

import os
import numpy as np
import pandas as pd


def generate_dataset(n_students: int = 500, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)

    student_ids = [f"STU{str(i).zfill(4)}" for i in range(1, n_students + 1)]

    # Assign faculty: first half -> FAC001, second half -> FAC002
    faculty_ids = [
        "FAC001" if i <= n_students // 2 else "FAC002"
        for i in range(1, n_students + 1)
    ]

    attendance            = np.random.normal(72, 18, n_students).clip(20, 100)
    assignment_score      = np.random.normal(65, 18, n_students).clip(0, 100)
    internal_marks        = np.random.normal(60, 15, n_students).clip(0, 100)
    quiz_score            = np.random.normal(62, 17, n_students).clip(0, 100)
    previous_semester_marks = np.random.normal(63, 16, n_students).clip(0, 100)

    average_score     = (assignment_score + internal_marks + quiz_score) / 3
    attendance_ratio  = attendance / 100
    performance_drop  = previous_semester_marks - average_score
    score_variance    = np.array([
        np.var([assignment_score[i], internal_marks[i], quiz_score[i]])
        for i in range(n_students)
    ])

    risk_scores = np.zeros(n_students)
    risk_scores += np.where(attendance < 60, 3, np.where(attendance < 75, 1, 0))
    risk_scores += np.where(average_score < 45, 3, np.where(average_score < 60, 1, 0))
    risk_scores += np.where(performance_drop > 15, 2, np.where(performance_drop > 5, 1, 0))
    risk_scores += np.where(score_variance > 300, 1, 0)

    risk_level = np.where(
        risk_scores >= 5, "High Risk",
        np.where(risk_scores >= 2, "Medium Risk", "Low Risk")
    )

    df = pd.DataFrame({
        "student_id":               student_ids,
        "faculty_id":               faculty_ids,
        "attendance":               np.round(attendance, 1),
        "assignment_score":         np.round(assignment_score, 1),
        "internal_marks":           np.round(internal_marks, 1),
        "quiz_score":               np.round(quiz_score, 1),
        "previous_semester_marks":  np.round(previous_semester_marks, 1),
        "average_score":            np.round(average_score, 2),
        "attendance_ratio":         np.round(attendance_ratio, 3),
        "performance_drop":         np.round(performance_drop, 2),
        "score_variance":           np.round(score_variance, 2),
        "risk_level":               risk_level,
    })
    return df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = generate_dataset(500)
    df.to_csv(os.path.join("data", "students.csv"), index=False)
    print(f"Dataset generated: {len(df)} students")
    print(df["risk_level"].value_counts().to_string())
    print(df["faculty_id"].value_counts().to_string())
