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

## 🔄 Data Synchronization

We separate **Code Sync** from **Data Sync** to prevent accidents.

### 1. Code (VS Code SFTP)
*   **Tools:** VS Code SFTP Plugin
*   **Purpose:** Syncs `.py`, `.html`, `.css`, `.js`
*   **Ignores:** Database (`instance/`), Audio (`static/audio`), Submissions (`submissions/`)
*   **Config:** `.vscode/sftp.json`

### 2. Data & Database (Python Script)
*   **Tool:** `scripts/sync_data.py`
*   **Purpose:** Safely syncs production data (DB/Audio) without overwriting.
*   **Usage:**
    *   **Install:** `pip install paramiko`
    *   **Download DB:** `python scripts/sync_data.py db` (Safe)
    *   **Download All Data:** `python scripts/sync_data.py all`
    *   **Upload (Danger):** `python scripts/sync_data.py all --push`

## 🛠 Management CLI

We have separate tools for different management tasks:

*   **Create Admin:** `python utility/manage_admin.py create [username]`
*   **Init Database:** `flask init-db` (Sets up tables & default config)
*   **Deploy (Automated):** `python scripts/deploy.py --force`

## 🏗 Architecture

*   **Backend:** Flask (Python)
*   **Database:** PostgreSQL (Production) / SQLite (Dev)
*   **Analysis:** Parselmouth (Praat), Librosa
*   **Frontend:** Jinja2 Templates, TailwindCSS, Vanilla JS

## ⚖ License
Proprietary / Closed Source.
