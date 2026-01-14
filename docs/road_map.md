# **Pronounce Web Upgrade: Implementation Roadmap**

## **1. Executive Summary**

Goal: Transition the existing Thesis Tool into a SaaS-ready MVP (Minimum Viable Product).

Key Features: User Accounts (Student/Teacher/Admin), Database Storage, Real-time Analysis, Integrated Student UI.

Tech Stack: Flask, SQLite (Dev) / PostgreSQL (Prod), SQLAlchemy, Flask-Login, Docker/Nginx.

## **2. Technology Stack**

### **Core Web Stack**

* **Backend:** Python 3.12+, Flask 3.0.  
* **Database:** SQLite (Development), PostgreSQL (Production/VPS).  
* **ORM:** SQLAlchemy (Data modeling), Flask-Migrate (Schema management).  
* **Authentication:** Flask-Login (Session management), Werkzeug (Security).

### **Scientific & Audio Stack (Server-Side)**

* **Praat-Parselmouth:** *CRITICAL.* Used for the "Adaptive Ceiling" formant analysis and VTLN calculations.  
* **Librosa:** Used for signal processing and duration analysis.  
* **NumPy / SciPy:** For statistical calculations (Euclidean distance, outlier detection).  
* **TTS & Reference Generation:** gTTS (Google Text-to-Speech).

### **Frontend & Interaction Stack (Client-Side)**

* **Templating:** Jinja2 (HTML generation).  
* **Styling:** Tailwind CSS (Modern Dashboard/Hybrid designs).  
* **Audio Recording:** MediaRecorder API / LAME.js (MP3 encoding).  
* **Visualization:** Wavesurfer.js (Interactive waveforms).  
* **Noise Control:** **Web Audio API (AudioContext)** for real-time monitoring.

## **3. Architecture Changes**

### **Current (Thesis Mode)**

* **Storage:** File System (./submissions/pre/...)  
* **Data:** CSV generated via batch script.  
* **Auth:** None (Manual entry of Name/ID).  
* **Analysis:** Offline / Batch.

### **New (Product Mode)**

* **Storage:** File System (Audio) + SQL Database (Metadata & Results).  
* **Data:** Relational Tables (users, submissions, analysis_results, words).  
* **Auth:** Session-based (Login/Logout) + **Explicit Data Consent**.  
* **Analysis:** On-Demand (Triggered immediately after upload).

## **4. Database Schema Design**

1. **User**: Credentials, Roles (student/teacher/admin), and Consent Timestamp.  
2. **Word**: Curriculum Source of Truth (20 words, IPA targets, Reference paths).  
3. **Submission**: Recording metadata and links to physical files.  
4. **AnalysisResult**: Raw/Normalized formants, VTLN scaling factors, and scores.

## **5. Phase-by-Phase Implementation**

### **Phase 0: Legacy Migration & Scaffolding (Completed)**

*1 [x] **Setup Script:** Create directory structure and placeholders (setup_structure.py).  
*2 [x] **Legacy Seed:** Populate Word table from audio/index.json (20 target words).  
*3 [x] **Migration Logic:** Create migrate_all_data.py to port legacy CSV and audio files.  
*4 [x] **Data Integrity:** Link existing Student IDs to new UUID-based file paths.

### **Phase 1: Foundation & Database (Completed)**

*5 [x] **Models:** Finalize SQLAlchemy schema in models.py.  
*6 [x] **Config:** Set up environment-based configurations in config.py.  
*7 [x] **Initialization:** Connect DB to Flask app and initialize instance folders.  
*8 [x] **Pathing:** Standardize internal paths for static assets and audio folders.

### **Phase 2: Authentication, Role Logic & Consent (Completed)**

*9 [x] **Auth Backend:** Create auth_routes.py with registration and login logic.  
*10 [x] **Role Selection:** Implemented **Teacher Invite Code** logic (TEACHER_INVITE_CODE).  
*11 [x] **Dynamic Registration UI:** Hide "Student ID" and "Consent Box" for verified instructors.  
*12 [x] **Protection:** Secured / and /upload routes with @login_required.

### **Phase 3: UI/UX Implementation (Core Thesis Tool)**

*13 [x] **Status Fix:** Update script.js to change text from "Connecting..." to "Online" after successful fetch.  
*14 [x] **Design Alignment (TODO):** Re-style the student recorder, word list, and sidebar dashboard to match the high-fidelity "Design Preview."  
*15 [x] **Progress Tracking:** Dynamically calculate completion (Words Done / 20) in the sidebar using existing JS logic.  
*16 [x] **Audio Engine:** Core logic for noise monitoring, trimming, and WAV conversion (Working).  
*17 [x] **Waveform Sync:** Standardized visual scaling via Wavesurfer.js.  
*18 [x] **Reset Logic:** Ensure UI purges old audio data when a new word is selected.
*19 [x] **Mic Permissions:** Design a "Permission Denied" modal with clear setup instructions.
*20 [x] **Routing Correction:** Update auth_routes.py to redirect Teachers/Admins to their dashboards.  
*21 [x] **Teacher View:** Create table monitoring class-wide progress and "Deep Voice" alerts.  
*22 [x] **Admin Console:** User management and curriculum (Word) editor.
*23 [x] **Recording Page Optimization:** Implemented single-page layout (100vh) with fixed waveform height and compact controls.
*24 [x] **Auth Page Refinement:** Balanced Login/Registration layouts (reduced whitespace, fixed typography).

### **Phase 4: Research & Instructor Dashboards (Completed)**
*25 [x] **Instructor Dashboard:** Class overview, deep voice alerts, student drill-down.
*26 [x] **Research Dashboard:** Raw data table, scatter plots, correlation analysis.
*27 [x] **Data Visualization:** Chart.js integration for vowel space and error histograms.

### **Phase 5: Audio Loading & Standardization (Completed)**
*28 [x] **Audio Standardization:** Audio loaded as mono, 16kHz, 32-bit float.
*29 [x] **Volume Normalization:** Applied to prevent loudness bias.

### **Phase 6: Real-Time Analysis Engine (Completed)**
*30 [x] **Server-Side Processing:** Ported `analyze_vowels.py` to `analysis_engine.py` using `parselmouth`.
*31 [x] **Adaptive Ceiling:** Implemented pitch-dependent ceiling logic (Reference vs Student).
*32 [x] **VTLN Scaling:** Implemented Vocal Tract Length Normalization (Alpha calculation).
*33 [x] **Database Integration:** Automatic population of `AnalysisResult` upon upload.
*34 [x] **Outlier Detection:** Flagging results with >5.0 Bark distance.

### **Phase 7: Student Feedback & Comparison (VTLN) (Completed)**
*35 [x] **Feedback Loop:** Return analysis scores (Match %) to the student UI in JSON response.
*36 [x] **Comparison Visuals:** Visualize Euclidean distance as a vector on the **Vowel Space Chart** (Student vs Reference point).
*37 [x] **Articulatory Recommendations:** Generate text feedback based on F1/F2 vectors (e.g., "Open mouth more", "Move tongue forward").
*38 [x] **UX/Design Consistency Audit:** Completed visual/mobile audit (Report available).

### **Phase 8: Quality Assurance & Staging (Completed)**
*Before any external sharing, we verify data accuracy and system stability.*
*39 [x] **Automated Testing Suite:** Implemented `pytest` for unit analysis (100% pass) and basic route integration.
*40 [x] **Linguistic & Concept Analysis:** Documented acoustic pitfalls and design validation strategy.
*41 [x] **Load Testing (Local):** Verified server efficiency (30ms processing time) using `simulate_student.py`.
*42 [x] **Remote Evaluation Prep:** Verified Ngrok tunnel performance (~130ms latency) for external access.
*43 [x] **Student Simulation:** Created automated script to simulate full user lifecycle (Register -> Pre/Post Test).

### **Phase 8.5: Documentation & Help System (Completed)**
*Comprehensive guides for all user roles.*
*44 [x] **User Manual Expansion:** Rewrote `/manual` with roles (Student/Teacher/Admin) and "Research Panel" guide.
*45 [x] **Role-Based Navigation:** Implemented dynamic header links and "Smart Manual" that adapts to user role.
*46 [x] **Glossary & FAQ:** Added technical definitions (Bark, Formants) and troubleshooting tips.

### **Phase 8.6: Client-Side Reliability Matrix (Hardware & Browsers)**
*Goal: Optimize testing by establishing a "Gold Standard" baseline first, then strictly validating variations.*

*   **Step 1: Signal Baseline (ASUS Laptop + Chrome)**
    *   **Action:** Tune **Trimming** (fix cutoff issues) and **Silence Detection** on this primary device.
    *   **Goal:** Establish a working baseline for internal microphones (highest noise floor scenario).
*   **Step 2: Browser Cross-Check (ASUS Laptop)**
    *   **Action:** Verify core functionality on **Edge, Opera, and Firefox**.
    *   **Optimization:** Focus purely on API compatibility (MediaRecorder), assuming signal logic holds from Step 1.
*   **Step 3: Hardware/Browser Interaction Matrix (The "Colleague's Bug" Check)**
    *   **Context:** User reported: *Headset works on Opera, fails on Chrome.*
    *   **Action:** Test **Headset (USB & 3.5mm)** specifically on **Chrome vs Opera**.
    *   **Goal:** Identify browser-specific handling of external audio devices (e.g., Chrome's strict AudioContext rules vs Opera).
    *   **Fix:** Ensure `handleDeviceChange` and `AudioContext.resume()` logic is robust across all browser/hardware combinations.
*   **Step 4: Mobile Verification (Poco F5)**
    *   **Action:** Test Chrome for Android.
    *   **Focus:** Verify responsive layout and mobile audio permissions.

### **Phase 8.8: Analysis Calibration & Fine-Tuning (Pre-Production)**
*CRITICAL: Ensure the engine is fair and accurate across different voices before public launch.*
*47 [x] **Data Prep:** Create `dataset/forvo` directory structure to organize diverse audio samples.
*48 [x] **Data Collection:** Fetched and structurized 81 diverse audio samples from Forvo.com (26 speakers) for calibration.
*49 [x] **Diversity Simulation:** Ran simulation on 81 diverse files. Verified robustness for high-pitched voices (e.g., corrected MichaelDS pitch ceiling).
*50 [ ] **Threshold Tuning:** Review the 1.5 Bark recommendation threshold. Is it too strict? Too lenient?
*51 [x] **False Positive/Negative Analysis:** Fixed "Unanalyzable" errors for whispered/noisy inputs (TopQuark, eggypp) and high pitch (MichaelDS).
*52 [ ] **Beta "Soft Launch":** Deploy to a small group (Staging) to gather real-world data for final tuning.

### **Phase 9: Production Deployment (Live Infrastructure)**
*The "Real-World" Environment.*
*51 [ ] **Infrastructure Provisioning:** DigitalOcean Droplet (Ubuntu LTS) with UFW Firewall.
*52 [ ] **Web Server Optimization:** Nginx tuned for file uploads (client_max_body_size) and Gzip compression.
*53 [ ] **Application Server:** Gunicorn with `gthread` workers to handle concurrent I/O (audio processing blocking).
*54 [ ] **Security:** SSL (Let's Encrypt), Rate Limiting (Flask-Limiter) to prevent abuse.
*55 [ ] **Observability:** Sentry integration for real-time error tracking and performance monitoring.

### **Phase 10: Scalability & Architecture (Post-MVP)**
*Optimizing for 100+ concurrent users.*
*50 [ ] **Asynchronous Processing:** Move `process_submission` to a background worker (Celery + Redis) to prevent HTTP timeouts.
*51 [ ] **Database Migration:** Migrate from SQLite (disk-locked) to PostgreSQL (concurrent-safe).
*52 [ ] **CDN Integration:** Serve static audio reference files via Cloudflare/AWS S3.


## **Project Structure**

```
c:\Users\rookie\Documents\Projects\pronounce-web\
├───.gitignore
├───analyze_vowels.ipynb
├───analyze_vowels.py
├───auth_routes.py
├───config.py
├───dashboard_routes.py
├───flask_app.py
├───models.py
├───readme.md
├───requirements.txt
├───road_map.md
├───sync_project_files.py
├───__pycache__\
├───docs\
│   └───road_map.md
├───utility\
│   ├───migrate_all_data.py
│   ├───deploy_pa_helpers.py (To be deleted)
│   └───setup_vps.sh (Coming soon)
├───scripts\
│   ├───__init__.py
│   ├───audio_processing.py
│   └───parser.py
├───tests\
│   ├───conftest.py
│   └───test_routes.py
├───archive\ (Obsolete scripts)
├───static\
├───templates\
├───analysis_engine.py
├───auth_routes.py
├───config.py
├───dashboard_routes.py
├───flask_app.py
├───models.py
├───requirements.txt
└───wsgi.py (To be deleted)
```