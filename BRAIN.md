# Project: Pronunciation Web App (Flask + Praat)

## Architecture
* **Stack:** Flask (Backend), SQLAlchemy (DB), Jinja2 (Templates), Wavesurfer.js (Frontend).
* **Core Logic:** `analysis_engine.py` (Praat/Parselmouth wrapper).
* **Code Style:** Python 3.12+, Black formatting. Use standard Flask decorators for routes.

## Critical Workflows
1.  **Student:** Register -> Login -> Recording page -> Noise detection on recording page -> Example Word playback -> Record Audio -> Own recording Playback -> View Feedback Score/Recommendations
2.  **Teacher:** Get Invite Code -> Register -> Login -> View Dashboard (Class Overview) -> Select Student -> View Student Detail (History, Scores) -> Listen to specific submissions -> Examine submissions (suggest mode automatic or manual) -> Export Report.
3.  **Admin:** Login -> Admin Panel -> User Management (Create/Edit/Delete Users) -> Word Management (Add/Edit Reference Words) -> System Config (Set Thresholds) -> View System Logs.

## Known Constraints
* **Audio:** All inputs are converted to 16kHz mono with loudness normalization before analysis.

## Development Rules
* **Scripts:** It is **NOT ALLOWED** to create fix, debug, or test scripts and files related to them outside the `tests/` directory. All such scripts must be placed in `tests/scripts/` or similar.
