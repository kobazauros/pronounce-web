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
