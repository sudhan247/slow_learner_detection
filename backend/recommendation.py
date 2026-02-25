"""
Recommendation Engine — Rule-Based
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Detects learning difficulty types and generates personalised remedial strategies.
"""

from __future__ import annotations
from typing import Any


def detect_difficulty_type(student_data: dict[str, Any]) -> list[str]:
    attendance       = student_data.get("attendance", 100)
    internal_marks   = student_data.get("internal_marks", 100)
    assignment_score = student_data.get("assignment_score", 100)
    quiz_score       = student_data.get("quiz_score", 100)
    score_variance   = student_data.get("score_variance", 0)
    performance_drop = student_data.get("performance_drop", 0)

    out: list[str] = []
    if attendance < 60:                              out.append("Attendance Issue")
    if internal_marks < 50 or quiz_score < 50:       out.append("Conceptual Weakness")
    if assignment_score < 50:                        out.append("Practice Inconsistency")
    if score_variance > 300 or abs(performance_drop) > 15:
        out.append("Performance Fluctuation")
    return out or ["General Improvement Needed"]


def get_recommendations(student_data: dict[str, Any], risk_level: str) -> dict[str, Any]:
    attendance       = student_data.get("attendance", 100)
    internal_marks   = student_data.get("internal_marks", 100)
    assignment_score = student_data.get("assignment_score", 100)
    quiz_score       = student_data.get("quiz_score", 100)
    score_variance   = student_data.get("score_variance", 0)
    performance_drop = student_data.get("performance_drop", 0)

    recommendations: list[dict] = []

    # Rule 1 — Attendance
    if attendance < 60:
        recommendations.append({
            "category": "Attendance Management",
            "priority": "Critical",
            "strategies": [
                "Enrol in immediate attendance improvement programme",
                "One-on-one counselling with academic mentor",
                "Flexible scheduling and make-up class support",
                "Peer buddy system for attendance accountability",
                "Parental / guardian engagement sessions",
            ],
            "resources": ["Student Support Centre", "Online lecture recordings", "Attendance app"],
        })
    elif attendance < 75:
        recommendations.append({
            "category": "Attendance Management",
            "priority": "High",
            "strategies": [
                "Bi-weekly attendance review with faculty",
                "Peer study group participation",
            ],
            "resources": ["Attendance tracking dashboard"],
        })

    # Rule 2 — Conceptual Weakness
    if internal_marks < 50 or quiz_score < 50:
        recommendations.append({
            "category": "Concept Reinforcement",
            "priority": "Critical",
            "strategies": [
                "Extra tutoring sessions (3x per week)",
                "Concept mapping and mind-mapping exercises",
                "Flipped classroom methodology",
                "Daily concept review micro-quizzes",
                "Video-based micro-learning modules",
            ],
            "resources": ["Khan Academy / NPTEL", "Anki flashcard decks", "PhET Simulations"],
        })
    elif internal_marks < 65:
        recommendations.append({
            "category": "Concept Reinforcement",
            "priority": "Medium",
            "strategies": ["Weekly concept review", "Practice problem sets with solutions"],
            "resources": ["Coursera / edX", "Topic revision worksheets"],
        })

    # Rule 3 — Practice Inconsistency
    if assignment_score < 50:
        recommendations.append({
            "category": "Practice Improvement Plan",
            "priority": "High",
            "strategies": [
                "Daily assignment tracking with accountability check-ins",
                "Gamified coding / problem challenges",
                "Step-by-step problem-solving workshops",
                "Scaffolded exercises with progressive difficulty",
            ],
            "resources": ["LeetCode / HackerRank", "Curated practice problem bank"],
        })

    # Rule 4 — Performance Fluctuation
    if score_variance > 300 or abs(performance_drop) > 15:
        recommendations.append({
            "category": "Performance Stabilisation",
            "priority": "High",
            "strategies": [
                "Bi-weekly mock test series",
                "Stress management and study-skills workshop",
                "Consistent daily study timetable",
                "Goal-setting sessions with academic counsellor",
            ],
            "resources": ["TestBook / Embibe", "Study planner template", "Academic counselling centre"],
        })

    # Global risk-level plan
    if risk_level == "High Risk":
        recommendations.append({
            "category": "Intensive Remedial Programme",
            "priority": "Critical",
            "strategies": [
                "Enrol in intensive remedial teaching programme immediately",
                "Assign dedicated academic mentor (weekly 1:1)",
                "Develop a custom adaptive learning path",
                "Multi-stakeholder weekly progress review",
            ],
            "resources": ["LMS (Moodle / Canvas)", "Individual Learning Plan (ILP)", "Adaptive tools"],
        })
    elif risk_level == "Medium Risk":
        recommendations.append({
            "category": "Targeted Support Plan",
            "priority": "Medium",
            "strategies": [
                "Bi-weekly academic progress monitoring",
                "Peer mentoring programme",
                "Subject-specific skill-building workshops",
            ],
            "resources": ["Supplementary reading lists", "Online practice test portal"],
        })
    else:
        recommendations.append({
            "category": "Excellence Enhancement",
            "priority": "Low",
            "strategies": [
                "Advanced elective modules",
                "Faculty-led research participation",
                "Peer-teaching and academic leadership roles",
                "National / international competition preparation",
            ],
            "resources": ["IEEE Xplore / ResearchGate", "Hackathons / GATE prep"],
        })

    return {
        "recommendations":    recommendations,
        "innovative_methods": _innovative_methods(risk_level),
        "difficulty_types":   detect_difficulty_type(student_data),
        "priority_action":    recommendations[0]["category"] if recommendations else "No action needed",
    }


def _innovative_methods(risk_level: str) -> list[dict]:
    if risk_level in ("High Risk", "Medium Risk"):
        return [
            {"method": "Adaptive Learning Technology",
             "description": "AI-powered personalised learning paths adjusting to student pace.",
             "tools": ["Khan Academy", "Smart Sparrow", "Coursera for Campus"]},
            {"method": "Gamification",
             "description": "Points, badges, and leaderboards to boost motivation.",
             "tools": ["Kahoot!", "Quizlet", "Classcraft"]},
            {"method": "Microlearning Modules",
             "description": "Bite-sized 5-10 minute focused lessons for better retention.",
             "tools": ["EdPuzzle", "Byte-sized videos", "Daily challenges"]},
            {"method": "Peer Learning Networks",
             "description": "Structured collaborative study groups with accountability partners.",
             "tools": ["Study buddy system", "Group project sprints", "Peer review"]},
        ]
    return [
        {"method": "Project-Based Learning",
         "description": "Real-world projects to deepen understanding and build portfolios.",
         "tools": ["GitHub", "Kaggle", "Hackathons"]},
        {"method": "Flipped Classroom",
         "description": "Pre-class video study; in-class collaborative problem solving.",
         "tools": ["YouTube EDU", "EdPuzzle", "Google Classroom"]},
        {"method": "Research Participation",
         "description": "Active involvement in faculty research for higher-order thinking.",
         "tools": ["IEEE Xplore", "Academia.edu", "ResearchGate"]},
    ]
