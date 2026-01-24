**VTLN Calculation Scaling**: In analysis_engine.py, the VTLN (Vocal Tract Length Normalization) calculates the median ratio by querying all historical results for a user every single time. As a student reaches 100+ recordings, this DB join and median calculation will become increasingly expensive.

**Optimization**: Store a "running average" or "cached alpha" in the User table and update it incrementally.

**Static Asset Handling in Production**: The app currently serves user uploads via send_from_directory. While functional, this is suboptimal for production.

**Optimization**: As noted in your roadmap, Nginx should serve these files directly, or you should move to a dedicated object store like AWS S3 or Cloudinary.

**Synchronous Configuration Checks**: The check_for_maintenance hook performs a database query (SystemConfig.get_bool) on every single request.

**Optimization**: Cache this setting in Redis or in the app's memory to avoid unnecessary database hits for every static file or API call.


**Refactoring Without Breaking the UI/UX Flow**
To ensure the frontend continues to function while you refactor the backend, focus on maintaining the API Contract established in flask_app.py:

**Preserve Response Schemas**: The UI/UX depends on specific JSON keys. Specifically, api_process_audio must always return {"status": "success", "path": "...", "url": "..."}. If you change how files are stored, ensure the url key still points to a valid source so WaveSurfer.js doesn't fail to load the waveform.

**Task Polling Consistency**: The UI currently polls /api/status/<task_id>. During refactoring, ensure that get_task_status remains consistent in its states (PENDING, SUCCESS, FAILURE). If you move toward a WebSocket-based push notification system later, keep the polling endpoint as a fallback to avoid breaking older client sessions.

Error Handling Gracefully: The current engine uses a "Diagnostic Flags" system (e.g., is_outlier, is_deep_voice_corrected). When refactoring analysis_engine.py, ensure these flags are still populated even if the analysis fails. The UI likely uses these to show or hide specific feedback modules.