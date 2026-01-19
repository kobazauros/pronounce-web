#!/bin/bash
# Database Health Check Script
# Run this weekly or after any deployment to verify database integrity

echo "=== Migration Status ==="
flask db current

echo -e "\n=== Sequence Health ==="
sudo -u postgres psql -d pronounce_db -c "
SELECT 
    tablename,
    pg_get_serial_sequence('public.'||tablename, 'id') as sequence,
    (SELECT last_value FROM pg_get_serial_sequence('public.'||tablename, 'id')) as next_id
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'submissions', 'analysis_results', 'invite_codes');"

echo -e "\n=== Critical Columns Check ==="
echo "Checking system_config..."
sudo -u postgres psql -d pronounce_db -c "\d system_config" | grep -E "key|value"

echo -e "\nChecking users..."
sudo -u postgres psql -d pronounce_db -c "\d users" | grep -E "is_guest|is_test_account|email|locked_until"

echo -e "\nChecking submissions..."
sudo -u postgres psql -d pronounce_db -c "\d submissions" | grep "score"

echo -e "\n=== Recent Errors (last hour) ==="
sudo journalctl -u pronounce-web --since "1 hour ago" | grep -i "error\|exception" | tail -5

echo -e "\n=== Celery Status ==="
sudo systemctl status pronounce-celery --no-pager | head -5
