I# Pronounce Web - Deployment Guide

This guide covers the end-to-end process of deploying Pronounce Web to a production VPS (Virtual Private Server), specifically DigitalOcean.

---

### Step 1: Register
1.  Go to [DigitalOcean.com](https://www.digitalocean.com/).
2.  Click **"Sign Up"**. You can use Google or GitHub OAuth for speed.
3.  You will need to add a payment method (Credit Card or PayPal) to verify your account. They usually offer a $200 credit trial for 60 days.

### Step 2: Create a Droplet (VPS)
*If you are using DigitalOcean, follow these steps. If you are using **GreenCloud, Hetzner, or others**, simply create a VPS with **Ubuntu 22.04 LTS** and 2GB+ RAM.*

**For DigitalOcean Users:**
Once logged in to your dashboard:
1.  Click the big green **"Create"** button -> **"Droplets"**.
2.  **Region:** Choose a region closest to your users.
3.  **OS:** Select **Ubuntu** -> Version **22.04 (LTS)**.
4.  **Droplet Type (Critical for Pricing):**
    *   Find the **"Basic"** or **"Shared CPU"** plan tab.
    *   **CPU Options:** You MUST select **"Regular"** (Disk type: SSD). 
    *   **Price:** 
        *   **Recommended:** **$12/mo (2GB RAM)**.
        *   *Minimum:* **$6/mo (1GB RAM)**.
5.  **Authentication Method:**
    *   Select **"SSH Key"**.
    *   Click "New SSH Key" and paste your public key (generated via `ssh-keygen` on your PC).

**For GreenCloud / Other Providers:**
1.  Select **Ubuntu 22.04 LTS** during checkout.
2.  They will likely email you a **root password** if you don't provide an SSH key.
3.  You will log in like this: `ssh root@<IP_ADDRESS>` -> Enter Password.
    *   Click "New SSH Key".
    *   **On your Local Machine (Terminal/PowerShell):**
        *   Run `ssh-keygen -t rsa` (Press Enter through defaults).
        *   Copy the content of your public key. On Windows: `type $env:USERPROFILE\.ssh\id_rsa.pub`
        *   Paste this key into DigitalOcean.
6.  **Hostname:** Give it a simple name (e.g., `pronounce-server`).
7.  Click **"Create Droplet"**.

### Step 3: Get IP Address
Wait ~30 seconds. Your new server will appear with an IP address (e.g., `159.223.x.x`). Copy this IP.

---

## Part 2: Configuring the Server

### Step 1: Connect
Open your local terminal (PowerShell or Bash):
```bash
ssh root@<YOUR_DROPLET_IP>
```
Type `yes` to accept the fingerprint. You are now "in" the server.

### Step 2: Prepare the Application
1.  Clone your repository (assuming you pushed your code to GitHub):
    ```bash
    git clone https://github.com/YOUR_GITHUB_USER/pronounce-web.git /var/www/pronounce-web
    ```
2.  Navigate to the directory:
    ```bash
    cd /var/www/pronounce-web
    ```

### Step 3: Run the Auto-Installer
We have updated the `setup_vps.sh` script to handle everything.

1.  Make the script executable:
    ```bash
    chmod +x utility/setup_vps.sh
    ```
2.  Run it:
    ```bash
    ./utility/setup_vps.sh
    ```
3.  **Prompts:**
    *   **Domain Name:** Enter your domain (e.g., `pronounce.example.com`) or your **IP Address** if you don't have a domain yet.
    *   **SSL:** If you entered a domain, say `y` to setup HTTPS. If using just an IP, say `n`.

### Step 4: Verify
Visit `http://<YOUR_IP>` or `http://<YOUR_DOMAIN>` in your browser. The app should be live!

---

## Part 3: Troubleshooting

*   **Logs:**
    *   App Logs: `journalctl -u pronounce-web`
    *   Nginx Logs: `tail -f /var/log/nginx/error.log`
*   **Restart App:**
    *   `systemctl restart pronounce-web`
