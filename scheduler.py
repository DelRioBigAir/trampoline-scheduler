
import sqlite3
import hashlib
import os

DB_NAME = "database.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================
# PASSWORD HELPERS
# =========================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


# =========================
# DATABASE SETUP (FORCE SCHEMA)
# =========================

def setup_database():
    conn = get_connection()
    c = conn.cursor()

    # Drop users table to guarantee correct schema
    c.execute("DROP TABLE IF EXISTS users")

    c.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        employee_id INTEGER,
        role TEXT,
        must_change_password INTEGER DEFAULT 1,
        failed_attempts INTEGER DEFAULT 0,
        locked INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# =========================
# USER FUNCTIONS
# =========================

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    user = c.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    return user


def update_password(user_id, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET password = ?,
            must_change_password = 0,
            failed_attempts = 0,
            locked = 0
        WHERE id = ?
    """, (hash_password(new_password), user_id))
    conn.commit()
    conn.close()


def add_admin_user():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO users (username, password, employee_id, role)
        VALUES (?, ?, ?, ?)
    """, (
        "adminuser",
        hash_password("changeme123"),
        1,
        "admin"
    ))

    conn.commit()
    conn.close()
