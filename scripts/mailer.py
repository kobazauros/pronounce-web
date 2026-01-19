from threading import Thread
from flask import current_app, render_template
from flask_mail import Message  # type: ignore
from models import mail, User


def send_async_email(app, msg):
    with app.app_context():
        try:
            print(f"DEBUG: Attempting to send email: {msg.subject} to {msg.recipients}")
            mail.send(msg)
            print("DEBUG: Email sent successfully.")
        except Exception as e:
            print(f"ERROR: Async email failed: {e}")
            import traceback

            traceback.print_exc()
            current_app.logger.error(f"Async email failed: {e}")


def send_email(
    subject: str, sender: str, recipients: list[str], text_body: str, html_body: str
):
    """
    Send an email asynchronously via threading.
    """
    msg = Message(subject, sender=sender, recipients=recipients)  # type: ignore
    msg.body = text_body
    msg.html = html_body

    # Get the real app object (not the proxy)
    app = current_app._get_current_object()  # type: ignore

    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user: User):
    """
    Sends a password reset email to the user with a unique link.
    """
    token = user.get_reset_password_token()
    if not user.email:
        return

    send_email(
        subject="[Pronounce Web] Reset Your Password",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email],
        text_body=render_template("email/reset_password.txt", user=user, token=token),
        html_body=render_template("email/reset_password.html", user=user, token=token),
    )


def send_admin_change_password_notification(user: User, new_password: str):
    """
    Notifies the user that an Admin has changed their password.
    Includes the new password in the email (plain text).
    """
    if not user.email:
        return

    send_email(
        subject="[Pronounce Web] Your Password Was Changed by Admin",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email],
        text_body=render_template(
            "email/admin_password_change.txt", user=user, new_password=new_password
        ),
        html_body=render_template(
            "email/admin_password_change.html", user=user, new_password=new_password
        ),
    )
