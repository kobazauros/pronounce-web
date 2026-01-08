from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from models import User, db

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Please check your login details and try again.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=remember)
        return redirect(url_for("index"))

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Fetch the code from config to pass to template and check in POST
    teacher_code = current_app.config.get("TEACHER_INVITE_CODE", "MCU-2024-PRO")

    if request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        student_id = request.form.get("student_id")
        password = request.form.get("password")
        consent = request.form.get("consent")
        invite_code = request.form.get("invite_code")

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Check Role
        role = "student"
        is_teacher = False
        if invite_code and invite_code.strip() == teacher_code:
            role = "teacher"
            is_teacher = True

        # Validation: Only students are strictly required to provide a tickmark
        if not is_teacher and not consent:
            flash(
                "Students must consent to data collection to use this tool.", "warning"
            )
            return redirect(url_for("auth.register"))

        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            student_id=student_id if role == "student" else None,
            role=role,
            # Consent is recorded as "system-bypassed" or timestamp for students
            consented_at=datetime.now(timezone.utc),
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        if role == "teacher":
            flash(
                "Instructor account created! No student ID or consent required.",
                "success",
            )
        else:
            flash("Student registration successful!", "success")

        return redirect(url_for("auth.login"))

    # Pass the code to the template for the real-time UI "disappearing" act
    return render_template("register.html", teacher_code=teacher_code)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
