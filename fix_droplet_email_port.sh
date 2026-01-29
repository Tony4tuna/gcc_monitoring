#!/bin/bash
# Fix email port on droplet - switch from 587 to 2525

echo "Updating EmailSettings to port 2525..."
cd ~/gcc_monitoring

sqlite3 data/app.db "UPDATE EmailSettings SET smtp_port=2525 WHERE id=1"

echo "Verifying update..."
sqlite3 data/app.db "SELECT smtp_host, smtp_port, smtp_user FROM EmailSettings WHERE id=1"

echo ""
echo "Done! Port updated to 2525 for DigitalOcean."
echo "Now restart the app with: sudo systemctl restart gcc_monitoring"
