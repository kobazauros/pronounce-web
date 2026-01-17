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
