# Deployment Instructions for GCC Monitoring System

## Recent Changes
- Fixed-height dashboard grids with horizontal and vertical scrollbars
- Both grids are equal size and display properly
- Version label remains visible at bottom
- Back button added to navigation
- Centralized logging system
- Error handling throughout

## Deploy to Digital Ocean

### Option 1: Using the deployment script (requires SSH key)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy.ps1
```

### Option 2: Manual deployment via SSH
```bash
# 1. SSH into your server
ssh tony@gcchvacr.com

# 2. Navigate to the app directory
cd /var/www/gcc_monitoring

# 3. Pull latest changes (if using git)
git pull origin main

# 4. Or upload files via SCP
# From local machine:
scp -r core pages ui schema app.py requirements.txt tony@gcchvacr.com:/var/www/gcc_monitoring/

# 5. Install/update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 6. Restart the service
sudo systemctl restart gcc_monitoring

# 7. Check status
sudo systemctl status gcc_monitoring
```

### Option 3: Create tarball and upload
```powershell
# From local Windows machine
tar -czf gcc_deploy.tar.gz app.py core pages ui schema requirements.txt
scp gcc_deploy.tar.gz tony@gcchvacr.com:/tmp/

# On server
ssh tony@gcchvacr.com
cd /var/www/gcc_monitoring
tar -xzf /tmp/gcc_deploy.tar.gz --strip-components=0
sudo systemctl restart gcc_monitoring
```

## Git Repository

Repository already initialized locally. To push to GitHub:

1. Create a new repository at https://github.com/new named `gcc_monitoring`
2. Then run:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/gcc_monitoring.git
git push -u origin main
```

## Files Changed in This Session
- `ui/layout.py` - Dashboard grid CSS (fixed-height, scrollbars, equal sizing)
- `pages/dashboard.py` - Grid layout with proper wrapping, back button
- `pages/clients.py` - Fixed-height grid with pagination
- `pages/locations.py` - Fixed-height grid with pagination
- `pages/equipment.py` - Fixed-height grid with pagination
- `pages/settings.py` - Fixed-height grids for all tables
- `core/logger.py` - NEW: Centralized logging system
- `ui/unit_issue_dialog.py` - Complete ticket creation workflow

## Testing Locally
```powershell
.venv\Scripts\python.exe app.py
# Then open http://localhost:8080
```

## Server Details
- **Domain**: gcchvacr.com
- **IP**: 167.71.111.170
- **User**: tony
- **App Path**: /var/www/gcc_monitoring
- **Service**: gcc_monitoring.service
