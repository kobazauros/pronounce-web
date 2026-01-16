# Development Log

## 1. VTLN Derivation (Vocal Tract Length Normalization)

### Problem
Student formants (F1, F2) vary significantly based on vocal tract length (e.g., children have highest formants, adult males lowest). Direct comparison to a fixed reference (e.g., adult male standard) produced inaccurate scores for women and children.

### Theoretical Basis
The vocal tract length can be approximated as a scaling factor ($\alpha$) relative to a reference tract.
$$ F_{student} \approx \alpha \cdot F_{reference} $$

> **Note:** The initial parameters for this normalization, including the reference formant values, were established using recordings provided by the thesis author.

### Implementation
We implemented a **Cumulative VTLN** approach in `analysis_engine.py`:
1.  **Metric:** We calculate the ratio $F_{raw} / F_{ref}$ for both F1 and F2.
2.  **History:** We query all previous valid submissions for the student.
3.  **Calculation:**
    $$ \alpha = \text{Median}( \forall \text{historical ratios} \cup \text{current ratios} ) $$
4.  **Normalization:**
    $$ F_{norm} = F_{raw} / \alpha $$
    Distance is then calculated using these normalized values against the reference.

---

## 2. Issues & Corrections (Jan 2026)

### Case Study: MichaelDS ('cat')
*   **Issue:** User `MichaelDS` submitted 'cat' but received no score (Missing Analysis).
*   **Diagnosis:**
    *   Server logs showed analysis failure.
    *   Spectrogram analysis revealed a high fundamental frequency (~780 Hz).
    *   The syllable detection heuristic (`find_syllable_nucleus`) used a `pitch_ceiling` of 600 Hz.
    *   This caused the pitch detector to reject the voiced segment, treating it as silence/noise ("No voiced intervals found").
*   **Correction:**
    *   Modified `analysis_engine.py` to increase `pitch_ceiling` from 600 Hz to **1200 Hz**.
*   **Result:**
    *   Re-analysis successful. Score: **0.82 Bark**.

### Case Study: High-Noise Recordings (TopQuark, eggypp)
*   **Issue:** Users `TopQuark` ('hot') and `eggypp` ('book') received no scores.
*   **Diagnosis:**
    *   Spectrograms showed absence of harmonics (unvoiced/whisper) and high noise levels.
    *   This is a valid "Unanalyzable" result, not a system error.
*   **Correction:**
    *   Updated **Instructor Dashboard** to explicitly handle `NaN` (Not a Number) results.
    *   Added "N/A Results" card to statistics.
    *   Added "N/A" badge to Student Directory.

### Case Study: High Fidelity Noise Floor (Fidelity Test)
*   **Issue:** User reported internal laptop microphone recordings were being cut off prematurely, particularly on soft endings ("cat", "book"), while external headsets performed better.
*   **analysis:** 
    *   Conducted forensic analysis of 23 submissions (Internal vs Headset).
    *   **Internal Mic:** Avg Score 2.05 Bark. Trailing silence ~0.1ms (Premature cut).
    *   **Headset:** Avg Score 1.72 Bark. Cleaner signal.
*   **Root Cause:**
    *   "High Fidelity Mode" disables browser-side noise suppression (`echoCancellation: false`, `noiseSuppression: false`).
    *   On laptop internal mics (positioned near fans/keyboards), the physical noise floor is high.
    *   The server-side trimmer interprets this high noise floor as "signal," preventing the silence detection algorithm from finding a valid "quiet" pad at the end of the word.
*   **Solution:**
    *   Instead of enabling aggressive software filtering (which distorts vowel formants), we chose to enforce **Environmental Requirements**.
    *   **UI Update:** Added "Best Practices" modal to the recorder.
    *   **Documentation:** Updated manuals to explicitly state "Quiet Room Required" for High Fidelity Mode.

## 3. Infrastructure & Observability (Jan 2026)

### Database Migration (SQLite to PostgreSQL)
*   **Problem:** SQLite caused "Database Locked" errors during concurrent audio submissions because it locks the entire file for writes.
*   **Solution:** Migrated to PostgreSQL, which supports row-level locking and true concurrency.
*   **Implementation:** 
    *   Created `utility/migrate_to_postgres.py` to transfer data while preserving foreign key relationships.
    *   Updated `models.py` to be compatible with both (using SQLAlchemy abstraction).

### Observability (Sentry)
*   **Goal:** Catch unhandled exceptions in production without ssh-ing into logs.
*   **Implementation:**
    *   Integrated `sentry-sdk[flask]`.
    *   Captures full stack traces, user context (ID), and request data.
    *   Wrapped in `try/except` to ensure local development works without credentials.
    
## 4. Development Workflow: Code vs. Data

To prevent production data loss during rapid development cycles, we have enforced a strict separation of concerns in our tooling.

*   **Code (.py, .js, .html):** managed via **VS Code SFTP**.
    *   *Constraint:* Configured to explicitly **IGNORE** `instance/`, `submissions/`, and `static/audio`.
    *   *Reason:* Prevents `uploadOnSave` from accidentally overwriting the live database with a local empty test database.

*   **Data (DB, Audio Assets):** managed via **`scripts/sync_data.py`**.
    *   *Constraint:* Requires explicit command execution (not automatic).
    *   *Reason:* Forces intent. You must consciously choose to download or overwrite production data.
    *   *Implementation:* Uses `paramiko` to read `sftp.json` creds but executes independent logic.
