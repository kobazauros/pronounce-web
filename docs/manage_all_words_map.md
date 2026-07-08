# Manage All Words Page (`manage_all_words.html`)

**Route:** `GET /dashboard/admin/words`  
**Handler:** `dashboard_routes.manage_all_words()` → `dashboard_routes.py:891-915`  
**Template:** `templates/dashboards/manage_all_words.html`  
**Extends:** `base.html`

> **Note:** Admin-only page. Provides overview of all words in the curriculum with statistics and management actions.

---

## Page Purpose

Wordlist management overview:
- Display all words in the system
- Show IPA transcription and audio preview
- Track submission counts per word
- Show last activity date
- Access to add/edit/delete words

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `word_stats` | List of dicts | Word objects with statistics |
| `is_demo` | Context processor | Toggle demo mode restrictions |

### word_stats Structure

```python
{
    "word": Word,           # Word model instance
    "submission_count": int, # Total submissions for this word
    "last_submission_str": str  # Formatted date or "Never"
}
```

---

## UI Elements

### Header Section

| Element | Type | Purpose |
|---------|------|---------|
| Page Title | `<h1>` | "Manage Wordlist" |
| Description | `<p>` | Explains mono-syllabic requirement |
| Back to Dashboard | `<a>` | Return to admin dashboard |
| Add New Word | `<a>` | Navigate to add word page |

---

### Words Table

| Column | Content | Source |
|--------|---------|--------|
| Word | Bold word text | `word_stat.word.text` |
| IPA | Monospace transcription | `word_stat.word.ipa` |
| Audio Preview | HTML5 audio player | `word_stat.word.audio_path` |
| Submissions | Count number | `word_stat.submission_count` |
| Last Activity | Date or "Never" | `word_stat.last_submission_str` |
| Actions | Edit / Delete buttons | Links to edit/delete routes |

---

### Action Buttons (Per Row)

| Button | Target | Condition |
|--------|--------|-----------|
| Edit | `/dashboard/admin/word/<id>/edit` | Always visible |
| Delete | Opens delete modal | Disabled in demo mode |

---

## Delete Modal

**ID:** `#word-delete-modal`

### Modal Structure

| Element | ID | Purpose |
|---------|----|---------|
| Form | `#word-delete-form` | POST to delete route |
| Word Name Display | `#modal-word-name` | Shows word being deleted |
| Delete Word Checkbox | `#delete-word-checkbox` | Required to enable delete |
| Delete Submissions Checkbox | `#delete-submissions-checkbox` | Optional cascade delete |
| Cancel Button | `#word-cancel-btn` | Close modal |
| Delete Button | `#word-delete-submit-btn` | Submit delete (disabled until checkbox) |

### Checkbox Dependencies

| State | Delete Submissions | Submit Button |
|-------|-------------------|---------------|
| Word checkbox unchecked | Disabled | Disabled |
| Word checkbox checked | Enabled | Enabled |

---

## Backend Processing

### manage_all_words (GET)

| Step | Action |
|------|--------|
| 1 | Query all Words ordered by text |
| 2 | For each word, count submissions |
| 3 | Get last submission timestamp |
| 4 | Build word_stats list |
| 5 | Render template |

### delete_word (POST /dashboard/admin/word/<id>/delete)

**Handler:** `dashboard_routes.delete_word()` → `dashboard_routes.py:834-888`

| Step | Condition | Action |
|------|-----------|--------|
| 1 | `delete_word` unchecked | Flash warning, redirect |
| 2 | `delete_submissions` checked | Delete all submissions + files |
| 3 | — | Delete audio file from static folder |
| 4 | — | Delete Word record |
| 5 | — | Commit, flash success |

### Delete Form Fields

| Field | Name | Purpose |
|-------|------|---------|
| Delete Word | `delete_word` | Confirmation checkbox |
| Delete Submissions | `delete_submissions` | Cascade delete option |

---

## Flash Messages

| Message | Type | Trigger |
|---------|------|---------|
| "Access denied." | danger | Non-admin access |
| "You must confirm deletion by checking the first box." | warning | Unchecked confirmation |
| "Deleted all student submissions for 'X'." | info | Submissions deleted |
| "Successfully deleted the word 'X'." | success | Delete complete |
| "Could not delete: X" | danger | Delete error |

---

## JavaScript Functions

**Location:** Lines 153-210

| Function | Purpose |
|----------|---------|
| `openWordDeleteModal(id, name, url)` | Open modal with word details |
| `closeWordDeleteModal()` | Close and reset modal |
| Checkbox change handler | Enable/disable dependent checkbox |
| Demo delete handler | Show alert for demo mode |

---

## Demo Mode Behavior

| Element | Behavior |
|---------|----------|
| Delete buttons | Grayed out, disabled cursor |
| Click delete | Shows "disabled in DEMO mode" alert |
| Edit buttons | Still functional (view only) |
| Add New Word | Links to add page |

---

## Navigation Links

| Link | Target |
|------|--------|
| Back to Dashboard | `/admin` |
| Add New Word | `/dashboard/admin/word/add?next=/dashboard/admin/words` |
| Edit (per word) | `/dashboard/admin/word/<id>/edit?next=/dashboard/admin/words` |

---

## Related Routes

| Route | Handler | Purpose |
|-------|---------|---------|
| `/dashboard/admin/word/add` | `add_word()` | Add new word |
| `/dashboard/admin/word/<id>/edit` | `edit_word()` | Edit word |
| `/dashboard/admin/word/<id>/delete` | `delete_word()` | Delete word |
| `/dashboard/admin/generate-pronunciation` | `generate_pronunciation()` | Auto-fetch data |

---

## Database Queries

| Query | Purpose |
|-------|---------|
| `Word.query.order_by(Word.text).all()` | Get all words |
| `word.submissions.count()` | Count submissions per word |
| `word.submissions.order_by(desc).first()` | Get last submission |

---

## Refactoring Notes

1. **Add pagination** → Update query with `.paginate()`, add pagination UI
2. **Add search/filter** → Add search input, update query with filter
3. **Add bulk actions** → Add checkboxes, bulk delete/export
4. **Add sort options** → Add column header clicks, order_by parameter
5. **Change table columns** → Update `<thead>` and row template
6. **Add word status (active/inactive)** → Would require Word model update
