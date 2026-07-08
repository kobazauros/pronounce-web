# Concurrency Map - Audio Processing Pipeline

**Focus:** Audio recording, processing, analysis, and storage flow with Redis/Celery async task handling.

---

## Overview

| Stage | Sync/Async | Location |
|-------|------------|----------|
| Example Word Playback | Sync (client) | `script.js` → static files |
| User Recording | Sync (client) | `script.js` → Web Audio API |
| Audio Processing | Sync (server) | `/api/process_audio` → `audio_processing.py` |
| User Playback | Sync (client) | `script.js` → processed file |
| Submission | Sync (server) | `/api/submit_recording` → creates DB record |
| Acoustic Analysis | **Async (Celery)** | `tasks.async_process_submission` |
| Result Polling | Sync (client) | `/api/status/<task_id>` |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 CLIENT (Browser)                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   [1] SELECT WORD ─► loadWordList() ─► GET /api/word_list                       │
│                              │                                                   │
│                              ▼                                                   │
│   [2] PLAY EXAMPLE ─► fetch(/static/audio/{word}.mp3) ─► WaveSurfer.js          │
│                              │                                                   │
│                              ▼                                                   │
│   [3] RECORD ─► Web Audio API (AudioWorklet) ─► recordedBlob                    │
│                              │                                                   │
│                              ▼                                                   │
│   [4] PROCESS ─► POST /api/process_audio ─────────────────────────┐             │
│                              │                                     │             │
│                              ▼                                     │             │
│   [5] PLAY USER ─► fetch(processedUrl) ─► WaveSurfer.js           │             │
│                              │                                     │             │
│                              ▼                                     │             │
│   [6] SUBMIT ─► POST /api/submit_recording ───────────────────────┼─┐           │
│                              │                                     │ │           │
│                              ▼                                     │ │           │
│   [7] POLL ─► GET /api/status/{task_id} (loop until done) ────────┼─┼─┐         │
│                              │                                     │ │ │         │
└──────────────────────────────┼─────────────────────────────────────┼─┼─┼─────────┘
                               │                                     │ │ │
┌──────────────────────────────┼─────────────────────────────────────┼─┼─┼─────────┐
│                          FLASK SERVER                              │ │ │         │
├──────────────────────────────┼─────────────────────────────────────┼─┼─┼─────────┤
│                              │                                     │ │ │         │
│   ┌──────────────────────────┴───────────────────┐                 │ │ │         │
│   │         /api/process_audio (SYNC)            │◄────────────────┘ │ │         │
│   │   • Receive raw audio blob                   │                   │ │         │
│   │   • Trim silence, normalize, convert to MP3  │                   │ │         │
│   │   • Save to submissions/{user_id}/{uuid}.mp3 │                   │ │         │
│   │   • Return { url, path }                     │                   │ │         │
│   └──────────────────────────────────────────────┘                   │ │         │
│                                                                      │ │         │
│   ┌──────────────────────────────────────────────┐                   │ │         │
│   │       /api/submit_recording (SYNC)           │◄──────────────────┘ │         │
│   │   • Create Submission record in DB           │                     │         │
│   │   • Dispatch Celery task ─────────────────────────────────────────┐│         │
│   │   • Return { status: "processing", task_id } │                    ││         │
│   └──────────────────────────────────────────────┘                    ││         │
│                                                                       ││         │
│   ┌──────────────────────────────────────────────┐                    ││         │
│   │         /api/status/{task_id} (SYNC)         │◄───────────────────┼┘         │
│   │   • Query AsyncResult from Redis             │                    │          │
│   │   • Return { status, score, analysis }       │                    │          │
│   └──────────────────────────────────────────────┘                    │          │
│                                                                       │          │
└───────────────────────────────────────────────────────────────────────┼──────────┘
                                                                        │
┌───────────────────────────────────────────────────────────────────────┼──────────┐
│                            REDIS (Message Broker)                     │          │
├───────────────────────────────────────────────────────────────────────┼──────────┤
│   • Task Queue: tasks.async_process_submission                        │          │
│   • Result Backend: Task status & return values                       │          │
│   • Connection: redis://localhost:6379/0                              │◄─────────┘
└───────────────────────────────────────────────────────────────────────┬──────────┘
                                                                        │
┌───────────────────────────────────────────────────────────────────────┼──────────┐
│                            CELERY WORKER                              │          │
├───────────────────────────────────────────────────────────────────────┼──────────┤
│                                                                       │          │
│   ┌─────────────────────────────────────────────────────────┐         │          │
│   │     async_process_submission(submission_id) [ASYNC]     │◄────────┘          │
│   │                                                         │                    │
│   │   1. Load Submission from DB                            │                    │
│   │   2. Call process_submission() ─────────────────────────┼───┐                │
│   │   3. Calculate score from distance_bark                 │   │                │
│   │   4. Generate recommendations                           │   │                │
│   │   5. Update Submission.score in DB                      │   │                │
│   │   6. Return result dict to Redis                        │   │                │
│   └─────────────────────────────────────────────────────────┘   │                │
│                                                                 │                │
│   ┌─────────────────────────────────────────────────────────┐   │                │
│   │        process_submission() - analysis_engine.py        │◄──┘                │
│   │                                                         │                    │
│   │   1. Load student audio & reference audio               │                    │
│   │   2. Analyze formants (F1, F2) using Praat/Parselmouth  │                    │
│   │   3. Calculate VTLN alpha (cumulative median)           │                    │
│   │   4. Normalize student formants                         │                    │
│   │   5. Calculate Bark distance                            │                    │
│   │   6. Save AnalysisResult to DB                          │                    │
│   └─────────────────────────────────────────────────────────┘                    │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Example Word Playback

**Flow:** Client-only, synchronous

```
User clicks Play Example
    │
    ▼
script.js: UI.playBtn.onclick
    │
    ▼
fetch(`/static/audio/${selectedWord}.mp3`)
    │
    ▼
AudioContext.decodeAudioData()
    │
    ▼
WaveSurfer.js visualization + playback
```

| Component | Detail |
|-----------|--------|
| Audio Source | `/static/audio/{word}.mp3` |
| Visualization | WaveSurfer.js (`sampleWS`) |
| Color | Purple (`Config.COLORS.MODEL`) |

---

## 2. User Voice Recording

**Flow:** Client-only, synchronous

```
User clicks Record
    │
    ▼
script.js: UI.recStartBtn.onclick
    │
    ├─► Request microphone access
    │       navigator.mediaDevices.getUserMedia()
    │
    ├─► Create AudioWorkletNode (for processing)
    │
    ├─► Start auto-stop timer (silence detection)
    │       • MAX_RECORDING_MS: 8000ms
    │       • AUTO_STOP_SILENCE_MS: 600ms
    │
    └─► Collect audio chunks into recordedBlob
```

**Auto-Stop Logic:**
- Maximum recording: 8 seconds
- Silence threshold: Measured noise floor × 2.5
- Silence duration to stop: 600ms

---

## 3. Audio Processing (Sync Server)

**Endpoint:** `POST /api/process_audio`  
**Handler:** `flask_app.api_process_audio()` → `flask_app.py:269-335`  
**Processor:** `scripts/audio_processing.process_audio_data()`

### Request

| Field | Type | Source |
|-------|------|--------|
| `audio` | File (blob) | FormData from recorder |
| `noiseFloor` | Float | Measured client noise |

### Processing Steps

| Step | Action | Detail |
|------|--------|--------|
| 1 | Load audio | Librosa reads raw bytes |
| 2 | Convert to mono | Mix stereo if needed |
| 3 | Detect clipping | Reject if > 0.5% samples saturated |
| 4 | Trim silence | RMS + ZCR analysis, asymmetric padding |
| 5 | Peak normalize | Target 0.95 (-0.5dB) |
| 6 | Export MP3 | Via soundfile |
| 7 | Save file | `submissions/{user_id}/{uuid}.mp3` |

### Response

```json
{
  "url": "/submissions/1/abc123.mp3",
  "path": "1/abc123.mp3"
}
```

---

## 4. User Playback

**Flow:** Client-only, synchronous

```
User clicks Play User
    │
    ▼
script.js: UI.playUserBtn.onclick
    │
    ▼
Load userBuf (already decoded from process_audio response)
    │
    ▼
WaveSurfer.js visualization + playback
```

| Component | Detail |
|-----------|--------|
| Audio Source | Decoded from processed MP3 URL |
| Visualization | WaveSurfer.js (`userWS`) |
| Color | Orange (`Config.COLORS.USER`) |

---

## 5. Submission (Sync Server + Async Dispatch)

**Endpoint:** `POST /api/submit_recording`  
**Handler:** `flask_app.submit_recording()` → `flask_app.py:339-378`

### Request

```json
{
  "word_id": 1,
  "file_path": "1/abc123.mp3",
  "test_type": "pre"
}
```

### Sync Processing

| Step | Action |
|------|--------|
| 1 | Validate word exists |
| 2 | Create `Submission` record |
| 3 | Set `file_path`, `word_id`, `user_id`, `test_type` |
| 4 | Commit to database |

### Async Dispatch

```python
task = celery.send_task("tasks.async_process_submission", args=[sub.id])
return jsonify({"status": "processing", "task_id": task.id}), 202
```

---

## 6. Acoustic Analysis (Async Celery)

**Task:** `tasks.async_process_submission`  
**Location:** `tasks.py:13-103`  
**Worker Command:** `celery -A flask_app.celery worker --loglevel=info`

### Celery Configuration

| Setting | Value | Source |
|---------|-------|--------|
| Broker URL | `redis://localhost:6379/0` | `CELERY_BROKER_URL` |
| Result Backend | `redis://localhost:6379/0` | `CELERY_RESULT_BACKEND` |
| Max Retries | 3 | `@shared_task(max_retries=3)` |

### Analysis Flow

```
async_process_submission(submission_id)
    │
    ├─► Load Submission from DB
    │
    ├─► Call process_submission(submission_id)
    │       │
    │       ├─► Load student audio file
    │       ├─► Load reference audio file (/static/audio/{word}.mp3)
    │       │
    │       ├─► analyze_formants_from_path() for BOTH
    │       │       │
    │       │       ├─► load_audio_mono() - Librosa
    │       │       ├─► find_syllable_nucleus() - Praat/Parselmouth
    │       │       ├─► measure_formants() - F1, F2 extraction
    │       │       └─► Deep voice correction if needed (4000Hz ceiling)
    │       │
    │       ├─► Calculate Cumulative VTLN Alpha
    │       │       • Query historical AnalysisResult for user
    │       │       • Compute median of all F1/F2 ratios
    │       │
    │       ├─► Normalize student formants (F1/alpha, F2/alpha)
    │       │
    │       ├─► calculate_distance() - Hz and Bark
    │       │
    │       └─► Save AnalysisResult to DB
    │
    ├─► Calculate score: max(0, min(100, 100 - (dist * 20)))
    │
    ├─► Generate recommendation based on F1/F2 differences
    │
    ├─► Update Submission.score
    │
    └─► Return result dict to Redis
```

### Return Value (stored in Redis)

```python
{
    "status": "success",
    "score": 85,
    "category": "success",  # or "warning" or "danger"
    "distance": "0.75 Bark",
    "analysis": {
        "distance_bark": 0.75,
        "recommendation": "Good effort! Keep practicing."
    }
}
```

---

## 7. Result Polling

**Endpoint:** `GET /api/status/<task_id>`  
**Handler:** `flask_app.get_task_status()` → `flask_app.py:381-400`

### Polling Logic (Client)

```javascript
let polling = true;
while (polling) {
    await new Promise(r => setTimeout(r, 1000)); // Wait 1s
    const pollRes = await fetch(`/api/status/${taskId}`);
    const pollData = await pollRes.json();
    
    if (pollData.status === 'success' || pollData.status === 'error') {
        data = pollData;
        polling = false;
    }
}
```

### Task States (Celery)

| State | Response |
|-------|----------|
| `PENDING` | `{ "status": "processing" }` |
| `SUCCESS` | Full result dict from task |
| `FAILURE` | `{ "status": "error", "message": "..." }` |

---

## 8. Database Storage

### Submission Model

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer | Primary key |
| `user_id` | Integer | FK to User |
| `word_id` | Integer | FK to Word |
| `test_type` | String | "pre" or "post" |
| `file_path` | String | Relative path to MP3 |
| `score` | Integer | 0-100 (calculated) |
| `timestamp` | DateTime | Submission time |

### AnalysisResult Model

| Field | Type | Purpose |
|-------|------|---------|
| `submission_id` | Integer | FK to Submission |
| `f1_raw` | Float | Student F1 (Hz) |
| `f2_raw` | Float | Student F2 (Hz) |
| `f1_ref` | Float | Reference F1 (Hz) |
| `f2_ref` | Float | Reference F2 (Hz) |
| `scaling_factor` | Float | VTLN alpha |
| `f1_norm` | Float | Normalized F1 |
| `f2_norm` | Float | Normalized F2 |
| `distance_hz` | Float | Euclidean distance (Hz) |
| `distance_bark` | Float | Perceptual distance |
| `is_deep_voice_corrected` | Boolean | Used 4000Hz ceiling |
| `is_outlier` | Boolean | Distance > 5.0 Bark |

---

## Redis/Celery Configuration

### config.py

```python
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
```

### flask_app.py (Celery Init)

```python
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config)
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

celery = celery_init_app(app)
import tasks  # Register tasks with worker
```

---

## Starting the System

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A flask_app.celery worker --loglevel=info

# Terminal 3: Flask App
flask run
# or
gunicorn -c gunicorn_config.py flask_app:app
```

---

## Error Handling

| Stage | Error | Handling |
|-------|-------|----------|
| Recording | Clipping detected | `audio_processing.py` raises ValueError |
| Processing | Empty audio | Returns original bytes |
| Submission | Word not found | 404 response |
| Analysis | File missing | `process_submission` returns False |
| Task | Any exception | Logged, returned as error status |

---

## Refactoring Notes

1. **Change polling interval** → Update `1000` in `script.js:1270`
2. **Change max retries** → Update `max_retries=3` in `tasks.py:13`
3. **Change Bark scoring** → Update `100 - (dist * 20)` in `tasks.py:38`
4. **Add new formant analysis** → Extend `analysis_engine.py`
5. **Change silence thresholds** → Update `audio_processing.py:95-97`
6. **Scale workers** → Use `celery -A flask_app.celery worker --concurrency=4`
