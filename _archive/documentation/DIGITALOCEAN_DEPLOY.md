# Deploy to DigitalOcean Droplet

## Quick Deployment Guide

### Prerequisites
- DigitalOcean droplet running Ubuntu 22.04 or 24.04
- SSH access to your droplet
- Domain name (optional, for HTTPS)

---

## Step 1: Connect to Your Droplet

```bash
ssh root@your_droplet_ip
```

---

## Step 2: Initial Server Setup

```bash
# Update system packages
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git nginx ufw

# Create application user (security best practice)
adduser gcc --disabled-password --gecos ""
usermod -aG sudo gcc

# Switch to application user
su - gcc
```

---

## Step 3: Upload Application Files

**Option A: Using git (if you have a repository)**
```bash
cd /home/gcc
git clone https://github.com/yourusername/gcc_monitoring.git
cd gcc_monitoring
```

**Option B: Using SCP (from your local machine)**
```powershell
# On your Windows machine, compress the files first
cd C:\Users\Public\GCC_Monitoring
tar -czf gcc_monitoring.tar.gz gcc_monitoring/

# Upload to droplet
scp gcc_monitoring.tar.gz root@your_droplet_ip:/home/gcc/

# On droplet, extract
ssh root@your_droplet_ip
cd /home/gcc
tar -xzf gcc_monitoring.tar.gz
chown -R gcc:gcc gcc_monitoring
su - gcc
cd gcc_monitoring
```

**Option C: Using SFTP (FileZilla, WinSCP)**
1. Connect to your droplet via SFTP
2. Upload the entire `gcc_monitoring` folder to `/home/gcc/`

---

## Step 4: Setup Application

```bash
# Navigate to application directory
cd /home/gcc/gcc_monitoring

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env
```

**Edit `.env` file:**
```bash
ADMIN_EMAIL=admin
ADMIN_PASSWORD=YourSecurePassword123!
STORAGE_SECRET=your_secret_generated_key
HOST=0.0.0.0
PORT=8080
```

**Generate secure secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output and paste as STORAGE_SECRET in .env
```

**Set secure permissions:**
```bash
chmod 600 .env
chmod 700 data
```

---

## Step 5: Test the Application

```bash
# Make sure you're in the app directory with venv activated
cd /home/gcc/gcc_monitoring
source venv/bin/activate

# Test run
python app.py
```

Press `Ctrl+C` to stop after verifying it starts successfully.

---

## Step 6: Create Systemd Service

```bash
# Exit to root user
exit
exit

# Create service file
sudo nano /etc/systemd/system/gcc-monitoring.service
```

**Paste this configuration:**
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

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gcc-monitoring
sudo systemctl start gcc-monitoring
sudo systemctl status gcc-monitoring
```

---

## Step 7: Configure Firewall

```bash
# Allow SSH (important - don't lock yourself out!)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application port (if accessing directly)
sudo ufw allow 8080/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

---

## Step 8: Setup Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/gcc-monitoring
```

**Paste this configuration:**
```nginx
server {
    listen 80;
    server_name your_domain.com;  # Change to your domain or droplet IP

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-polling
        proxy_read_timeout 86400;
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/gcc-monitoring /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 9: Add SSL Certificate (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (change your_domain.com to your actual domain)
sudo certbot --nginx -d your_domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Step 10: Verify Deployment

**Access your application:**
- With domain: `https://your_domain.com`
- Without domain: `http://your_droplet_ip`

**Login credentials:**
- Username: `admin`
- Password: (the one you set in `.env`)

---

## Maintenance Commands

**View logs:**
```bash
# Application logs
sudo journalctl -u gcc-monitoring -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

**Restart service:**
```bash
sudo systemctl restart gcc-monitoring
```

**Update application:**
```bash
cd /home/gcc/gcc_monitoring
git pull  # If using git
sudo systemctl restart gcc-monitoring
```

**Database backup:**
```bash
# Create backup
cp /home/gcc/gcc_monitoring/data/app.db /home/gcc/backups/app.db.$(date +%Y%m%d_%H%M%S)

# Automated daily backup (add to crontab)
crontab -e
# Add this line:
0 2 * * * cp /home/gcc/gcc_monitoring/data/app.db /home/gcc/backups/app.db.$(date +\%Y\%m\%d) && find /home/gcc/backups -name "app.db.*" -mtime +7 -delete
```

---

## Performance Optimization

**For high traffic:**
```bash
# Increase Nginx worker connections
sudo nano /etc/nginx/nginx.conf
# Set: worker_connections 2048;

# Add swap space if needed (for small droplets)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Troubleshooting

**Service won't start:**
```bash
# Check status
sudo systemctl status gcc-monitoring

# Check logs
sudo journalctl -u gcc-monitoring -n 50 --no-pager

# Verify environment variables
sudo cat /home/gcc/gcc_monitoring/.env
```

**Can't access website:**
```bash
# Check if service is running
sudo systemctl status gcc-monitoring

# Check if port is listening
sudo netstat -tulpn | grep 8080

# Check Nginx status
sudo systemctl status nginx

# Check firewall
sudo ufw status
```

**Database errors:**
```bash
# Check database file permissions
ls -la /home/gcc/gcc_monitoring/data/app.db

# Fix permissions if needed
sudo chown gcc:gcc /home/gcc/gcc_monitoring/data/app.db
```

---

## Security Checklist

✅ Changed default admin password  
✅ Set secure STORAGE_SECRET  
✅ UFW firewall enabled  
✅ SSL certificate installed  
✅ Running as non-root user  
✅ Database file permissions (600)  
✅ .env file permissions (600)  
✅ Regular backups configured  

---

## Quick Reference

**DigitalOcean Droplet Info:**
```bash
# Your droplet IP: [Check DigitalOcean dashboard]
# SSH: ssh root@your_droplet_ip
# App location: /home/gcc/gcc_monitoring
# Service name: gcc-monitoring
```

**Common Commands:**
```bash
# Restart app
sudo systemctl restart gcc-monitoring

# View logs
sudo journalctl -u gcc-monitoring -f

# Update code
cd /home/gcc/gcc_monitoring && git pull && sudo systemctl restart gcc-monitoring

# Backup database
cp data/app.db backups/app.db.$(date +%Y%m%d)
```

---

## Next Steps

1. ✅ Deploy application
2. ✅ Configure domain name in DigitalOcean DNS
3. ✅ Install SSL certificate
4. ✅ Setup automated backups
5. ✅ Configure monitoring/alerts (optional)
6. Test with real equipment data
7. Add additional users via admin panel

---

## Cost Optimization

**Recommended DigitalOcean Droplet:**
- **Starter:** $6/month (1GB RAM, 1 vCPU) - Up to 10 units
- **Standard:** $12/month (2GB RAM, 1 vCPU) - Up to 50 units
- **Production:** $24/month (4GB RAM, 2 vCPU) - 100+ units

**Enable automatic backups:** $1.20/month (20% of droplet cost)

---

## Support

Need help? Check:
1. Application logs: `sudo journalctl -u gcc-monitoring -f`
2. Nginx logs: `/var/log/nginx/error.log`
3. Database integrity: `sqlite3 data/app.db "PRAGMA integrity_check;"`
