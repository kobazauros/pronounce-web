# Index Page - Student Practice (`index.html`)

**Route:** `GET /`  
**Handler:** `flask_app.index()` → `flask_app.py:152-166`  
**Template:** `templates/index.html`  
**Extends:** `base.html`  
**JavaScript:** `static/js/script.js`

> **Note:** Requires authentication. Unauthenticated users of all possible roles see `login.html`. Teachers are redirected to `/dashboard/teacher`. Admins are redirected to `/dashboard/admin`

---

## Page Purpose

Main practice interface where students:
1. Select words from vocabulary list
2. Listen to model pronunciation
3. Record their own pronunciation
4. Submit for analysis and scoring

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `current_user.username` | Flask-Login | Displayed in hidden state div |
| `enable_logging` | `SystemConfig.get_bool("enable_logging")` | Controls JS event logging (configured in Admin Panel) |

---

## UI Sections

### 1. Center Stage (Recording Area)

| Element | ID | Purpose |
|---------|----|---------|
| Word Display | `#sample-word-placeholder` | Shows selected word |
| Phonetic Display | `#phonetic-display` | Shows IPA transcription |
| Tips Button | `#open-tips-btn` | Opens recording tips modal |
| Settings Button | `#open-settings-btn` | Opens audio settings modal |
| Waveform Container | `#difference-waveform-container` | Visualizes audio waveforms |
| Message Box | `#message-box` | Status messages (READY, RECORDING, PLAYBACK, TOO NOISY, etc.) - updated dynamically based on noise level |
| Comparison Legend | `#comparison-legend` | Shows Model (blue) / You (red) waveform legend |

### 2. Control Buttons

| Element | ID | Type | Purpose |
|---------|----|----|---------|
| Play Sample | `#play-sample` | `<button>` | Play model pronunciation |
| Record Start | `#record-start` | `<button>` | Start recording (dynamically disabled when noise is too high) |
| Record Stop | `#record-stop` | `<button>` | Stop recording (hidden) |
| Play User | `#play-user` | `<button>` | Play user's recording |
| Submit | `#submit-recording` | `<button>` | Submit for analysis |
| Next Word | `#next-word-btn` | `<button>` | Advance to next word |
| Submit Message | `#submit-msg` | `<p>` | Bark score with color-coded feedback (green/yellow/red) and recommendations |

### 3. Recording Tips Modal

| Element | ID | Purpose |
|---------|----|---------|
| Modal Container | `#recording-tips-modal` | Hidden by default |
| Close Button | `#close-tips-btn` | Closes modal |

### 4. Audio Settings Modal

| Element | ID | Purpose |
|---------|----|---------|
| Modal Container | `#audio-settings-modal` | Hidden by default |
| Mic Select | `#audio-input-select` | Microphone selection dropdown |
| High Fidelity Button | `#mode-fidelity` | Audio mode toggle |
| Noise Reduce Button | `#mode-reduction` | Audio mode toggle |
| Audio Mode Value | `#audio-mode-value` | Hidden input storing selected mode |
| Input Level Meter | `#settings-meter-bar` | Visual audio input level indicator |
| Close Button | `#close-settings-btn` | Closes modal |

### 5. Monitor Footer

| Element | ID | Purpose |
|---------|----|---------|
| Noise Indicator | `#noise-indicator-icon` | Color-coded noise level indicator |
| Noise/Status Text | `#noise-level-display` | Shows noise level OR status (RECORDING/PLAYBACK) |
| Footer Container | `#monitor-footer` | Contains noise and status indicators |

### 6. Right Sidebar

| Element | ID | Purpose |
|---------|----|---------|
| Test Type Select | `#test-type` | Pre-Test / Post-Test selector |
| Progress Percent | `#progress-percent` | Shows mastery percentage |
| Progress Bar | `#progress-bar-fill` | Visual progress indicator |
| Word List Container | `#word-list` | Vocabulary items (JS populated) |

### 7. Hidden State

| Element | ID | Data Attributes | Purpose |
|---------|----|----|---------|
| App State | `#app-state` | `data-username`, `data-logging` | Pass server data to JS |

---

## API Endpoints (called from script.js)

| Endpoint | Method | Trigger | Handler | Purpose |
|----------|--------|---------|---------|---------|
| `/api/log_event` | POST | Various user actions | `flask_app.log_event()` | Analytics logging |
| `/api/word_list` | GET | Page load | `flask_app.get_word_list()` | Fetch vocabulary |
| `/get_progress` | GET | Page load, after submit | `flask_app.get_progress()` | Get user's completion status |
| `/api/process_audio` | POST | After recording | `flask_app.api_process_audio()` | Upload & process audio |
| `/api/submit_recording` | POST | Submit button click | `flask_app.submit_recording()` | Analyze pronunciation |
| `/api/status/<task_id>` | GET | After submit (polling) | `flask_app.get_task_status()` | Check Celery task status |
| `/static/audio/<word>.webm` | GET | Word selection | Static file | Fetch model audio |

---

## API Details

### `/api/word_list`
**Response:**
```json
[
  {"id": 1, "word": "cat", "ipa": "/kæt/", "audio": "cat.webm"},
  ...
]
```

### `/get_progress`
**Response:**
```json
{
  "progress": {"pre": 50, "post": 0},
  "stage": "pre",
  "pre_words": ["cat", "dog"],
  "post_words": []
}
```

### `/api/process_audio`
**Request:** Multipart form with `audio` file + `noiseFloor`  
**Response:**
```json
{"url": "/uploads/user_recordings/..."}
```

### `/api/submit_recording`
**Request:**
```json
{"word_id": 1, "file_path": "...", "test_type": "pre"}
```
**Response:**
```json
{"status": "processing", "task_id": "abc123"}
```

### `/api/status/<task_id>`
**Response (pending):**
```json
{"status": "processing"}
```
**Response (done):**
```json
{"status": "success", "score": 85, "feedback": "..."}
```

---

## JavaScript Functions (script.js)

| Function | Purpose |
|----------|---------|
| `loadWordList()` | Fetches and renders word list |
| `buildWordList()` | Creates word item elements |
| `selectWord(word)` | Selects a word, loads sample |
| `loadSample()` | Fetches model audio file |
| `startRecording()` | Begins microphone recording |
| `stopRecording()` | Ends recording, triggers processing |
| `submitRecording()` | Sends to analysis API |
| `pollTaskStatus()` | Polls Celery task status |
| `updateProgress()` | Refreshes progress bar |
| `logEvent()` | Sends analytics events |

---

## Global JS Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `window.CURRENT_USER` | `#app-state` data attribute | Current username |
| `window.ENABLE_LOGGING` | `#app-state` data attribute | Toggle event logging |
| `WORDS` | `/api/word_list` response | Word list array |
| `selectedWord` | User selection | Currently active word |
| `sampleBuf` | Decoded audio | Model audio buffer |
| `userBuf` | Recorded audio | User's audio buffer |
| `measuredNoiseFloor` | Noise monitor | Tracked background noise level |

## Config Constants

| Constant | Default | Purpose |
|----------|---------|---------|
| `AUTO_STOP_SILENCE_MS` | 1500 | Silence duration (ms) before auto-stop recording |
| `MAX_RECORDING_MS` | 5000 | Maximum recording duration (ms) |
| `NOISE_BLOCK_THRESHOLD` | 0.04 | Peak level above which recording is blocked |
| `TRIM_THRESHOLD_FACTOR` | 3.5 | Multiplier for silence trimming threshold |

---

## Navigation

| Action | Destination |
|--------|-------------|
| (None from this page) | Users stay on this page |
| Logout (from base.html) | `/logout` |

---

## Noise-Based Recording Protection

The system dynamically monitors ambient noise levels and **blocks recording when noise is too high** to ensure quality audio submissions.

### How It Works

1. **Continuous Monitoring:** The `startNoiseMonitor()` function continuously analyzes microphone input via Web Audio API
2. **Threshold Check:** Peak audio levels are compared against `Config.NOISE_BLOCK_THRESHOLD` (default: 0.04)
3. **Dynamic Button State:** When noise exceeds threshold:
   - Record button is **disabled** and grayed out (opacity 0.5)
   - Button tooltip shows "Too noisy to record - find a quieter spot"
   - Message box displays "TOO NOISY" in amber color
4. **Auto-Recovery:** When noise drops below threshold:
   - Record button is **re-enabled** automatically
   - Message box returns to "Ready"

### Configuration

| Constant | Location | Default | Purpose |
|----------|----------|---------|---------|
| `NOISE_BLOCK_THRESHOLD` | `Config` in `script.js` | 0.04 | Peak level above which recording is blocked |

### Visual Feedback

| State | Record Button | Message Box | Noise Icon |
|-------|---------------|-------------|------------|
| Quiet | Enabled, full opacity | "Ready" | Green |
| Noisy (below threshold) | Enabled | "Ready" | Amber, pulsing |
| Too Noisy (above threshold) | **Disabled**, 50% opacity | "TOO NOISY" (amber) | Amber, pulsing |

### Conditions for Noise Blocking

Noise-based blocking only applies when:
- A word is selected
- Not currently recording or busy with other operations
- The "Listen Before Record" requirement has been met (user has played the sample)

---

## Refactoring Notes

1. **Rename word display** → Update `#sample-word-placeholder` (line 22-23)
2. **Change test type values** → Update `#test-type` options (lines 279-281) + backend handlers
3. **Modify API endpoints** → Update `script.js` fetch URLs + `flask_app.py` route decorators
4. **Add new control buttons** → Update control area (lines 186-229) + JS handlers
5. **Change progress calculation** → Update `/get_progress` handler in `flask_app.py`
6. **Modify word list structure** → Update `/api/word_list` response + `buildWordList()` in JS
