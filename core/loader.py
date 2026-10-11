import json
import os
import random

COGNITIVE_DOMAINS = ["verbal", "numerical", "logical", "spatial"]
COGNITIVE_TIERS = ["beginner", "intermediate", "advanced"]


# ---------- COGNITIVE ----------

def load_cognitive(domain: str, tier: str) -> list:
    """Load questions for a specific cognitive domain + tier."""
    path = os.path.join("data", "cognitive", f"{domain}_{tier}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def load_cognitive_pool(domain: str, tier: str = "all") -> list:
    """
    Load cognitive questions for a domain.
    If tier='all', merges beginner + intermediate + advanced.
    """
    if tier == "all":
        pool = []
        for t in COGNITIVE_TIERS:
            pool.extend(load_cognitive(domain, t))
        return pool
    return load_cognitive(domain, tier)


# ---------- CURRICULUM ----------

def load_subjects() -> list:
    path = os.path.join("data", "curriculum", "subjects.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)["subjects"]
    except FileNotFoundError:
        return []


def load_topic(subject_id: str, topic_id: str) -> list:
    path = os.path.join("data", "curriculum", subject_id, f"{topic_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def load_subject(subject_id: str) -> list:
    subjects = load_subjects()
    subject = next((s for s in subjects if s["id"] == subject_id), None)
    if subject is None:
        return []
    pool = []
    for topic in subject["topics"]:
        pool.extend(load_topic(subject_id, topic["id"]))
    return pool


def load_onboarding_pretest() -> list:
    """Load the onboarding pretest questions."""
    path = os.path.join("data", "onboarding", "pretest.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def load_pretest(per_subject: int = 10) -> list:
    """
    Load `per_subject` random questions from each subject.
    Tags each question with its subject name so results can be grouped.
    """
    subjects = load_subjects()
    pool = []

    for subject in subjects:
        subject_questions = load_subject(subject["id"])
        if not subject_questions:
            continue
        sample_size = min(per_subject, len(subject_questions))
        picked = random.sample(subject_questions, sample_size)

        for q in picked:
            q = dict(q)  # copy so we don't mutate the cached list
            q["_subject_id"] = subject["id"]
            q["_subject_name"] = subject["name"]
            pool.append(q)

    random.shuffle(pool)
    return pool


# ---------- SHARED ----------

def load_eq_assessment() -> list:
    """Load EQ assessment questions."""
    path = os.path.join("data", "emotional", "eq_assessment.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def load_licensure_exams() -> list:
    """Load licensure exam categories."""
    path = os.path.join("data", "licensure", "exams.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("exams", []) if isinstance(data, dict) else []
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def load_licensure_exam(exam_id: str) -> list:
    """Load questions for a specific licensure exam."""
    path = os.path.join("data", "licensure", f"{exam_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def pick_questions(pool: list, count: int) -> list:
    """Randomly pick `count` questions from a pool. If pool is smaller, return all."""
    if count >= len(pool):
        return pool[:]
    return random.sample(pool, count)