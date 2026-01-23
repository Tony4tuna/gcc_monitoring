# Deployment Guide - GCC Monitoring System

## Production Deployment Checklist

### 1. Environment Setup

Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` and set **required** production values:

```bash
# Generate a secure password
ADMIN_PASSWORD=YourSecurePassword123!

# Generate a secure storage secret
# Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
STORAGE_SECRET=your_generated_secret_key_here
```

### 2. Database Preparation

Ensure your database is ready:
```bash
# Backup existing database if upgrading
cp data/app.db data/app.db.backup_$(date +%Y%m%d)

# Apply schema if fresh install
python utility/apply_schema.py
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 4. Security Considerations

**Critical:**
- ✅ Never use default passwords in production
- ✅ Set `STORAGE_SECRET` to a cryptographically secure random value
- ✅ Use HTTPS in production (configure reverse proxy)
- ✅ Restrict database file permissions (chmod 600 data/app.db on Linux)
- ✅ Keep `data/` directory outside web root
- ✅ Test data generator is disabled by default (only runs if ENABLE_TEST_DATA=1)

### 5. Running in Production

**Option A: Direct (Testing)**
```bash
# Set environment variables
export ADMIN_PASSWORD="your_password"
export STORAGE_SECRET="your_secret"

# Run
python app.py
```

**Option B: systemd Service (Linux Production)**

Create `/etc/systemd/system/gcc-monitoring.service`:
```ini
[Unit]
Description=GCC Monitoring System
After=network.target

[Service]
Type=simple
User=gcc
WorkingDirectory=/opt/gcc_monitoring
Environment="ADMIN_PASSWORD=your_password"
Environment="STORAGE_SECRET=your_secret"
Environment="HOST=127.0.0.1"
Environment="PORT=8080"
ExecStart=/opt/gcc_monitoring/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable gcc-monitoring
sudo systemctl start gcc-monitoring
sudo systemctl status gcc-monitoring
```

**Option C: Docker (Recommended)**

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t gcc-monitoring .
docker run -d \
  -p 8080:8080 \
  -v /path/to/data:/app/data \
  -e ADMIN_PASSWORD="your_password" \
  -e STORAGE_SECRET="your_secret" \
  --name gcc-monitoring \
  gcc-monitoring
```

### 6. Reverse Proxy (Nginx)

Example Nginx configuration:
```nginx
server {
    listen 80;
    server_name monitoring.yourcompany.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name monitoring.yourcompany.com;
    
    ssl_certificate /etc/ssl/certs/yourcompany.crt;
    ssl_certificate_key /etc/ssl/private/yourcompany.key;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. Monitoring & Logs

**View logs:**
```bash
# systemd
journalctl -u gcc-monitoring -f

# Docker
docker logs -f gcc-monitoring
```

**Health check endpoint:**
```bash
curl http://localhost:8080/
```

### 8. Backup Strategy

**Automated backup script:**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp data/app.db backups/app.db.$DATE
# Keep last 7 days
find backups/ -name "app.db.*" -mtime +7 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/gcc_monitoring/backup.sh
```

### 9. Updates & Maintenance

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart gcc-monitoring
```

### 10. Troubleshooting

**Service won't start:**
- Check environment variables are set
- Verify database file exists and is readable
- Check port 8080 is available: `netstat -tuln | grep 8080`

**Can't login:**
- Verify ADMIN_PASSWORD is set correctly
- Check logs for authentication errors

**Performance issues:**
- Database indexes are pre-configured in schema
- Consider SQLite → PostgreSQL migration for >50 units
- Enable query caching if needed

## Production Differences from Development

✅ **Disabled by default:**
- Test data generator (requires ENABLE_TEST_DATA=1)
- Auto-reload
- Default passwords

✅ **Required in production:**
- ADMIN_PASSWORD environment variable
- STORAGE_SECRET environment variable

✅ **Recommended:**
- HTTPS via reverse proxy
- Firewall rules (only allow 80/443)
- Regular database backups
- Log rotation
- Monitoring/alerting

## Support

For issues, check:
- Application logs
- Browser console (F12)
- Database integrity: `sqlite3 data/app.db "PRAGMA integrity_check;"`
