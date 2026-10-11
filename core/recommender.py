import json
import os
from core import database as db


def get_study_plan(user_id: int) -> list:
    """
    Generate a personalized study plan based on user's test results.

    Returns a list of recommended subjects/topics with priority levels.
    """
    weak_areas = db.get_weak_areas(user_id, threshold=65.0)
    stats = db.get_user_stats(user_id)

    recommendations = []

    # Priority 1: Weakest areas (below 50%)
    for area in weak_areas:
        if area["avg_score"] < 50:
            recommendations.append({
                "subject": area["subject"],
                "priority": "High",
                "reason": f"Your average score is {area['avg_score']}% — needs focused attention.",
                "action": "Review lessons and take practice quizzes.",
            })
        else:
            recommendations.append({
                "subject": area["subject"],
                "priority": "Medium",
                "reason": f"Your average score is {area['avg_score']}% — room for improvement.",
                "action": "Practice with additional quizzes.",
            })

    # Priority 2: Subjects not yet tested
    tested_subjects = {s["subject"] for s in stats.get("by_subject", [])}
    all_subjects = ["Mathematics", "English / Language Arts", "Sciences",
                    "Social Studies / History", "Arts & Humanities",
                    "Technology & Business", "Foreign Languages",
                    "Health & Physical Education"]
    for subj in all_subjects:
        if subj not in tested_subjects:
            recommendations.append({
                "subject": subj,
                "priority": "Low",
                "reason": "You haven't tested this subject yet.",
                "action": "Take a test to assess your knowledge.",
            })

    # If no recommendations, suggest maintenance
    if not recommendations:
        recommendations.append({
            "subject": "General",
            "priority": "Low",
            "reason": "You're performing well across all tested subjects!",
            "action": "Keep practicing to maintain your skills.",
        })

    return recommendations


def get_lesson(subject_id: str) -> dict:
    """Load lesson content for a subject."""
    path = os.path.join("data", "lessons", f"{subject_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_available_lessons() -> list:
    """Get list of available lesson subjects."""
    lessons_dir = os.path.join("data", "lessons")
    lessons = []
    if os.path.exists(lessons_dir):
        for filename in os.listdir(lessons_dir):
            if filename.endswith(".json"):
                subject_id = filename[:-5]
                lesson = get_lesson(subject_id)
                if lesson:
                    lessons.append({
                        "id": subject_id,
                        "name": lesson.get("title", subject_id),
                        "description": lesson.get("description", ""),
                    })
    return lessons


def get_homework_quiz(subject_id: str, count: int = 5) -> list:
    """Generate a mini homework quiz from curriculum questions."""
    from core.loader import load_subject, pick_questions
    questions = load_subject(subject_id)
    if not questions:
        return []
    return pick_questions(questions, count)
