# Base Template (`base.html`)

**Template:** `templates/base.html`  
**Type:** Layout template (extended by all pages)  
**JavaScript:** `static/js/script.js`  
**CSS:** `static/css/styles.css`

---

## Purpose

Master layout template providing:
- Navigation bar with role-based menu
- Flash message display
- Footer with project links
- Global keyboard shortcuts

---

## Template Blocks (for child templates)

| Block | Location | Purpose |
|-------|----------|---------|
| `{% block title %}` | Line 7 | Page title in `<title>` tag |
| `{% block head %}` | Line 12 | Additional `<head>` content (scripts, styles) |
| `{% block content %}` | Line 108 | Main page content area |

---

## External Dependencies

| Resource | CDN/Path | Purpose |
|----------|----------|---------|
| Tailwind CSS | `cdn.tailwindcss.com` | CSS framework |
| Font Awesome 6 | `cdnjs.cloudflare.com` | Icon library |
| WaveSurfer.js 7 | `unpkg.com` | Audio waveform visualization |
| Custom CSS | `static/css/styles.css` | Project-specific styles |
| Custom JS | `static/js/script.js` | Main application JavaScript |

---

## UI Sections

### 1. Navigation Bar

| Element | Condition | Purpose |
|---------|-----------|---------|
| Logo/Home Link | Always | Links to `index` route |
| Demo Badge | `is_demo=True` | Red badge indicating demo mode |
| Connection Status | `role='student'` | WebSocket status indicator (hidden on mobile) |
| Teacher Menu | `role='teacher'` | Dashboard, Research links |
| Admin Menu | `role='admin'` | Studio, Admin Panel, Teacher View, Research links |
| User Info | Authenticated | Shows first/last name (hidden on mobile) |
| Logout Button | Authenticated | Links to `auth.logout` |
| Login Link | Not authenticated | Links to `auth.login` |
| Register Button | Not authenticated | Links to `auth.register` (disabled in demo) |

### 2. Navigation Elements by Role

**Student:**
| Element | ID | Purpose |
|---------|----|---------|
| Status Dot | `#status-dot` | Connection status indicator |
| Status Text | `#connection-status` | "Connecting...", "Connected", etc. |

**Teacher:**
| Link | Route | Text |
|------|-------|------|
| Dashboard | `dashboards.teacher_dashboard` | Dashboard |
| Research | `dashboards.research_dashboard` | Research |

**Admin:**
| Link | Route | Text |
|------|-------|------|
| Studio | `index` | Studio |
| Admin Panel | `dashboards.admin_dashboard` | Admin Panel |
| Teacher View | `dashboards.teacher_dashboard` | Teacher View |
| Research | `dashboards.research_dashboard` | Research |

### 3. Flash Messages Area

| Category | Background | Border | Icon |
|----------|------------|--------|------|
| `danger` | `bg-rose-50` | `border-rose-200` | `fa-exclamation-circle` |
| `success` | `bg-emerald-50` | `border-emerald-200` | `fa-check-circle` |
| `warning` | `bg-amber-50` | `border-amber-200` | `fa-info-circle` |
| `info` (default) | `bg-sky-50` | `border-sky-200` | `fa-info-circle` |

### 4. Footer

| Link | Route | Text |
|------|-------|------|
| About | `about` | About Project |
| Manual | `manual` | User Manual |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `is_demo` | Context processor (`flask_app.py:146`) | Show demo badge, disable register |
| `current_user` | Flask-Login | User object for auth state and role |
| `current_user.is_authenticated` | Flask-Login | Check if logged in |
| `current_user.role` | User model | Determine menu visibility |
| `current_user.first_name` | User model | Display in nav |
| `current_user.last_name` | User model | Display in nav |

---

## JavaScript (embedded)

**Location:** Lines 128-136

| Action | Trigger | Effect |
|--------|---------|--------|
| F1 Shortcut | `keydown` event | Navigates to manual page |

---

## Navigation Routes Summary

| Route | Handler | Access |
|-------|---------|--------|
| `index` | `flask_app.index()` | All |
| `auth.login` | `auth_routes.login()` | Unauthenticated |
| `auth.logout` | `auth_routes.logout()` | Authenticated |
| `auth.register` | `auth_routes.register()` | Unauthenticated (disabled in demo) |
| `dashboards.admin_dashboard` | `dashboard_routes.admin_dashboard()` | Admin |
| `dashboards.teacher_dashboard` | `dashboard_routes.teacher_dashboard()` | Teacher, Admin |
| `dashboards.research_dashboard` | `dashboard_routes.research_dashboard()` | Teacher, Admin |
| `about` | `flask_app.about()` | All |
| `manual` | `flask_app.manual()` | All |

---

## Responsive Behavior

| Element | Mobile | Desktop |
|---------|--------|---------|
| Connection Status | Hidden | Visible |
| Role-specific Menu | Hidden | Visible |
| User Name Display | Hidden | Visible |
| Logo Text | Smaller | Larger |
| Register Button | Smaller padding | Larger padding |

---

## Refactoring Notes

1. **Change app name** → Update logo text (lines 26-27)
2. **Add new nav link** → Add to appropriate role block (lines 41-62)
3. **Change flash message style** → Update category classes (lines 95-99)
4. **Add global shortcut** → Add to embedded script (lines 128-136)
5. **Change footer links** → Update footer section (lines 117-124)
6. **Modify user display** → Update authenticated user section (lines 65-69)
