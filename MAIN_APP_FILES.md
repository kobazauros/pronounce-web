# Main Application Files

Files loaded at runtime (Flask, Gunicorn, Celery).

> **See Also:** `PROJECT_MAP.md` for code details

---

## Summary

| Category | Count |
|----------|-------|
| Entry Points | 4 |
| Core Modules | 5 |
| Runtime Scripts | 3 |
| Templates | 19 |
| Static Assets | 27 |
| **Total** | **58** |

---

## Entry Points

| File | Role |
|------|------|
| `flask_app.py` | Main app, routes, Celery |
| `wsgi.py` | WSGI entry (production) |
| `gunicorn_config.py` | Server settings |
| `config.py` | Configuration |

### Startup Flow

```
gunicorn → wsgi.py → flask_app.py
                      ├── config.Config
                      ├── models (db, mail)
                      ├── auth_routes
                      ├── dashboard_routes
                      └── warmup_audio_engine()
```

---

## Core Modules

| File | Exports |
|------|---------|
| `models.py` | db, mail, 8 model classes |
| `auth_routes.py` | auth Blueprint |
| `dashboard_routes.py` | dashboards Blueprint |
| `analysis_engine.py` | 9 analysis functions |
| `tasks.py` | async_process_submission |

---

## Runtime Scripts

| File | Imported By |
|------|-------------|
| `scripts/audio_processing.py` | flask_app, dashboard_routes |
| `scripts/mailer.py` | auth_routes, dashboard_routes |
| `scripts/parser.py` | flask_app, dashboard_routes |

---

## Templates

**Layout:** base.html

**Auth:** login.html, register.html, auth/reset_password*.html

**Pages:** index.html, about.html, manual.html, maintenance.html

**Dashboards:** admin_view, teacher_view, student_detail, research_view, edit_user, manage_word, manage_all_words

**Email:** reset_password.html/.txt, admin_password_change.html/.txt

---

## Static Assets

| Type | Files |
|------|-------|
| CSS | styles.css |
| JS | script.js, recorder-worklet.js |
| Audio | 21 MP3 files + index.json |
| Images | 6 files |

---

## Support Files (NOT Runtime)

| File | Purpose |
|------|---------|
| `utility/manage_admin.py` | Admin CLI |
| `utility/manage_project.py` | Deployment |
| `utility/fix_sequences.py` | Postgres sequences |
| `migrations/*` | DB migrations |

---

## Dependencies

| Component | Dependency | If Missing |
|-----------|------------|------------|
| App | models.py, config.py | Won't start |
| Audio | librosa, soundfile | Upload fails |
| Analysis | parselmouth | Analysis fails |
| Tasks | Celery, Redis | Tasks queue |
| Email | Flask-Mail, SMTP | Silent fail |

---

## Request Flow

```
HTTP → Gunicorn → Flask
        ↓
    check_for_maintenance()
        ↓
    Route Handler
    ├── Auth (models, mailer)
    ├── Dashboard (models, audio, parser)
    └── API (audio, Celery)
            ↓
        Celery Worker → analysis_engine → models
```
