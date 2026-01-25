#!/bin/bash
# Simple GitHub deployment script
set -e

echo "🚀 Deploying GCC Monitoring from GitHub..."

# Clone fresh copy
cd ~
rm -rf gcc_monitoring_new
git clone https://github.com/Tony4tuna/gcc_monitoring.git gcc_monitoring_new

# Setup
cd gcc_monitoring_new
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q

# Create .env
cat > .env << 'EOF'
ADMIN_EMAIL=admin
ADMIN_PASSWORD=1931
HOST=0.0.0.0
PORT=8000
STORAGE_SECRET=devsecret
EOF

# Copy database if exists
if [ -f ~/gcc_monitoring/data/app.db ]; then
    mkdir -p data
    cp ~/gcc_monitoring/data/app.db data/app.db
    echo "✓ Copied existing database"
fi

# Run migrations (only if DB exists)
if [ -f data/app.db ]; then
    venv/bin/python utility/add_installed_location_column.py
    venv/bin/python utility/create_setpoints_table.py
    echo "✓ Migrations complete"
else
    echo "⚠ No database found - will create on first run"
fi

# Stop old app
pkill -f 'python.*app.py' || true
sleep 2

# Swap directories
rm -rf ~/gcc_monitoring_old
mv ~/gcc_monitoring ~/gcc_monitoring_old 2>/dev/null || true
mv ~/gcc_monitoring_new ~/gcc_monitoring

# Start new app
cd ~/gcc_monitoring
nohup venv/bin/python app.py > app.out 2>&1 &
sleep 3

# Verify
echo ""
if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Deployment successful! App running on port 8000"
    echo "📋 Recent logs:"
    tail -20 app.out
else
    echo "❌ App not running. Check logs:"
    tail -50 app.out
fi
