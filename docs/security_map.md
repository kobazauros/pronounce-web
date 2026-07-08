# Security Map - Password & Authentication

**Focus:** Password security measures, authentication controls, and account protection mechanisms.

---

## Overview

| Security Feature | Implementation |
|------------------|----------------|
| Password Hashing | Werkzeug `generate_password_hash()` / `check_password_hash()` |
| Password Strength | Enforced complexity requirements |
| Password History | Last 3 passwords stored, reuse prevention |
| Account Lockout | 5 failed attempts = 15-minute lock |
| Reset Tokens | Secure, time-limited, single-use tokens |
| Session Management | Flask-Login with configurable "remember me" |

---

## 1. Password Hashing

**Location:** `models.py` → `User` class

### Storage

| Field | Type | Purpose |
|-------|------|---------|
| `password_hash` | `String(256)` | Hashed password (never plain text) |

### Implementation

```python
# Setting password (line 154-165)
def set_password(self, password: str) -> None:
    self.password_hash = generate_password_hash(password)
    # Also stores in password_history for reuse prevention

# Checking password (line 167-168)
def check_password(self, password: str) -> bool:
    return check_password_hash(self.password_hash, password)
```

### Hash Algorithm

| Library | Function | Algorithm |
|---------|----------|-----------|
| Werkzeug Security | `generate_password_hash()` | PBKDF2-SHA256 (default) |

**Note:** Werkzeug uses salted hashes with configurable iterations, providing protection against rainbow table attacks.

---

## 2. Password Strength Requirements

**Location:** `models.py` → `User.validate_password_strength()` (lines 208-227)

### Complexity Rules

| Requirement | Minimum |
|-------------|---------|
| Length | 8 characters |
| Uppercase letters | 1 |
| Lowercase letters | 1 |
| Numbers | 1 |
| Special characters | 1 |

### Validation Logic

```python
def validate_password_strength(password: str) -> tuple[bool, str]:
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("at least one number")
    if not any(not c.isalnum() for c in password):
        errors.append("at least one special character")
    
    if errors:
        return False, "Password must include: " + "; ".join(errors) + "."
    return True, ""
```

### Enforcement Points

| Location | When Called |
|----------|-------------|
| `auth_routes.py` → `register()` | New user registration |
| `auth_routes.py` → `reset_password()` | Self-service password reset |
| `dashboard_routes.py` → `edit_user()` | Admin password reset |

---

## 3. Password History & Reuse Prevention

**Location:** `models.py` → `PasswordHistory` class (lines 62-71)

### Database Model

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (PK) | Record identifier |
| `user_id` | Integer (FK) | Reference to user |
| `password_hash` | String(256) | Historical password hash |
| `created_at` | DateTime | When password was set |

### Storage Mechanism

When `User.set_password()` is called:
1. New password is hashed
2. Hash is stored in `password_history` table
3. Linked to user via `user_id`

### Retention Policy

| Setting | Value |
|---------|-------|
| Passwords stored | Last 3 |
| Pruning | Planned (see code comment line 164-165) |

### Relationship

```python
# User model (lines 126-128)
password_history = db.relationship(
    "PasswordHistory", backref="user", lazy="dynamic", cascade="all, delete-orphan"
)
```

---

## 4. Account Lockout Protection

**Location:** `models.py` → `User` class + `auth_routes.py` → `login()`

### Database Fields

| Field | Type | Purpose |
|-------|------|---------|
| `failed_login_attempts` | Integer | Counter for consecutive failures |
| `locked_until` | DateTime | Lock expiration timestamp |

### Lockout Parameters

| Parameter | Value |
|-----------|-------|
| Max failed attempts | 5 |
| Lockout duration | 15 minutes |

### Lockout Flow

```
Login Attempt
    │
    ├─► Check locked_until
    │       │
    │       ├─► Still locked → Flash error, redirect
    │       │
    │       └─► Expired → Clear lockout, continue
    │
    ├─► Check credentials
    │       │
    │       ├─► Invalid:
    │       │       ├─► Increment failed_login_attempts
    │       │       ├─► If attempts >= 5:
    │       │       │       └─► Set locked_until = now + 15 min
    │       │       └─► Flash error
    │       │
    │       └─► Valid:
    │               ├─► Reset failed_login_attempts = 0
    │               ├─► Clear locked_until = None
    │               └─► Login user
```

### Implementation (auth_routes.py lines 79-123)

| Step | Code |
|------|------|
| Check lock | `if user.locked_until > datetime.now(timezone.utc)` |
| Increment failures | `user.failed_login_attempts += 1` |
| Apply lock | `user.locked_until = datetime.now() + timedelta(minutes=15)` |
| Clear on success | `user.failed_login_attempts = 0; user.locked_until = None` |

### Lockout Reset Points

| Action | Location | Resets Lockout |
|--------|----------|----------------|
| Successful login | `auth_routes.login()` | Yes |
| Self-service password reset | `auth_routes.reset_password()` | Yes |
| Admin password reset | `dashboard_routes.edit_user()` | Yes |
| CLI password reset | `manage_admin.py` | Yes |

---

## 5. Password Reset Tokens

**Location:** `models.py` → `PasswordResetToken` class (lines 416-437)

### Token Model

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (PK) | Token identifier |
| `user_id` | Integer | User requesting reset |
| `token_hash` | String(256) | Hashed token (not plain!) |
| `created_at` | DateTime | Creation timestamp |
| `expires_at` | DateTime | Expiration timestamp |
| `used` | Boolean | Single-use enforcement |

### Token Security Features

| Feature | Implementation |
|---------|----------------|
| Secure generation | `secrets.token_urlsafe(32)` |
| Hashed storage | Token itself never stored, only hash |
| Time-limited | Default 10 minutes (`expires_in=600`) |
| Single-use | `used` flag prevents replay attacks |

### Token Generation Flow

```python
def get_reset_password_token(self, expires_in: int = 600) -> str:
    token = secrets.token_urlsafe(32)           # Generate secure random
    token_hash = generate_password_hash(token)  # Hash for storage
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    reset_token = PasswordResetToken(
        user_id=self.id, 
        token_hash=token_hash, 
        expires_at=expires_at
    )
    db.session.add(reset_token)
    db.session.commit()
    
    return f"{reset_token.id}.{token}"  # Return id.token format
```

### Token Verification Flow

```python
@staticmethod
def verify_reset_password_token(token: str) -> Optional[User]:
    # Parse token format: "id.random_string"
    token_id, random_str = token.split(".", 1)
    
    # Fetch record
    reset_token = PasswordResetToken.query.get(token_id)
    
    # Validate:
    # 1. Record exists
    # 2. Not already used
    # 3. Not expired
    # 4. Hash matches
    
    if check_password_hash(reset_token.token_hash, random_str):
        return User.query.get(reset_token.user_id)
    return None
```

---

## 6. Session Security

**Location:** `config.py` + `flask_app.py`

### Flask Secret Key

| Setting | Source | Purpose |
|---------|--------|---------|
| `SECRET_KEY` | Environment variable or fallback | Session signing |

```python
# config.py line 10
SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-please-change-in-production"
```

**Warning:** The fallback key should never be used in production.

### Flask-Login Configuration

| Feature | Implementation |
|---------|----------------|
| User loader | `flask_app.py` line 107 |
| Remember me | Checkbox on login form |
| Session protection | Flask-Login defaults |

---

## 7. Guest User Security

**Location:** `auth_routes.py` lines 115-118

| Measure | Implementation |
|---------|----------------|
| Prevent standard login | Guest accounts blocked from form login |
| Demo mode only | Guests created only via "Try Demo" button |
| No password | Guest accounts have no credentials to compromise |

```python
if user.is_guest:
    flash("Guest accounts cannot login via standard form.", "danger")
    return redirect(url_for("auth.login"))
```

---

## 8. Admin Password Protection

**Location:** `dashboard_routes.py` → `edit_user()`

| Restriction | Reason |
|-------------|--------|
| Admin passwords cannot be reset via web UI | Higher privilege requires CLI access |
| CLI-only reset | `python utility/manage_admin.py reset-password <username>` |

```python
if user_to_edit.role == "admin":
    flash("Admin passwords must be reset via server console.", "danger")
    return render_template(...)
```

---

## 9. Email Requirements for Password Operations

| Operation | Email Required | Reason |
|-----------|----------------|--------|
| Self-service reset | Yes | Token sent to email |
| Admin password reset | Yes | Notification with new password sent |
| Registration (student) | No | Invite code flow |
| Registration (teacher) | No | Invite code flow |

---

## Security Summary Table

| Attack Vector | Protection |
|---------------|------------|
| Password guessing | Account lockout after 5 attempts |
| Weak passwords | Complexity requirements enforced |
| Password reuse | History prevents last 3 |
| Rainbow tables | Salted PBKDF2 hashing |
| Token theft | Hashed storage, single-use, expiration |
| Session hijacking | Flask secret key signing |
| Brute force reset | Time-limited tokens (10 min) |
| Privilege escalation | Admin passwords require CLI access |

---

## Configuration Locations

| Setting | File | Line |
|---------|------|------|
| Secret key | `config.py` | 10 |
| Password hash | `models.py` | 154-168 |
| Password validation | `models.py` | 208-227 |
| Lockout settings | `auth_routes.py` | 79-123 |
| Token expiration | `models.py` | 170 (600 seconds default) |
| History retention | `models.py` | 164-165 (3 passwords) |

---

## Refactoring Notes

1. **Change lockout duration** → Update `timedelta(minutes=15)` in `auth_routes.py:103-105`
2. **Change max attempts** → Update `>= 5` check in `auth_routes.py:101`
3. **Change password rules** → Update `validate_password_strength()` in `models.py`
4. **Change token expiration** → Update `expires_in=600` default in `get_reset_password_token()`
5. **Change history depth** → Update pruning logic in `set_password()` (currently not implemented)
6. **Add rate limiting** → Consider Flask-Limiter for additional protection
7. **Add 2FA** → Would require new model and login flow modifications
