# Edit User Page (`edit_user.html`)

**Route:** `GET/POST /admin/user/<user_id>/edit`  
**Handler:** `dashboard_routes.edit_user()` → `dashboard_routes.py:422-628`  
**Template:** `templates/dashboards/edit_user.html`  
**Extends:** `base.html`

> **Note:** Admin-only page. Disabled in demo mode. Users are redirected to this page from the admin dashboard User Directory.

---

## Page Purpose

Admin interface for editing user details:
- Update personal information (name, email)
- Change user role (with restrictions)
- Manage student ID
- Reset user password (with email notification)
- View teacher invite code

---

## Access Control

| Condition | Result |
|-----------|--------|
| Non-admin user | Redirect to index with "Access denied" |
| Admin user | Full access to edit form |
| Demo mode | All inputs disabled, actions blocked |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `user` | `User.query.get_or_404(user_id)` | User object being edited |
| `search_query` | `request.args.get("search")` | Preserve search state for back link |
| `page` | `request.args.get("page")` | Preserve pagination for back link |
| `is_demo` | Context processor | Toggle demo mode restrictions |

---

## Form Elements

### Header Section

| Element | Type | Purpose |
|---------|------|---------|
| Page Title | `<h1>` | "Edit User: {{ user.username }}" |
| Back Link | `<a>` | Return to admin dashboard (preserves page/search) |

---

### Personal Information Fields

| Field | Name | ID | Type | Required | Purpose |
|-------|------|----|------|----------|---------|
| First Name | `first_name` | `#first_name` | `text` | Yes | User's first name |
| Last Name | `last_name` | `#last_name` | `text` | Yes | User's last name |
| Email | `email` | `#email` | `email` | No | Email address (enables Secure status) |

---

### Role Field

| Field | Name | ID | Type | Options | Purpose |
|-------|------|----|------|---------|---------|
| Role | `role` | `#role` | `select` | student, teacher, admin | User's role |

**Role Field Conditions:**

| Condition | Behavior |
|-----------|----------|
| Editing admin user | Dropdown disabled, hidden input preserves "admin" value |
| Editing non-admin | Dropdown enabled with student/teacher/admin options |

---

### Student ID Field

| Field | Name | ID | Type | Purpose |
|-------|------|----|------|---------|
| Student ID | `student_id` | `#student_id` | `text` | Unique student identifier |

**Student ID Conditions:**

| Role | Field State |
|------|-------------|
| Student | Enabled, value preserved |
| Teacher/Admin | Disabled, value cleared |

---

### Teacher Invite Code Section

**Displayed when:** `user.role == 'teacher' and user.used_invite`

| Element | Content |
|---------|---------|
| Section Title | "Teacher Invite Code" |
| Code Display | `<code>` with invite code (selectable) |
| Assignment Date | When code was assigned to teacher |

---

### Password Reset Section

**Conditional display based on user state:**

#### Case 1: Admin User

| Element | Content |
|---------|---------|
| Info Banner | Blue info box |
| Message | "Administrator passwords must be managed via the server console" |
| CLI Command | `python utility/manage_admin.py reset-password {{ user.username }}` |

#### Case 2: No Email Address

| Element | Content |
|---------|---------|
| Warning Banner | Yellow warning box |
| Message | "Password reset requires an email address" |
| Action Hint | "Add an email above to enable password reset" |

#### Case 3: Has Email (Password Reset Enabled)

| Field | Name | ID | Type | Placeholder | Purpose |
|-------|------|----|------|-------------|---------|
| New Password | `new_password` | `#new_password` | `password` | "Leave blank to keep unchanged" | New password |
| Confirm Password | `confirm_password` | `#confirm_password` | `password` | "Confirm new password" | Password confirmation |

**Note:** Shows target email: "The new password will be sent to {{ user.email }}."

---

### Action Buttons

| Button | Type | Class | Purpose |
|--------|------|-------|---------|
| Cancel | `<a>` | Secondary (white) | Return to dashboard |
| Save Changes | `<button type="submit">` | Primary (indigo) | Submit form |

**Demo Mode:** Both buttons show alert and prevent action.

---

## Form Data Attribute

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `data-is-demo` | `"true"` or `"false"` | Control demo mode behavior in JS |

---

## Backend Processing (POST)

### 1. Personal Info Update

| Field | Validation | Processing |
|-------|------------|------------|
| `first_name` | Required, trimmed | Direct assignment |
| `last_name` | Required, trimmed | Direct assignment |

### 2. Email Update

| Condition | Action |
|-----------|--------|
| New email provided | Check uniqueness (case-insensitive), assign, set `is_test_account = False` |
| Email cleared | Set to `None`, set `is_test_account = True` (for non-admin) |
| Email already exists | Flash error, re-render form |

### 3. Role Change & Invite Code Management

| Transition | Action |
|------------|--------|
| Any → Teacher | Auto-generate invite code (marked as used by this teacher) |
| Teacher → Student | Delete associated invite code |
| Admin role | Cannot be changed via this form |

#### Auto-Generate Invite Code (Promotion to Teacher)

**Condition:** `old_role != "teacher" and new_role == "teacher" and not user.used_invite`

| Step | Action |
|------|--------|
| 1 | Generate unique 10-char uppercase code via `uuid.uuid4().hex[:10].upper()` |
| 2 | Check uniqueness in `InviteCode` table, regenerate if exists |
| 3 | Create `InviteCode(code=code, created_by=current_user.id)` |
| 4 | Set `invite.is_used = True`, `invite.used_by_user_id = user.id`, `invite.used_at = datetime.now()` |
| 5 | Add to session, log action |

**Result:** New teacher has an invite code displayed in the Teacher Invite Code section.

#### Auto-Delete Invite Code (Demotion from Teacher)

**Condition:** `old_role == "teacher" and new_role == "student" and user.used_invite`

| Step | Action |
|------|--------|
| 1 | Get invite code via `user.used_invite` |
| 2 | Delete from database via `db.session.delete(user.used_invite)` |
| 3 | Log action with deleted code value |

**Result:** Demoted user no longer has an associated invite code.

### 4. Student ID Update

| Role | Action |
|------|--------|
| Student | Validate uniqueness, assign |
| Teacher/Admin | Clear to `None` |

### 5. Password Reset

| Validation | Error Message |
|------------|---------------|
| Admin user | "Admin passwords must be reset via server console" |
| No email | "Cannot reset password: user has no email address" |
| Passwords don't match | "Passwords do not match" |
| Password too weak | Dynamic message from `User.validate_password_strength()` |
| Password reuse | Error from `set_password()` |

**On Success:**
- Call `user.set_password(new_password)`
- Reset `failed_login_attempts = 0` and `locked_until = None`
- Send email via `send_admin_change_password_notification(user, new_password)`

> **Security:** Password strength rules, hashing, history/reuse prevention, and admin protections documented in [`security_map.md`](security_map.md).

---

## Flash Messages

| Message | Type | Trigger |
|---------|------|---------|
| "Access denied." | danger | Non-admin access |
| "Email 'X' is already registered to another user." | danger | Duplicate email |
| "Student ID 'X' is already assigned to another user." | danger | Duplicate student ID |
| "Admin passwords must be reset via server console." | danger | Attempt to reset admin password |
| "Cannot reset password: user has no email address." | danger | Missing email for password reset |
| "Passwords do not match." | danger | Confirmation mismatch |
| Password strength error | danger | Weak password |
| Password reuse error | danger | Recent password reused |
| "User 'X' was updated successfully." | success | Successful update |
| "An error occurred while updating the user." | danger | Database error |

---

## JavaScript Functions

**Location:** Lines 177-212

| Function/Logic | Purpose |
|----------------|---------|
| `toggleStudentIdField()` | Enable/disable student ID based on role |
| Role change listener | Trigger student ID field toggle |
| Demo mode handler | Make all inputs readonly, show alerts on interaction |

### Demo Mode Behavior

| Action | Result |
|--------|--------|
| Click any input | Alert "This feature is disabled in DEMO mode" |
| Submit form | Blocked with alert |
| Cancel button | Blocked with alert |

---

## Navigation Links

| Link | Target | Preserved Params |
|------|--------|------------------|
| Back to Dashboard | `/admin` | `page`, `search` |
| Cancel button | `/admin` | `page`, `search` |

---

## Related Backend Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `User.validate_password_strength()` | `models.py` | Check password requirements |
| `User.set_password()` | `models.py` | Hash password, check reuse |
| `send_admin_change_password_notification()` | `scripts/mailer.py` | Send email with new password |

---

## Refactoring Notes

1. **Add new field** → Add to form grid (lines 22-68), update POST handler in `dashboard_routes.py`
2. **Change role options** → Update `<select>` options (lines 52-54) and backend validation
3. **Modify password rules** → Update `User.validate_password_strength()` in `models.py`
4. **Change email template** → Edit `templates/email/admin_password_change.html`
5. **Add validation** → Update POST handler with new checks (lines 438-595 in handler)
6. **Change invite code display** → Update teacher invite section (lines 70-83)
7. **Modify demo mode behavior** → Update JS block (lines 177-212)
