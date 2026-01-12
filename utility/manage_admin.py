import sys
import os
import getpass
import click

# Add parent directory to path to import flask_app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask_app import app, db, User


@click.group()
def cli():
    """Administrative utility for managing admin users."""
    pass


@cli.command("create")
@click.argument("username")
def create_admin(username):
    """Create a new admin user [USERNAME]."""
    with app.app_context():
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
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
def delete_admin(username):
    """Delete an admin user [USERNAME]."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()

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
            db.session.delete(user)
            db.session.commit()
            click.echo(f"Admin user '{username}' deleted.")


@cli.command("list")
def list_admins():
    """List all admin users."""
    with app.app_context():
        admins = User.query.filter_by(role="admin").all()
        if not admins:
            click.echo("No admin users found.")
            return

        click.echo(f"Found {len(admins)} admin(s):")
        for admin in admins:
            click.echo(
                f" - {admin.username} (ID: {admin.id}, Name: {admin.first_name} {admin.last_name})"
            )


if __name__ == "__main__":
    cli()
