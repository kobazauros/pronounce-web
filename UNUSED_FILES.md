# Unused Files - Cleanup List

Files that are unused, deprecated, or candidates for removal.

---

## Safe to Delete

| File | Reason |
|------|--------|
| `temp_old_edit_user.html` | Old backup |
| `repro_error.txt` | Test output |
| `test_output.txt` | Pytest output |

---

## Review Required

| File | Issue |
|------|-------|
| `docs/audio_processing_v2.md` | Not linked |
| `docs/deployment.md` | Duplicate of deployment_guide.md |
| `docs/postgres_setup_summary.md` | Not referenced |
| `docs/readme.md` | Duplicate of README.md |
| `docs/working_with_antigravity.md` | Not referenced |
| `docs/feature_password_security.md` | Not referenced |
| `docs/tasks/postgres_setup_tasks.md` | May be completed |

---

## Keep (Support)

| File | Purpose |
|------|---------|
| `scripts/db_health_check.sh` | Maintenance |
| `run_worker.bat` | Windows Celery |
| `utility/manage_admin.py` | Admin CLI |
| `utility/fix_sequences.py` | Postgres recovery |
| `utility/manage_project.py` | Deployment |

---

## Confirmed USED

**Python:** flask_app.py, wsgi.py, gunicorn_config.py, config.py, models.py, auth_routes.py, dashboard_routes.py, analysis_engine.py, tasks.py, scripts/*.py, utility/*.py

**Templates:** All in templates/

**Static:** All in static/

**Migrations:** All in migrations/

**Documentation:** README.md, INDEX.md, PROJECT_MAP.md, MAIN_APP_FILES.md, UNUSED_FILES.md, docs/deployment_guide.md, docs/development.md, docs/road_map.md, docs/analyse_vowel.md, docs/database_sync.md

---

## Action Items

### Immediate

- [ ] Delete `temp_old_edit_user.html`
- [ ] Delete `repro_error.txt`
- [ ] Delete `test_output.txt`

### Before Release

- [ ] Merge docs/deployment.md → deployment_guide.md
- [ ] Delete docs/readme.md
- [ ] Archive postgres setup docs
