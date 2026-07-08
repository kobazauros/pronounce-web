# Email Templates

**Location:** `templates/email/`  
**Sent via:** `scripts/mailer.py`  
**Type:** Jinja2 email templates (HTML + plain text versions)

---

## Overview

| Template Pair | Purpose | Sender Function |
|---------------|---------|-----------------|
| `reset_password.html/.txt` | Self-service password reset | `send_password_reset_email()` |
| `admin_password_change.html/.txt` | Admin-initiated password reset | `send_admin_change_password_notification()` |

---

# 1. Password Reset Email (`reset_password.html`)

**Triggered by:** User clicking "Forgot Password" on login page  
**Handler:** `auth_routes.reset_password_request()`  
**Sender:** `scripts/mailer.send_password_reset_email(user)`

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `user.first_name` | User model | Personalize greeting |
| `token` | `User.get_reset_password_token()` | Unique reset token |

---

## HTML Version (`reset_password.html`)

| Element | Content |
|---------|---------|
| Greeting | "Dear {{ user.first_name }}," |
| Reset Link | Clickable link to reset page |
| Plain URL | Full URL for copy/paste |
| Ignore Notice | "If you have not requested..." |
| Signature | "Sincerely, The Pronounce Team" |

### Generated URLs

| URL | Route | Purpose |
|-----|-------|---------|
| `url_for('auth.reset_password', token=token, _external=True)` | `/reset_password/<token>` | Reset password page |

---

## Plain Text Version (`reset_password.txt`)

Same content as HTML without markup. Used as fallback for email clients that don't support HTML.

---

## Refactoring Notes

1. **Change greeting** → Update line 5 (HTML) / line 1 (TXT)
2. **Change signature** → Update line 11 (HTML) / lines 8-9 (TXT)
3. **Add branding/logo** → Add `<img>` tag in HTML version
4. **Change reset link text** → Update line 6-7 (HTML)

---

# 2. Admin Password Change Email (`admin_password_change.html`)

**Triggered by:** Admin resetting user password via Edit User page  
**Handler:** `dashboard_routes.edit_user()`  
**Sender:** `scripts/mailer.send_admin_change_password_notification(user, new_password)`

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `user.first_name` | User model | Personalize greeting |
| `new_password` | Generated password | Display new password to user |

---

## HTML Version (`admin_password_change.html`)

| Element | Content |
|---------|---------|
| Greeting | "Hello {{ user.first_name }}," |
| Notice | "An administrator has manually changed your password..." |
| Password Label | "Your NEW Password is:" |
| Password Display | `<h3>` styled in red (`#d9534f`) |
| Action | "Please login and change this password immediately..." |
| Login Link | Clickable link to login page |
| Security Notice | "If you did not request this change..." |
| Signature | "Best regards, Pronounce Web Team" |

### Generated URLs

| URL | Route | Purpose |
|-----|-------|---------|
| `url_for('auth.login', _external=True)` | `/login` | Login page |

---

## Plain Text Version (`admin_password_change.txt`)

Same content as HTML without markup. Password displayed as plain text.

---

## Security Considerations

| Concern | Implementation |
|---------|----------------|
| Password in email | Displayed once; user encouraged to change immediately |
| Plain text fallback | Password visible in both HTML and TXT versions |
| No password storage | Password sent immediately after generation, not stored in email logs |

---

## Refactoring Notes

1. **Change app name** → Update "Pronounce Web" references (lines 3, 14-15 HTML)
2. **Change password styling** → Update `<h3>` style (line 6 HTML)
3. **Add branding/logo** → Add `<img>` tag in HTML version
4. **Change signature** → Update lines 14-15 (HTML) / lines 14-15 (TXT)
5. **Add password requirements reminder** → Add text after password display

---

## Email Sending Flow

```
User Action
    │
    ├─► Self-service Reset:
    │       User → "Forgot Password" → reset_password_request()
    │           → send_password_reset_email(user)
    │           → Email with reset link (no password shown)
    │
    └─► Admin Reset:
            Admin → Edit User → Submit new password
                → edit_user() → send_admin_change_password_notification(user, new_password)
                → Email with new password displayed
```

---

## Mailer Functions

**Location:** `scripts/mailer.py`

| Function | Purpose |
|----------|---------|
| `send_email(subject, sender, recipients, text_body, html_body)` | Core email sending |
| `send_async_email(app, msg)` | Background thread email delivery |
| `send_password_reset_email(user)` | Sends reset link email |
| `send_admin_change_password_notification(user, new_password)` | Sends admin password change notification |
