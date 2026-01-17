# Audio Processing V2: Asymmetric Trimming & Noise Safety

## Overview
This document details the "V2" improvements made to the audio recording and processing pipeline to ensure "snappy" starts and "smooth" tails, while robustly handling noise.

## Key Architectures

### 1. Hybrid Noise Floor (Safety Buffer)
We discovered that Client-side **Peak** amplitude is consistently higher (~1.4x - 1.7x) than Server-side **RMS**.
*   **Client:** Sends `noiseFloor` (Peak).
*   **Server:** Receives this Peak value but applies it against RMS measurements.
*   **Result:** This creates a natural **Safety Buffer**. The server perceives the floor as "louder" than average, making the Voice Activity Detection (VAD) more conservative/strict, preventing false positives from background noise.

### 2. Frontend Tail Buffer (Client-Side)
To prevent cutting off the final "tail" (consonant release or reverb) when the user clicks "Stop":
*   **Mechanism:** `UI.recStopBtn` now triggers a **500ms delay** before actually stopping the `MediaRecorder`.
*   **UX:** The UI updates immediately (Opacity 0.5, "CAPTURING TAIL...") to remain responsive.

### 3. Asymmetric Trimming (Server-Side)
We moved from symmetric padding to asymmetric padding in `scripts/audio_processing.py`.

| Parameter | Old Value | New Value | Purpose |
| :--- | :--- | :--- | :--- |
| **Start Padding** | 100ms | **10ms** | Ensures "Snappy" start. Aligns perfectly with "Reference" audio. |
| **End Padding** | 100ms | **300ms** | Preserves the "Fade Out" / Reverb. Prevents abrupt cuts on words like "Book". |
| **Vol Threshold** | 0.015 | **0.010** | Increased sensitivity to catch breathy starts. |

## File Manifest
*   `static/js/script.js`: Implements the 500ms `setTimeout` on stop.
*   `flask_app.py`: Correctly parses `noiseFloor` (camelCase) from FormData.
*   `scripts/audio_processing.py`: Implements the `padding_start` vs `padding_end` logic.

## Usage
No manual action required. These logic paths are active for all `/api/process_audio` requests.

## Appendix A: Audio Trimming Derivation
The audio preprocessing stage (before analysis) uses usage-specific padding derived from acoustic data and theory:

**1. End Padding (300ms) - The "Reverb Tail"**
The 300ms padding buffer was chosen to preserve the natural decay of the voice in a room, preventing abrupt cuts.
*   **Reference Data:** Batch analysis of **20 reference files** (including `call`, `cat`, `moon`) showed natural fade-outs ("tails") ranging from **40ms to 120ms**. The maximum detected tail was 120ms (`cat.mp3`).
*   **Acoustic Theory:** In typical untreated rooms (bedrooms/offices), the Reverberation Time (RT60) is often between **300ms and 500ms**.
*   **Decision:** We selected **300ms** as a safety buffer. This is >2x the reference tail (covering consonant releases like /k/ or /t/) and matches the lower bound of room reverb, ensuring the user's voice decays naturally without capturing excessive dead air.

*   A tight **10ms** padding is used at the start to ensure the recording aligns "snappily" with the playback, matching the instant attack of reference files.

## Appendix B: Full Reference Tail Data
The following table lists the measured "Tail Duration" (fade from Peak > 0.05 to Silence < 0.01) for all reference files:

| File | Tail Duration (s) |
| :--- | :--- |
| **cat.mp3** | **0.120** (Max) |
| moon.mp3 | 0.120 |
| call.mp3 | 0.100 |
| bike.mp3 | 0.080 |
| cup.mp3 | 0.080 |
| bird.mp3 | 0.060 |
| boat.mp3 | 0.060 |
| book.mp3 | 0.060 |
| boy.mp3 | 0.060 |
| cake.mp3 | 0.060 |
| chair.mp3 | 0.060 |
| dark.mp3 | 0.060 |
| ear.mp3 | 0.060 |
| tour.mp3 | 0.060 |
| cow.mp3 | 0.040 |
| green.mp3 | 0.040 |
| hot.mp3 | 0.040 |
| red.mp3 | 0.040 |
| sit.mp3 | 0.040 |
| wait.mp3 | 0.020 |

**Conclusion:** The **300ms** padding encompasses the longest detected tail (120ms) with a >2.5x safety margin.
