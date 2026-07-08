# Manage Word Page (`manage_word.html`)

**Routes:**  
- `GET/POST /dashboard/admin/word/add` → Add new word  
- `GET/POST /dashboard/admin/word/<word_id>/edit` → Edit existing word

**Handlers:**  
- `dashboard_routes.add_word()` → `dashboard_routes.py:733-779`  
- `dashboard_routes.edit_word()` → `dashboard_routes.py:783-830`

**Template:** `templates/dashboards/manage_word.html`  
**Extends:** `base.html`

> **Note:** Admin-only page. Disabled in demo mode. Used for both adding and editing words (determined by presence of `word` variable).

---

## Page Purpose

Word management interface for:
- Adding new words to the curriculum
- Editing existing word details
- Auto-fetching pronunciation data from Cambridge Dictionary
- Manual audio upload and preview
- Audio normalization on save

---

## Page Modes

| Mode | Condition | Title |
|------|-----------|-------|
| Add | `word` is None | "Add New Word" |
| Edit | `word` exists | "Edit Word" |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `word` | `Word.query.get_or_404(word_id)` or None | Word being edited (None for add) |
| `is_demo` | Context processor | Toggle demo mode restrictions |
| `next` | `request.args.get('next')` | Return URL after save |

---

## Form Elements

### Header Section

| Element | Type | Purpose |
|---------|------|---------|
| Page Title | `<h1>` | "Edit Word" or "Add New Word" |
| Back Link | `<a>` | Return to previous page (uses `next` param) |

### Instructions Panel (Collapsible)

| Step | Description |
|------|-------------|
| 1 | Input Word → Click Auto-Fetch |
| 2 | Review waveform for noise |
| 3 | Manual Correction if needed |
| 4 | Save to finalize |

---

### Form Fields

| Field | Name | ID | Type | Required | Purpose |
|-------|------|----|------|----------|---------|
| Target Word | `word_text` | `#word_text` | `text` | Yes | The word itself |
| IPA Transcription | `ipa_transcription` | `#ipa_transcription` | `text` | No | IPA pronunciation |
| Audio File | `audio_file` | `#audio_file` | `file` | No | Manual MP3/WAV upload |

### Auto-Fetch Button

| Element | ID | Action |
|---------|----|--------|
| Auto-Fetch | `#generate-btn` | Calls `/dashboard/admin/generate-pronunciation?word=X` |

---

## Audio Preview Panel

### Elements

| Element | ID | Purpose |
|---------|----|---------|
| Status Message | `#audio-status` | "No audio loaded" placeholder |
| Waveform | `#waveform` | WaveSurfer.js visualization |
| Play/Pause | `#play-pause-btn` | Toggle audio playback |
| Time Display | `#time-display` | Current / Total time |
| Download | `#download-btn` | Download current audio |

### WaveSurfer Configuration

| Setting | Value |
|---------|-------|
| Container | `#waveform` |
| Wave Color | `#C7D2FE` (indigo-200) |
| Progress Color | `#4F46E5` (indigo-600) |
| Bar Width | 3px |
| Height | 96px |

---

## Action Buttons

| Button | Type | Purpose |
|--------|------|---------|
| Save / Create | `<button submit>` | Submit form |

---

## Backend Processing

### Add Word (POST /dashboard/admin/word/add)

| Step | Action |
|------|--------|
| 1 | Validate word_text not empty |
| 2 | Check for duplicate word (case-insensitive) |
| 3 | Determine next sequence_order |
| 4 | Create Word record |
| 5 | Handle audio file (upload or from session) |
| 6 | Commit to database |
| 7 | Redirect to `next` or admin dashboard |

### Edit Word (POST /dashboard/admin/word/<id>/edit)

| Step | Action |
|------|--------|
| 1 | Validate word_text not empty |
| 2 | Check for duplicate if text changed |
| 3 | Update word.text and word.ipa |
| 4 | Handle audio file update |
| 5 | Commit to database |
| 6 | Redirect to `next` or admin dashboard |

### Audio Handling

| Source | Processing |
|--------|------------|
| Uploaded file | Save to `static/audio/{word}.mp3` |
| Auto-fetched | Stored in session as `generated_audio_path` |

---

## API Endpoint: Auto-Fetch

**Route:** `GET /dashboard/admin/generate-pronunciation`  
**Handler:** `dashboard_routes.generate_pronunciation()` → lines 680-730

### Request

| Parameter | Type | Purpose |
|-----------|------|---------|
| `word` | Query string | Word to fetch |

### Processing

| Step | Action |
|------|--------|
| 1 | Call `word_parser.get_word_data(word_text)` |
| 2 | Extract IPA and audio bytes |
| 3 | Process audio via `process_audio_data()` |
| 4 | Save to `static/audio/{word}.mp3` |
| 5 | Store path in session |

### Response

```json
{
  "ipa": "/həˈloʊ/",
  "audio_path": "/static/audio/hello.mp3"
}
```

---

## Flash Messages

| Message | Type | Trigger |
|---------|------|---------|
| "Word text cannot be empty." | danger | Empty word_text |
| "The word 'X' already exists in the wordlist." | danger | Duplicate word |
| "Successfully added the word 'X'." | success | Add success |
| "Successfully updated 'X'." | success | Edit success |

---

## JavaScript Functions

**Location:** Lines 173-365

| Function/Logic | Purpose |
|----------------|---------|
| WaveSurfer.create() | Initialize audio visualization |
| `updateTimeDisplay()` | Update time counter |
| `loadAudioPreview(url)` | Load audio into waveform |
| Auto-Fetch click handler | Call API, update form |
| File input change handler | Preview uploaded audio |
| Demo mode handlers | Block all actions in demo |

---

## Demo Mode Behavior

| Element | Behavior |
|---------|----------|
| Word input | Read-only, shows alert on click |
| IPA input | Read-only, shows alert on click |
| Auto-Fetch button | Blocked with alert |
| Drop zone | Blocked with alert |
| Save button | Blocked with alert |

---

## Navigation Links

| Link | Target |
|------|--------|
| Back | `next` param or admin dashboard |

---

## Refactoring Notes

1. **Change word validation** → Update `dashboard_routes.py:743-750`
2. **Add new field** → Add to form, update POST handler
3. **Change audio storage path** → Update lines 759-763 and 811-815
4. **Change waveform colors** → Update JS lines 197-198
5. **Add stressed vowel field** → Would require Word model update and form addition
