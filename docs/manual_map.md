# Manual Page (`manual.html`)

**Route:** `GET /manual`  
**Handler:** `flask_app.manual()` → `flask_app.py:175-178`  
**Template:** `templates/manual.html`  
**Extends:** `base.html`

> **Note:** Accessible to all users (authenticated and unauthenticated). Can be opened with F1 keyboard shortcut (defined in `base.html`).

---

## Page Purpose

Comprehensive user guide covering:
- Technical requirements and browser settings
- Registration process for students and teachers
- Student practice workflow
- Teacher dashboard usage
- Admin panel operations
- Research panel analysis tools
- Glossary of scientific terms

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| (none) | — | Static content page |

---

## Page Sections

### 1. Header

| Element | Purpose |
|---------|---------|
| Title | "User Manual" |
| Subtitle | Guide description + F1 shortcut hint |

### 2. Quick Navigation Cards

| Card | Anchor Link | Icon |
|------|-------------|------|
| Student Guide | `#student-guide` | `fa-user-graduate` |
| Teacher Guide | `#teacher-guide` | `fa-chalkboard-teacher` |
| Admin Guide | `#admin-guide` | `fa-user-shield` |
| Technical Setup | `#technical-setup` | `fa-cogs` |

### 3. Sidebar Navigation (Desktop Only)

| Link | Anchor |
|------|--------|
| Technical Setup | `#technical-setup` |
| Registration | `#registration` |
| Student Guide | `#student-guide` |
| Teacher Guide | `#teacher-guide` |
| Admin Guide | `#admin-guide` |
| Research Panel | `#research-panel` |
| Glossary | `#glossary` |

---

## Content Sections

### Technical Setup (`#technical-setup`)

| Topic | Content |
|-------|---------|
| Recommended Browsers | Chrome (best), Edge, Firefox. Avoid Opera Mini, UC Browser, in-app browsers |
| Audio Modes | High Fidelity (default, requires quiet room), Noise Reduce |
| Data Saver Warning | Must disable browser data saver/lite modes |
| Hardware | Wired headset recommended, Bluetooth may drop to 8kHz |

### Registration (`#registration`)

| Topic | Content |
|-------|---------|
| Student Registration | Username, Name, 10-digit Student ID, Password, Consent required |
| Teacher Registration | Requires Invite Code from admin, Student ID not required |
| Password Recovery | Forgot password link, 10-minute expiry |
| Account Lockout | 5 failed attempts = 15 minute lockout |
| Password Requirements | 8+ chars, mixed case, numbers, special; no reuse of last 3 |

### Student Guide (`#student-guide`)

| Step | Description |
|------|-------------|
| 1. Check Word | Auto-selected first incomplete word, manual selection available |
| 2. Listen & Practice | Play model pronunciation (blue waveform) |
| 3. Record & Submit | Record, listen to playback, save |
| 4. Analyze Feedback | Bark score with colors (green/yellow/red) |
| 5. Recommendations | Formant-based suggestions for improvement |
| 6. Troubleshooting | LOG checkbox for diagnostic data |

### Teacher Guide (`#teacher-guide`)

| Topic | Content |
|-------|---------|
| Navigation | Search bar, pagination (10 per page) |
| Dashboard Columns | Progress bars, VTLN Alpha, Flags (Outlier, Deep Voice) |
| Student Details | Submission history, filter by test type, audio playback, formant charts |

### Research Panel (`#research-panel`)

| Visualization | Purpose |
|---------------|---------|
| Vowel Space (F1 vs F2) | Scatter plot of tongue height/backness |
| Error Distribution | Histogram of Bark error magnitudes |
| F1 Correlation | Student vs Reference F1 with trend line |
| F2 Correlation | Student vs Reference F2 with trend line |
| Raw Data Table | Detailed per-recording data |

### Admin Guide (`#admin-guide`)

| Topic | Content |
|-------|---------|
| CLI Commands | `flask create-admin`, `flask reset-password`, `flask delete-user`, `flask bulk-reset` |
| User Management | Edit role, assign Student ID, manage invite codes, delete user |
| Word Management | Auto-fetch IPA/audio, waveform editor, upload custom audio |
| System Config | Maintenance mode, Registration toggle, Logging toggle, System logs download |
| Health Metrics | DB size, CPU load |

### Glossary (`#glossary`)

| Term | Definition |
|------|------------|
| Formants (F1 & F2) | Resonant frequencies; F1=jaw opening, F2=tongue advancement |
| Bark Scale | Logarithmic frequency scale matching human perception |
| VTLN (Alpha) | Vocal Tract Length Normalization factor for speaker comparison |
| Euclidean Distance | Error measurement in F1-F2 space |

---

## CSS Features

| Feature | Class/Behavior |
|---------|----------------|
| Sticky Sidebar | `sticky top-24` (desktop only) |
| Scroll Margin | `scroll-mt-24` on sections for anchor links |
| Responsive Grid | 4-column on desktop, 1-column on mobile |
| Prose Styling | `prose prose-slate` for content sections |

---

## Navigation Links

| Link | Target |
|------|--------|
| (Internal anchors only) | Jump to page sections |

---

## Refactoring Notes

1. **Add new section** → Add anchor link to sidebar + quick nav cards + new `<section>` in content
2. **Update CLI commands** → Edit Admin Guide section (lines 556-575)
3. **Change score thresholds** → Update Student Guide step 4 (lines 334-345)
4. **Add new glossary term** → Add to glossary grid (lines 672-716)
5. **Modify browser recommendations** → Update Technical Setup section (lines 107-116)
