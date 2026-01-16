# Pronounce Web - Production Deployment Guide

This guide covers the end-to-end process of deploying Pronounce Web to a production VPS (Virtual Private Server).

## 1. Infrastructure Provisioning

### Server Requirements
*   **OS:** Ubuntu 22.04 LTS (Recommended)
*   **Specs:** 2GB RAM / 1 vCPU (Minimum)
*   **Provider:** GreenCloudVPS (or any standard VPS provider)

### Initial Setup
1.  **SSH into Server:**
    ```bash
    ssh root@<YOUR_IP>
    ```
2.  **Clone Repository:**
    ```bash
    git clone https://github.com/YOUR_GITHUB_USER/pronounce-web.git /var/www/pronounce-web
    cd /var/www/pronounce-web
    ```
3.  **Run Auto-Installer:**
    ```bash
    chmod +x utility/setup_vps.sh
    ./utility/setup_vps.sh
    ```
    *Input your domain info when prompted to automate Nginx and SSL setup.*

---

## 2. Configuration & Environment

### Environment Variables
Production requires specific secrets. Create a `.env` file or set them in Systemd:

```bash
# Security
SECRET_KEY="<generated_secure_key>"

# Database (PostgreSQL)
DATABASE_URL="postgresql://user:password@localhost/pronounce_db"

# Observability (Sentry)
SENTRY_DSN="<your_sentry_dsn>"
```

### Nginx Optimization (Critical for Audio)
Ensure `deploy/nginx.conf` is linked:
```bash
sudo ln -sf /var/www/pronounce-web/deploy/nginx.conf /etc/nginx/sites-enabled/pronounce-web
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```
*   **Why?** Sets `client_max_body_size 20M` to allow large audio uploads.
*   **Why?** Enables Gzip compression for speed.

### SSL (HTTPS)
If Nginx config changes, you may need to re-apply SSL:
```bash
sudo certbot --nginx -d your-domain.com
```

---

## 3. Database Migration (Postgres)

We use PostgreSQL in production for checking concurrency locking issues.

1.  **Ensure Postgres is running:** `systemctl status postgresql`
2.  **Run Migration Script:**
    ```bash
    python utility/migrate_to_postgres.py
    ```
    *This interactive script will copy all data from the local SQLite (`instance/pronounce.db`) to the production PostgreSQL database.*

---

## 4. Monitoring & Maintenance

### Logs
*   **Application:** `sudo journalctl -u pronounce-web -f`
*   **Web Server:** `sudo tail -f /var/log/nginx/error.log`

### Updates
To deploy new code:
1.  `git pull`
2.  `pip install -r requirements.prod.txt` (if deps changed)
3.  `sudo systemctl restart pronounce-web`
