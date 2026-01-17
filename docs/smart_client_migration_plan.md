# Trimming & Recording Architecture Migration Plan

## Goal Description
Migrate from "Backside (Server) Trimming" to a **"Hybrid Smart Client"** architecture. This places the recording quality control and decision-making in the user's hands via the frontend, ensuring no data loss and "white-box" transparency.

## User Review Required
> [!IMPORTANT]
> This is a significant architectural shift. It moves complexity from Python (Server) to JavaScript (Client).
> **Key Decisions:**
> 1. **Block vs Warn:** We will BLOCK recording if the noise floor is too high (The Bouncer).
> 2. **Visual Verification:** Users *must* see and confirm the waveform region before submission.
> 3. **Format:** We will likely need to send WAV/Blob slices from the client, or timecode metadata if sending the full file. (Recommendation: Send the sliced Blob to save bandwidth).

## Current Architecture (Backside Trimming)

### Frontend (`static/js/script.js`)
- **Recording:** Captures raw audio via `AudioWorkletNode`.
- **Noise Monitoring:** **Non-Restrictive Active Monitor**. It actively calculates `measuredNoiseFloor` to update the visual UI, but it **does not block** recording even if the noise level makes analysis impossible.
- **Transmission:** The **entire** recording session is bundled as a WAV blob and uploaded to `/api/process_audio`, **along with the `measuredNoiseFloor`**.
- **Client-Side Trimming:** The `trimSilence` function exists in JS but is currently used primarily for **playback visualization** of samples, not for processing user uploads before transmission.

### Backend (`flask_app.py` & `scripts/audio_processing.py`)
- **Endpoint:** `/api/process_audio` receives the raw upload.
- **Processing Logic (`process_audio_data`):**
    1.  **Format:** Converts input to 16kHz Mono.
    2.  **Noise Floor:** Uses client-provided floor (if `> 0.0001`) or estimates it via 10th percentile of RMS.
    3.  **Trimming:** Applies a heuristic "Voice Activity Detection" (VAD) using RMS amplitude (> 2.0x floor) and Zero-Crossing Rate (> 0.1).
    4.  **Padding:** Adds ~100ms padding.
    5.  **Normalization:** Peak normalizes to -0.5dB.
    6.  **Output:** Saves as MP3.
- **Workflow & Issues:**
    - **Step 1 (Upload):** User records -> Full blob sent to `/api/process_audio`.
    - **Step 2 (Server Trim):** Server applies blind VAD trimming and saves the file.
    - **Step 3 (Verification):** User sees the waveform of the *already trimmed* file.
    - **The Problem:** If the server cuts off a final consonant (e.g., "cat" becomes "ca"), the user sees a truncated waveform and must re-record. They cannot "undo" the trim because the data is already lost on the server.

### User Priorities
- **Efficiency/Latency:** **Low Priority**. The user accepts 1-2s latency and bandwidth overhead as "intentional architecture" trade-offs.
- **Critical Goal:** **Careful Trimming**. The absolute priority is ensuring the trim is *correct* and does not lose data (transparency).
- **Motivation for Change:** Moving trimming to the client is purely to **visualize and verify** the cut before submission, removing the "Black Box" risk.




### Submission & Analysis (Redis/Celery)
- **Workflow:** After verification, the user clicks "Submit".
- **Async Processing:** The request is offloaded to a **Celery Worker** (via Redis broker) to perform the heavy Praat/Parselmouth analysis (`tasks.async_process_submission`).
- **Polling:** The frontend polls `/api/status/<task_id>` until the worker completes.
- **Critical Issues:**
    - **Black Box (Data Loss):** User has no control over the cut. If server VAD is too aggressive (e.g., for trailing 't' or 'k'), the data is discarded permanently.
    - **Transparency:** The user cannot see *why* a recording was rejected or trimmed poorly.
    - *(Note: User has explicitly stated latency is acceptable, so we focus purely on Quality/Transparency).*





## Proposed Changes

### 1. "The Bouncer" (Adaptive Noise Gate)
**Component:** `static/js/script.js`
- **Current:** **Non-Restrictive Active Monitor** (icon color change only).
- **New:**
    - Calculate **Dynamic Range** (Peak - Floor).
    - **Active Block:** If Dynamic Range < 10dB (configurable), disable the "Record" button and show a specific error: "Too Noisy for Analysis".
    - **UI:** Add a clear metric display (e.g., "Signal Quality: Poor/Good") next to the record button.

### 2. "Record Everything" (Buffer Management)
**Component:** `static/js/script.js` & `recorder-worklet.js`
- **Current:** `AudioWorklet` captures raw chunks. Recording stops via:
    1.  **Manual:** User clicks "Stop".
    2.  **Max Duration:** Hard limit of 5 seconds (`Config.MAX_RECORDING_MS`).
    3.  **Auto-Silence:** If signal < Threshold for 1.5 seconds.
    *Upon stop, data is flattened and sent immediately.*
- **New:**
- **New:**
    - Continue using `AudioWorklet` (verified present).
    - **Change:** Instead of auto-uploading on stop, we simply hold the full buffer in memory (`userBuf`) and render it to the screen.
    - **Safety Padding:** When the user stops, *do not* cut immediately. We technically record "everything" the user *intended*.
    - *Correction:* The user proposal says "Record Everything... applies a Safety Padding... around detected voice activity". This implies *internal* VAD (Voice Activity Detection) during the recording session?
    - **Refined Approach:** We will record the entire session (Press Start -> Press Stop). The *VAD* happens *post-recording* (The Barber) to suggest a region. We don't want to cut *during* recording (Live VAD) because that risks the "glottal stop" data loss mentioned.

### 3. "Smart Auto-Trim" (Client-Side Logic)
**Component:** `static/js/script.js`
- **Goal:** Zero Latency, Zero User Effort.
- **Logic:**
    - On `stopRecording()`, immediately run `trimSilence()` on the raw buffer.
    - **Crucial:** Pass the confirmed `measuredNoiseFloor` (from The Bouncer) to the trim function.
    - **Verify:** Render the *trimmed* waveform immediately.
    - **Fallback:** If the user sees it's cut wrong, they click "Record" again (Retake). No drag handles, no complex UI.
    - **Submit:** Send the *active trimmed blob* to the server.

### 4. Backend Update (Streamlined)
**Component:** `flask_app.py`
- **New:**
    - Accept `audio` file (MP3/WAV) as **Final Data**.
    - **Skip Trimming:** Do NOT run `process_audio_data` trimming logic.
    - **Action:** Convert to standard format (16kHz Mono) and save.


### 5. Submission Pipeline (Unchanged)
- **Workflow:** The `/api/submit_recording` endpoint remains the same.
- **Architecture:** It continues to use **Redis & Celery** for asynchronous scoring. The only difference is that the input file it processes is now guaranteed to be "User-Verified" rather than "Server-Trimmed".


## Verification Plan

### Manual Verification
1.  **Noise Block Test:** Play white noise (fan). Verify "Record" button is disabled/warns.
2.  **Trimming Test:** Record "Cat" (with faint 't').
    - Verify the "Auto-Suggest" region includes the 't'.
    - Manually adjust the region to cut the 't' -> Verify submission is bad.
    - Manually adjust to keep 't' -> Verify submission is good.
3.  **Data Loss Check:** Pause for 1 second in the middle of a sentence. Ensure it's not cut if the region covers it.
