# Deployment Guide

This guide describes the non-destructive approach to deploying your application to the server.

## 1. Prerequisites
Ensure your server has the following configured:
- **PostgreSQL**: The application now strictly requires a PostgreSQL database (SQLite is disabled).
- **Redis**: Required for background tasks (Celery). Ensure Redis is installed and running (`sudo apt install redis-server`).
- **Environment Variables**: The `.env` file is **git-ignored** for security. You must **manually create/edit** it on the server.
    - Create it in the app root: `nano .env`
    - It must contain:
      ```bash
      DATABASE_URL=postgresql://user:password@localhost/dbname
      SECRET_KEY=your-production-secret-key
      ```
    - *Do not commit your local .env to Git.*

## 2. Deployment Workflow

The recommended safe workflow avoids overwriting the live database with your local database. Instead, you sync the **code** and apply **schema changes**.

### Step 1: Commit and Push Code
On your local machine:
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### Step 2: Backup Server Database (Safety First)
On your server (SSH in):
```bash
# Create a timestamped backup
pg_dump -U <username> -h localhost <db_name> > backup_$(date +%F_%H-%M-%S).sql
```

### Step 3: Pull Changes
On your server:
```bash
cd /path/to/app
git pull origin main
```

### Step 4: Update Dependencies
If you changed `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 5: "Push" Database Changes (Migrations)
Do **NOT** copy your local database file or try to force push your local data if you want to preserve server data. Instead, upgrade the server's database schema to match your code.

On your server:
```bash
flask db upgrade
```
*This command applies any new tables or column changes defined in your migration scripts (`migrations/` folder) without deleting existing data.*

### Step 6: Restart Application
```bash
sudo systemctl restart myapp  # or however you run your app (e.g., supervisor, gunicorn)
```

## Creating Migrations (Local Development)
When you modify `models.py` locally, you must generate a migration script before deploying:
1.  Make changes to `models.py`.
2.  Run: `flask db migrate -m "Description of changes"`
3.  Commit the new file in `migrations/versions/` to Git.
4.  Deploy (follow steps above).

## Full Database Overwrite (Use with Caution)
If you specifically intend to **replace** the server's data with your local data (wiping out server data):
1.  **Local**: `pg_dump -U <local_user> <local_db> > local_dump.sql`
2.  **Transfer**: `scp local_dump.sql user@server:/path/to/remote/`
3.  **Server**: `psql -U <server_user> <server_db> < local_dump.sql`
