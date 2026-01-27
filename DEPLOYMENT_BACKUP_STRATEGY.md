# Deployment & Backup Strategy

## Problem Solved
**Issue**: Deployments could overwrite or lose database data  
**Solution**: Automatic backups BEFORE every deployment + manual backup scripts

---

## Automatic Backups (Built-in)

Every deployment now **automatically backs up the database** on the droplet BEFORE pulling new code:

```powershell
.\deploy_ssh_auto.ps1
```

Will:
1. ✓ Backup current database: `app.db.backup_YYYYMMDD_HHMMSS`
2. ✓ Pull latest code from GitHub
3. ✓ Run migrations
4. ✓ Restart app

---

## Manual Backups (Anytime)

### Backup droplet database locally:
```powershell
.\backup_droplet_db.ps1
```
Saves to: `data/backups/app.db.droplet_YYYYMMDD_HHMMSS`

### Backup local database only:
```powershell
.\backup_droplet_db.ps1 -Local
```
Saves to: `data/backups/app.db.local_YYYYMMDD_HHMMSS`

---

## Restore from Backup

### Restore on droplet:
```powershell
ssh tony@gcchvacr.com "cd ~/gcc_monitoring/data && cp app.db.backup_20260127_163412 app.db && echo '✓ Restored'"
```

### Restore locally:
```powershell
Copy-Item "data/backups/app.db.droplet_20260127_163412" "data/app.db"
```

---

## Backup Locations

**On Droplet:**
```
/home/tony/gcc_monitoring/data/
├── app.db (current)
├── app.db.backup_20260127_163412
├── app.db.backup_20260125_012021
└── app.db.backup_20260119_230629
```

**Locally:**
```
data/backups/
├── app.db.droplet_20260127_163412
├── app.db.local_20260127_160000
└── ...
```

---

## Workflow: Safe Deployment

1. **Create new tickets/data** locally
2. **Backup before deployment:**
   ```powershell
   .\backup_droplet_db.ps1  # Download droplet DB as backup
   ```
3. **Deploy:**
   ```powershell
   .\deploy_ssh_auto.ps1    # Auto-backup + deploy
   ```
4. **Sync your local data:**
   ```powershell
   scp -o StrictHostKeyChecking=no data/app.db tony@gcchvacr.com:/home/tony/gcc_monitoring/data/
   ```
5. **Verify:**
   ```powershell
   ssh tony@gcchvacr.com "cd ~/gcc_monitoring && ./venv/bin/python -c 'import sqlite3; c=sqlite3.connect(\"data/app.db\"); print(\"Tickets:\", c.execute(\"SELECT COUNT(*) FROM ServiceCalls\").fetchone()[0])'"
   ```

---

## Future Deployments

From now on, your deployment scripts will:
- ✅ **Always backup database first** (on droplet)
- ✅ **Never lose data** on deployment
- ✅ **Automatic recovery** if something goes wrong

✅ **Safe to deploy with confidence!**
