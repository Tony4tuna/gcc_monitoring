@echo off
REM Complete GitHub deployment for GCC Monitoring
REM This will prompt for SSH password twice (once for Nginx update, once for deployment)

echo Deploying GCC Monitoring from GitHub...
echo You'll be prompted for password: Fortuna2017
echo.

echo Step 1: Update Nginx to port 8000
ssh tony@gcchvacr.com "echo Fortuna2017 | sudo -S sed -i 's/8080/8000/g' /etc/nginx/sites-available/default && echo Fortuna2017 | sudo -S nginx -t && echo Fortuna2017 | sudo -S systemctl reload nginx && echo '✓ Nginx updated'"

echo.
echo Step 2: Deploy from GitHub
ssh tony@gcchvacr.com "cd ~ && rm -rf gcc_monitoring_new && git clone https://github.com/Tony4tuna/gcc_monitoring.git gcc_monitoring_new && cd gcc_monitoring_new && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt -q && printf 'ADMIN_EMAIL=admin\nADMIN_PASSWORD=1931\nHOST=0.0.0.0\nPORT=8000\nSTORAGE_SECRET=devsecret\n' > .env && venv/bin/python utility/add_installed_location_column.py && venv/bin/python utility/create_setpoints_table.py && pkill -f 'python.*app.py' || true && sleep 2 && rm -rf ~/gcc_monitoring_old && mv ~/gcc_monitoring ~/gcc_monitoring_old 2>/dev/null || true && mv ~/gcc_monitoring_new ~/gcc_monitoring && nohup ~/gcc_monitoring/venv/bin/python ~/gcc_monitoring/app.py > ~/gcc_monitoring/app.out 2>&1 & && sleep 3 && echo '' && echo '✅ Deployment complete!' && pgrep -f 'python.*app.py' && echo '✓ App is running on port 8000' && tail -20 ~/gcc_monitoring/app.out"

echo.
echo ========================================
echo Done! Check https://gcchvacr.com
echo ========================================
pause
