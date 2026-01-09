import os
import shutil
from datetime import datetime, timezone

import psutil
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from models import Submission, User, Word, db

dashboards = Blueprint("dashboards", __name__)


@dashboards.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied. Administrator privileges required.", "danger")
        return redirect(url_for("index"))

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 8  # Display 8 users per page

    # Fetch Paginated Data
    users_pagination = User.query.order_by(User.created_at.desc()).paginate(  # type: ignore
        page=page, per_page=per_page, error_out=False
    )
    words = Word.query.all()

    # Process user data for the view to include initials and formatted dates
    user_data = []
    for u in users_pagination.items:
        user_data.append(
            {
                "id": u.id,
                "name": f"{u.first_name} {u.last_name}",
                "username": u.username,
                "role": u.role.capitalize(),
                "student_id": u.student_id or "N/A",
                "initials": (u.first_name[0] + u.last_name[0]).upper()
                if u.first_name and u.last_name
                else u.username[0].upper(),
                "joined_str": u.created_at.strftime("%Y-%m-%d")
                if u.created_at
                else "Unknown",
            }
        )

    # Get today's date in UTC for filtering
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # --- Calculate DB Size ---
    db_size_str = "N/A"
    try:
        db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            # Correctly construct the absolute path from the basedir in config
            db_path = db_uri.split("sqlite:///")[1]
            if os.path.exists(db_path):
                db_size_bytes = os.path.getsize(db_path)
                if db_size_bytes < 1024**2:  # Less than 1 MB
                    db_size_str = f"{db_size_bytes / 1024:.1f} KB"
                else:  # Show as MB
                    db_size_str = f"{db_size_bytes / (1024**2):.1f} MB"
    except Exception:
        pass  # Keep it as N/A if anything goes wrong

    # --- Calculate CPU Load ---
    cpu_load_percent = 0
    try:
        # Get CPU load over a short interval to get a representative value
        cpu_load_percent = psutil.cpu_percent(interval=0.1)
    except Exception:
        # psutil might not be installed or could fail
        pass

    # Calculate Stats
    stats = {
        "total_users": User.query.count(),
        "new_users_today": User.query.filter(User.created_at >= today_start).count(),
        "total_submissions": Submission.query.count(),
        "active_words": len(words),
        "total_teachers": User.query.filter_by(role="teacher").count(),
        "total_students": User.query.filter_by(role="student").count(),
        "db_size": db_size_str,
        "cpu_load": cpu_load_percent,
    }

    return render_template(
        "dashboards/admin_view.html",
        stats=stats,
        users=user_data,
        pagination=users_pagination,
        words=words,
    )


@dashboards.route("/teacher")
@login_required
def teacher_dashboard():
    if current_user.role != "teacher":
        flash("Access denied. Instructor privileges required.", "danger")
        return redirect(url_for("index"))

    # 1. Fetch all students
    students = User.query.filter_by(role="student").all()

    student_data = []
    total_pre_progress = 0
    total_post_progress = 0
    deep_voice_count = 0
    active_today = 0
    today_date = datetime.now(timezone.utc).date()

    for s in students:
        # Get submissions (lazy dynamic query)
        subs = s.submissions.all()

        # Split by test type
        pre_subs = [sub for sub in subs if sub.test_type == "pre"]
        post_subs = [sub for sub in subs if sub.test_type == "post"]

        # Calculate Unique Progress (Words / 20)
        pre_count = len({sub.word_id for sub in pre_subs})
        post_count = len({sub.word_id for sub in post_subs})

        # Calculate Progress (Cap at 100%)
        pre_pct = min(100, int((pre_count / 20) * 100))
        post_pct = min(100, int((post_count / 20) * 100))

        total_pre_progress += pre_pct
        total_post_progress += post_pct

        # Determine Last Active & VTLN Status
        last_active_str = "Never"
        vtln_alpha = None

        if subs:
            # Sort by timestamp descending to get latest
            subs.sort(key=lambda x: x.timestamp, reverse=True)
            last_sub = subs[0]

            last_active_str = last_sub.timestamp.strftime("%Y-%m-%d %H:%M")
            if last_sub.timestamp.date() == today_date:
                active_today += 1

            # Check for analysis data (if available)
            if last_sub.analysis:
                vtln_alpha = last_sub.analysis.scaling_factor
                if vtln_alpha > 1.15:
                    deep_voice_count += 1

        student_data.append(
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "student_id": s.student_id,
                "initials": (s.first_name[0] + s.last_name[0]).upper()
                if s.first_name
                else "??",
                "pre_completed_count": pre_count,
                "post_completed_count": post_count,
                "pre_progress_percent": pre_pct,
                "post_progress_percent": post_pct,
                "vtln_alpha": round(vtln_alpha, 2) if vtln_alpha else None,
                "last_active_str": last_active_str,
            }
        )

    # 2. Calculate Class Stats
    num_students = len(students) if students else 1
    avg_pre_completion = int(total_pre_progress / num_students)
    avg_post_completion = int(total_post_progress / num_students)

    class_stats = {
        "avg_pre_completion": avg_pre_completion,
        "avg_post_completion": avg_post_completion,
        "deep_voice_count": deep_voice_count,
        "active_today": active_today,
    }

    return render_template(
        "dashboards/teacher_view.html", class_stats=class_stats, students=student_data
    )


@dashboards.route("/teacher/student/<int:user_id>")
@login_required
def student_detail(user_id):
    if current_user.role != "teacher":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    student = User.query.get_or_404(user_id)
    if student.role != "student":
        flash("Invalid student selection.", "warning")
        return redirect(url_for("dashboards.teacher_dashboard"))

    # Fetch submissions ordered by latest first
    submissions = student.submissions.order_by(Submission.timestamp.desc()).all()

    return render_template(
        "dashboards/student_detail.html", student=student, submissions=submissions
    )


@dashboards.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    """Displays a form to edit a user's details and handles the update."""
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    user_to_edit = User.query.get_or_404(user_id)

    if request.method == "POST":
        # --- Update Logic ---
        user_to_edit.first_name = request.form.get("first_name", "").strip()
        user_to_edit.last_name = request.form.get("last_name", "").strip()
        new_role = request.form.get("role")

        # 1. Validate and set Role, with a safeguard for the last admin
        if new_role in ["student", "teacher", "admin"]:
            if user_to_edit.role == "admin" and new_role != "admin":
                admin_count = User.query.filter_by(role="admin").count()
                if admin_count <= 1:
                    flash("Cannot change the role of the last administrator.", "danger")
                    return render_template(
                        "dashboards/edit_user.html", user=user_to_edit
                    )
            user_to_edit.role = new_role

        # 2. Handle Student ID based on the new role
        if user_to_edit.role == "student":
            new_student_id = request.form.get("student_id", "").strip()
            # Validate Student ID uniqueness if it has changed
            if new_student_id and new_student_id != user_to_edit.student_id:
                existing_user = User.query.filter(
                    User.student_id == new_student_id, User.id != user_id
                ).first()
                if existing_user:
                    flash(
                        f"Student ID '{new_student_id}' is already assigned to another user.",
                        "danger",
                    )
                    return render_template(
                        "dashboards/edit_user.html", user=user_to_edit
                    )
            user_to_edit.student_id = new_student_id if new_student_id else None
        else:
            # For teachers and admins, student_id should be null
            user_to_edit.student_id = None

        try:
            # 3. Commit to DB
            db.session.commit()
            current_app.logger.info(
                f"Admin '{current_user.username}' updated user '{user_to_edit.username}' (ID: {user_to_edit.id})."
            )
            flash(
                f"User '{user_to_edit.username}' was updated successfully.", "success"
            )
            page = request.args.get("page", 1, type=int)
            return redirect(url_for("dashboards.admin_dashboard", page=page))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user {user_id}: {e}")
            flash("An error occurred while updating the user.", "danger")

    # --- Display Form Logic (GET request) ---
    return render_template("dashboards/edit_user.html", user=user_to_edit)


@dashboards.route("/admin/logs/download")
@login_required
def download_logs():
    """Allows admins to download the application log file."""
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    log_dir = os.path.join(current_app.root_path, "logs")
    log_filename = "pronounce.log"
    log_path = os.path.join(log_dir, log_filename)

    if not os.path.exists(log_path):
        flash("Log file not found. It may not have been created yet.", "warning")
        return redirect(url_for("dashboards.admin_dashboard"))

    return send_from_directory(directory=log_dir, path=log_filename, as_attachment=True)


@dashboards.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    """Deletes a user and their associated submissions."""
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    user_to_delete = User.query.get_or_404(user_id)

    # Safety check: prevent admin from deleting their own account
    if user_to_delete.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("dashboards.admin_dashboard"))

    # Path to the user's upload directory
    user_upload_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_to_delete.id)
    )

    try:
        # 1. Delete submission records from DB
        Submission.query.filter_by(user_id=user_to_delete.id).delete()

        # 2. Delete the user record from DB
        db.session.delete(user_to_delete)
        db.session.commit()

        # 3. If DB deletion is successful, delete the physical files/directory
        if os.path.exists(user_upload_dir):
            shutil.rmtree(user_upload_dir)

        current_app.logger.info(
            f"Admin '{current_user.username}' deleted user '{user_to_delete.username}' (ID: {user_to_delete.id})."
        )
        flash(
            f"User '{user_to_delete.username}' and all their data have been deleted.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting user {user_id} by admin {current_user.username}: {e}"
        )
        flash(f"An error occurred while deleting the user: {e}", "danger")

    return redirect(url_for("dashboards.admin_dashboard"))
