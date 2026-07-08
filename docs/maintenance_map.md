# Maintenance Page (`maintenance.html`)

**Template:** `templates/maintenance.html`  
**Type:** Standalone page (does NOT extend `base.html`)  
**Rendered by:** `auth_routes.login()` when maintenance mode is active

> **Note:** This is a standalone HTML page with its own `<html>`, `<head>`, and `<body>` tags. It does not use the base template.

---

## Page Purpose

Displayed to non-admin users when the system is in maintenance mode. Blocks access to the application during updates or scheduled downtime.

---

## When Displayed

| Condition | Result |
|-----------|--------|
| Maintenance mode ON + User is admin | Normal login proceeds |
| Maintenance mode ON + User is NOT admin | This page rendered with HTTP 503 |

**Trigger location:** `auth_routes.py` login handler

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| (none) | — | Static content page |

---

## UI Elements

| Element | Type | Content |
|---------|------|---------|
| Clock Icon | SVG | Visual indicator of maintenance |
| Title | `<h1>` | "Under Maintenance" |
| Message 1 | `<p>` | "Our site is currently undergoing scheduled maintenance..." |
| Message 2 | `<p>` | "We'll be back online shortly. Thank you for your patience!" |

---

## External Dependencies

| Resource | CDN/Path | Purpose |
|----------|----------|---------|
| Tailwind CSS | `cdn.tailwindcss.com` | CSS framework |

---

## Page Structure

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Site Maintenance</title>
    <script src="tailwindcss"></script>
  </head>
  <body>
    <div class="centered-container">
      <svg clock-icon />
      <h1>Under Maintenance</h1>
      <p>Message 1</p>
      <p>Message 2</p>
    </div>
  </body>
</html>
```

---

## CSS Classes Used

| Class | Purpose |
|-------|---------|
| `min-h-screen` | Full viewport height |
| `flex flex-col items-center justify-center` | Center content vertically/horizontally |
| `text-center` | Center text |
| `bg-gray-100` | Light gray background |
| `text-gray-400/600/800` | Text color variations |
| `max-w-lg` | Limit content width |

---

## Navigation

| Action | Destination |
|--------|-------------|
| (none) | No links on this page - user must wait |

---

## Related Configuration

| Setting | Location | Purpose |
|---------|----------|---------|
| Maintenance Mode Toggle | Admin Panel → System Config | Enable/disable maintenance |
| `SystemConfig.get_bool("maintenance_mode")` | `models.py` | Check maintenance status |

---

## Refactoring Notes

1. **Change maintenance message** → Update `<p>` content (lines 14-18)
2. **Add contact info** → Add new element after message
3. **Change icon** → Replace SVG (line 12)
4. **Add estimated downtime** → Add dynamic content (requires passing variable from handler)
5. **Customize styling** → Update Tailwind classes
