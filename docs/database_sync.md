# Database Synchronization Guide

This document provides procedures to verify, maintain, and recover database synchronization between your code and production database.

## Why Database Desync Happens

1. **Restoring from backups** - Sequences aren't automatically updated
2. **Manual SQL changes** - Bypassing migration system
3. **Using `flask db stamp`** - Marks migrations as applied without running them
4. **Interrupted migrations** - Partial schema changes
5. **Importing data with explicit IDs** - Sequences fall behind

---

## Pre-Deployment Verification

**Run these checks BEFORE deploying code changes:**

### 1. Check Migration Status
```bash
# On server
flask db current
# Should show: <revision_id> (head)
```

### 2. Verify Schema Matches Code
```bash
# Compare local (working) vs server
# Local:
flask db current

# Server (SSH):
flask db current

# Both should show the SAME revision ID
```

### 3. Check for Pending Migrations
```bash
flask db heads
# Should show only ONE head (no branches)
```

---

## Post-Deployment Verification

**Run these checks AFTER `git pull` and `flask db upgrade`:**

### 1. Verify All Sequences Are Synced
```sql
-- Run on server
sudo -u postgres psql -d pronounce_db << 'EOF'
SELECT 
    schemaname,
    tablename,
    (SELECT last_value FROM pg_get_serial_sequence(schemaname||'.'||tablename, 'id')) as seq_value,
    (SELECT MAX(id) FROM information_schema.tables WHERE table_schema = schemaname AND table_name = tablename) as max_id
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'submissions', 'analysis_results', 'invite_codes');
EOF
```

**Expected:** `seq_value` should be >= `max_id` for each table.

### 2. Verify Critical Columns Exist
```sql
-- Check system_config
sudo -u postgres psql -d pronounce_db -c "\d system_config"
# Should show: key (PRIMARY KEY), value

-- Check users
sudo -u postgres psql -d pronounce_db -c "\d users"
# Should include: is_guest, is_test_account, email, locked_until

-- Check submissions
sudo -u postgres psql -d pronounce_db -c "\d submissions"
# Should include: score
```

---

## Recovery Procedures

### Scenario 1: Sequence Out of Sync
**Symptoms:** `duplicate key value violates unique constraint "<table>_pkey"`

**Fix:**
```bash
# Reset ALL sequences
sudo -u postgres psql -d pronounce_db << 'EOF'
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
SELECT setval('submissions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM submissions));
SELECT setval('analysis_results_id_seq', (SELECT COALESCE(MAX(id), 1) FROM analysis_results));
SELECT setval('invite_codes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM invite_codes));
EOF
```

### Scenario 2: Missing Column
**Symptoms:** `column "<name>" does not exist`

**Diagnosis:**
```bash
# Check which migration adds the column
grep -r "add_column.*<column_name>" migrations/versions/
```

**Fix:**
```bash
# Option A: If migration exists but wasn't run
flask db downgrade <previous_revision>
flask db upgrade head

# Option B: Manual SQL (faster, but bypasses migration tracking)
sudo -u postgres psql -d pronounce_db -c "ALTER TABLE <table> ADD COLUMN <name> <type>;"
```

### Scenario 3: Wrong Primary Key
**Symptoms:** `duplicate key value violates unique constraint` on non-id column

**Example Fix (system_config):**
```bash
sudo -u postgres psql -d pronounce_db << 'EOF'
ALTER TABLE system_config DROP CONSTRAINT IF EXISTS system_config_pkey CASCADE;
ALTER TABLE system_config DROP COLUMN IF EXISTS id;
ALTER TABLE system_config ADD PRIMARY KEY (key);
EOF
```

### Scenario 4: Migration Says "Head" But Schema Is Old
**Symptoms:** `flask db current` shows latest revision, but columns are missing

**Cause:** Someone ran `flask db stamp head` without running migrations.

**Fix:**
```bash
# 1. Backup first
pg_dump -U <user> -h localhost pronounce_db > emergency_backup.sql

# 2. Manually apply missing changes
# Review each migration file in migrations/versions/
# Run the SQL from upgrade() functions that weren't applied

# 3. Verify schema matches models.py
python << 'EOF'
from flask_app import app, db
from models import User, Submission, AnalysisResult, SystemConfig
with app.app_context():
    # This will show warnings if schema doesn't match
    db.create_all()
EOF
```

---

## Safe Migration Practices

### ✅ DO
1. **Always backup before migrations**
   ```bash
   pg_dump -U <user> pronounce_db > backup_$(date +%F_%H-%M-%S).sql
   ```

2. **Test migrations locally first**
   ```bash
   # Local
   flask db migrate -m "Description"
   flask db upgrade
   # Test app thoroughly
   git add migrations/
   git commit
   ```

3. **Run migrations incrementally**
   ```bash
   # Don't skip versions
   flask db upgrade head  # ✅ Good
   ```

4. **Verify after each deployment**
   ```bash
   flask db current
   # Check sequences (see above)
   ```

### ❌ DON'T
1. **Never use `flask db stamp` unless recovering from a known state**
   - It marks migrations as done WITHOUT running them
   - Only use if you manually applied changes and need to sync the version

2. **Never delete migrations/ folder**
   - This is your database's version history
   - Deleting it causes "fresh" migrations to try recreating existing tables

3. **Never manually edit the database without documenting it**
   - If you must use SQL, document it in a migration file
   - Or at minimum, note it in deployment.md

4. **Never run migrations on production without testing locally**

---

## Emergency: Complete Schema Reset

**⚠️ DESTRUCTIVE - Only use if database is completely broken**

```bash
# 1. Backup everything
pg_dump -U <user> pronounce_db > full_backup_$(date +%F).sql

# 2. Export data only (no schema)
pg_dump -U <user> --data-only pronounce_db > data_only.sql

# 3. Drop and recreate database
sudo -u postgres psql << 'EOF'
DROP DATABASE pronounce_db;
CREATE DATABASE pronounce_db OWNER <user>;
EOF

# 4. Run all migrations from scratch
flask db upgrade head

# 5. Restore data (may require manual fixes for changed schemas)
sudo -u postgres psql -d pronounce_db < data_only.sql

# 6. Fix sequences
# (Run sequence sync commands from Scenario 1)
```

---

## Monitoring

### Daily Health Check Script
Create `scripts/db_health_check.sh`:

```bash
#!/bin/bash
echo "=== Migration Status ==="
flask db current

echo -e "\n=== Sequence Health ==="
sudo -u postgres psql -d pronounce_db -c "
SELECT 
    tablename,
    pg_get_serial_sequence('public.'||tablename, 'id') as sequence,
    (SELECT last_value FROM pg_get_serial_sequence('public.'||tablename, 'id')) as next_id,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = tablename) as exists
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'submissions', 'analysis_results');"

echo -e "\n=== Recent Errors ==="
sudo journalctl -u pronounce-web --since "1 hour ago" | grep -i "error\|exception" | tail -5
```

Run weekly:
```bash
chmod +x scripts/db_health_check.sh
./scripts/db_health_check.sh
```

---

## Troubleshooting Checklist

When something breaks:

- [ ] Check `flask db current` - is it at head?
- [ ] Check sequences - are they ahead of max IDs?
- [ ] Check schema - do critical columns exist?
- [ ] Check Celery logs - `sudo journalctl -u pronounce-celery -n 50`
- [ ] Check Gunicorn logs - `sudo journalctl -u pronounce-web -n 50`
- [ ] Verify `.env` file exists and has correct DATABASE_URL
- [ ] Restart services after ANY database change
