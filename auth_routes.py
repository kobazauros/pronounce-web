from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from models import SystemConfig, User, InviteCode, db

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect them away from login page,
    # UNLESS maintenance mode is active, in which case they may need to re-login as admin.
    if current_user.is_authenticated and not SystemConfig.get_bool("maintenance_mode"):
        if current_user.role == "admin":
            return redirect(url_for("dashboards.admin_dashboard"))
        elif current_user.role == "teacher":
            return redirect(url_for("dashboards.teacher_dashboard"))
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Please check your login details and try again.", "danger")
            return redirect(url_for("auth.login"))

        # If maintenance mode is on, show maintenance page to non-admins trying to log in.
        if SystemConfig.get_bool("maintenance_mode") and user.role != "admin":
            return render_template("maintenance.html"), 503

        login_user(user, remember=remember)
        current_app.logger.info(f"User '{user.username}' logged in successfully.")

        if user.role == "admin":
            return redirect(url_for("dashboards.admin_dashboard"))
        elif user.role == "teacher":
            return redirect(url_for("dashboards.teacher_dashboard"))

        return redirect(url_for("index"))

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Check if registration is open
    if not SystemConfig.get_bool("registration_open", default=True):
        flash("New user registration is currently closed by the administrator.", "info")
        return redirect(url_for("auth.login"))

    # Fetch the code from config to pass to template and check in POST
    # teacher_code = current_app.config.get("TEACHER_INVITE_CODE", "MCU-2024-PRO")

    if request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        student_id = request.form.get("student_id")
        password = request.form.get("password")
        consent = request.form.get("consent")
        invite_code = request.form.get("invite_code")

        if not first_name or not last_name or not username or not password:
            flash(
                "All fields (First Name, Last Name, Username, Password) are mandatory.",
                "danger",
            )
            return redirect(url_for("auth.register"))

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Helper to validate student ID format
        def is_valid_student_id(sid):
            return sid and len(sid) == 10 and sid.isdigit()

        # Check Role & Validate Logic
        role = "student"
        invite_record = None

        if invite_code and invite_code.strip():
            # Attempting to register as teacher
            code_str = invite_code.strip().upper()
            invite_record = InviteCode.query.filter_by(
                code=code_str, is_used=False
            ).first()

            if not invite_record:
                flash("Invalid or already used invite code.", "danger")
                return redirect(url_for("auth.register"))

            role = "teacher"

        # Student specific validation
        if role == "student":
            if not student_id:
                flash("Student ID is mandatory for students.", "danger")
                return redirect(url_for("auth.register"))

            if not is_valid_student_id(student_id):
                flash("Student ID must be exactly 10 digits.", "danger")
                return redirect(url_for("auth.register"))

            # Check uniqueness
            if User.query.filter_by(student_id=student_id).first():
                flash("A user with this Student ID is already registered.", "danger")
                return redirect(url_for("auth.register"))

            if not consent:
                flash("Students must consent to data collection.", "warning")
                return redirect(url_for("auth.register"))

        final_student_id = student_id if role == "student" else None

        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            student_id=final_student_id,
            role=role,
            # Consent is recorded as "system-bypassed" or timestamp for students
            consented_at=datetime.now(timezone.utc),
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)

            # If teacher, mark invite as used
            if role == "teacher" and invite_record:
                # We need to flush first to get the new_user.id
                db.session.flush()
                invite_record.is_used = True
                invite_record.used_by_user_id = new_user.id
                invite_record.used_at = datetime.now(timezone.utc)

            db.session.commit()
            current_app.logger.info(
                f"New user registered: '{username}' with role '{role}'."
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during user registration: {e}")
            flash(
                "A server error occurred during registration. Please try again later.",
                "danger",
            )
            return redirect(url_for("auth.register"))

        if role == "teacher":
            flash(
                "Instructor account created! No student ID or consent required.",
                "success",
            )
        else:
            flash("Student registration successful!", "success")

        return redirect(url_for("auth.login"))

    # Pass the code to the template for the real-time UI "disappearing" act
    return render_template("register.html")


@auth.route("/auth/check-invite", methods=["POST"])
def check_invite():
    """API to check if an invite code is valid and unused."""
    data = request.get_json()
    code = data.get("code", "").strip().upper()

    if not code:
        return jsonify({"valid": False})

    invite = InviteCode.query.filter_by(code=code, is_used=False).first()
    return jsonify({"valid": True if invite else False})


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
