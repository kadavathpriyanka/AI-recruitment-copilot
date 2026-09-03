import sqlite3
import json
import pandas as pd
from datetime import datetime

DB_PATH = "data/recruitment.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            education TEXT,
            skills TEXT,
            experience TEXT,
            certifications TEXT,
            uploaded_by TEXT,
            created_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            required_skills TEXT,
            required_experience_years INTEGER,
            required_education TEXT,
            raw_text TEXT,
            created_by TEXT,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_candidate(candidate, uploaded_by):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO candidates (name, email, phone, education, skills, experience, certifications, uploaded_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate.get("name"),
        candidate.get("email"),
        candidate.get("phone"),
        json.dumps(candidate.get("education", [])),
        json.dumps(candidate.get("skills", [])),
        json.dumps(candidate.get("experience", [])),
        json.dumps(candidate.get("certifications", [])),
        uploaded_by,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_all_candidates():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM candidates ORDER BY id ASC", conn)
    conn.close()

    for col in ["education", "skills", "experience", "certifications"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.loads(x) if x else [])

    return df

def clear_all_candidates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    conn.commit()
    conn.close()

def insert_job(job, created_by):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (title, required_skills, required_experience_years, required_education, raw_text, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("title"),
        json.dumps(job.get("required_skills", [])),
        job.get("required_experience_years", 0),
        json.dumps(job.get("required_education", [])),
        job.get("raw_text", ""),
        created_by,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_all_jobs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM jobs ORDER BY id DESC", conn)
    conn.close()

    for col in ["required_skills", "required_education"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.loads(x) if x else [])

    return df