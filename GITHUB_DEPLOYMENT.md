# GitHub Deployment Setup for GCC Monitoring

## One-Time Server Setup

SSH into your server and run:

```bash
ssh tony@gcchvacr.com

# Clone repository (first time only)
cd ~
git clone https://github.com/Tony4tuna/gcc_monitoring.git
cd gcc_monitoring

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
ADMIN_EMAIL=admin
ADMIN_PASSWORD=1931
HOST=0.0.0.0
PORT=8000
STORAGE_SECRET=devsecret
EOF

# Run migrations
venv/bin/python utility/add_installed_location_column.py
venv/bin/python utility/create_setpoints_table.py

# Make deploy script executable
chmod +x deploy_from_github.sh

# Start app
nohup venv/bin/python app.py > app.out 2>&1 &
```

## Future Deployments (After Creating GitHub Repo)

From your Windows machine:
```powershell
# 1. Commit and push changes
git add -A
git commit -m "Your changes"
git push origin main

# 2. Deploy to server
ssh tony@gcchvacr.com "cd ~/gcc_monitoring && ./deploy_from_github.sh"
```

## Update Nginx (One-Time)
```bash
ssh tony@gcchvacr.com
sudo sed -i 's/8080/8000/g' /etc/nginx/sites-available/default
sudo nginx -t && sudo systemctl reload nginx
```

## Benefits of GitHub Deployment
- ✅ Version control and history
- ✅ Easy rollbacks (`git checkout <commit>`)
- ✅ No need to upload tarballs
- ✅ Cleaner deployment process
- ✅ Can add CI/CD with GitHub Actions later
