# DASHBOARD QUICK REFERENCE - January 18, 2026

## 🚀 START HERE

### Access Dashboard
```
URL: http://localhost:8080
Login: admin / 1931
Auto-refresh: Every 30 seconds
```

---

## 📊 Dashboard Structure

### Top Section (Key Metrics)
- **Active Units**: Count of units with health score ≥ 80
- **Warnings**: Count of units with health score 60-79
- **Faults**: Count of units with health score < 60
- **Avg Supply Temp**: Average across all units

### Main Section (Equipment Table)
```
Columns: Unit | Customer | Location | Equipment | Status | Supply | ΔT | Fault | Last
Action: Click any row → View detailed modal
```

### Right Sidebar (Analysis & Alerts)
- **Performance Trends**: Placeholder for IA module data
- **Active Alerts**: Real-time critical/warning alerts

### Bottom Section (Parts & Maintenance)
- **Parts Table**: Compressor, Filter, Condenser, Evaporator status
- **Maintenance Schedule**: Upcoming service dates

### Bottom Expansion (Detailed Analysis)
- **Unit Cards**: 4 quick-view cards for each unit
- **Click to Details**: Open full modal per unit

---

## 🔧 Key Information

### Current Test Data
```
Unit 2: York 12344        | Health: 50/100 (Fair)   | Fault: LOW_DELTA_T
Unit 3: Trane RTU-2026    | Health: 50/100 (Fair)   | Fault: HIGH_DISCHARGE_PSI
Unit 4: ggggg ggggg       | Health: 65/100 (Good)   | Fault: HIGH_DISCHARGE_TEMP
Unit 5: piprir ffffff     | Health: 70/100 (Good)   | Fault: None
```

### Database
- **Type**: SQLite
- **File**: `data/app.db`
- **Readings**: 28+ and growing
- **Update Rate**: 4 new readings/minute

### Auto-Updates
- **Generator**: `test_data_generator.py` (running)
- **Refresh Rate**: 30 seconds (JavaScript)
- **Data Delay**: 60-90 seconds (batch interval)

---

## 🎯 What to Check Tomorrow

### Before Building Modules
1. Verify dashboard still running
2. Check test data generating
3. Confirm all 4 units visible
4. Alert system working
5. Health scores calculating

### Then Build (In Order)
1. **IA Module** → Integrate into Performance Trends
2. **Maintenance Module** → Integrate into Parts Table
3. **Reporting Module** → New `/reports` page
4. **Finish & Test** → Full dashboard flow

---

## 📈 Files to Know

### Dashboard
- `pages/dashboard.py` - Main dashboard (561 lines)
  - `get_unit_stats()` - Data gathering
  - `show_unit_details()` - Modal window
  - `page()` - Main function

### Core Modules (Already Done)
- `core/equipment_analysis.py` - Health scoring
- `core/alert_system.py` - Alert generation
- `core/statistics.py` - Statistics

### Test Data
- `test_data_generator.py` - Continuous data generation
- `test_modules.py` - Unit tests

### Documentation
- `DASHBOARD_REDESIGN.md` - Layout details
- `TOMORROW_PLAN.md` - Development roadmap
- `DASHBOARD_LIVE.md` - Current status

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| No data showing | Wait 60 sec for data generator |
| Old cache | Ctrl+Shift+R (hard refresh) |
| Port 8080 busy | `Get-Process python \| Stop-Process -Force` |
| App crashed | Check for syntax errors in dashboard.py |
| Alerts not showing | Check fault_code in database |
| Table not clickable | Make sure unit data is loaded |

---

## 📝 Color Codes

### Health Status
- 🟢 Green (≥80): Online/Good
- 🟡 Yellow (60-79): Warning/Fair
- 🔴 Red (<60): Fault/Poor

### Operating Mode
- 🔵 Cyan: Cooling
- 🟠 Orange: Heating
- 🔹 Blue: Economizer
- ⚫ Gray: Idle/Off

---

## 💡 Pro Tips

1. **Auto-refresh**: Dashboard updates every 30 sec automatically
2. **Offline work**: You can still view last data without generator running
3. **Click units**: All table rows are clickable for drill-down
4. **Mobile view**: Works on phones/tablets (responsive)
5. **Logout**: Button in top-right corner

---

## 📞 Support

### Issues?
1. Check logs in terminal
2. Verify test_data_generator running
3. Try hard refresh (Ctrl+Shift+R)
4. Restart app if needed

### Documentation
- See `TOMORROW_PLAN.md` for development guide
- See `DASHBOARD_REDESIGN.md` for layout specs

---

## ✅ Checklist for Tomorrow

Morning:
- [ ] Dashboard still running
- [ ] All 4 units visible
- [ ] Alerts working
- [ ] Data flowing

Development:
- [ ] Build IA Module
- [ ] Build Maintenance Module
- [ ] Integrate both into dashboard
- [ ] Create Reporting page
- [ ] Full testing

---

**Last Updated**: Jan 18, 2026  
**Status**: 🟢 LIVE  
**Next Phase**: Module Integration (Tomorrow)
