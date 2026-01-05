
### **Technical Justification for Adaptive Formant Analysis and Vocal Tract Length Normalization (VTLN)**

**1. The Problem: Anatomical Bias in Standard Acoustic Analysis**
Standard acoustic analysis software (such as Praat) typically uses default settings optimized for an "average" male voice (vocal tract length ~17cm). However, the participant pool includes individuals with significantly varying vocal tract dimensions, specifically deep male voices with longer vocal tracts (e.g., Participant ID 670120182, height 188cm).

Using standard settings (Maximum Formant Frequency = 5500 Hz) on these subjects resulted in two critical types of data failure:

* **Measurement Failure (The "Moon" Error):** For back vowels like /uː/ (*moon*) and /ɔː/ (*call*), the Second Formant (F2) in deep voices often drops below 500 Hz, becoming acoustically close to the First Formant (F1). Standard algorithms failed to distinguish F1 from F2, often merging them into a single peak. Consequently, the software incorrectly identified the Third Formant (F3) as F2, resulting in errors of >1500 Hz (e.g., measuring *moon* with an F2 of ~2080 Hz instead of ~450 Hz).
* **Comparison Failure (The "Size" Bias):** Even when measured correctly, a larger student’s formants are naturally lower than the reference model’s simply due to physics, not pronunciation error. A direct comparison (Euclidean distance in Hz) would penalize students for having a larger head size, yielding high "error" scores even for native-like pronunciation.

**2. Solution I: Adaptive Formant Estimation (AFE)**
To resolve Measurement Failure, we implemented an **Adaptive Ceiling Algorithm**. Instead of applying a static ceiling (cutoff frequency) for all files, the system now employs a two-pass logic:

* **Pass 1 (Standard):** The system attempts to measure formants using standard settings (Ceiling: 5500 Hz).
* **Pass 2 (Deep Voice Correction):** If the detected formants are physically impossible for a given vowel (e.g., an F2 > 1500 Hz for the back vowel /uː/), the system triggers a "Deep Voice Retry." It re-analyzes the specific file with a lowered ceiling (4000 Hz).
* *Justification:* Lowering the ceiling forces the Linear Predictive Coding (LPC) algorithm to allocate its poles to the lower frequency range, successfully resolving the "merged" F1/F2 cluster in deep voices.
* *Impact:* This correction reduced the measured distance for the word *moon* from an erroneous **1544 Hz** (artifact) to a valid **~300 Hz** (actual pronunciation difference).



**3. Solution II: Vocal Tract Length Normalization (VTLN)**
To resolve Comparison Failure, we implemented **VTLN** to separate anatomical differences from pronunciation skill.

* **Scaling Factor ():** For each student, the system calculates a unique acoustic scaling factor () based on the ratio of their formants to the reference model’s formants across multiple vowels.
* *Example:* For Participant 670120182, the system calculated , indicating a vocal tract roughly 20% longer/deeper than the reference.


* **Normalization:** Before scoring, the student’s raw frequency data is normalized using the formula: .
* *Justification:* This mathematical transformation effectively "resizes" the student’s acoustic vowel space to match the reference model’s dimensions.
* *Impact:* The final "Distance" score now reflects only **phonetic placement** (tongue position and lip rounding)—which the student can control—rather than vocal tract length, which they cannot.



**4. Conclusion**
These modifications ensure that the assessment system is **robust** (capable of analyzing diverse voice types without crashing or generating artifacts) and **fair** (grading students on linguistic performance rather than biological traits).