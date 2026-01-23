# Dashboard Overview - What's Being Displayed

## Current Dashboard Structure

The dashboard is **already integrated into the home page** at `/`. When you log in as an admin, you automatically see the dashboard.

## Dashboard Layout

### 1. **Top Section - Quick Metrics (4 Cards)**

```
┌─────────────────────────────────────────────────────────────────┐
│  Active Units          Warnings           Faults            Avg Temp   │
│  [GREEN]              [YELLOW]           [RED]              [BLUE]     │
│  4 units              2 warnings         0 critical         62.5°F     │
│  Online now           Need attention     Critical issues    Across site │
└─────────────────────────────────────────────────────────────────┘
```

**What it shows:**
- **Active Units** - Count of equipment with health score ≥ 80
- **Warnings** - Count of equipment with health score 60-79
- **Faults** - Count of equipment with health score < 60
- **Avg Supply Temp** - Average supply temperature across all units

---

### 2. **Main Content - Two-Column Layout**

#### **Left Column (75% width) - Equipment Status Table**

```
Equipment Status
┌─────────────────────────────────────────────────────────────────┐
│ Unit | Equipment        | Status    | Supply | ΔT    | Fault    │
├─────────────────────────────────────────────────────────────────┤
│ U-1  │ Carrier 5T       │ Cooling   │ 55°F   │ 10°F  │ --       │
│ U-2  │ Trane XR15       │ Heating   │ 75°F   │ -8°F  │ --       │
│ U-3  │ York Affinity    │ Idle      │ 68°F   │ --    │ F0123    │
│ U-4  │ Lennox SL280UH   │ Fault     │ --     │ --    │ F0456    │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- **Color-coded Status**: 
  - Cyan = Cooling
  - Orange = Heating
  - Blue = Economizer
  - Gray = Idle/Off
  - Red = Fault

- **ΔT Highlighting**: 
  - Yellow = Low efficiency (<14°F)
  - White = Normal

- **Click to Expand**: Click any row to see detailed equipment analysis

---

#### **Right Column (25% width) - Alerts & Activity**

```
Alerts & Activity
┌────────────────────────────────┐
│ ⚠️ Critical Alerts             │
│ • Unit 3: F0123 Fault Code     │
│ • Unit 4: F0456 Fault Code     │
│                                │
│ ⚠️ Warnings                    │
│ • Unit 1: LOW_DELTA_T          │
│ • Unit 2: HIGH_SUPERHEAT       │
│                                │
│ • Unit 5: Phase Imbalance      │
│                                │
│ All systems normal if empty    │
└────────────────────────────────┘
```

**Shows:**
- Critical alerts in red
- Warnings in yellow
- Latest 5 alerts
- Auto-updates every 30 seconds

---

### 3. **Unit Details Modal (Click on Equipment Row)**

When you click a unit row, a modal opens showing:

```
Unit 1 - Carrier 5T [Close]
┌─────────────────────────────────────────────┐
│ Equipment Health Score                      │
│              75                            │
│            / 100                           │
│         Good                               │
│                                            │
│ Issues detected:                           │
│ • Low Delta-T - poor cooling capacity      │
│ • Phase imbalance: 8.2% (should be <10%)   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Equipment Info                              │
│ Customer:  ABC Facilities                  │
│ Location:  Building A, Floor 3             │
│ Model:     Carrier Infinity 5T             │
│ Serial:    CAR-2024-001                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Operating Data                              │
│ Mode:         Cooling                      │
│ Supply Temp:  55°F                         │
│ Return Temp:  65°F                         │
│ Delta-T:      -10°F ⚠️ LOW                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Refrigerant & Pressure                     │
│ Discharge PSI:  280 PSI                    │
│ Suction PSI:    75 PSI                     │
│ Superheat:      12°F                       │
│ Subcooling:     8°F                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Alerts & Status                            │
│ Status:        Online                      │
│ Fault Code:    None                        │
│                                            │
│ System Alerts: (Top 5)                     │
│ [WARNING] LOW_DELTA_T                      │
│   Low Delta-T (10°F) - Poor efficiency     │
│ [WARNING] PHASE_IMBALANCE                  │
│   Phase imbalance: 8.2%                    │
└─────────────────────────────────────────────┘

Last Update: 2m ago (2026-01-18T10:45:32)
```

---

## Data Flow

```
DATABASE (SQLite)
    ↓
  UnitReadings (latest per unit)
    ↓
get_unit_stats()
    ├─→ Get all units with latest readings
    ├─→ Calculate health scores
    ├─→ Generate alerts
    └─→ Count by category
    ↓
Dashboard Display
    ├─→ Metrics (4 cards)
    ├─→ Equipment table (clickable)
    └─→ Alerts sidebar
    ↓
Click Unit
    ↓
show_unit_details(unit_id)
    ├─→ Fetch detailed reading
    ├─→ Calculate comprehensive analysis
    └─→ Display in modal
```

---

## What the Core Modules Are Doing

### **Equipment Analysis Module**
- **Health Score**: 0-100 based on temperature, pressure, electrical
- **Issues**: Lists specific problems (low Delta-T, phase imbalance, etc.)
- **Sub-analyses**: Temperature, Pressure, Electrical breakdowns

### **Alert System Module**
- **Severity Levels**: 
  - 🔴 CRITICAL - Immediate action needed
  - 🟡 WARNING - Monitor and address soon
  - 🔵 INFO - Informational

- **Alert Categories**:
  - Temperature-based (freezing, overheating, low efficiency)
  - Pressure-based (low discharge, high discharge, ratio issues)
  - Electrical-based (phase imbalance, overload, compressor issues)
  - Fault codes

---

## Current Home Page Integration

In `app.py`:
```python
@ui.page("/")
def home():
    user = current_user()
    if not user:
        ui.navigate.to("/login")
        return
    if is_admin():
        dashboard.page()  # ← Shows dashboard for admins
    else:
        client_home.page()  # ← Shows different page for clients
```

**So the flow is:**
1. User logs in at `/login`
2. Redirected to `/` (home page)
3. If admin → Shows **dashboard** (equipment overview)
4. If client → Shows **client_home** (their specific equipment)

---

## Dashboard Features in Action

### **Auto-Refresh**
- Dashboard reloads every 30 seconds
- Always shows latest data from database
- Test data generator continuously adding new readings

### **Color-Coded Status**
- Green metrics = All good
- Yellow = Warnings/needs attention
- Red = Critical issues
- Blue = Information

### **Real-Time Alerts**
- Top 5 critical + warning alerts displayed
- Updated from actual equipment analysis
- Linked to specific units

### **Detailed Analysis**
- Click any unit to see:
  - Health score calculation breakdown
  - All active alerts with descriptions
  - Temperature and pressure data
  - Electrical readings
  - Time of last update

---

## What You Can Customize

### 1. **Threshold Values**
Edit `core/alert_system.py`:
```python
TEMP_THRESHOLDS = {
    'low_delta_t': 10,      # Change to 12 for stricter
    'high_delta_t': 25,
}

PRESSURE_THRESHOLDS = {
    'min_discharge': 100,   # Change as needed
    'max_discharge': 400,
}
```

### 2. **Metric Cards**
Edit `pages/dashboard.py` to add/remove metrics:
```python
_metric("Your Title", "Value", "Subtitle", "text-color")
```

### 3. **Table Columns**
Edit the columns in `get_unit_stats()` to show different data

### 4. **Alert Display**
Edit alert filtering in `get_unit_stats()`:
```python
'alerts': alerts[:5]  # Change 5 to show more
```

### 5. **Colors**
Edit `get_status_color()` function for different mode colors

---

## Example: What Dashboard Reads Right Now

Based on test data being generated:

```
DASHBOARD DISPLAY:
═════════════════════════════════════════════════════════════

Metrics:
┌─────────┬──────────┬────────┬──────────────┐
│ Active  │ Warnings │ Faults │ Avg Supply   │
│ 3 units │ 1        │ 0      │ 62.3°F       │
└─────────┴──────────┴────────┴──────────────┘

Equipment Table:
┌──────┬──────────────────┬──────────┬────────┬────────┐
│ Unit │ Equipment        │ Mode     │ Supply │ ΔT     │
├──────┼──────────────────┼──────────┼────────┼────────┤
│ U-1  │ Carrier 5T       │ Cooling  │ 55°F   │ -10°F  │
│ U-2  │ Trane XR15       │ Heating  │ 78°F   │ -5°F   │
│ U-3  │ York Affinity    │ Idle     │ 68°F   │ --     │
│ U-4  │ Lennox SL280UH   │ Cooling  │ 52°F   │ -12°F  │
└──────┴──────────────────┴──────────┴────────┴────────┘

Alerts:
⚠️ Unit 1: LOW_DELTA_T - Low efficiency
⚠️ Unit 4: PHASE_IMBALANCE - 8% variation
```

---

## Summary

✅ **Dashboard is fully integrated into home page**
✅ **Real-time health scores calculated**
✅ **Alerts auto-generated from equipment data**
✅ **Equipment details available on click**
✅ **Auto-refreshes every 30 seconds**
✅ **Color-coded for quick status assessment**

**The dashboard is the main interface admins see when they log in!**

Next steps if you want to customize:
1. Change thresholds → Edit `core/alert_system.py`
2. Add metrics → Edit dashboard.py `_metric()` calls
3. Change colors → Edit `get_status_color()` function
4. Add columns → Edit SQL query in `get_unit_stats()`
