# Research Dashboard (`research_view.html`)

**Route:** `GET /dashboard/teacher/research`  
**Handler:** `dashboard_routes.research_dashboard()` → `dashboard_routes.py:369-417`  
**Template:** `templates/dashboards/research_view.html`  
**Extends:** `base.html`

> **Note:** Accessible to teachers and admins. Provides acoustic analysis visualization for research purposes.

---

## Page Purpose

Acoustic research interface displaying:
- Vowel space visualization (F1 vs F2)
- Error distribution histogram
- F1/F2 correlation charts with trend lines
- Raw data table with search

---

## Access Control

| Role | Access |
|------|--------|
| Student | Denied → redirect to index |
| Teacher | Full access |
| Admin | Full access |

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `analysis_data` | List of dicts | Flattened analysis results for JS |

### analysis_data Structure

```python
{
    "username": str,       # User's username
    "student_id": str,     # Student ID or None
    "word": str,           # Target word text
    "vowel": str,          # Stressed vowel IPA
    "f1_s": float,         # Student normalized F1 (Hz)
    "f2_s": float,         # Student normalized F2 (Hz)
    "f1_r": float,         # Reference F1 (Hz)
    "f2_r": float,         # Reference F2 (Hz)
    "dist_bark": float,    # Bark distance
    "alpha": float,        # VTLN scaling factor
    "is_outlier": bool     # Distance > 5.0 Bark
}
```

---

## External Dependencies

| Resource | CDN | Purpose |
|----------|-----|---------|
| Chart.js | `cdn.jsdelivr.net/npm/chart.js` | All visualizations |

---

## UI Layout

### Header Section

| Element | Content |
|---------|---------|
| Back Link | "← Back to Teacher Dashboard" |
| Page Title | "Acoustic Research Dashboard" |
| Description | "Deep dive into formant analysis..." |
| Total Samples | Dynamic count from JS |

### Empty State

Displayed when `analysis_data|length == 0`:

| Element | Content |
|---------|---------|
| Icon | Flask/beaker SVG |
| Title | "No Research Data" |
| Message | Instructions to run analysis |

---

## Charts (Row 1)

### 1. Vowel Space Chart (2/3 width)

**Canvas ID:** `#vowelSpaceChart`

| Feature | Description |
|---------|-------------|
| Type | Scatter plot |
| X-axis | F2 (Backness) - Reversed |
| Y-axis | F1 (Height) - Reversed |
| Datasets | Student (indigo) + Reference (green) |

**Vowel Filters:**

| Element | ID | Purpose |
|---------|----|---------|
| Select All | `#selectAllBtn` | Check all vowels |
| Deselect All | `#deselectAllBtn` | Uncheck all vowels |
| Checkboxes | `#vowelCheckboxes` | Filter by vowel |

**Chart Options:**

| Setting | Value |
|---------|-------|
| X min/max | 800 - 3000 Hz |
| Y min/max | 200 - 1000 Hz |
| Both reversed | Yes (phonetic convention) |

### 2. Error Histogram (1/3 width)

**Canvas ID:** `#distributionChart`

| Feature | Description |
|---------|-------------|
| Type | Bar chart |
| X-axis | Bark distance intervals (0.5 steps) |
| Y-axis | Count |
| Bins | 12 bins (0-6 Bark) |

---

## Charts (Row 2)

### 3. F1 Correlation Chart

**Canvas ID:** `#correlationChartF1`

| Feature | Description |
|---------|-------------|
| Type | Scatter + Line |
| X-axis | Reference F1 (Hz) |
| Y-axis | Student Normalized F1 (Hz) |
| Trend Line | Linear regression |
| Color | Amber |

### 4. F2 Correlation Chart

**Canvas ID:** `#correlationChartF2`

| Feature | Description |
|---------|-------------|
| Type | Scatter + Line |
| X-axis | Reference F2 (Hz) |
| Y-axis | Student Normalized F2 (Hz) |
| Trend Line | Linear regression |
| Color | Blue |

---

## Data Table

**ID:** `#dataTable`

### Columns

| Column | Data Field | Notes |
|--------|------------|-------|
| Username | `username` | Bold |
| Student ID | `student_id` | Italic "None" if empty |
| Word | `word` | Bold |
| Vowel | `vowel` | IPA symbol |
| F1 (Norm) | `f1_s` | Rounded integer |
| F2 (Norm) | `f2_s` | Rounded integer |
| Dist (Bark) | `dist_bark` | Red if > 3.0 |
| Alpha | `alpha` | 2 decimal places |
| Outlier | `is_outlier` | "YES" (red) or "-" |

### Search

| Element | ID | Purpose |
|---------|----|---------|
| Search Input | `#tableSearch` | Filter table rows |
| Search Fields | Username, Student ID, Word | Columns searched |

---

## Backend Query

```python
results = (
    db.session.query(AnalysisResult, Submission, User, Word)
    .join(Submission, AnalysisResult.submission_id == Submission.id)
    .join(User, Submission.user_id == User.id)
    .join(Word, Submission.word_id == Word.id)
    .filter(User.role == "student")  # Only students
    .all()
)
```

### Data Transformation

| Source | Transformation | Output |
|--------|----------------|--------|
| `res.f1_norm` | NaN check | `f1_s` or None |
| `res.f2_norm` | NaN check | `f2_s` or None |
| `res.f1_ref` | NaN check | `f1_r` or None |
| `res.f2_ref` | NaN check | `f2_r` or None |
| `res.distance_bark` | NaN check | `dist_bark` or None |
| `res.scaling_factor` | NaN check → 1.0 | `alpha` |

---

## JavaScript Functions

**Location:** Lines 136-443

### Data Processing

| Function/Logic | Purpose |
|----------------|---------|
| `rawData = JSON.parse(...)` | Load data from script tag |
| Filter valid data | Exclude rows with null F1/F2 |
| Extract unique vowels | Build filter checkboxes |

### Chart Functions

| Function | Purpose |
|----------|---------|
| `renderCheckboxes()` | Build vowel filter UI |
| `updateChart()` | Refresh vowel space with filters |
| `calculateTrendLine()` | Linear regression for correlation |
| `createCorrelationChart()` | Factory for F1/F2 charts |

### Table Functions

| Logic | Purpose |
|-------|---------|
| `rawData.forEach(...)` | Populate table body |
| Search keyup handler | Filter rows by search term |

---

## Data Payload

**Script Tag ID:** `#research-data`

```html
<script id="research-data" type="application/json">
    {{ analysis_data | tojson }}
</script>
```

---

## Color Scheme

| Element | Color | Hex/RGBA |
|---------|-------|----------|
| Student points | Indigo | `rgba(79, 70, 229, 0.6)` |
| Reference points | Green | `rgba(16, 185, 129, 0.4)` |
| Histogram bars | Indigo | `rgba(99, 102, 241, 0.5)` |
| F1 correlation | Amber | `rgba(245, 158, 11, 0.6)` |
| F2 correlation | Blue | `rgba(59, 130, 246, 0.6)` |
| Trend lines | Gray | `rgba(75, 85, 99, 0.8)` |
| High error text | Red | Tailwind `text-red-600` |

---

## Navigation Links

| Link | Target |
|------|--------|
| Back to Teacher Dashboard | `/dashboard/teacher` |

---

## Flash Messages

| Message | Type | Trigger |
|---------|------|---------|
| "Access denied." | danger | Non-teacher/admin access |

---

## Refactoring Notes

1. **Add date range filter** → Add date picker, update backend query
2. **Add export to CSV** → Add button, implement download logic
3. **Add per-student filter** → Add student dropdown
4. **Change histogram bins** → Update JS lines 307-319
5. **Add F3 analysis** → Extend AnalysisResult model, add chart
6. **Add vowel grouping** → Group by vowel type (front/back/central)
7. **Change chart colors** → Update color constants in JS
8. **Add audio playback** → Link to submission files from table
