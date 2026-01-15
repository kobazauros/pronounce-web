import os
import shutil
from datetime import datetime, timezone
import math

import psutil
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
    session,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from models import Submission, SystemConfig, User, Word, InviteCode, db
from scripts import parser as word_parser
from scripts.audio_processing import process_audio_data


dashboards = Blueprint("dashboards", __name__)


@dashboards.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied. Administrator privileges required.", "danger")
        return redirect(url_for("index"))

    # Search and Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 10  # Display 10 users per page
    search_query = request.args.get("search", "")

    # Base query
    users_query = User.query

    # Apply search filter if a query is provided
    if search_query:
        search_term = f"%{search_query}%"
        users_query = users_query.filter(
            db.or_(
                User.username.ilike(search_term),  # type: ignore
                User.first_name.ilike(search_term),  # type: ignore
                User.last_name.ilike(search_term),  # type: ignore
            )
        )

    # Fetch Paginated Data
    users_pagination = users_query.order_by(User.created_at.desc()).paginate(  # type: ignore
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
                "role": u.role,
                "student_id": u.student_id or "N/A",
                "initials": (
                    (u.first_name[0] + u.last_name[0]).upper()
                    if u.first_name and u.last_name
                    else u.username[0].upper()
                ),
                "joined_str": (
                    u.created_at.strftime("%Y-%m-%d") if u.created_at else "Unknown"
                ),
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
    cpu_load_percent = "N/A"
    try:
        # Get CPU load over a slightly longer interval for better accuracy
        # usage=0.0 is common on powerful servers with low load if interval is too short
        cpu_load_percent = psutil.cpu_percent(interval=0.5)
    except Exception as e:
        # Log the error to debug why it might be failing
        current_app.logger.error(f"Error reading CPU load: {e}")
        cpu_load_percent = "Err"

    # Calculate Stats
    stats = {
        "total_users": User.query.count(),
        "new_users_today": User.query.filter(User.created_at >= today_start).count(),
        "UTC_now": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "total_submissions": Submission.query.count(),
        "active_words": len(words),
        "total_teachers": User.query.filter_by(role="teacher").count(),
        "total_students": User.query.filter_by(role="student").count(),
        "db_size": db_size_str,
        "cpu_load": cpu_load_percent,
    }

    # --- Get System Config ---
    # This ensures default values are created on first run
    config_settings = {
        "registration_open": SystemConfig.get_bool("registration_open", True),
        "maintenance_mode": SystemConfig.get_bool("maintenance_mode", False),
        "enable_logging": SystemConfig.get_bool("enable_logging", False),
    }
    # If the keys don't exist, set them to their default values
    if SystemConfig.get("registration_open") is None:
        SystemConfig.set("registration_open", True)
    if SystemConfig.get("maintenance_mode") is None:
        SystemConfig.set("maintenance_mode", False)
    if SystemConfig.get("enable_logging") is None:
        SystemConfig.set("enable_logging", False)
    db.session.commit()

    # --- Invite Codes ---
    invite_codes = InviteCode.query.order_by(InviteCode.created_at.desc()).all()

    return render_template(
        "dashboards/admin_view.html",
        stats=stats,
        users=user_data,
        pagination=users_pagination,
        words=words,
        invite_codes=invite_codes,
        config=config_settings,
        search_query=search_query,
    )


@dashboards.route("/teacher")
@login_required
def teacher_dashboard():
    if current_user.role not in ["teacher", "admin"]:
        flash("Access denied. Instructor privileges required.", "danger")
        return redirect(url_for("index"))

    # --- 1. Class Stats Calculation (All Students) ---
    all_students = User.query.filter_by(role="student").all()

    total_pre_progress = 0
    total_post_progress = 0
    deep_voice_count = 0
    outlier_count = 0
    missing_count = 0
    active_today = 0
    today_date = datetime.now(timezone.utc).date()

    for s in all_students:
        subs = s.submissions.all()
        # Progress Calculation
        pre_subs = [sub for sub in subs if sub.test_type == "pre"]
        post_subs = [sub for sub in subs if sub.test_type == "post"]

        pre_count = len({sub.word_id for sub in pre_subs})
        post_count = len({sub.word_id for sub in post_subs})

        pre_pct = min(100, int((pre_count / 20) * 100))
        post_pct = min(100, int((post_count / 20) * 100))

        total_pre_progress += pre_pct
        total_post_progress += post_pct

        if subs:
            # Sort by timestamp descending to get latest
            subs.sort(key=lambda x: x.timestamp, reverse=True)
            last_sub = subs[0]
            if last_sub.timestamp.date() == today_date:
                active_today += 1

            # Count distinct students with flags
            has_deep_voice = any(
                sub.analysis and sub.analysis.is_deep_voice_corrected for sub in subs
            )
            has_outlier = any(sub.analysis and sub.analysis.is_outlier for sub in subs)
            has_missing = any(
                sub.analysis and sub.analysis.distance_bark is None for sub in subs
            )

            if has_deep_voice:
                deep_voice_count += 1
            if has_outlier:
                outlier_count += 1
            if has_missing:
                missing_count += 1

    num_students = len(all_students) if all_students else 1
    class_stats = {
        "avg_pre_completion": int(total_pre_progress / num_students),
        "avg_post_completion": int(total_post_progress / num_students),
        "deep_voice_count": deep_voice_count,
        "outlier_count": outlier_count,
        "missing_count": missing_count,
        "active_today": active_today,
    }

    # --- 2. Table Data (Paginated & Searched) ---
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("search", "")
    per_page = 10

    query = User.query.filter_by(role="student")

    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),  # type: ignore
                User.first_name.ilike(search_term),  # type: ignore
                User.last_name.ilike(search_term),  # type: ignore
                User.student_id.ilike(search_term),  # type: ignore
            )
        )

    pagination = query.order_by(User.first_name.asc()).paginate(  # type: ignore
        page=page, per_page=per_page, error_out=False
    )

    student_data = []

    for s in pagination.items:
        subs = s.submissions.all()
        # Quick re-calc for table view only
        pre_count = len({sub.word_id for sub in subs if sub.test_type == "pre"})
        post_count = len({sub.word_id for sub in subs if sub.test_type == "post"})

        pre_pct = min(100, int((pre_count / 20) * 100))
        post_pct = min(100, int((post_count / 20) * 100))

        last_active_str = "Never"
        has_deep_voice = False
        has_outlier = False
        has_missing = False

        if subs:
            subs.sort(key=lambda x: x.timestamp, reverse=True)
            last_active_str = subs[0].timestamp.strftime("%Y-%m-%d %H:%M")
            has_deep_voice = any(
                sub.analysis and sub.analysis.is_deep_voice_corrected for sub in subs
            )
            has_outlier = any(sub.analysis and sub.analysis.is_outlier for sub in subs)
            has_missing = any(
                sub.analysis and sub.analysis.distance_bark is None for sub in subs
            )

        student_data.append(
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "student_id": s.student_id,
                "initials": (
                    (s.first_name[0] + s.last_name[0]).upper() if s.first_name else "??"
                ),
                "pre_completed_count": pre_count,
                "post_completed_count": post_count,
                "pre_progress_percent": pre_pct,
                "post_progress_percent": post_pct,
                "last_active_str": last_active_str,
                "has_deep_voice": has_deep_voice,
                "has_outlier": has_outlier,
                "has_missing": has_missing,
            }
        )

    return render_template(
        "dashboards/teacher_view.html",
        class_stats=class_stats,
        students=student_data,
        pagination=pagination,
        search_query=search_query,
    )


@dashboards.route("/teacher/student/<int:user_id>")
@login_required
def student_detail(user_id):
    if current_user.role not in ["teacher", "admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    student = User.query.get_or_404(user_id)
    if student.role != "student":
        flash("Invalid student selection.", "warning")
        return redirect(url_for("dashboards.teacher_dashboard"))

    # Fetch submissions with filtering and pagination
    test_type_filter = request.args.get("test_type", "all")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = student.submissions.order_by(Submission.timestamp.desc())

    if test_type_filter in ["pre", "post"]:
        query = query.filter(Submission.test_type == test_type_filter)

    submissions_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "dashboards/student_detail.html",
        student=student,
        submissions=submissions_pagination,
        current_filter=test_type_filter,
    )


@dashboards.route("/teacher/research")
@login_required
def research_dashboard():
    if current_user.role not in ["teacher", "admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    from models import AnalysisResult

    # Fetch all analysis results with related data
    results = (
        db.session.query(AnalysisResult, Submission, User, Word)
        .join(Submission, AnalysisResult.submission_id == Submission.id)
        .join(User, Submission.user_id == User.id)
        .join(Word, Submission.word_id == Word.id)
        .filter(User.role == "student")  # type: ignore # Only analyze students
        .all()
    )

    data = []
    for res, sub, user, word in results:
        # Flatten data for easier JS consumption
        data.append(
            {
                "username": user.username,
                "student_id": user.student_id,
                "word": word.text,
                "vowel": word.stressed_vowel,
                "f1_s": res.f1_norm,  # Normalized Student
                "f2_s": res.f2_norm,
                "f1_r": res.f1_ref,  # Reference
                "f2_r": res.f2_ref,
                "dist_bark": res.distance_bark,
                "alpha": res.scaling_factor,
                "is_outlier": res.is_outlier,
            }
        )

    return render_template("dashboards/research_view.html", analysis_data=data)


@dashboards.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    """Displays a form to edit a user's details and handles the update."""
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    user_to_edit = User.query.get_or_404(user_id)
    search_query = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)

    if request.method == "POST":
        # --- Update Logic ---
        user_to_edit.first_name = request.form.get("first_name", "").strip()
        user_to_edit.last_name = request.form.get("last_name", "").strip()
        new_role = request.form.get("role")

        # 1. Validate and set Role, with safeguards
        if user_to_edit.role == "admin":
            # Admins CANNOT change their own role or other admins' roles via this form
            new_role = "admin"
        elif new_role in ["student", "teacher", "admin"]:
            user_to_edit.role = new_role

        # 2. Handle Student ID based on the new role
        if user_to_edit.role == "student":
            new_student_id = request.form.get("student_id", "").strip()
            # Validate Student ID uniqueness if it has changed
            if new_student_id and new_student_id != user_to_edit.student_id:
                existing_user = User.query.filter(
                    db.and_(User.student_id == new_student_id, User.id != user_id)
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
            return redirect(
                url_for("dashboards.admin_dashboard", page=page, search=search_query)
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user {user_id}: {e}")
            flash("An error occurred while updating the user.", "danger")

    # --- Display Form Logic (GET request) ---
    return render_template(
        "dashboards/edit_user.html",
        user=user_to_edit,
        search_query=search_query,
        page=page,
    )


@dashboards.route("/admin/config/update", methods=["POST"])
@login_required
def update_config():
    """API endpoint to update system configuration."""
    if current_user.role != "admin":
        return jsonify({"success": False, "error": "Access denied"}), 403

    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    if key not in ["registration_open", "maintenance_mode", "enable_logging"]:
        return jsonify({"success": False, "error": "Invalid configuration key"}), 400

    try:
        SystemConfig.set(key, value)
        db.session.commit()
        current_app.logger.info(
            f"Admin '{current_user.username}' updated system config: set '{key}' to '{value}'."
        )
        return jsonify({"success": True, "key": key, "value": value})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating system config: {e}")
        return (
            jsonify({"success": False, "error": "Database error occurred"}),
            500,
        )


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


@dashboards.route("/admin/generate-pronunciation")
@login_required
def generate_pronunciation():
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    word_text = request.args.get("word", "").strip()
    if not word_text:
        return jsonify({"error": "Word parameter is required"}), 400

    try:
        ipa, audio_bytes = word_parser.get_word_data(word_text)

        if not ipa and not audio_bytes:
            return (
                jsonify({"error": f"Could not retrieve any data for '{word_text}'."}),
                404,
            )

        response_data = {"ipa": ipa}

        if audio_bytes:
            processed_bytes = process_audio_data(audio_bytes)

            audio_folder = os.path.join(current_app.static_folder or "static", "audio")
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)

            filename = secure_filename(f"{word_text.lower()}.mp3")
            save_path = os.path.join(audio_folder, filename)

            with open(save_path, "wb") as f:
                f.write(processed_bytes)

            db_audio_path = f"audio/{filename}"
            session["generated_audio_path"] = db_audio_path
            response_data["audio_path"] = url_for("static", filename=db_audio_path)

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(
            f"Error generating pronunciation for '{word_text}': {e}"
        )
        return jsonify({"error": "An internal server error occurred."}), 500


@dashboards.route("/admin/word/add", methods=["GET", "POST"])
@login_required
def add_word():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        word_text = request.form.get("word_text", "").strip()
        ipa = request.form.get("ipa_transcription", "").strip()
        audio_file = request.files.get("audio_file")

        if not word_text:
            flash("Word text cannot be empty.", "danger")
            return render_template("dashboards/manage_word.html", word=None)

        # Check for duplicate word
        if Word.query.filter(Word.text.ilike(word_text)).first():  # type: ignore
            flash(f"The word '{word_text}' already exists in the wordlist.", "danger")
            return render_template("dashboards/manage_word.html", word=None)

        # Determine the next sequence order
        max_sequence = db.session.query(db.func.max(Word.sequence_order)).scalar() or 0
        new_word = Word(text=word_text, ipa=ipa, sequence_order=max_sequence + 1)

        # Handle audio file
        audio_path = None
        if audio_file and audio_file.filename:
            audio_folder = os.path.join(current_app.static_folder or "static", "audio")
            filename = secure_filename(f"{word_text.lower()}.mp3")
            audio_path = os.path.join(audio_folder, filename)
            audio_file.save(audio_path)
            new_word.audio_path = f"audio/{filename}"
        elif session.get("generated_audio_path"):
            new_word.audio_path = session.pop("generated_audio_path", None)

        db.session.add(new_word)
        db.session.commit()

        flash(f"Successfully added the word '{word_text}'.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("dashboards.admin_dashboard"))

    # For GET request
    session.pop("generated_audio_path", None)  # Clear session cache
    return render_template("dashboards/manage_word.html", word=None)


@dashboards.route("/admin/word/edit/<int:word_id>", methods=["GET", "POST"])
@login_required
def edit_word(word_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    word = Word.query.get_or_404(word_id)

    if request.method == "POST":
        word_text = request.form.get("word_text", "").strip()
        ipa = request.form.get("ipa_transcription", "").strip()
        audio_file = request.files.get("audio_file")

        if not word_text:
            flash("Word text cannot be empty.", "danger")
            return render_template("dashboards/manage_word.html", word=word)

        # Check if text is being changed to something that already exists
        if word_text.lower() != word.text.lower():
            if Word.query.filter(Word.text.ilike(word_text)).first():  # type: ignore
                flash(f"The word '{word_text}' already exists.", "danger")
                return render_template("dashboards/manage_word.html", word=word)

        word.text = word_text
        word.ipa = ipa

        # Handle audio file update
        if audio_file and audio_file.filename:
            # If a new file is uploaded, save it and update path
            audio_folder = os.path.join(current_app.static_folder or "static", "audio")
            filename = secure_filename(f"{word_text.lower()}.mp3")
            audio_path = os.path.join(audio_folder, filename)
            audio_file.save(audio_path)
            word.audio_path = f"audio/{filename}"
        elif session.get("generated_audio_path"):
            # If a file was generated, use that path
            word.audio_path = session.pop("generated_audio_path", None)

        db.session.commit()
        flash(f"Successfully updated '{word_text}'.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("dashboards.admin_dashboard"))

    # For GET request
    session.pop("generated_audio_path", None)  # Clear session cache
    return render_template("dashboards/manage_word.html", word=word)


@dashboards.route("/admin/word/<int:word_id>/delete", methods=["POST"])
@login_required
def delete_word(word_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    word = Word.query.get_or_404(word_id)
    word_text = word.text
    next_url = request.args.get("next")
    redirect_url = next_url or url_for("dashboards.admin_dashboard")

    delete_word_flag = request.form.get("delete_word") == "on"
    delete_submissions_flag = request.form.get("delete_submissions") == "on"

    if not delete_word_flag:
        flash("You must confirm deletion by checking the first box.", "warning")
        return redirect(redirect_url)

    try:
        # 1. Delete associated submissions if requested
        if delete_submissions_flag:
            submissions = Submission.query.filter_by(word_id=word_id).all()
            for sub in submissions:
                # Delete associated analysis results (cascade should handle this)
                # Delete physical submission file
                if sub.file_path:
                    full_path = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], sub.file_path
                    )
                    if os.path.exists(full_path):
                        os.remove(full_path)
                db.session.delete(sub)
            flash(f"Deleted all student submissions for '{word_text}'.", "info")

        if word.audio_path:
            static_dir = current_app.static_folder or "static"
            full_audio_path = os.path.join(static_dir, word.audio_path)
            if os.path.exists(full_audio_path):
                os.remove(full_audio_path)

        # 3. Delete the word itself
        db.session.delete(word)
        db.session.commit()

        flash(f"Successfully deleted the word '{word_text}'.", "success")
        return redirect(redirect_url)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting word '{word_text}': {e}")
        flash("An error occurred while deleting the word.", "danger")
        return redirect(redirect_url)


@dashboards.route("/admin/words")
@login_required
def manage_all_words():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    words = Word.query.order_by(Word.text).all()
    word_stats = []
    for word in words:
        submission_count = word.submissions.count()
        last_submission = word.submissions.order_by(Submission.timestamp.desc()).first()
        word_stats.append(
            {
                "word": word,
                "submission_count": submission_count,
                "last_submission_str": (
                    last_submission.timestamp.strftime("%Y-%m-%d")
                    if last_submission
                    else "Never"
                ),
            }
        )

    return render_template("dashboards/manage_all_words.html", word_stats=word_stats)


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

    # Enhance Safety: Admins cannot delete other admins via UI
    if user_to_delete.role == "admin":
        flash(
            "Security Alert: Administrators cannot be deleted via the web panel. Usage of the command-line utility is required.",
            "warning",
        )
        return redirect(url_for("dashboards.admin_dashboard"))

    # Path to the user's upload directory
    user_upload_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_to_delete.id)
    )

    try:
        # 1. Cascade Delete: Remove associated InviteCode if this user used one
        invite_used = InviteCode.query.filter_by(
            used_by_user_id=user_to_delete.id
        ).first()
        if invite_used:
            db.session.delete(invite_used)
            current_app.logger.info(
                f"Cascade deleted invite code '{invite_used.code}' used by '{user_to_delete.username}'"
            )

        # 2. Delete submission records from DB
        Submission.query.filter_by(user_id=user_to_delete.id).delete()

        # 3. Delete the user record from DB
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


@dashboards.route("/api/submission/<int:submission_id>/analysis")
@login_required
def get_analysis_data(submission_id):
    """Returns analysis data for a specific submission."""
    # Ensure user has access (Teacher can view all, Student only their own)
    submission = Submission.query.get_or_404(submission_id)
    if current_user.role == "student" and submission.user_id != current_user.id:
        return jsonify({"error": "Access denied"}), 403

    if not submission.analysis:
        return jsonify({"error": "No analysis data found"}), 404

    res = submission.analysis

    return jsonify(
        {
            "student": {
                "f1": res.f1_norm,
                "f2": res.f2_norm,
                "color": "rgba(54, 162, 235, 1)",  # Blue
            },
            "reference": {
                "f1": res.f1_ref,
                "f2": res.f2_ref,
                "color": "rgba(75, 192, 192, 1)",  # Green
            },
            "metrics": {
                "distance_bark": (
                    round(res.distance_bark, 2) if res.distance_bark else None
                ),
                "vowel_label": submission.target_word.stressed_vowel,
                "is_outlier": res.is_outlier,
            },
        }
    )


@dashboards.route("/admin/invite/generate", methods=["POST"])
@login_required
def generate_invite():
    """Generates a new random invite code."""
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    import uuid

    code = uuid.uuid4().hex[:10].upper()

    # Ensure uniqueness (simple retry)
    while InviteCode.query.filter_by(code=code).first():
        code = uuid.uuid4().hex[:10].upper()

    new_invite = InviteCode(code=code, created_by=current_user.id)

    try:
        db.session.add(new_invite)
        db.session.commit()
        flash(f"Generated new invite code: {code}", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating invite code: {e}")
        flash("Failed to generate invite code.", "danger")

    return redirect(url_for("dashboards.admin_dashboard"))


@dashboards.route("/admin/invite/<int:invite_id>/delete", methods=["POST"])
@login_required
def delete_invite(invite_id):
    """Deletes an invite code."""
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    invite = InviteCode.query.get_or_404(invite_id)

    # Security Check: Cannot delete used invites manually
    if invite.is_used:
        flash(
            "Cannot delete a used invite code. Delete the teacher user instead.",
            "warning",
        )
        return redirect(url_for("dashboards.admin_dashboard"))

    try:
        db.session.delete(invite)
        db.session.commit()
        flash("Invite code deleted.", "info")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting invite code: {e}")
        flash("Failed to delete invite code.", "danger")

    return redirect(url_for("dashboards.admin_dashboard"))
