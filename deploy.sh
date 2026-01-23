#!/bin/bash
# Quick production deployment script for Linux servers

set -e

echo "=== GCC Monitoring System - Production Setup ==="

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate secure secrets
    ADMIN_PWD=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(20)))")
    STORAGE_SEC=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated values
    sed -i "s/your_secure_password_here/$ADMIN_PWD/" .env
    sed -i "s/your_secret_key_here/$STORAGE_SEC/" .env
    
    echo ""
    echo "✅ Generated .env file with secure credentials:"
    echo "   Admin password: $ADMIN_PWD"
    echo "   (Saved in .env file)"
    echo ""
fi

# Create necessary directories
mkdir -p data backups logs

# Set secure permissions
chmod 600 .env
chmod 700 data
chmod 600 data/*.db 2>/dev/null || true

# Check database
if [ ! -f "data/app.db" ]; then
    echo "Database not found. Please run schema initialization first:"
    echo "  python utility/apply_schema.py"
    exit 1
fi

echo ""
echo "✅ Production setup complete!"
echo ""
echo "To start the server:"
echo "  1. Review .env file and update settings if needed"
echo "  2. Run: source venv/bin/activate && python app.py"
echo ""
echo "For systemd service setup, see DEPLOYMENT.md"
