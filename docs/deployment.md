# Pronounce-Web Deployment Guide

This guide details the standard procedure for deploying changes to the production server.

## 1. Prerequisites (Server Config)
Ensure your server has the following services running:
1.  **PostgreSQL**: Strictly required. (SQLite is disabled).
2.  **Redis**: Required for Celery background tasks (audio analysis).
    *   Install: `sudo apt install redis-server`

### Environment Variables (`.env`)
The `.env` file contains secrets and **must be managed manually** on the server. It is ignored by Git.

**Create/Edit on Server:**
```bash
nano /var/www/pronounce-web/.env
```

**Required Content:**
```ini
# Database (URL-encode special characters like '#')
DATABASE_URL=postgresql://user:password@localhost/pronounce_db

# Security (REQUIRED for sessions)
SECRET_KEY=generate-long-random-string

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@pronounce-web.com

# Celery (Defaults usually work, but good to be explicit)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 2. Standard Deployment Workflow

Follow this to update code and database schema without losing data.

### Step 1: Push Code (Local)
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

### Step 2: Backup Database (Server)
**Always** backup before applying changes.
```bash
pg_dump -U <username> -h localhost pronounce_db > backup_$(date +%F_%H-%M-%S).sql
```

### Step 3: Pull & Update (Server)
```bash
cd /var/www/pronounce-web
git pull origin main

# Update Python dependencies if requirements.txt changed
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Apply Database Migrations (Server)
This applies schema changes (new columns/tables) non-destructively.
```bash
flask db upgrade
```

### Step 5: Restart Services (Server)
Restart to load new code.
```bash
sudo systemctl restart pronounce-web
```

### Step 6: Verify Deployment (Server)
Check that the database version matches the code.
```bash
flask db current
# Should show the latest migration ID (e.g., 87c5d6b3f863 (head))
```

---

## 4. Best Practices (Preventing Errors)

To avoid migration conflicts in the future:

1.  **NEVER delete the `migrations/` folder.**
    *   This folder contains the history of your database. If you delete it and generate a "fresh" migration, it will try to recreate existing tables (causing the error you just faced).

2.  **Migrate Incrementally.**
    *   Change `models.py`.
    *   Run `flask db migrate -m "Added X field"`.
    *   Commit that single small file.
    *   *Do not let changes pile up.*

3.  **Avoid Manual Server Changes.**
    *   Never create tables or columns manually on the server using SQL (unless fixing a broken state like today). Let `flask db upgrade` handle it.


## 5. Troubleshooting: Database Desynchronization
**Critical Warning:** If you run `flask db stamp head`, you tell the system "Assume the database is perfect." If the database is actually missing columns, **migrations will stop running** and your app will crash with integrity errors.

**Symptoms:**
*   `flask db current` shows `(head)`.
*   App crashes with "column does not exist" or "key already exists".

**Fix:**
You must manually align the database schema using SQL.
1.  **Check what is broken:** Log in to `psql` and `\d table_name` to see if columns are old.
2.  **Manually Execute Changes:** Run the specific `ALTER TABLE` commands that the skipped migration *would* have run.
3.  **Do NOT stamp again** unless you have verified the schema matches `models.py` exactly.

