# Register Page (`register.html`)

**Route:** `GET/POST /register`  
**Handler:** `auth_routes.register()` → `auth_routes.py:144-291`  
**Template:** `templates/register.html`  
**Extends:** `base.html`

> **Note:** This page is **NOT ACCESSIBLE in Demo Mode**. Users are redirected to `/login` with a warning message.

---

## Page States

The register page has **two dynamic modes** controlled by invite code validation:

| Mode | Condition | Display |
|------|-----------|---------|
| **Student** | No valid invite code | Student ID required, Consent required |
| **Teacher** | Valid invite code entered | Student ID disabled, Consent disabled |

---

## Form Elements

| Element | Type | ID/Name | Location | Required | Action |
|---------|------|---------|----------|----------|--------|
| First Name | `<input text>` | `id="first_name"` `name="first_name"` | Line 20 | Yes | Sent to handler |
| Last Name | `<input text>` | `id="last_name"` `name="last_name"` | Line 26 | Yes | Sent to handler |
| Username | `<input text>` | `id="username"` `name="username"` | Line 33 | Yes | Sent to handler |
| Email | `<input email>` | `id="email"` `name="email"` | Line 39 | Yes | Sent to handler |
| Student ID | `<input text>` | `id="student_id"` `name="student_id"` | Line 46 | Student only | Sent to handler |
| Invite Code | `<input text>` | `id="invite_code"` `name="invite_code"` | Line 54 | No | Sent to handler, triggers validation |
| Password | `<input password>` | `id="password"` `name="password"` | Line 66 | Yes | Sent to handler |
| Confirm Password | `<input password>` | `id="confirm_password"` `name="confirm_password"` | Line 73 | Yes | Sent to handler |
| Consent Checkbox | `<input checkbox>` | `id="consent"` `name="consent"` | Line 84 | Student only | Sent to handler |
| Sign Up | `<button submit>` | — | Line 97 | — | Submit form |
| Login Link | `<a>` | — | Line 103 | — | → `auth.login` |

**Form Action:** `POST` (current URL, no explicit action)

---

## Dynamic UI Elements

| Element | ID | Purpose |
|---------|-----|---------|
| Invite Status Icon | `id="invite-status"` | Shows loading/valid/invalid icon |
| Invite Message | `id="invite-msg"` | Shows validation result text |
| Student ID Container | `id="student-id-container"` | Wrapper for disabling |
| Consent Section | `id="consent-section"` | Wrapper for disabling |

---

## Backend Processing Flow

```
POST /register
    │
    ├─► User authenticated?
    │       └─► Yes: redirect /
    │
    ├─► Registration closed?
    │       └─► Yes: flash("Registration closed") → redirect /login
    │
    ├─► Demo mode active?
    │       └─► Yes: flash("Registration disabled in Demo") → redirect /login
    │
    ├─► Get all form fields
    │
    ├─► Validate required fields (first_name, last_name, username, email, password)
    │       └─► Missing: flash("All fields mandatory") → redirect /register
    │
    ├─► Passwords match?
    │       └─► No: flash("Passwords do not match") → redirect /register
    │
    ├─► Password strong enough?
    │       └─► No: flash(strength message) → redirect /register
    │
    ├─► Username exists?
    │       └─► Yes: flash("Username already exists") → redirect /register
    │
    ├─► Email exists?
    │       └─► Yes: flash("Email already registered") → redirect /register
    │
    ├─► Invite code provided?
    │       │
    │       ├─► Yes: Code valid & unused?
    │       │       ├─► No: flash("Invalid or used invite") → redirect /register
    │       │       └─► Yes: role = "teacher"
    │       │
    │       └─► No: role = "student"
    │
    ├─► If Student:
    │       ├─► Student ID provided?
    │       │       └─► No: flash("Student ID mandatory") → redirect /register
    │       ├─► Student ID valid (10 digits)?
    │       │       └─► No: flash("Must be 10 digits") → redirect /register
    │       ├─► Student ID unique?
    │       │       └─► No: flash("Already registered") → redirect /register
    │       └─► Consent checked?
    │               └─► No: flash("Must consent") → redirect /register
    │
    ├─► Create User
    │       └─► Error: flash("Server error") → redirect /register
    │
    ├─► If Teacher: Mark invite code as used
    │
    └─► Success: flash(role-specific message) → redirect /login
```

---

## Flash Messages (from handler)

| Message | Category | Trigger | Line |
|---------|----------|---------|------|
| "New user registration is currently closed..." | `info` | Registration closed | 151 |
| "Registration is disabled in Demo Mode." | `warning` | Demo mode active | 156 |
| "All fields (First Name, Last Name, Username, Email, Password) are mandatory." | `danger` | Missing required fields | 174 |
| "Passwords do not match." | `danger` | password ≠ confirm_password | 181 |
| Password strength message | `danger` | Weak password | 186 |
| "Username already exists." | `danger` | Duplicate username | 193 |
| "Email already registered." | `danger` | Duplicate email | 197 |
| "Invalid or already used invite code." | `danger` | Bad invite code | 217 |
| "Student ID is mandatory for students." | `danger` | No student ID | 225 |
| "Student ID must be exactly 10 digits." | `danger` | Invalid format | 229 |
| "A user with this Student ID is already registered." | `danger` | Duplicate student ID | 234 |
| "Students must consent to data collection." | `warning` | No consent | 238 |
| "A server error occurred during registration..." | `danger` | DB error | 274 |
| "Instructor account created! No student ID or consent required." | `success` | Teacher success | 281 |
| "Student registration successful!" | `success` | Student success | 286 |

---

## JavaScript Functions

**Location:** Lines 110-198

| Function/Action | Purpose |
|-----------------|---------|
| `debounce(callback, time)` | Delays invite validation by 500ms |
| `setTeacherMode(isTeacher)` | Toggles Student ID and Consent visibility |
| `validateInvite(code)` | Calls API to check invite code validity |
| `inviteInput.addEventListener('input')` | Triggers debounced validation on typing |
| `window.addEventListener('load')` | Initializes student mode |

---

## API Calls (from JavaScript)

| Endpoint | Method | Trigger | Handler | Response |
|----------|--------|---------|---------|----------|
| `/auth/check-invite` | POST | Invite code input | `auth_routes.check_invite()` | `{"valid": true/false}` |

**API Handler:** `auth_routes.py:294-306`

```python
@auth.route("/auth/check-invite", methods=["POST"])
def check_invite():
    data = request.get_json()
    code = data.get("code", "").strip().upper()
    invite = InviteCode.query.filter_by(code=code, is_used=False).first()
    return jsonify({"valid": invite is not None})
```

---

## Navigation Links

| Link | Target Route |
|------|--------------|
| Login | `auth.login` |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| (none) | — | No server-side variables passed |

---

## CSS Classes for Dynamic State

| Class | Applied To | Effect |
|-------|------------|--------|
| `opacity-50` | `#consent-section`, `#student-id-container` | Visual disabled state |
| `pointer-events-none` | `#consent-section`, `#student-id-container` | Prevents interaction |
| `hidden` | `#invite-status`, `#invite-msg` | Hides element |

---

## Validation Patterns

| Field | Pattern | Validation |
|-------|---------|------------|
| Student ID | `\d{10}` | HTML pattern attribute |
| Email | Built-in | HTML type="email" |
| Password | Backend | 8+ chars, mixed case, number, special |

---

## Refactoring Notes

1. **Rename form fields** → Update template (name/id) + handler (`request.form.get()`)
2. **Change invite code API** → Update JS fetch URL (line 162) + route decorator (line 294)
3. **Modify student ID validation** → Update `is_valid_student_id()` (line 201) + HTML pattern (line 48)
4. **Change consent behavior** → Update `setTeacherMode()` in JS + backend check (line 237)
5. **Rename route** → Update `url_for('auth.register')` in templates + handler redirects
