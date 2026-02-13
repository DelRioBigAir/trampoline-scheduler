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

        user = scheduler.get_user(username)

        if not user:
            return "Invalid login"

        # Safely check locked column (index 7 now)
        if len(user) > 7 and user[7] == 1:
            return "Account locked. Contact admin."

        if scheduler.verify_password(password, user[2]):
            session["user_id"] = user[0]
            session["role"] = user[4]

            if user[5] == 1:
                return redirect("/change_password")

            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_password = request.form["new_password"]
        scheduler.update_password(session["user_id"], new_password)
        return redirect("/dashboard")

    return render_template("change_password.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return "Dashboard Loaded Successfully"


if __name__ == "__main__":
    app.run()
