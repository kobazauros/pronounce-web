# pyright: strict
import sys
import os
import getpass
import click
from typing import cast, List

# Add parent directory to path to import flask_app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask_app import app, db, User


@click.group()
def cli():
    """Administrative utility for managing admin users."""
    pass


@cli.command("create")
@click.argument("username")
def create_admin(username: str):
    """
    Create a new admin user [ADMIN_USERNAME].

    Example:
      python utility/manage_admin.py create [ADMIN_USERNAME]
    """
    with app.app_context():
        # Check if user exists
        existing_user = cast(
            User | None, User.query.filter_by(username=username).first()
        )
        if existing_user:
            if existing_user.role == "admin":
                click.echo(f"User '{username}' is already an admin.")
                return
            else:
                click.confirm(
                    f"User '{username}' exists with role '{existing_user.role}'. Promote to admin?",
                    abort=True,
                )
                existing_user.role = "admin"
                db.session.commit()
                click.echo(f"User '{username}' promoted to admin.")
                return

        # Create new user
        password = getpass.getpass(f"Enter password for {username}: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            click.echo("Passwords do not match.")
            return

        print(f"Creating admin user: {username}")
        new_admin = User(
            username=username,
            first_name="System",
            last_name="Admin",
            role="admin",
            student_id=None,
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        click.echo(f"Admin user '{username}' created successfully.")


@cli.command("delete")
@click.argument("username")
def delete_admin(username: str):
    """
    Delete an admin user [ADMIN_USERNAME].

    Example:
      python utility/manage_admin.py delete [ADMIN_USERNAME]
    """
    with app.app_context():
        user = cast(User | None, User.query.filter_by(username=username).first())

        if not user:
            click.echo(f"User '{username}' not found.")
            return

        if user.role != "admin":
            click.echo(
                f"User '{username}' is not an admin (Role: {user.role}). Use the web dashboard or other tools to manage non-admin users."
            )
            return

        # Count admins (prevent deleting last one)
        admin_count = User.query.filter_by(role="admin").count()
        if admin_count <= 1:
            click.echo("Error: Cannot delete the last administrator.")
            return

        if click.confirm(
            f"Are you sure you want to delete admin '{username}'? This cannot be undone."
        ):
            # 1. Clean up potential submissions (mostly for testing)
            from models import Submission, InviteCode

            # Handle Invite Codes (Reassign to another admin to preserve history)
            # Handle Invite Codes (Reassign to another admin to preserve history)
            user_invites = cast(
                List[InviteCode], InviteCode.query.filter_by(created_by=user.id).all()
            )
            if user_invites:
                # Find a successor (another admin)
                successor = cast(
                    User | None,
                    User.query.filter_by(role="admin")
                    .filter(User.id != user.id)
                    .first(),
                )

                if successor:
                    for invite in user_invites:
                        invite.created_by = cast(int, successor.id)
                    db.session.commit()
                    click.echo(
                        f"Reassigned {len(user_invites)} invite codes to admin '{successor.username}' (ID: {successor.id})."
                    )
                else:
                    # Should be unreachable if 'admin_count <= 1' check works, but safe fallback
                    click.echo(
                        "Error: Cannot delete admin. They own invite codes and no other admin exists to inherit them."
                    )
                    return

            submissions = cast(
                List[Submission], Submission.query.filter_by(user_id=user.id).all()
            )
            for sub in submissions:
                if sub.file_path:
                    # Construct absolute path assuming default upload folder structure
                    # We need to reach into app config, but we are in app_context so current_app works?
                    # No, we are in 'with app.app_context()', so 'app' is available.
                    upload_folder = cast(
                        str, app.config.get("UPLOAD_FOLDER", "uploads")  # type: ignore
                    )  # type: ignore
                    full_path = os.path.join(upload_folder, sub.file_path)
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                        except OSError:
                            pass
                db.session.delete(sub)

            # 2. Clean up user directory if exists
            user_upload_dir = os.path.join(
                cast(str, app.config.get("UPLOAD_FOLDER", "uploads")), str(user.id)  # type: ignore
            )
            if os.path.exists(user_upload_dir):
                import shutil

                shutil.rmtree(user_upload_dir)

            db.session.delete(user)
            db.session.commit()
            click.echo(f"Admin user '{username}' and associated data deleted.")


@cli.command("reset-password")
@click.argument("username")
def reset_password(username: str):
    """
    Reset password for an admin user [ADMIN_USERNAME].

    Example:
      python utility/manage_admin.py reset-password [ADMIN_USERNAME]
    """
    with app.app_context():
        user = cast(User | None, User.query.filter_by(username=username).first())

        if not user:
            click.echo(f"User '{username}' not found.")
            return

        if user.role != "admin":
            click.echo(f"User '{username}' is not an admin. Use web dashboard.")
            # Actually, maybe we allow resetting any user password via CLI?
            # But the prompt specifically said "admins can change their own...".
            # For robustness, I'll allow resetting any user if the CLI admin wants.
            # But the prompt context is specifically about admin restrictions.
            # I'll warn but proceed? Or strict?
            # Let's be strict for "admin" based on function name.
            if not click.confirm(f"User '{username}' is not an admin. Reset anyway?"):
                return

        password = getpass.getpass(f"Enter new password for {username}: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            click.echo("Passwords do not match.")
            return

        # Check Complexity
        is_strong, msg = User.validate_password_strength(password)
        if not is_strong:
            click.echo(f"Error: Password is too weak. {msg}")
            return

        try:
            user.set_password(password)
            # Reset lockout
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            click.echo(f"Password for '{username}' has been updated.")
        except ValueError as e:
            click.echo(f"Error: {e}")


@cli.command("bulk-reset")
@click.option(
    "--role",
    default="student",
    help="Target user role [student|teacher] (default: student)",
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="New password for all users. If omitted, you will be prompted securely.",
)
def bulk_reset(role: str, password: str):
    """
    Reset passwords for ALL users with a specific role.
    USE WITH CAUTION.

    Example:
      python utility/manage_admin.py bulk-reset --role student
    """
    with app.app_context():
        if role == "admin":
            click.echo(
                "Error: Bulk reset is NOT allowed for admins. Use 'reset-password' per user."
            )
            return

        # Check Complexity Early
        is_strong, msg = User.validate_password_strength(password)
        if not is_strong:
            click.echo(f"Error: Password is too weak. {msg}")
            return

        users = cast(
            List[User],
            User.query.filter_by(role=role)
            .filter(User.is_test_account == False)  # type: ignore
            .all(),
        )
        if not users:
            click.echo(f"No users found with role '{role}'.")
            return

        if not click.confirm(
            f"WARNING: This will reset passwords for {len(users)} users with role '{role}'. Continue?"
        ):
            return

        click.echo("Processing...")
        count = 0
        # Import here to avoid circular dependencies at top level if any exists (though unlikely for utility)
        # But manage_admin imports 'app', 'db', 'User' from flask_app.
        # 'utility.mailer' imports 'current_app' and 'mail' and 'User' from models.
        # Should be safe.
        from scripts.mailer import send_admin_change_password_notification

        # Use request context for url_for in templates
        base_url = os.environ.get("BASE_URL", "http://localhost:5000")
        with app.test_request_context(base_url=base_url):
            for user in users:
                try:
                    user.set_password(password)
                    # Reset lockout
                    user.failed_login_attempts = 0
                    user.locked_until = None

                    # Notify
                    send_admin_change_password_notification(user, password)

                    count += 1
                except Exception as e:
                    click.echo(f"Failed to reset {user.username}: {e}")

            db.session.commit()
            click.echo(
                f"Successfully reset passwords for {count}/{len(users)} users. Notifications sent."
            )


@cli.command("list")
def list_admins():
    """
    List all admin users.

    Example:
      python utility/manage_admin.py list
    """
    with app.app_context():
        admins = cast(List[User], User.query.filter_by(role="admin").all())
        if not admins:
            click.echo("No admin users found.")
            return

        click.echo(f"Found {len(admins)} admin(s):")
        for admin in admins:
            click.echo(
                f" - {admin.username} (ID: {admin.id}, Name: {admin.first_name} {admin.last_name})"
            )


@cli.command("fix-legacy-accounts")
def fix_legacy_accounts():
    """
    Mark all existing non-admin users as 'Test Accounts'.
    run this after deploying to production to fix legacy data.
    """
    with app.app_context():
        click.echo("Syncing Test Account status based on Email...")

        # 1. Mark No-Email users as Test Accounts
        legacy_count = User.query.filter(
            User.role != "admin", User.email == None  # type: ignore
        ).update(
            {User.is_test_account: True}, synchronize_session=False  # type: ignore
        )

        # 2. Mark Email users as Real Accounts (Recover from over-aggressive previous run)
        real_count = User.query.filter(User.email != None).update(  # type: ignore
            {User.is_test_account: False}, synchronize_session=False  # type: ignore
        )

        db.session.commit()
        click.echo(f"✅ Marked {legacy_count} legacy users as Test Accounts.")
        click.echo(f"✅ Restored {real_count} verified users as Real Accounts.")


@cli.command("toggle-demo")
def toggle_demo_mode():
    """
    Toggle DEMO Mode ON/OFF automatically.

    Detects the current state and switches to the opposite.
    - If currently OFF → turns ON (enables guest login)
    - If currently ON → turns OFF (disables guest login and deletes all guest users and their submissions)

    Example:
      python utility/manage_admin.py toggle-demo
    """
    from models import SystemConfig, Submission

    with app.app_context():
        is_demo = SystemConfig.is_demo_mode()
        new_state = not is_demo

        click.echo(f"Current Demo Mode: {'ON' if is_demo else 'OFF'}")

        if new_state:
            # Turning ON
            SystemConfig.set("demo_mode", "True")
            db.session.commit()
            click.echo("✅ DEMO MODE ENABLED. Guest Login is now active.")
        else:
            # Turning OFF - CLEANUP
            click.echo("⚠️  Disabling Demo Mode and cleaning up Guest sessions...")

            SystemConfig.set("demo_mode", "False")

            guests = cast(List[User], User.query.filter_by(is_guest=True).all())
            guest_count = len(guests)
            submission_count = 0

            upload_folder = cast(str, app.config.get("UPLOAD_FOLDER", "uploads"))  # type: ignore

            for guest in guests:
                # 1. Delete Submissions
                user_subs = cast(
                    List[Submission], Submission.query.filter_by(user_id=guest.id).all()
                )
                for sub in user_subs:
                    if sub.file_path:
                        full_path = os.path.join(upload_folder, sub.file_path)
                        if os.path.exists(full_path):
                            try:
                                os.remove(full_path)
                            except OSError:
                                pass
                    db.session.delete(sub)
                    submission_count += 1

                # 2. Delete User Directory
                user_dir = os.path.join(upload_folder, str(guest.id))
                if os.path.exists(user_dir):
                    import shutil

                    shutil.rmtree(user_dir, ignore_errors=True)

                # 3. Delete Guest User
                db.session.delete(guest)

            db.session.commit()

            click.echo(f"✅ DEMO MODE DISABLED.")
            click.echo(
                f"🧹 Cleanup: Removed {guest_count} guest users and {submission_count} submissions."
            )


if __name__ == "__main__":
    cli()
