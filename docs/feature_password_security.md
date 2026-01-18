# Password Security System

## Overview
This document details the password security features implemented in **Pronounce Web** as of Jan 2026. The system now supports secure password resets via email, enforcement of email uniqueness, and account lockout protection.

## Features

### 1. Account Security
*   **Password Policy:** Minimum **8 characters**. Must include at least **1 uppercase**, **1 lowercase**, **1 number**, and **1 special character**.
*   **Password History:** Users cannot reuse any of their **last 3 passwords**.
*   **Account Lockout:** An account is locked for **15 minutes** after **5 consecutive failed login attempts**.
*   **Password Hashing:** Uses `werkzeug.security` (scrypt/pbkdf2 default) for secure storage.
*   **Registration:** New users (Student/Teacher) must provide a unique email address.

### 2. Password Reset
*   **Flow:** Forgot Password Link -> Email with Token -> Reset Page.
*   **Tokens:** Secure, time-limited (10 minutes), single-use tokens.
*   **Legacy Users:** Users created before this update (without emails) are marked as **Legacy Test Accounts** and cannot use self-service reset.

### 3. Administrator Tools

#### Dashboard Management
Admins can manage user security via the Admin Dashboard:
*   **View Security Status:**
    *   **Secure (Green):** User has an email and can reset their own password.
    *   **Legacy (Yellow):** User has no email.
*   **Edit User:**
    *   **Add/Edit Email:** Adding an email to a Legacy account upgrades it to **Secure**.
    *   **Reset Password:** Admins can manually set a new password for any user immediately.

#### Admin Self-Protection
For security, **Administrators cannot reset their own passwords via the Web Dashboard or Email.** They must use the server CLI.

**Blocked Channels:**
*   Edit User Page (Web Dashboard)
*   Forgot Password Link (Email)

**CLI Command:**
```bash
python utility/manage_admin.py reset-password <username>
```

## Configuration

The email system requires the following `.env` variables:

```ini
MAIL_SERVER=smtp.gmail.com  # or localhost for testing
MAIL_PORT=587               # or 8025
MAIL_USE_TLS=True           # or False
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=app-password
MAIL_DEFAULT_SENDER=noreply@pronounce-web.com
```

### Local Testing (Mock Server)
To test email functionality without real credentials:
1.  Run the mock server: `.\start_mail_server.ps1`
2.  Set `.env`: `MAIL_SERVER=localhost`, `MAIL_PORT=8025`.
