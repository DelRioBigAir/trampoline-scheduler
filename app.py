
from flask import Flask, render_template, redirect, request, session
import scheduler
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback")

scheduler.setup_database()


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = scheduler.get_connection().cursor().execute(
            "SELECT * FROM users WHERE username = %s", (username,)
        )

        user = scheduler.get_connection().cursor().fetchone()

        if not user:
            return "Invalid login"

        if user[7] == 1:
            return "Account locked."

        if scheduler.verify_password(password, user[2]):
            session["user_id"] = user[0]
            session["role"] = user[4]
            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    employees = scheduler.get_all_employees()
    users = scheduler.get_all_users()

    return render_template("admin_dashboard.html",
                           employees=employees,
                           users=users)


@app.route("/add_employee", methods=["POST"])
def add_employee():
    name = request.form["name"]
    max_hours = request.form["max_hours"]
    roles = request.form.getlist("roles")

    scheduler.add_employee(name, max_hours, roles)
    return redirect("/dashboard")


@app.route("/deactivate/<int:employee_id>")
def deactivate(employee_id):
    scheduler.deactivate_employee(employee_id)
    return redirect("/dashboard")


@app.route("/reset_password/<int:user_id>")
def reset_password(user_id):
    scheduler.reset_user_password(user_id)
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run()
