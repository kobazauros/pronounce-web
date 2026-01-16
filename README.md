# Pronounce Web

A web-based pronunciation assessment tool using formant analysis and vocal tract length normalization (VTLN).

## 📂 Documentation

*   **[Deployment Guide](docs/deployment_guide.md):** How to deploy to production (DigitalOcean/Nginx/Postgres).
*   **[Development Log](docs/development.md):** Technical implementation details and algorithms.
*   **[Roadmap](docs/road_map.md):** Project status and future plans.
*   **[Analysis Engine](docs/analyse_vowel.md):** Explanation of the acoustic analysis pipeline.

## 🚀 Quick Start (Local Dev)

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Initialize DB:**
    ```bash
    flask db upgrade
    ```
3.  **Run Server:**
    ```bash
    flask run
    ```

## 🏗 Architecture

*   **Backend:** Flask (Python)
*   **Database:** PostgreSQL (Production) / SQLite (Dev)
*   **Analysis:** Parselmouth (Praat), Librosa
*   **Frontend:** Jinja2 Templates, TailwindCSS, Vanilla JS

## ⚖ License
Proprietary / Closed Source.
