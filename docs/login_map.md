# Login Page (`login.html`)

**Route:** `GET/POST /login`  
**Handler:** `auth_routes.login()` → `auth_routes.py:38-141`  
**Template:** `templates/login.html`  
**Extends:** `base.html`

---

## Page States

The login page has **two display modes** controlled by `is_demo` variable:

| Mode | Condition | Display |
|------|-----------|---------|
| **Standard** | `is_demo=False` | Normal login form |
| **Demo** | `is_demo=True` | Guest login button + disabled form |

---

## Elements (Standard Mode)

| Element | Type | ID/Name | Location | Action |
|---------|------|---------|----------|--------|
| Username | `<input text>` | `name="username"` | Line 80 | Sent to handler |
| Password | `<input password>` | `name="password"` | Line 86 | Sent to handler |
| Remember Me | `<input checkbox>` | `name="remember"` | Line 94 | Sent to handler |
| Sign In | `<button submit>` | — | Line 108 | Submit form |
| Forgot Password | `<a>` | — | Line 100 | → `auth.reset_password_request` |
| Register Link | `<a>` | — | Line 114 | → `auth.register` |

**Form Action:** `POST {{ url_for('auth.login') }}`

---

## Elements (Demo Mode)

| Element | Type | ID/Name | Location | Action |
|---------|------|---------|----------|--------|
| Demo Banner | `<div>` | — | Line 9 | Display only |
| Guest Login | `<button submit>` | — | Line 26 | Submit form |
| Hidden Action | `<input hidden>` | `name="action" value="guest_login"` | Line 24 | Triggers guest flow |
| Disabled Form | `<div>` | `.opacity-50` | Line 42 | Click → alert |

**Form Action:** `POST {{ url_for('auth.login') }}`

---

## Backend Processing Flow

```
POST /login
    │
    ├─► action == "guest_login"?
    │       │
    │       ├─► Yes: Demo mode active?
    │       │       ├─► No: flash("Demo Mode not active") → redirect /login
    │       │       └─► Yes: Create guest_user → login_user() → redirect /
    │       │
    │       └─► No: Continue to standard login
    │
    ├─► Get username, password, remember from form
    │
    ├─► User exists?
    │       └─► No: flash("Check details") → redirect /login
    │
    ├─► User locked?
    │       └─► Yes + not expired: flash("Account locked") → redirect /login
    │       └─► Yes + expired: Clear lockout → continue
    │
    ├─► Password correct?
    │       └─► No: Increment failed_login_attempts
    │               ├─► >= 5 attempts: Lock for 15 min
    │               └─► flash("Check details") → redirect /login
    │
    ├─► User is_guest?
    │       └─► Yes: flash("Guest cannot login") → redirect /login
    │
    ├─► Maintenance mode + not admin?
    │       └─► Yes: render maintenance.html (503)
    │
    └─► Success: login_user() → redirect based on role
            ├─► admin → /dashboard/admin
            ├─► teacher → /dashboard/teacher
            └─► student → /
```

> **Security:** Account lockout, password hashing, and session management details in [`security_map.md`](security_map.md).

---

## Flash Messages (from handler)

| Message | Category | Trigger |
|---------|----------|---------|
| "Demo Mode is not currently active." | `warning` | Guest login when demo off |
| "Welcome to Demo Mode! You are logged in as a Guest User." | `success` | Guest login success |
| "Account locked due to multiple failed login attempts..." | `danger` | Account locked |
| "Account locked for 15 minutes..." | `danger` | Just locked (5th fail) |
| "Please check your login details and try again." | `danger` | Invalid credentials |
| "Guest accounts cannot login via standard form." | `danger` | Guest trying standard login |

---

## JavaScript (Demo Mode Only)

**Location:** Lines 122-146

| Action | Effect |
|--------|--------|
| On page load | Removes `pointer-events-none` from disabled container |
| Click on disabled form | Shows alert: "This feature is disabled in DEMO mode" |
| All inputs in disabled form | Set `disabled=true` and `pointer-events: none` |

---

## Navigation Links

| Link | Target Route | Condition |
|------|--------------|-----------|
| Forgot Password | `auth.reset_password_request` | Standard mode only |
| Register | `auth.register` | Standard mode only |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `is_demo` | `SystemConfig.is_demo_mode()` | Toggle page mode |

---

## Refactoring Notes

1. **Rename `username` field** → Update line 80 (template) + line 73 (handler)
2. **Rename `password` field** → Update line 86 (template) + line 74 (handler)
3. **Rename `remember` field** → Update line 94 (template) + line 75 (handler)
4. **Change guest action value** → Update line 24 (template) + line 42 (handler)
5. **Rename route** → Update `url_for('auth.login')` in template + all redirects
