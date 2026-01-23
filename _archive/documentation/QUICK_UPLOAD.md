# Quick Upload to DigitalOcean Droplet

## Step 1: Create Deployment Package

Run this on your Windows machine:

```powershell
cd C:\Users\Public\GCC_Monitoring\gcc_monitoring
.\create_deployment_package.bat
```

This creates `gcc_monitoring_deploy.tar.gz` with only the files you need.

---

## Step 2: Upload to Your Droplet

Replace `YOUR_DROPLET_IP` with your actual droplet IP address:

```powershell
scp gcc_monitoring_deploy.tar.gz root@YOUR_DROPLET_IP:/tmp/
```

**Example:**
```powershell
scp gcc_monitoring_deploy.tar.gz root@64.23.145.89:/tmp/
```

---

## Step 3: Setup on Droplet

SSH into your droplet and run these commands:

```bash
ssh root@YOUR_DROPLET_IP

# Extract files
cd /tmp
tar -xzf gcc_monitoring_deploy.tar.gz

# Move to application directory
mkdir -p /home/gcc
mv deployment /home/gcc/gcc_monitoring
cd /home/gcc/gcc_monitoring

# Run setup script
bash deploy.sh
```

---

## Step 4: Configure Environment

Edit the `.env` file:

```bash
nano .env
```

Set these values:
```
ADMIN_PASSWORD=YourSecurePassword123
STORAGE_SECRET=paste_generated_secret_here
```

Generate secret:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 5: Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/gcc-monitoring.service
```

Paste:
```ini
[Unit]
Description=GCC Monitoring System
After=network.target

[Service]
Type=simple
User=gcc
WorkingDirectory=/home/gcc/gcc_monitoring
Environment="PATH=/home/gcc/gcc_monitoring/venv/bin"
EnvironmentFile=/home/gcc/gcc_monitoring/.env
ExecStart=/home/gcc/gcc_monitoring/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gcc-monitoring
sudo systemctl start gcc-monitoring
```

---

## Step 6: Setup Nginx (Optional)

```bash
sudo nano /etc/nginx/sites-available/gcc-monitoring
```

Paste:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/gcc-monitoring /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 7: Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Done!

Access your application:
- **http://YOUR_DROPLET_IP**

Login:
- Username: `admin`
- Password: (what you set in .env)

---

## Troubleshooting

**Check if service is running:**
```bash
sudo systemctl status gcc-monitoring
```

**View logs:**
```bash
sudo journalctl -u gcc-monitoring -f
```

**Restart service:**
```bash
sudo systemctl restart gcc-monitoring
```

---

## Update Application

When you make changes:

1. Create new package on Windows
2. Upload to droplet
3. Extract and replace files
4. Restart service:

```bash
sudo systemctl restart gcc-monitoring
```
