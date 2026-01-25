#!/bin/bash
# Update Nginx to proxy to port 8000

NGINX_CONF="/etc/nginx/sites-available/default"
BACKUP="/etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)"

# Backup current config
sudo cp "$NGINX_CONF" "$BACKUP"
echo "Backed up to: $BACKUP"

# Update proxy_pass to point to 8000
sudo sed -i 's/proxy_pass http:\/\/127\.0\.0\.1:8080/proxy_pass http:\/\/127.0.0.1:8000/g' "$NGINX_CONF"
sudo sed -i 's/proxy_pass http:\/\/localhost:8080/proxy_pass http:\/\/localhost:8000/g' "$NGINX_CONF"

# Test and reload
echo "Testing Nginx config..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Config valid. Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✓ Nginx updated and reloaded"
    echo "Current proxy config:"
    sudo grep -A 5 "proxy_pass" "$NGINX_CONF" | head -10
else
    echo "✗ Config test failed. Restoring backup..."
    sudo cp "$BACKUP" "$NGINX_CONF"
fi
