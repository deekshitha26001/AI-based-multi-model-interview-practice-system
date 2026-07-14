"""
database.py
Handles SQLite connection and table creation for the Interview Practice System.
Simple, single-file database layer — no ORM used, to keep the project easy to understand.
"""

import sqlite3
from datetime import datetime

DB_NAME = "interview_system.db"


def get_connection():
    """
    Creates and returns a new SQLite connection.
    check_same_thread=False allows FastAPI (which is multi-threaded) to use SQLite safely.
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, like a dictionary
    return conn


def init_db():
    """
    Creates all required tables if they don't already exist.
    Called once when the FastAPI app starts up.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 2. INTERVIEW SESSIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            interview_type TEXT NOT NULL,       -- HR / Technical / Behavioral
            resume_text TEXT,                   -- optional, extracted resume content
            status TEXT DEFAULT 'in_progress',  -- in_progress / completed
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # 3. QUESTIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_number INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
        )
    """)

    # 4. ANSWERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT,                   -- transcribed text from Whisper
            voice_metrics TEXT,                 -- JSON string: clarity, speed, pauses
            face_metrics TEXT,                  -- JSON string: eye contact, smile, emotions
            created_at TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
    """)

    # 5. SCORES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            overall_score REAL NOT NULL,
            communication_score REAL NOT NULL,
            technical_score REAL NOT NULL,
            confidence_score REAL NOT NULL,
            strengths TEXT,                     -- JSON list stored as string
            weaknesses TEXT,                    -- JSON list stored as string
            suggestions TEXT,                   -- JSON list stored as string
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


def get_timestamp():
    """Utility function to get current time as a string, used across the app."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
