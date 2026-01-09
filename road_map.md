# **Pronounce Web Upgrade: Implementation Roadmap**

## **1\. Executive Summary**

Goal: Transition the existing Thesis Tool into a SaaS-ready MVP (Minimum Viable Product).

Key Features: User Accounts (Student/Teacher/Admin), Database Storage, Real-time Analysis, Integrated Student UI.

Tech Stack: Flask, SQLite (Dev) / PostgreSQL (Prod), SQLAlchemy, Flask-Login, Docker/Nginx.

## **2\. Technology Stack**

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

## **3\. Architecture Changes**

### **Current (Thesis Mode)**

* **Storage:** File System (./submissions/pre/...)  
* **Data:** CSV generated via batch script.  
* **Auth:** None (Manual entry of Name/ID).  
* **Analysis:** Offline / Batch.

### **New (Product Mode)**

* **Storage:** File System (Audio) \+ SQL Database (Metadata & Results).  
* **Data:** Relational Tables (users, submissions, analysis\_results, words).  
* **Auth:** Session-based (Login/Logout) \+ **Explicit Data Consent**.  
* **Analysis:** On-Demand (Triggered immediately after upload).

## **4\. Database Schema Design**

1. **User**: Credentials, Roles (student/teacher/admin), and Consent Timestamp.  
2. **Word**: Curriculum Source of Truth (20 words, IPA targets, Reference paths).  
3. **Submission**: Recording metadata and links to physical files.  
4. **AnalysisResult**: Raw/Normalized formants, VTLN scaling factors, and scores.

## **5\. Phase-by-Phase Implementation**

### **Phase 0: Legacy Migration & Scaffolding (Completed)**

* \[x\] **Setup Script:** Create directory structure and placeholders (setup\_structure.py).  
* \[x\] **Legacy Seed:** Populate Word table from audio/index.json (20 target words).  
* \[x\] **Migration Logic:** Create migrate\_all\_data.py to port legacy CSV and audio files.  
* \[x\] **Data Integrity:** Link existing Student IDs to new UUID-based file paths.

### **Phase 1: Foundation & Database (Completed)**

* \[x\] **Models:** Finalize SQLAlchemy schema in models.py.  
* \[x\] **Config:** Set up environment-based configurations in config.py.  
* \[x\] **Initialization:** Connect DB to Flask app and initialize instance folders.  
* \[x\] **Pathing:** Standardize internal paths for static assets and audio folders.

### **Phase 2: Authentication, Role Logic & Consent (Completed)**

* \[x\] **Auth Backend:** Create auth\_routes.py with registration and login logic.  
* \[x\] **Role Selection:** Implemented **Teacher Invite Code** logic (TEACHER\_INVITE\_CODE).  
* \[x\] **Dynamic Registration UI:** Hide "Student ID" and "Consent Box" for verified instructors.  
* \[x\] **Protection:** Secured / and /upload routes with @login\_required.

### **Phase 3: UI/UX Implementation (Core Thesis Tool)**

* [x] **Status Fix:** Update script.js to change text from "Connecting..." to "Online" after successful fetch.  
* \[ \] **Design Alignment (TODO):** Re-style the student recorder, word list, and sidebar dashboard to match the high-fidelity "Design Preview."  
* [x] **Progress Tracking:** Dynamically calculate completion (Words Done / 20\) in the sidebar using existing JS logic.  
* \[x\] **Audio Engine:** Core logic for noise monitoring, trimming, and WAV conversion (Working).  
* \[x\] **Waveform Sync:** Standardized visual scaling via Wavesurfer.js.  
* \[x\] **Reset Logic:** Ensure UI purges old audio data when a new word is selected.
* [x] **Mic Permissions:** Design a "Permission Denied" modal with clear setup instructions.
* [x] **Routing Correction:** Update auth_routes.py to redirect Teachers/Admins to their dashboards.  
* [x] **Teacher View:** Create table monitoring class-wide progress and "Deep Voice" alerts.  
* [x] **Admin Console:** User management and curriculum (Word) editor.

### **Phase 4: Real-Time Analysis (The Vowel Engine)**

* \[ \] **Refactor Engine:** Port analyze\_vowels.py logic into a server-side function.  
* \[ \] **Praat Integration:** Trigger parselmouth formant extraction immediately upon file save.  
* \[ \] **Adaptive Ceiling:** Implement Pitch-Dependent ceiling logic (5000Hz/5500Hz) for accuracy.  
* \[ \] **Data Persistence:** Store f1\_raw, f2\_raw, and distance\_hz in the AnalysisResult table.

### **Phase 5: Normalization & Comparison (VTLN)**

* \[ \] **Scaling Logic:** Implement Vocal Tract Length Normalization (Alpha calculation).  
* \[ \] **Normalization Sync:** Store normalized formants and perceptual (Bark) distances.  
* \[ \] **Feedback Loop:** Return analysis scores (Match %) to the student UI in JSON response.  
* \[ \] **Comparison Visuals:** Display Euclidean distance $d \= \\sqrt{(F1\_1-F1\_2)^2 \+ (F2\_1-F2\_2)^2}$ on waveform.

### **Phase 6: Quality Assurance, UX & Accessibility**

* \[ \] **Error Handling:** Implement global handlers for analysis failures (e.g., silence/clipping).  
* \[ \] **Mobile Optimization:** Ensure the waveform comparison and sidebar are responsive.  

### **Phase 7: Deployment & Infrastructure**

* \[ \] **VPS Setup:** Provision DigitalOcean droplet (Singapore region).  
* \[ \] **Security:** Implement SSL (Certbot) — Mandatory for production microphone access.  
* \[ \] **Production Config:** Set up Gunicorn app server and Nginx reverse proxy.

### **Phase 8: Future Optimization (Post-Thesis / Version 2.0)**

* \[ \] **HTMX Refactor:** Replace UI JavaScript with HTMX to reduce frontend complexity.  
* \[ \] **Performance Polish:** Move audio analysis to a background task queue (Celery/Redis).  
* \[ \] **Advanced Visualization:** Implement D3.js for the scientific vowel chart in the student dashboard.