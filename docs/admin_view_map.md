# Admin Console (`admin_view.html`)

**Route:** `GET /dashboard/admin`  
**Handler:** `dashboard_routes.admin_dashboard()` → `dashboard_routes.py:33-178`  
**Template:** `templates/dashboards/admin_view.html`  
**Extends:** `base.html`

> **Note:** Primary admin interface for system management. Includes user directory, wordlist, invite codes, system config, and KPI monitoring.

---

## Page Purpose

Central administrative dashboard providing:
- System KPIs (users, submissions, health)
- User directory with search, pagination, edit/delete
- Wordlist overview with quick edit/delete
- Teacher invite code management
- System configuration toggles

---

## Access Control

| Role | Access |
|------|--------|
| Student | Denied → redirect to index |
| Teacher | Denied → redirect to index |
| Admin | Full access |

---

## Demo Mode

When `is_demo == True`:
- Displays red animated banner: "Demo Mode Active"
- Disables destructive actions (delete, config changes)
- Buttons show `alert('This feature is disabled in DEMO mode')`

---

## Template Variables

| Variable | Type | Source |
|----------|------|--------|
| `stats` | dict | Calculated KPIs |
| `users` | list[dict] | Processed user data |
| `pagination` | Pagination | Flask-SQLAlchemy pagination |
| `words` | list[Word] | All words in curriculum |
| `invite_codes` | list[InviteCode] | All invite codes |
| `config` | dict | System configuration flags |
| `search_query` | str | Current search term |
| `is_demo` | bool | Demo mode flag (from context processor) |

---

## KPI Cards

### Card 1: Total Users

| Field | Source |
|-------|--------|
| Value | `stats.total_users` |
| Subtext | `stats.new_users_today` today |
| Timestamp | `stats.UTC_now` UTC time |

### Card 2: Submissions

| Field | Source |
|-------|--------|
| Value | `stats.total_submissions` |
| Subtext | Across `stats.active_words` active words |

### Card 3: Instructors

| Field | Source |
|-------|--------|
| Value | `stats.total_teachers` |
| Subtext | Managing `stats.total_students` students |

### Card 4: System Status

| Field | Source |
|-------|--------|
| Value | "Online" (hardcoded) |
| Subtext | DB: `stats.db_size` • CPU: `stats.cpu_load`% |

### Stats Calculation (Backend)

```python
stats = {
    "total_users": User.query.count(),
    "new_users_today": User.query.filter(User.created_at >= today_start).count(),
    "UTC_now": datetime.now(timezone.utc).strftime("%H:%M:%S"),
    "total_submissions": Submission.query.count(),
    "active_words": len(words),
    "total_teachers": User.query.filter_by(role="teacher").count(),
    "total_students": User.query.filter_by(role="student").count(),
    "db_size": db_size_str,    # PostgreSQL pg_database_size()
    "cpu_load": cpu_load_percent,  # psutil.cpu_percent()
}
```

---

## Header Actions

| Button | Route | Condition |
|--------|-------|-----------|
| Export Logs | `dashboards.download_logs` | Disabled in demo |
| Add Word | `dashboards.add_word` | Always enabled |

---

## User Directory

### Location: Left panel (3/4 width)

### Search Form

**Method:** GET (AJAX-enhanced)  
**Debounce:** 300ms

| Element | Name | Purpose |
|---------|------|---------|
| Text Input | `search` | Filter by name/username |

### AJAX Search Behavior

1. User types in search box
2. After 300ms debounce, fetch updated page
3. Replace `#admin-user-results` content
4. Update URL history (pushState)

### Table Columns

| Column | Data Source | Notes |
|--------|-------------|-------|
| User Identity | `user.name`, `user.username`, `user.initials` | Avatar + name + username |
| Role | `user.role` | Badge: Admin/Teacher/Student |
| Email | `user.email` | Truncated with tooltip |
| Type | `user.is_test_account` | Legacy (yellow) / Secure (green) |
| Joined | `user.joined_str` | Format: YYYY-MM-DD |
| Actions | - | Edit + Delete buttons |

### Role Badges

| Role | Style |
|------|-------|
| Admin | Gray pill |
| Teacher | Purple pill |
| Student | Blue pill |

### Account Type Badges

| Type | Condition | Style |
|------|-----------|-------|
| Legacy | `is_test_account == True` | Yellow pill |
| Secure | `is_test_account == False` | Green pill |

### Action Buttons

| Button | Route | Conditions |
|--------|-------|------------|
| Edit | `dashboards.edit_user` | Always shown |
| Delete | Opens modal | Hidden for admins, disabled in demo |

### Pagination

**Per Page:** 10 users

| Element | Content |
|---------|---------|
| Info | "Showing X of Y users" |
| Previous | Link or disabled |
| Next | Link or disabled |

---

## Wordlist Panel

### Location: Right panel (1/4 width)

### Display

| Element | Content |
|---------|---------|
| Header | "Wordlist" + word count badge |
| Max Height | 600px (scrollable) |

### Per Word Row

| Element | Content |
|---------|---------|
| Word Text | Bold |
| IPA | Monospace font |
| Edit Icon | Link to `dashboards.edit_word` |
| Delete Icon | Opens word delete modal |

### Footer Link

**Text:** "Manage All Words"  
**Route:** `dashboards.manage_all_words`

---

## Teacher Invites Section

### Location: Below user directory (3/4 width)

### Generate Button

| Mode | Action |
|------|--------|
| Normal | POST to `dashboards.generate_invite` |
| Demo | Alert disabled message |

### Generate Invite Handler

**Route:** `POST /dashboard/admin/invite/generate`  
**Handler:** `dashboard_routes.generate_invite()` → `dashboard_routes.py:1053-1079`

```python
code = uuid.uuid4().hex[:10].upper()
# Ensure uniqueness via retry loop
new_invite = InviteCode(code=code, created_by=current_user.id)
```

### Invite Code Display

| Field | Display |
|-------|---------|
| Code | Monospace, selectable |
| Status | "Active" (blue) / "Used" (green) / Username (green) |
| Creator | "by @username" (purple) |
| Delete | Icon (only for unused codes) |

### Delete Invite Handler

**Route:** `POST /dashboard/admin/invite/<int:invite_id>/delete`  
**Handler:** `dashboard_routes.delete_invite()` → `dashboard_routes.py:1082-1108`

**Security:** Cannot delete used invite codes

---

## System Config Panel

### Location: Right panel (1/4 width), below wordlist

### Toggle Switches

| Setting | Key | Default | Ring Color |
|---------|-----|---------|------------|
| Registration Open | `registration_open` | True | Indigo |
| Maintenance Mode | `maintenance_mode` | False | Red |
| Enable Logging | `enable_logging` | False | Indigo |

### Config Update API

**Route:** `POST /dashboard/admin/config/update`  
**Handler:** `dashboard_routes.update_config()` → `dashboard_routes.py:631-658`

**Request:**
```json
{ "key": "registration_open", "value": true }
```

**Response:**
```json
{ "success": true, "key": "registration_open", "value": true }
```

**Valid Keys:** `registration_open`, `maintenance_mode`, `enable_logging`

---

## User Delete Modal

**ID:** `#delete-modal`

### Elements

| Element | ID | Purpose |
|---------|----|---------|
| User Name | `#modal-user-name` | Display target user |
| Delete User Checkbox | `#delete-user-checkbox` | Enable deletion |
| Delete Submissions Checkbox | `#delete-user-submissions-checkbox` | Cascade option |
| Confirm Button | `#confirm-delete-btn` | Submit form |
| Cancel Button | `#cancel-btn` | Close modal |

### Checkbox Logic

1. "Delete User Account" must be checked first
2. "Delete All Student Submissions" becomes enabled
3. Both must be checked to enable submit button

### Delete User Handler

**Route:** `POST /dashboard/admin/user/<int:user_id>/delete`  
**Handler:** `dashboard_routes.delete_user()` → `dashboard_routes.py:918-950`

**Safety Checks:**
- Cannot delete own account
- Cannot delete other admins via UI
- Deletes user's upload directory
- Clears `used_by_user_id` on associated invite code

---

## Word Delete Modal

**ID:** `#word-delete-modal`

### Elements

| Element | ID | Purpose |
|---------|----|---------|
| Word Name | `#modal-word-name` | Display target word |
| Delete Word Checkbox | `#delete-word-checkbox` | Enable deletion |
| Delete Submissions Checkbox | `#delete-submissions-checkbox` | Cascade option |
| Submit Button | `#word-delete-submit-btn` | Submit form |
| Cancel Button | `#word-cancel-btn` | Close modal |

### Checkbox Logic

1. "Delete Word Entry" must be checked first
2. "Delete All Student Submissions" becomes enabled
3. Submit enabled when word checkbox checked

### Delete Word Handler

**Route:** `POST /dashboard/admin/word/<int:word_id>/delete`  
**Handler:** `dashboard_routes.delete_word()` (defined elsewhere)

---

## Download Logs Handler

**Route:** `GET /dashboard/admin/logs/download`  
**Handler:** `dashboard_routes.download_logs()` → `dashboard_routes.py:661-677`

**Returns:** `logs/pronounce.log` as attachment

---

## JavaScript Functions

### User Delete Modal

| Function | Purpose |
|----------|---------|
| `openDeleteModal(userId, userName)` | Show modal, set form action |
| `closeDeleteModal()` | Hide modal, reset state |

### Word Delete Modal

| Function | Purpose |
|----------|---------|
| `openWordDeleteModal(wordId, wordName)` | Show modal, set form action |
| `closeWordDeleteModal()` | Hide modal, reset checkboxes |

### System Config Toggles

**Event:** `DOMContentLoaded`

```javascript
toggles.forEach(toggle => {
    toggle.addEventListener('change', (event) => {
        const key = event.target.dataset.key;
        const value = event.target.checked;
        fetch('/dashboard/admin/config/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value }),
        });
    });
});
```

### AJAX Search

**Event:** Input with 300ms debounce

```javascript
const performSearch = (searchTerm) => {
    // Update URL with search param
    // Fetch page, replace #admin-user-results
    // Push state to history
};
```

---

## Backend Query (User Directory)

```python
# Base query
users_query = User.query

# Apply search filter
if search_query:
    search_term = f"%{search_query}%"
    users_query = users_query.filter(
        db.or_(
            User.username.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
        )
    )

# Paginate
users_pagination = users_query.order_by(User.created_at.desc()).paginate(
    page=page, per_page=10, error_out=False
)
```

### User Data Processing

```python
user_data = [{
    "id": u.id,
    "name": f"{u.first_name} {u.last_name}",
    "username": u.username,
    "role": u.role,
    "initials": (u.first_name[0] + u.last_name[0]).upper(),
    "joined_str": u.created_at.strftime("%Y-%m-%d"),
    "email": u.email,
    "is_test_account": u.is_test_account,
} for u in users_pagination.items]
```

---

## Flash Messages

| Message | Type | Trigger |
|---------|------|---------|
| "Access denied. Administrator privileges required." | danger | Non-admin access |
| "Generated new invite code: {code}" | success | Invite generated |
| "Failed to generate invite code." | danger | DB error |
| "Invite code deleted." | info | Successful delete |
| "Cannot delete a used invite code..." | warning | Delete used invite |
| "You cannot delete your own account." | danger | Self-delete attempt |
| "Security Alert: Administrators cannot be deleted..." | warning | Admin delete attempt |
| "Log file not found..." | warning | Missing log file |

---

## Navigation Links

| Link | Target |
|------|--------|
| Add Word | `/dashboard/admin/word/add` |
| Edit User | `/dashboard/admin/user/{id}/edit` |
| Edit Word | `/dashboard/admin/word/{id}/edit` |
| Manage All Words | `/dashboard/admin/words` |
| Export Logs | `/dashboard/admin/logs/download` |

---

## Refactoring Notes

1. **Add bulk user delete** → Add checkboxes + bulk action button
2. **Add user export** → CSV download of user list
3. **Add invite code expiration** → Add expiry date field
4. **Add real-time system metrics** → WebSocket for CPU/DB updates
5. **Add audit log viewer** → New section for system events
6. **Change pagination size** → Update `per_page=10` in handler
7. **Add role filter** → Dropdown to filter by admin/teacher/student
8. **Add advanced search** → Filter by date range, role, account type
9. **Add dark mode toggle** → System config for UI theme
10. **Separate invite management** → Move to dedicated page if list grows
