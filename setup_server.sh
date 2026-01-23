#!/bin/bash
# Simple deployment script for DigitalOcean
# Run this on your server after uploading the files

set -e

echo "=== GCC Monitoring - Server Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use: sudo bash setup_server.sh)"
    exit 1
fi

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt install -y python3 python3-pip python3-venv nginx ufw

# Create application user
if ! id "gcc" &>/dev/null; then
    echo "Creating gcc user..."
    adduser gcc --disabled-password --gecos ""
fi

# Setup application directory
APP_DIR="/home/gcc/gcc_monitoring"
mkdir -p $APP_DIR

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Upload your application files to: $APP_DIR"
echo "2. Run as gcc user: su - gcc"
echo "3. Navigate to app: cd $APP_DIR"
echo "4. Run setup: bash deploy.sh"
echo ""
