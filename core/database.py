import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join("data", "study_app.db")


def _get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database, creating it if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize the database schema. Safe to call multiple times."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            test_type TEXT NOT NULL,
            subject TEXT,
            score REAL NOT NULL,
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            duration_seconds INTEGER,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT NOT NULL,
            topic TEXT,
            completed INTEGER DEFAULT 0,
            last_score REAL,
            last_attempted TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------- USER OPERATIONS ----------

def _hash_password(password: str) -> str:
    """Simple password hashing for local storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(name: str, email: str = None, password: str = None) -> dict:
    """Create a new user and return the user dict."""
    conn = _get_connection()
    cursor = conn.cursor()
    password_hash = _hash_password(password) if password else None

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        user = get_user(user_id)
        conn.close()
        return user
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user(user_id: int) -> dict:
    """Get a user by ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_user_by_email(email: str) -> dict:
    """Get a user by email."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def login_user(email: str, password: str) -> dict:
    """Authenticate a user by email and password."""
    user = get_user_by_email(email)
    if user and user.get("password_hash") == _hash_password(password):
        return user
    return None


def update_user_name(user_id: int, name: str):
    """Update a user's display name."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    conn.close()


# ---------- TEST RESULTS ----------

def save_test_result(user_id: int, test_type: str, subject: str,
                     correct: int, total: int, score: float,
                     duration_seconds: int = None, details: str = None):
    """Save a test result to the database."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO test_results
           (user_id, test_type, subject, score, correct, total, duration_seconds, details)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, test_type, subject, score, correct, total, duration_seconds, details)
    )
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    return result_id


def get_user_test_results(user_id: int, limit: int = 50) -> list:
    """Get recent test results for a user."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM test_results
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_test_results_by_type(user_id: int, test_type: str) -> list:
    """Get test results filtered by type."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM test_results
           WHERE user_id = ? AND test_type = ?
           ORDER BY created_at DESC""",
        (user_id, test_type)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- STATISTICS ----------

def get_user_stats(user_id: int) -> dict:
    """Get aggregated statistics for a user."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Total tests
    cursor.execute(
        "SELECT COUNT(*) as count FROM test_results WHERE user_id = ?",
        (user_id,)
    )
    total_tests = cursor.fetchone()["count"]

    # Average score
    cursor.execute(
        "SELECT AVG(score) as avg_score FROM test_results WHERE user_id = ?",
        (user_id,)
    )
    avg_score = cursor.fetchone()["avg_score"] or 0.0

    # Best score
    cursor.execute(
        "SELECT MAX(score) as best_score FROM test_results WHERE user_id = ?",
        (user_id,)
    )
    best_score = cursor.fetchone()["best_score"] or 0.0

    # Scores by subject
    cursor.execute(
        """SELECT subject, AVG(score) as avg_score, COUNT(*) as test_count
           FROM test_results
           WHERE user_id = ?
           GROUP BY subject
           ORDER BY avg_score ASC""",
        (user_id,)
    )
    by_subject = [dict(r) for r in cursor.fetchall()]

    # Scores by type
    cursor.execute(
        """SELECT test_type, AVG(score) as avg_score, COUNT(*) as test_count
           FROM test_results
           WHERE user_id = ?
           GROUP BY test_type
           ORDER BY avg_score ASC""",
        (user_id,)
    )
    by_type = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "total_tests": total_tests,
        "average_score": round(avg_score, 1),
        "best_score": round(best_score, 1),
        "by_subject": by_subject,
        "by_type": by_type,
    }


def get_weak_areas(user_id: int, threshold: float = 60.0) -> list:
    """Get subjects/topics where the user scored below the threshold."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT subject, AVG(score) as avg_score, COUNT(*) as test_count
           FROM test_results
           WHERE user_id = ?
           GROUP BY subject
           HAVING avg_score < ?
           ORDER BY avg_score ASC""",
        (user_id, threshold)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- PROGRESS ----------

def update_progress(user_id: int, subject: str, topic: str = None,
                    score: float = None):
    """Update or create a progress entry for a subject/topic."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Check if entry exists
    cursor.execute(
        """SELECT id FROM progress
           WHERE user_id = ? AND subject = ? AND (topic IS ? OR topic = ?)""",
        (user_id, subject, topic, topic)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """UPDATE progress
               SET completed = completed + 1,
                   last_score = ?,
                   last_attempted = datetime('now')
               WHERE id = ?""",
            (score, existing["id"])
        )
    else:
        cursor.execute(
            """INSERT INTO progress (user_id, subject, topic, completed, last_score)
               VALUES (?, ?, ?, 1, ?)""",
            (user_id, subject, topic, score)
        )

    conn.commit()
    conn.close()


def get_user_progress(user_id: int) -> list:
    """Get all progress entries for a user."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM progress
           WHERE user_id = ?
           ORDER BY last_attempted DESC""",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- PREFERENCES ----------

def set_preference(user_id: int, key: str, value: str):
    """Set a user preference."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO preferences (user_id, key, value)
           VALUES (?, ?, ?)""",
        (user_id, key, value)
    )
    conn.commit()
    conn.close()


def get_preference(user_id: int, key: str) -> str:
    """Get a user preference."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT value FROM preferences WHERE user_id = ? AND key = ?",
        (user_id, key)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return None


# ---------- CSV EXPORT ----------

def export_results_to_csv(user_id: int, filename: str = None):
    """Export test results to a CSV file."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results_{timestamp}.csv"

    filepath = os.path.join("results", filename)
    os.makedirs("results", exist_ok=True)

    results = get_user_test_results(user_id)
    if not results:
        return None

    with open(filepath, "w", encoding="utf-8") as f:
        # Header
        f.write("Date,Test Type,Subject,Score,Correct,Total,Duration\n")
        for r in results:
            duration = r.get("duration_seconds") or ""
            f.write(f"{r['created_at']},{r['test_type']},{r.get('subject', '')},"
                    f"{r['score']},{r['correct']},{r['total']},{duration}\n")

    return filepath


# Initialize on import
init_db()
