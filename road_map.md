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

* [x] **Setup Script:** Create directory structure and placeholders (setup_structure.py).  
* [x] **Legacy Seed:** Populate Word table from audio/index.json (20 target words).  
* [x] **Migration Logic:** Create migrate_all_data.py to port legacy CSV and audio files.  
* [x] **Data Integrity:** Link existing Student IDs to new UUID-based file paths.

### **Phase 1: Foundation & Database (Completed)**

* [x] **Models:** Finalize SQLAlchemy schema in models.py.  
* [x] **Config:** Set up environment-based configurations in config.py.  
* [x] **Initialization:** Connect DB to Flask app and initialize instance folders.  
* [x] **Pathing:** Standardize internal paths for static assets and audio folders.

### **Phase 2: Authentication, Role Logic & Consent (Completed)**

* [x] **Auth Backend:** Create auth_routes.py with registration and login logic.  
* [x] **Role Selection:** Implemented **Teacher Invite Code** logic (TEACHER_INVITE_CODE).  
* [x] **Dynamic Registration UI:** Hide "Student ID" and "Consent Box" for verified instructors.  
* [x] **Protection:** Secured / and /upload routes with @login_required.

### **Phase 3: UI/UX Implementation (Core Thesis Tool)**

* [x] **Status Fix:** Update script.js to change text from "Connecting..." to "Online" after successful fetch.  
* [x] **Design Alignment (TODO):** Re-style the student recorder, word list, and sidebar dashboard to match the high-fidelity "Design Preview."  
* [x] **Progress Tracking:** Dynamically calculate completion (Words Done / 20) in the sidebar using existing JS logic.  
* [x] **Audio Engine:** Core logic for noise monitoring, trimming, and WAV conversion (Working).  
* [x] **Waveform Sync:** Standardized visual scaling via Wavesurfer.js.  
* [x] **Reset Logic:** Ensure UI purges old audio data when a new word is selected.
* [x] **Mic Permissions:** Design a "Permission Denied" modal with clear setup instructions.
* [x] **Routing Correction:** Update auth_routes.py to redirect Teachers/Admins to their dashboards.  
* [x] **Teacher View:** Create table monitoring class-wide progress and "Deep Voice" alerts.  
* [x] **Admin Console:** User management and curriculum (Word) editor.

### **Phase 4: Preliminary Deployment on PythonAnyWhere.**

### **Phase 5: Real-Time Analysis and Normalization (The Vowel Engine)**

* [ ] **Refactor Engine:** Port analyze_vowels.py logic into a server-side function.  
* [ ] **Praat Integration:** Trigger parselmouth formant extraction immediately upon file save.  
* [ ] **Adaptive Ceiling:** Implement Pitch-Dependent ceiling logic (5000Hz/5500Hz) for accuracy.  
* [ ] **Data Persistence:** Store f1_raw, f2_raw, and distance_hz in the AnalysisResult table.
* [ ] **Scaling Logic:** Implement Vocal Tract Length Normalization (Alpha calculation).  
* [ ] **Normalization Sync:** Store normalized formants and perceptual (Bark) distances. 

### **Phase 5: Comparison (VTLN)**

* [ ] **Feedback Loop:** Return analysis scores (Match %) to the student UI in JSON response.  
* [ ] **Comparison Visuals:** Display Euclidean distance $d = \sqrt{(F1_1-F1_2)^2 + (F2_1-F2_2)^2}$ on waveform.

### **Phase 6: Quality Assurance, UX & Accessibility**

* [ ] **Error Handling:** Implement global handlers for analysis failures (e.g., silence/clipping).  
* [ ] **Mobile Optimization:** Ensure the waveform comparison and sidebar are responsive.  

### **Phase 7: Deployment & Infrastructure**

* [ ] **VPS Setup:** Provision DigitalOcean droplet (Singapore region).  
* [ ] **Security:** Implement SSL (Certbot) — Mandatory for production microphone access.  
* [ ] **Production Config:** Set up Gunicorn app server and Nginx reverse proxy.

### **Phase 8: Future Optimization (Post-Thesis / Version 2.0)**

* [ ] **HTMX Refactor:** Replace UI JavaScript with HTMX to reduce frontend complexity.  
* [ ] **Performance Polish:** Move audio analysis to a background task queue (Celery/Redis).  
* [ ] **Advanced Visualization:** Implement D3.js for the scientific vowel chart in the student dashboard.

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
├───.git\...
├───.venv\
│   ├───Include\...
│   ├───Lib\...
│   ├───Scripts\...
│   └───share\...
├───.vscode\
│   ├───launch.json
│   └───settings.json
├───analysis_vowels\
│   └───final_thesis_data.csv
├───instance\
│   └───pronounce.db
├───logs\
│   └───pronounce.log
├───migrations\
│   ├───alembic.ini
│   ├───env.py
│   ├───README
│   ├───script.py.mako
│   ├───__pycache__\
│   └───versions\
│       ├───84b9f8c96a17_add_systemconfig_model.py
│       ├───f6ce5bc614e8_initial_migration.py
│       └───__pycache__\
├───scripts\
│   ├───__init__.py
│   ├───fix_db_paths.py
│   ├───migrate_all_data.py
│   ├───parser.py
│   └───__pycache__\
├───static\
│   ├───audio\
│   │   ├───bike.mp3
│   │   ├───bird.mp3
│   │   ├───boat.mp3
│   │   ├───book.mp3
│   │   ├───boy.mp3
│   │   ├───cake.mp3
│   │   ├───call.mp3
│   │   ├───cat.mp3
│   │   ├───chair.mp3
│   │   ├───cow.mp3
│   │   ├───cup.mp3
│   │   ├───dark.mp3
│   │   ├───ear.mp3
│   │   ├───green.mp3
│   │   ├───hello.mp3
│   │   ├───hot.mp3
│   │   ├───index.json
│   │   ├───moon.mp3
│   │   ├───red.mp3
│   │   ├───sit.mp3
│   │   ├───tour.mp3
│   │   └───wait.mp3
│   ├───css\
│   │   └───styles.css
│   └───js\
│       └───script.js
├───submissions\
│   ├───1\...
│   ├───2\...
│   └───3\...
├───templates\
│   ├───base.html
│   ├───index.html
│   ├───login.html
│   ├───maintenance.html
│   ├───register.html
│   └───dashboards\
│       ├───admin_view.html
│       ├───edit_user.html
│       ├───manage_all_words.html
│       ├───manage_word.html
│       ├───student_detail.html
│       └───teacher_view.html
└───tests\
    ├───test_analyze_vowels.py
    ├───test_deploy_fetch.py
    ├───test_parselmouth_stubs.py
    ├───test_replace_audio.py
    ├───test_stub_verification.py
    ├───test_web_interface.py
    └───__pycache__\
```