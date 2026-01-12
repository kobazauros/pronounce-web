**Pass 1: Raw Formant Analysis**
This is the initial data extraction phase, performed by the analyze_raw_data function on each student's audio file.

***File Discovery:*** (now all the files are in DB)
The script scans the submissions directory for all *.mp3 files.

***Metadata Parsing:*** (now all the files are in DB)
For each file, it extracts the student ID, student name, and the spoken word from the filename (e.g., 1_John-Doe_book.mp3).

***Audio Loading:***
The student's audio file and the corresponding reference audio file (e.g., static/audio/book.mp3) are loaded. The load_audio_mono function ensures the audio is:
Converted to mono.
Resampled to a consistent sample rate (16000 Hz).
Volume-normalized to prevent loudness from affecting the analysis.

***Syllable Nucleus Detection:***
The find_syllable_nucleus function identifies the core, loudest part of the vowel in the recording. It does this by analyzing the audio's pitch and intensity to find the most prominent voiced segment.

***Formant Measurement:***
The measure_formants function measures the F1 and F2 frequencies (which correspond to vowel quality) within the detected syllable nucleus.
For simple vowels (monophthongs), it measures at the 50% midpoint of the nucleus.
For complex vowels (diphthongs), it measures at the 20% and 80% points to capture the vowel's movement.
Adaptive Ceiling Logic: A key feature is its adaptive analysis. It first attempts to measure formants with a standard frequency ceiling (5500 Hz). However, if the script is analyzing a "back vowel" (like in "boot" or "boat") and gets a missing or suspiciously high F2 value, it automatically re-runs the measurement with a lower ceiling (4000 Hz). This helps to correctly identify F2 in deep voices where it can be merged with F1. This logic is applied to both the student's and the reference audio.
Storing Raw Data: The raw F1 and F2 measurements for both the student and the reference speaker are stored for the next pass.

**Pass 2: Calculating the Normalization Factor (VTLN)**
This pass calculates a unique vocal tract length normalization (VTLN) factor for each student. This is crucial for comparing speakers with different vocal tract sizes (e.g., comparing a child to an adult).

***Grouping by Student:***
All raw measurements from Pass 1 are grouped by student ID.

***Calculating Ratios:***
For every word, the script calculates the ratio of the student's formants to the reference speaker's formants (e.g., student_F1 / ref_F1, student_F2 / ref_F2).

***Finding the Median:***
It collects all these ratios for a single student across all their recordings and calculates the median. This median value becomes the student's personal scaling factor (alpha). The median is used to ensure that a few outlier recordings don't skew the result.

**Pass 3: Applying Normalization and Saving Results**
The final pass uses the scaling factor from Pass 2 to normalize the data and compute the final results.
***Applying Normalization:*** 
The script iterates through the raw results again. Each of the student's raw formant measurements (F1, F2) is divided by their personal alpha factor. This adjusts their vowel sounds to the scale of the reference speaker, allowing for a fair comparison.
***Calculating Distance:*** 
After normalization, it calculates the "distance" between the student's normalized vowel and the reference vowel in acoustic space. This is done using the Euclidean distance formula, providing a single number that represents how different the pronunciations are. The distance is calculated in both Hertz (Hz) and the psychoacoustic Bark scale.
***Exporting to CSV:*** 
All the data—including student info, raw formants, the scaling factor, normalized formants, and the final distance metrics—is compiled into a pandas DataFrame and saved to a single CSV file: analysis_vowels/final_thesis_data.csv.

**Pass 4: Articulatory Feedback Generation**
This final step translates the acoustic distance into actionable advice for the student. It compares the student's normalized formants (F1_norm, F2_norm) to the reference target (F1_ref, F2_ref) using linguistic heuristics:

***F1 (Tongue Height / Jaw Opening):***
*   **Student F1 < Target:** Tongue/Jaw is too high/closed. -> *"Open your mouth more."*
*   **Student F1 > Target:** Tongue/Jaw is too low/open. -> *"Close your mouth slightly."*

***F2 (Tongue Backness / Lip Rounding):***
*   **Student F2 < Target:** Tongue is too far back (or lips too rounded). -> *"Move your tongue forward."* (For front vowels like /i/, *"Smile/Spread lips"*).
*   **Student F2 > Target:** Tongue is too far forward (or lips too widespread). -> *"Move your tongue back."* (For back vowels like /u/, *"Round your lips"*).

This feedback is returned immediately to the user interface.