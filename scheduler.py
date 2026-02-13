
import sqlite3
import hashlib

DB_NAME = "database.db"
MAX_FAILED_ATTEMPTS = 5


# =====================================================
# PASSWORD HELPERS
# =====================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


# =====================================================
# DATABASE SETUP
# =====================================================

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        max_hours INTEGER,
        hours_assigned REAL DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS employee_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
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


# =====================================================
# USER FUNCTIONS
# =====================================================

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    user = c.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    return user


def record_failed_login(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        UPDATE users 
        SET failed_attempts = failed_attempts + 1
        WHERE id = ?
    """, (user_id,))

    c.execute("""
        SELECT failed_attempts FROM users WHERE id = ?
    """, (user_id,))
    attempts = c.fetchone()[0]

    if attempts >= MAX_FAILED_ATTEMPTS:
        c.execute("""
            UPDATE users SET locked = 1 WHERE id = ?
        """, (user_id,))

    conn.commit()
    conn.close()


def reset_failed_attempts(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        UPDATE users 
        SET failed_attempts = 0 
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def update_password(user_id, new_password):
    conn = sqlite3.connect(DB_NAME)
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


def admin_reset_password(user_id):
    default_password = "changeme123"
    update_password(user_id, default_password)


# =====================================================
# EMPLOYEE FUNCTIONS
# =====================================================

def add_employee(name, max_hours, roles):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "INSERT INTO employees (name, max_hours) VALUES (?, ?)",
        (name, max_hours)
    )

    employee_id = c.lastrowid

    for role in roles:
        c.execute(
            "INSERT INTO employee_roles (employee_id, role) VALUES (?, ?)",
            (employee_id, role)
        )

    username = name.lower().replace(" ", "")
    default_password = "changeme123"

    c.execute("""
        INSERT INTO users 
        (username, password, employee_id, role, must_change_password)
        VALUES (?, ?, ?, ?, 1)
    """, (username, hash_password(default_password), employee_id, "employee"))

    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    users = c.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users
