# About Page (`about.html`)

**Route:** `GET /about`  
**Handler:** `flask_app.about()` → `flask_app.py:169-172`  
**Template:** `templates/about.html`  
**Extends:** `base.html`

> **Note:** Accessible to all users (authenticated and unauthenticated). Linked from footer in `base.html`.

---

## Page Purpose

Project information page displaying:
- University affiliation and thesis title
- Research context and mission
- Technical foundation overview
- Developer/researcher profile
- Donation/support options

---

## Template Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| (none) | — | Static content page |

---

## UI Sections

### 1. Header Section

| Element | Content |
|---------|---------|
| University Logo | `static/img/university_logo.png` |
| Thesis Title | Full research title text |
| Separator | Decorative indigo line |

### 2. Research Narrative

| Element | Content |
|---------|---------|
| Section Title | "Research Context" with book icon |
| Description | Core mission and purpose of the application |
| Details | Real-time acoustic analysis explanation |

### 3. Technical Foundation ("Powered By")

| Card | Icon | Label |
|------|------|-------|
| Praat Analysis | `fa-wave-square` (indigo) | Audio analysis engine |
| Formant Mapping | `fa-chart-line` (purple) | Vowel visualization |
| Real-time Feedback | `fa-bolt` (amber) | Instant results |

### 4. Developer Profile Card

| Element | Content |
|---------|---------|
| Author Photo | `static/img/author_profile.jpg` |
| Title | "Researcher & Developer" |
| Name | "Konstantin Bantov" |
| Bio | Short description text |

### 5. Support Section

| Button | Modal Type | Content |
|--------|------------|---------|
| PromptPay | `promptpay` | QR code for Thai banking |
| TrueMoney | `truemoney` | QR code + wallet ID (copyable) |
| Card | `card` | "Coming Soon" message |

---

## Static Assets Used

| Path | Purpose |
|------|---------|
| `static/img/university_logo.png` | University logo in header |
| `static/img/author_profile.jpg` | Developer photo |
| `static/img/icon_promptpay.png` | PromptPay button icon |
| `static/img/icon_truemoney.png` | TrueMoney button icon |
| `static/img/qr_promptpay.jpeg` | PromptPay QR code |
| `static/img/qr_truemoney.png` | TrueMoney QR code |

---

## Modal System

### Modal Container

| Element | ID | Purpose |
|---------|----|---------|
| Overlay | `#support-modal` | Background overlay with blur |
| Panel | `#modal-panel` | White card container |
| Title | `#modal-title` | Dynamic title text |
| Content | `#modal-content` | Dynamic content area |
| Close Button | `onclick="closeModal()"` | Close modal |

### Templates (Hidden)

| Template ID | Content |
|-------------|---------|
| `#tmpl-promptpay` | QR code image + scan instruction |
| `#tmpl-truemoney` | QR code + copyable wallet ID |
| `#tmpl-card` | Coming soon message with card icons |

---

## JavaScript Functions

**Location:** Lines 204-258

| Function | Purpose |
|----------|---------|
| `openModal(type)` | Opens modal with specified content type |
| `closeModal()` | Closes modal with animation |
| `copyToClipboard(elementId)` | Copies text to clipboard, shows toast |

### Modal Event Listeners

| Event | Action |
|-------|--------|
| Click outside modal | Closes modal |
| Click close button | Closes modal |
| Click wallet ID | Copies to clipboard |

---

## Toast Notification

| Element | ID | Purpose |
|---------|----|---------|
| Toast | `#copy-toast` | "Copied!" confirmation message |

---

## CSS Features

| Feature | Implementation |
|---------|----------------|
| Modal Animation | `opacity-0` → `opacity-100`, `scale-95` → `scale-100` |
| Backdrop Blur | `backdrop-blur-sm` on overlay |
| Hover Effects | `hover:scale-110` on support buttons |
| Card Shadows | `shadow-sm`, `shadow-lg`, `shadow-2xl` |

---

## Navigation Links

| Link | Target |
|------|--------|
| (none) | No outbound links from this page |

---

## Refactoring Notes

1. **Update thesis title** → Edit `<h1>` content (lines 17-20)
2. **Change author info** → Update developer profile section (lines 78-88)
3. **Add new support method** → Add button + template + modal case
4. **Update QR codes** → Replace images in `static/img/`
5. **Change research description** → Edit Research Narrative section (lines 33-44)
6. **Add new "Powered By" item** → Add grid item in Technical Foundation (lines 50-63)
