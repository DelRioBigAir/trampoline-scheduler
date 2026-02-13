
import os
import psycopg2
import hashlib

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# =========================
# PASSWORD HELPERS
# =========================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


# =========================
# DATABASE SETUP
# =========================

def setup_database():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        max_hours INTEGER,
        active BOOLEAN DEFAULT TRUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS employee_roles (
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        role TEXT,
        must_change_password INTEGER DEFAULT 1,
        failed_attempts INTEGER DEFAULT 0,
        locked INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# =========================
# EMPLOYEE MANAGEMENT
# =========================

def add_employee(name, max_hours, role_names):
    conn = get_connection()
    c = conn.cursor()

    c.execute("INSERT INTO employees (name, max_hours) VALUES (%s, %s) RETURNING id",
              (name, max_hours))
    employee_id = c.fetchone()[0]

    for role_name in role_names:
        c.execute("INSERT INTO roles (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                  (role_name,))
        c.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
        role_id = c.fetchone()[0]

        c.execute("INSERT INTO employee_roles (employee_id, role_id) VALUES (%s, %s)",
                  (employee_id, role_id))

    username = name.lower().replace(" ", "")
    default_password = hash_password("changeme123")

    c.execute("""
        INSERT INTO users (username, password, employee_id, role)
        VALUES (%s, %s, %s, %s)
    """, (username, default_password, employee_id, "employee"))

    conn.commit()
    conn.close()


def get_all_employees():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, max_hours, active
        FROM employees
        ORDER BY name
    """)

    employees = c.fetchall()
    conn.close()
    return employees


def deactivate_employee(employee_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE employees SET active = FALSE WHERE id = %s", (employee_id,))
    conn.commit()
    conn.close()


def reset_user_password(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET password = %s,
            must_change_password = 1,
            failed_attempts = 0,
            locked = 0
        WHERE id = %s
    """, (hash_password("changeme123"), user_id))

    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, username, role, locked
        FROM users
        ORDER BY username
    """)
    users = c.fetchall()
    conn.close()
    return users
