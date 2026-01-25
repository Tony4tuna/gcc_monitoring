#!/bin/bash
# GitHub-based deployment script for GCC Monitoring
# Run on server: ./deploy_from_github.sh

set -e

REPO_URL="https://github.com/Tony4tuna/gcc_monitoring.git"
DEPLOY_DIR="/home/tony/gcc_monitoring"
BRANCH="main"

echo "🚀 Deploying GCC Monitoring from GitHub..."

# Navigate to deployment directory
cd "$DEPLOY_DIR" || exit 1

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull origin "$BRANCH"

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run database migrations
echo "🔧 Running migrations..."
venv/bin/python utility/add_installed_location_column.py
venv/bin/python utility/create_setpoints_table.py

# Stop old process
echo "⏹️  Stopping old app process..."
pkill -f "python.*app.py" || true
sleep 2

# Ensure .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'ENVEOF'
ADMIN_EMAIL=admin
ADMIN_PASSWORD=1931
HOST=0.0.0.0
PORT=8000
STORAGE_SECRET=devsecret
ENVEOF
fi

# Start new app
echo "▶️  Starting application..."
nohup venv/bin/python app.py > "$DEPLOY_DIR/app.out" 2>&1 &
sleep 3

# Verify
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ Deployment successful! App is running on port 8000"
    echo "📋 Recent logs:"
    tail -20 "$DEPLOY_DIR/app.out"
else
    echo "❌ Deployment failed - app not running"
    tail -50 "$DEPLOY_DIR/app.out"
    exit 1
fi
