# Password Reset Pages

This document covers the two-step password reset flow.

---

# 1. Reset Password Request (`reset_password_request.html`)

**Route:** `GET/POST /reset_password_request`  
**Handler:** `auth_routes.reset_password_request()` → `auth_routes.py:316-346`  
**Template:** `templates/auth/reset_password_request.html`  
**Extends:** `base.html`

---

## Form Elements

| Element | Type | ID/Name | Location | Required | Action |
|---------|------|---------|----------|----------|--------|
| Email | `<input email>` | `id="email"` `name="email"` | Line 17 | Yes | Sent to handler |
| Submit | `<button submit>` | — | Line 24 | — | Submit form |
| Back to Login | `<a>` | — | Line 30 | — | → `auth.login` |

**Form Action:** `POST` (current URL, no explicit action)

---

## Backend Processing Flow

```
POST /reset_password_request
    │
    ├─► User authenticated?
    │       └─► Yes: redirect /
    │
    ├─► Email provided?
    │       └─► No: flash("Email is required") → redirect /reset_password_request
    │
    ├─► User found by email?
    │       │
    │       ├─► Yes: User is admin?
    │       │       ├─► Yes: flash("Admin cannot reset via email") → redirect /login
    │       │       └─► No: send_password_reset_email(user)
    │       │
    │       └─► No: (silent - no email sent)
    │
    └─► Always: flash("Check your email...") → redirect /login
```

> **Security Note:** The same success message is shown whether email exists or not, to prevent email enumeration attacks.

---

## Flash Messages

| Message | Category | Trigger | Line |
|---------|----------|---------|------|
| "Email is required" | `danger` | Empty email field | 324 |
| "Administrator passwords cannot be reset via email..." | `danger` | Admin user | 331 |
| "Check your email for the instructions to reset your password" | `info` | Always (success or not) | 343 |

---

## Email Sent

| Function | Template | Trigger |
|----------|----------|---------|
| `send_password_reset_email(user)` | `email/reset_password.html` | Valid non-admin user |

---

## Navigation Links

| Link | Target Route |
|------|--------------|
| Back to Login | `auth.login` |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| (none) | — | No server-side variables passed |

---

## Refactoring Notes

1. **Rename email field** → Update line 17 (template) + line 322 (handler)
2. **Rename route** → Update decorator (line 316) + `url_for('auth.reset_password_request')` in templates

---

# 2. Reset Password (`reset_password.html`)

**Route:** `GET/POST /reset_password/<token>`  
**Handler:** `auth_routes.reset_password(token)` → `auth_routes.py:349-388`  
**Template:** `templates/auth/reset_password.html`  
**Extends:** `base.html`

> **Note:** This page requires a valid token from the password reset email. Invalid/expired tokens redirect to `/`.

---

## Form Elements

| Element | Type | ID/Name | Location | Required | Action |
|---------|------|---------|----------|----------|--------|
| New Password | `<input password>` | `id="password"` `name="password"` | Line 17 | Yes | Sent to handler |
| Confirm Password | `<input password>` | `id="confirm_password"` `name="confirm_password"` | Line 23 | Yes | Sent to handler |
| Submit | `<button submit>` | — | Line 30 | — | Submit form |
| Back to Login | `<a>` | — | Line 36 | — | → `auth.login` |

**Form Action:** `POST` (current URL with token)

---

## Backend Processing Flow

```
GET/POST /reset_password/<token>
    │
    ├─► User authenticated?
    │       └─► Yes: redirect /
    │
    ├─► Token valid?
    │       └─► No: flash("Invalid or expired") → redirect /
    │
    ├─► POST request:
    │       │
    │       ├─► Passwords match and not empty?
    │       │       └─► No: flash("Passwords must match") → redirect (same page)
    │       │
    │       ├─► Password strong enough?
    │       │       └─► No: flash(strength message) → redirect (same page)
    │       │
    │       ├─► Set new password
    │       │       ├─► Success: Reset lockout, mark token used → redirect /login
    │       │       └─► ValueError: flash(error) → redirect (same page)
    │       │
    │       └─► (password reuse blocked by set_password)
    │
    └─► GET request: render form
```

---

## Flash Messages

| Message | Category | Trigger | Line |
|---------|----------|---------|------|
| "Invalid or expired reset token." | `danger` | Bad/expired token | 356 |
| "Passwords must match and cannot be empty." | `danger` | Mismatch or empty | 364 |
| Password strength message | `danger` | Weak password | 369 |
| "Your password has been reset." | `success` | Success | 381 |
| ValueError message | `danger` | Password reuse | 384 |

---

## Side Effects on Success

| Action | Purpose |
|--------|---------|
| `user.set_password(password)` | Update password hash |
| `user.failed_login_attempts = 0` | Reset lockout counter |
| `user.locked_until = None` | Unlock account |
| `user.mark_reset_token_used(token)` | Invalidate token |

---

## Navigation Links

| Link | Target Route |
|------|--------------|
| Back to Login | `auth.login` |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| (none) | — | Token is in URL, not passed to template |

---

## Validation Rules

| Field | Rule | Source |
|-------|------|--------|
| Password | 8+ chars, uppercase, lowercase, number, special | `User.validate_password_strength()` |
| Password | Cannot reuse last 5 passwords | `User.set_password()` |

---

## Refactoring Notes

1. **Rename password fields** → Update lines 17, 23 (template) + lines 360-361 (handler)
2. **Change token URL parameter** → Update route decorator (line 349) + all `url_for` calls
3. **Modify password validation** → Update `User.validate_password_strength()` in `models.py`
