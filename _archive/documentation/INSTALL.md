# GCC Monitoring System - Installation Guide

## 📋 System Requirements
- Windows 10 or later
- Python 3.12 or later
- At least 500MB free disk space
- Internet connection (for first-time setup)

---

## 🚀 Quick Installation (Automatic)

### Option 1: Using Installation Script (Recommended)
1. Copy the entire `gcc_monitoring` folder to your office computer
2. Open PowerShell **as Administrator**
3. Navigate to the project folder:
   ```powershell
   cd "C:\Path\To\gcc_monitoring"
   ```
4. Run the installation script:
   ```powershell
   .\setup.ps1
   ```
5. Wait for completion (2-5 minutes)
6. Once done, the app will automatically start on `http://localhost:8080`

---

## 🔧 Manual Installation

If the automatic script doesn't work, follow these steps:

### Step 1: Install Python 3.12
1. Download from: https://www.python.org/downloads/
2. Run installer
3. ✅ **IMPORTANT: Check "Add Python to PATH"** during installation
4. Click "Install Now" or customize options

### Step 2: Verify Python Installation
Open PowerShell and run:
```powershell
python --version
```
Should show: `Python 3.12.x`

### Step 3: Navigate to Project Folder
```powershell
cd "C:\Path\To\gcc_monitoring"
```

### Step 4: Create Virtual Environment
```powershell
python -m venv venv
```

### Step 5: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate
```
(Prompt should show `(venv)` at the beginning)

### Step 6: Install Dependencies
```powershell
pip install nicegui passlib
```

### Step 7: Start the Application
```powershell
python app.py
```

### Step 8: Access the Application
Open your web browser and go to:
```
http://localhost:8080
```

---

## 🔐 Login Credentials

**Default Admin Account:**
- **Email:** `admin`
- **Password:** `1931`

---

## 📁 Project Structure
```
gcc_monitoring/
├── app.py                 # Main application entry point
├── setup.ps1             # Automatic installation script
├── INSTALL.md            # This file
├── core/                 # Core business logic
│   ├── auth.py          # Authentication & sessions
│   ├── db.py            # Database connection
│   └── ...
├── pages/                # Application pages
│   ├── dashboard.py      # Admin dashboard
│   ├── client_home.py    # Client home page
│   ├── login.py          # Login page
│   └── ...
├── ui/                   # UI components
│   └── layout.py         # Unified layout system
└── venv/                 # Virtual environment (created after setup)
```

---

## 🎯 Daily Usage (After Installation)

Every time you want to use the app:

1. **Open PowerShell** in the project folder
2. **Activate environment:**
   ```powershell
   .\venv\Scripts\Activate
   ```
3. **Start app:**
   ```powershell
   python app.py
   ```
4. **Open browser:** `http://localhost:8080`

---

## 🛑 Stopping the Application

To stop the app:
1. Press `Ctrl + C` in the PowerShell terminal
2. Or close the PowerShell window

---

## 🔄 Features

### Navigation Menu (Left Drawer)
- 🏠 **Home** - Main dashboard/client home
- 👥 **Clients** - Customer management
- 📍 **Locations** - Location management
- 📦 **Units** - HVAC unit monitoring
- 📹 **AI Cameras** - Camera monitoring (2 square frames)
- ⚙️ **Settings** - System settings
- 🔧 **Admin** - Administration panel

### Dashboard Features
- Real-time HVAC unit monitoring
- Spreadsheet-style unit table
- Health status indicators (color-coded)
- Temperature monitoring
- Fault detection
- Compact, professional design
- Dark theme with green accents (#16a34a)

### Security Features
- Session validation on server restart
- Auto-logout on login page access
- Green theme throughout
- Professional UI/UX

---

## 🐛 Troubleshooting

### Issue: "Python not found"
**Solution:** Python is not in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Users\...\Python312\python.exe app.py`

### Issue: "Module not found: nicegui"
**Solution:** Virtual environment not activated
- Run: `.\venv\Scripts\Activate`
- Then try: `pip install nicegui passlib`

### Issue: "Port 8080 already in use"
**Solution:** Another app is using port 8080
- Kill the process: `Get-Process python | Stop-Process -Force`
- Or use different port by editing `app.py`

### Issue: App closes immediately
**Solution:** Database or dependencies issue
- Try: `pip install --upgrade nicegui passlib`
- Delete `venv` folder and reinstall from Step 4

### Issue: Can't connect to localhost:8080
**Solution:** Firewall is blocking port
- Allow Python through Windows Firewall
- Or try: `http://127.0.0.1:8080`

---

## 📞 Support

For issues or questions:
1. Check this file first
2. Look at terminal error messages (usually show the problem)
3. Try reinstalling dependencies: `pip install --upgrade nicegui passlib`

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] App starts without errors
- [ ] Can access http://localhost:8080
- [ ] Can log in with admin/1931
- [ ] Dashboard shows HVAC units in table
- [ ] Left navigation menu works
- [ ] Can click all buttons without crashes
- [ ] AI Cameras dialog shows 2 square frames
- [ ] Settings dialog opens
- [ ] Dark theme with green accents visible

---

**Version:** 1.0  
**Last Updated:** January 18, 2026  
**Framework:** NiceGUI 3.5.0 + Python 3.12
