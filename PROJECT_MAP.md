# Pronounce-Web — Project Map

Detailed code documentation: classes, methods, functions, and component deep-dives.

> **See Also:** `INDEX.md` for routes, database schema, configuration

---

## Analysis Engine (`analysis_engine.py`)

Acoustic formant analysis for vowel pronunciation scoring.

### Functions

| Function | Purpose |
|----------|---------|
| `hz_to_bark(f)` | Hz → Bark scale |
| `get_vowel_type(vowel)` | "monophthong" or "diphthong" |
| `load_audio_mono(path, sr)` | Load, mono, resample, normalize |
| `find_syllable_nucleus(sound)` | Find loudest voiced segment |
| `measure_formants(sound, segment, points, ceiling)` | Measure F1/F2 |
| `analyze_formants_from_path(path, vowel, is_ref)` | Full analysis |
| `get_articulatory_feedback(f1n, f2n, f1r, f2r)` | Generate feedback |
| `calculate_distance(meas_s, meas_r, alpha)` | Hz and Bark distance |
| `process_submission(submission_id)` | **Main entry** — full pipeline |

### Pipeline

```
1. Load submission → resolve paths
2. Analyze formants (with deep voice correction)
3. Calculate cumulative VTLN alpha (median of history)
4. Normalize and calculate Bark distance
5. Save to AnalysisResult
6. Mark outlier if distance > 5.0 Bark
```

### Deep Voice Correction

For back vowels (`uː`, `ʊ`, `ɔː`, etc.) with high F2:
- Retry with 4000 Hz ceiling instead of 5500 Hz

---

## Admin CLI (`utility/manage_admin.py`)

Secure admin account management (not via web UI).

### Commands

| Command | Purpose |
|---------|---------|
| `create <user>` | Create admin or promote user |
| `delete <user>` | Delete admin (prevents last admin) |
| `reset-password <user>` | Reset via CLI |
| `bulk-reset --role <role>` | Reset all users of role |
| `list` | List all admins |
| `fix-legacy-accounts` | Sync test account status |
| `toggle-demo` | Toggle demo mode + cleanup |

---

## Frontend (`static/js/script.js`)

Recording, playback, visualization, API communication.

### Config

```javascript
Config = {
    AUTO_STOP_SILENCE_MS: 1500,
    MAX_RECORDING_MS: 5000,
    TARGET_RATE: 16000,
    COLORS: { MODEL: '#0ea5e9', USER: '#f43f5e' }
}
```

### UI Elements

| ID | Purpose |
|----|---------|
| `word-list` | Word list container |
| `play-sample` | Play reference |
| `record-start/stop` | Recording controls |
| `submit-recording` | Submit button |
| `difference-waveform-container` | Waveform area |
| `test-type` | Pre/Post selector |
| `progress-bar-fill` | Progress bar |

### Key Functions

| Function | Purpose |
|----------|---------|
| `loadWordList()` | Fetch words, build UI |
| `fetchUserProgress()` | Get completed words |
| `startNoiseMonitor()` | Mic monitoring |
| `stopRecording()` | Stop, process, upload |
| `renderComparison()` | Overlay waveforms |
| `autoProceed()` | Auto-advance |

### User Flow

```
1. loadWordList() → fetchUserProgress()
2. Click word → select
3. Click "Play Sample" → unlock record
4. Click "Record" → AudioWorklet starts
5. Auto-stop after silence
6. Upload to /api/process_audio
7. Submit → Celery task → poll status
8. Display score → autoProceed()
```

---

## All Classes (`models.py`)

### SystemConfig

| Method | Description |
|--------|-------------|
| `get(key, default)` | Get value |
| `get_bool(key, default)` | Get as boolean |
| `set(key, value)` | Set value |
| `is_demo_mode()` | Check demo mode |

### User

| Method | Description |
|--------|-------------|
| `set_password(password)` | Hash + add to history |
| `check_password(password)` | Verify |
| `get_reset_password_token()` | Generate token |
| `verify_reset_password_token(token)` | Verify token |
| `validate_password_strength(password)` | Check complexity |

**Relationships:** submissions, reset_tokens, password_history, created_invites, used_invite

### Submission

**Relationships:** user, target_word, analysis (cascade delete)

### AnalysisResult

**Fields:** f1_raw, f2_raw, f1_ref, f2_ref, scaling_factor, f1_norm, f2_norm, distance_hz, distance_bark, is_deep_voice_corrected, is_outlier

### InviteCode

**Relationships:** creator, used_by (one-to-one)

---

## All Functions by File

### flask_app.py

`celery_init_app`, `load_user`, `check_for_maintenance`, `inject_global_vars`, `index`, `about`, `manual`, `init_metrics`, `log_event`, `get_word_list`, `get_progress`, `api_process_audio`, `serve_upload`, `submit_recording`, `get_task_status`, `warmup_audio_engine`

### auth_routes.py

`login`, `register`, `check_invite`, `logout`, `reset_password_request`, `reset_password`

### dashboard_routes.py

`admin_dashboard`, `teacher_dashboard`, `student_detail`, `research_dashboard`, `edit_user`, `update_config`, `download_logs`, `add_word`, `edit_word`, `delete_word`, `manage_all_words`, `delete_user`, `get_analysis_data`, `generate_invite`, `delete_invite`

### scripts/

- `audio_processing.py`: `process_audio_data`
- `mailer.py`: `send_email`, `send_password_reset_email`, `send_admin_change_password_notification`
- `parser.py`: `get_word_data`, `update_word_list`

### tasks.py

`async_process_submission`

---

## Import Graph

```
flask_app.py
├── config.Config
├── models (db, mail, User, Word, Submission, SystemConfig)
├── auth_routes.auth
│   └── models, scripts.mailer
├── dashboard_routes.dashboards
│   └── models, scripts.parser, scripts.audio_processing, scripts.mailer
└── tasks
    └── analysis_engine → models

utility/manage_admin.py
├── flask_app (app, db, User)
├── models
└── scripts.mailer
```
