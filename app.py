
from flask import Flask, render_template, redirect, request, session
import scheduler

app = Flask(__name__)
app.secret_key = "super_secret_key"

scheduler.setup_database()


# =============================
# LOGIN
# =============================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = scheduler.get_user(username)

        if not user:
            return "Invalid login"

        if user[8] == 1:
            return "Account locked. Contact admin."

        if scheduler.verify_password(password, user[2]):
            scheduler.reset_failed_attempts(user[0])

            session["user_id"] = user[0]
            session["employee_id"] = user[3]
            session["role"] = user[4]

            if user[5] == 1:
                return redirect("/change_password")

            return redirect("/dashboard")

        scheduler.record_failed_login(user[0])
        return "Invalid login"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =============================
# CHANGE PASSWORD
# =============================

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_password = request.form["new_password"]
        scheduler.update_password(session["user_id"], new_password)
        return redirect("/dashboard")

    return render_template("change_password.html")


# =============================
# DASHBOARD
# =============================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html", role=session["role"])


# =============================
# ADMIN PANEL
# =============================

@app.route("/admin/users")
def admin_users():
    if "role" not in session or session["role"] != "admin":
        return "Access denied"

    users = scheduler.get_all_users()
    return render_template("admin_users.html", users=users)


@app.route("/admin/reset_password/<int:user_id>")
def admin_reset_password(user_id):
    if "role" not in session or session["role"] != "admin":
        return "Access denied"

    scheduler.admin_reset_password(user_id)
    return redirect("/admin/users")


if __name__ == "__main__":
    app.run(debug=True)
