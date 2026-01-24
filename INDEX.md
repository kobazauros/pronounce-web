# Pronounce-Web — Master Index

Web application for English vowel pronunciation training using acoustic analysis.

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `PROJECT_MAP.md` | Detailed code: classes, functions, components |
| `MAIN_APP_FILES.md` | Runtime files and dependencies |
| `UNUSED_FILES.md` | Cleanup tracking |

---

## Application Features

### Core Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| Vowel Pronunciation Training | Record words, analyze formants (F1/F2), provide feedback | `analysis_engine.py` |
| Pre/Post Testing | Two-stage curriculum with baseline and final assessment | `flask_app.py`, `script.js` |
| Real-time Waveform Visualization | WaveSurfer.js overlay comparing student vs reference | `script.js` |
| Automatic Silence Detection | Auto-stop after 1.5s silence or 5s max | `script.js` |
| VTLN Normalization | Vocal Tract Length Normalization using cumulative median | `analysis_engine.py` |
| Deep Voice Correction | 4000Hz ceiling for back vowels | `analysis_engine.py` |
| Articulatory Feedback | "Move tongue forward/back", "Open/close mouth" | `analysis_engine.py` |

### User Management

| Feature | Description | Implementation |
|---------|-------------|----------------|
| Role-Based Access | Student, Teacher, Admin permissions | `models.py`, `auth_routes.py` |
| Account Lockout | 5 failed attempts = 15 minute lockout | `auth_routes.py` |
| Password Complexity | 8+ chars, mixed case, number, special char | `models.py` |
| Password Reset | Secure token-based email reset | `auth_routes.py`, `mailer.py` |
| Invite Codes | Teacher registration requires admin invite | `models.py`, `auth_routes.py` |
| Demo Mode | Guest login for demonstrations | `auth_routes.py` |

### Dashboard Features

| Role | Features |
|------|----------|
| **Admin** | User CRUD, word management, system config, invite codes, logs |
| **Teacher** | Class stats, student progress, research data, F1/F2 scatter |
| **Student** | Recording interface, progress tracking |

---

## Database Schema

### Tables

| Table | Model | Description |
|-------|-------|-------------|
| `system_config` | `SystemConfig` | Key-value settings |
| `password_history` | `PasswordHistory` | Password reuse prevention |
| `users` | `User` | User accounts |
| `words` | `Word` | Curriculum (20 words) |
| `submissions` | `Submission` | Audio recordings |
| `analysis_results` | `AnalysisResult` | Acoustic analysis |
| `invite_codes` | `InviteCode` | Teacher registration codes |
| `password_reset_tokens` | `PasswordResetToken` | Secure reset tokens |

### Key Fields

**users:** id, username, password_hash, first_name, last_name, student_id, email, is_test_account, is_guest, failed_login_attempts, locked_until, role, consented_at, created_at

**words:** id, text, sequence_order, ipa, vowels, stressed_vowel, audio_path

**submissions:** id, user_id, word_id, test_type, file_path, file_size_bytes, score, timestamp

**analysis_results:** id, submission_id, f1_raw, f2_raw, f1_ref, f2_ref, scaling_factor, f1_norm, f2_norm, distance_hz, distance_bark, is_deep_voice_corrected, is_outlier

---

## All Routes

### Main App (`flask_app.py`)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Home page |
| GET | `/about`, `/manual` | Info pages |
| POST | `/api/log_event` | Analytics |
| GET | `/api/word_list` | Get words |
| GET | `/get_progress` | User progress |
| POST | `/api/process_audio` | Process audio |
| POST | `/api/submit_recording` | Submit recording |
| GET | `/api/status/<task_id>` | Task status |

### Auth (`/auth`)

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/login`, `/register` | Auth forms |
| GET | `/logout` | Logout |
| GET/POST | `/reset_password_request` | Request reset |
| GET/POST | `/reset_password/<token>` | Reset password |

### Dashboard (`/dashboard`)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/admin` | Admin dashboard |
| GET | `/teacher` | Teacher dashboard |
| GET | `/teacher/student/<id>` | Student detail |
| GET | `/teacher/research` | Research view |
| GET/POST | `/admin/user/<id>/edit` | Edit user |
| GET/POST | `/admin/word/*` | Word management |
| POST | `/admin/invite/*` | Invite codes |

---

## CLI Commands

### Flask

```bash
flask run                    # Dev server
flask db upgrade             # Apply migrations
flask process-submission <id> # Manual processing
flask init-words             # Populate words
```

### Admin CLI (`utility/manage_admin.py`)

```bash
python utility/manage_admin.py create <user>      # Create admin
python utility/manage_admin.py delete <user>      # Delete admin
python utility/manage_admin.py reset-password <user>
python utility/manage_admin.py bulk-reset --role student
python utility/manage_admin.py list
python utility/manage_admin.py fix-legacy-accounts
python utility/manage_admin.py toggle-demo
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret |
| `DATABASE_URL` | Yes | PostgreSQL URL |
| `MAIL_SERVER` | No | SMTP server |
| `CELERY_BROKER_URL` | No | Redis broker |

### System Config (Database)

| Key | Default | Description |
|-----|---------|-------------|
| `demo_mode` | False | Guest login |
| `maintenance_mode` | False | Maintenance page |
| `registration_open` | True | Allow registration |
| `enable_logging` | False | Frontend logging |
