# SSH Key Deployment Guide

## Why SSH Keys?
- ✅ **No password prompts** (automatic authentication)
- ✅ **Secure** (key-based, not password-based)
- ✅ **Fast** (single command to deploy)
- ✅ **One-time setup** (reusable for future deployments)

---

## First Time Setup (One-time)

### Step 1: Run the setup script
```powershell
.\deploy_ssh_setup.ps1
```

This will:
1. ✓ Generate SSH key (if needed)
2. ✓ Copy public key to droplet
3. ✓ Deploy the app
4. ✓ Show you the quick deploy command for next time

**You will be asked for your password ONCE** (to copy the SSH key)

---

## Future Deployments (Fast & Easy)

### Step 1: Just run the auto-deploy script
```powershell
.\deploy_ssh_auto.ps1
```

**No password prompts. No multiple authentications. Done in ~30 seconds.**

---

## What Each Script Does

### `deploy_ssh_setup.ps1` 
- **When**: First time only
- **Does**: SSH key setup + deployment
- **Prompts**: Password once (to copy key)
- **Result**: SSH key added to droplet, app deployed

### `deploy_ssh_auto.ps1`
- **When**: Every deployment after setup
- **Does**: Git pull + migrations + restart app
- **Prompts**: None (uses SSH key)
- **Result**: App updated & live in ~30 seconds

---

## Troubleshooting

### "SSH key not found"
```powershell
.\deploy_ssh_setup.ps1
```
Run the setup script first.

### "Permission denied (publickey)"
SSH key setup failed. Try again:
```powershell
.\deploy_ssh_setup.ps1
```

### "Port 8000 already in use"
Old app is still running. The auto script kills it automatically, but you can also:
```powershell
ssh tony@gcchvacr.com "pkill -u tony python"
```

---

## Manual Commands (if needed)

```powershell
# Check app status
ssh tony@gcchvacr.com "ps aux | grep app.py | grep -v grep"

# View app logs
ssh tony@gcchvacr.com "tail -50 ~/gcc_monitoring/app.out"

# Restart app manually
ssh tony@gcchvacr.com "cd ~/gcc_monitoring && ./venv/bin/python app.py &"
```

---

## Security Notes

- SSH keys are stored in: `C:\Users\<YourUser>\.ssh\id_ed25519`
- Public key copied to droplet: `~/.ssh/authorized_keys`
- No passwords stored anywhere
- Keys use Ed25519 (modern, secure encryption)

✅ **Setup complete! Next time just run: `.\deploy_ssh_auto.ps1`**
