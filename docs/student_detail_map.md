# Student Detail (`student_detail.html`)

**Route:** `GET /dashboard/teacher/student/<int:user_id>`  
**Handler:** `dashboard_routes.student_detail()` → `dashboard_routes.py:335-366`  
**Template:** `templates/dashboards/student_detail.html`  
**Extends:** `base.html`

> **Note:** Teacher/Admin page showing individual student's submission history with analysis results.

---

## Page Purpose

Displays a specific student's:
- Personal info (name, student ID)
- Full submission history with pagination
- Audio playback for each submission
- Analysis results (VTLN alpha, Bark score, flags)
- Vowel space chart modal per submission

---

## Access Control

| Role | Access |
|------|--------|
| Student | Denied → redirect to index |
| Teacher | Full access |
| Admin | Full access |

### Additional Validation

- Target user must have `role == "student"` or `is_guest == True`
- Invalid selection → redirect to teacher dashboard

---

## Template Variables

| Variable | Type | Source |
|----------|------|--------|
| `student` | User | `User.query.get_or_404(user_id)` |
| `submissions` | Pagination | Paginated Submission query |
| `current_filter` | str | `request.args.get("test_type", "all")` |

---

## External Dependencies

| Resource | CDN | Purpose |
|----------|-----|---------|
| Chart.js | `cdn.jsdelivr.net/npm/chart.js` | Vowel chart |
| Annotation Plugin | `cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1` | Distance line |

---

## CSS Overrides

```css
#noise-meter, #connection-status {
    display: none !important;
}
```

Hides audio monitoring elements inherited from `base.html`.

---

## UI Layout

### Header Section

| Element | Content |
|---------|---------|
| Back Link | "← Back to Dashboard" → `/dashboard/teacher` |
| Title | `{{ student.first_name }} {{ student.last_name }}` |
| Subtitle | `Student ID: {{ student.student_id }}` |

---

## Filter Form

**Method:** GET  
**Action:** Same page with filter applied

| Element | ID | Options |
|---------|----|---------|
| Filter Select | `#test_type` | "Show All", "Pre-Test Only", "Post-Test Only" |

**Behavior:** `onchange="this.form.submit()"` - auto-submits on selection

---

## Submissions Table

### Columns

| Column | Data Source | Notes |
|--------|-------------|-------|
| Date | `sub.timestamp` | Format: `YYYY-MM-DD HH:MM` |
| Test Type | `sub.test_type` | Badge: indigo (Pre) / green (Post) |
| Word | `sub.target_word.text` | Bold |
| Audio | `sub.file_path` | HTML5 audio player |
| VTLN | `sub.analysis.scaling_factor` | 2 decimal places |
| Score | `sub.analysis.distance_bark` | Color-coded Bark value |
| Flags | `is_deep_voice_corrected`, `is_outlier` | Badge pills |
| Action | - | "View Chart" button |

### Score Color Coding

| Condition | Color | Class |
|-----------|-------|-------|
| `d < 1.5` | Green | `text-green-600` |
| `1.5 ≤ d < 3.0` | Yellow | `text-yellow-600` |
| `d ≥ 3.0` | Red | `text-red-600` |

### Flag Badges

| Flag | Condition | Style |
|------|-----------|-------|
| Corrected | `is_deep_voice_corrected == True` | Blue pill |
| Outlier | `is_outlier == True` | Red pill |

### Pending Analysis State

When `sub.analysis` is None:

| Display | Content |
|---------|---------|
| Colspan | 4 columns |
| Text | "Pending Analysis..." (gray italic) |

---

## Pagination

**Condition:** Shown when `submissions.total > 10`

| Element | Content |
|---------|---------|
| Info | "Showing X of Y results" |
| Previous | Link or disabled button |
| Next | Link or disabled button |

### Pagination URLs

```
/dashboard/teacher/student/{user_id}?page={num}&test_type={filter}
```

---

## Vowel Chart Modal

**ID:** `#chartModal`

### Modal Elements

| Element | ID | Purpose |
|---------|----|---------|
| Container | `#chartModal` | Full-screen overlay |
| Title | `#modalTitle` | "Vowel Space: /{vowel}/" |
| Subtitle | `#modalSubtitle` | Distance in Bark |
| Canvas | `#vowelChart` | Chart.js scatter plot |
| Close Button | `#closeModal` | Hides modal |

### Modal Behavior

1. Click "View Chart" → `openChartModal(subId)`
2. Show modal, display "Loading data..."
3. Fetch `/dashboard/api/submission/{subId}/analysis`
4. Render chart with student + reference points
5. Click Close → hide modal

---

## API Endpoint (Chart Data)

**Route:** `GET /dashboard/api/submission/<int:submission_id>/analysis`  
**Handler:** `dashboard_routes.get_analysis_data()` → `dashboard_routes.py:1016-1050`

### Access Control

| Role | Access |
|------|--------|
| Teacher/Admin | All submissions |
| Student | Own submissions only |

### Response Format

```json
{
    "student": {
        "f1": 450.5,
        "f2": 1200.3,
        "color": "rgba(54, 162, 235, 1)"
    },
    "reference": {
        "f1": 480.0,
        "f2": 1150.0,
        "color": "rgba(75, 192, 192, 1)"
    },
    "metrics": {
        "distance_bark": 0.75,
        "vowel_label": "æ",
        "is_outlier": false
    }
}
```

### Error Responses

| Condition | Response |
|-----------|----------|
| No access | `{"error": "Access denied"}`, 403 |
| No analysis | `{"error": "No analysis data found"}`, 404 |

---

## JavaScript Functions

**Location:** Lines 186-296

### Global Variables

| Variable | Purpose |
|----------|---------|
| `myChart` | Current Chart.js instance |

### Functions

| Function | Purpose |
|----------|---------|
| `openChartModal(subId)` | Fetch data and render chart |
| `renderChart(data)` | Create/update Chart.js scatter plot |

### Chart Configuration

| Setting | Value |
|---------|-------|
| Type | Scatter |
| X-axis | F2 (Hz) - Reversed (500-3000) |
| Y-axis | F1 (Hz) - Reversed (200-1200) |
| Student point | Blue circle, radius 8 |
| Reference point | Green rotated rect, radius 8 |
| Connection line | Dashed gray with arrow |

---

## Backend Query

```python
# Get student
student = User.query.get_or_404(user_id)

# Validate role
if student.role != "student" and not student.is_guest:
    flash("Invalid student selection.", "warning")
    return redirect(...)

# Build query
query = student.submissions.order_by(Submission.timestamp.desc())

# Apply filter
if test_type_filter in ["pre", "post"]:
    query = query.filter(Submission.test_type == test_type_filter)

# Paginate
submissions_pagination = query.paginate(
    page=page, per_page=10, error_out=False
)
```

---

## Audio Playback

| Element | Attributes |
|---------|------------|
| `<audio>` | `controls`, `class="h-8 w-32"` |
| Source | `url_for('serve_upload', filename=sub.file_path)` |
| Type | `audio/mpeg` |

---

## Navigation Links

| Link | Target |
|------|--------|
| Back to Dashboard | `/dashboard/teacher` |

---

## Flash Messages

| Message | Type | Trigger |
|---------|------|---------|
| "Access denied." | danger | Non-teacher/admin access |
| "Invalid student selection." | warning | Target not a student |

---

## Empty State

When no submissions match filter:

| Display | Content |
|---------|---------|
| Text | "No submissions found for filter: {FILTER}." |
| Filter shown | Uppercase (ALL, PRE, POST) |

---

## Refactoring Notes

1. **Add date range filter** → Add date pickers to filter form
2. **Add export functionality** → Button to download CSV of submissions
3. **Add bulk delete** → Checkboxes + delete button
4. **Change pagination size** → Update `per_page=10` in handler
5. **Add comparison view** → Show pre/post side by side
6. **Inline audio waveform** → Replace HTML5 player with WaveSurfer.js
7. **Add formant values to table** → Show F1/F2 columns
8. **Link to word page** → Make word text clickable
