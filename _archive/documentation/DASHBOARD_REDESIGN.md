# Dashboard Redesign - Complete Layout (January 18, 2026)

## Overview
The dashboard has been completely reorganized to present all equipment data in a logical, hierarchical flow. It now includes placeholders for future IA module data (tendency graphs) and maintenance integration.

---

## New Dashboard Structure

### Section 1: KEY METRICS (Top)
```
┌─────────────────┬──────────────┬──────────┬─────────────────────┐
│ Active Units    │ Warnings     │ Faults   │ Avg Supply Temp     │
│       X         │      X       │    X     │      XX°F            │
└─────────────────┴──────────────┴──────────┴─────────────────────┘
```
- Quick overview of system health
- Color-coded (green/yellow/red)
- Auto-updates every 30 seconds

---

### Section 2: EQUIPMENT STATUS OVERVIEW (Main Content)

#### Left Side (70% width) - Equipment Table
```
EQUIPMENT TABLE
═══════════════════════════════════════════════════════════════════════════════════════════════════

┌──────┬──────────────────┬───────────────────────────────┬────────────────────────────┐
│ Unit │ Customer         │ Location                      │ Equipment                  │
├──────┼──────────────────┼───────────────────────────────┼────────────────────────────┤
│ 2    │ Park It          │ 160-162 West 124th Street     │ York 12344                 │
│ 3    │ Park It          │ 160-162 West 124th Street     │ Trane RTU-Test-2026        │
│ 4    │ Park It          │ 160-162 West 124th Street     │ ggggg ggggg                │
│ 5    │ Park It          │ 195 Havemeyer Street          │ piprir ffffff              │
└──────┴──────────────────┴───────────────────────────────┴────────────────────────────┘

┌──────────┬────────┬────────┬──────────┬─────────────────┐
│ Status   │ Supply │ ΔT     │ Fault    │ Last Update     │
├──────────┼────────┼────────┼──────────┼─────────────────┤
│ Cooling  │ 52°F   │ 18°F   │ --       │ 2m ago          │
│ Heating  │ 105°F  │ 28°F   │ --       │ 5m ago          │
│ Idle     │ 60°F   │ 0°F    │ FAULT_X  │ 1m ago          │
│ Cooling  │ 55°F   │ 15°F   │ --       │ 3m ago          │
└──────────┴────────┴────────┴──────────┴─────────────────┘

Features:
- Click any row to expand detailed unit analysis modal
- All customer and location info visible
- Real-time health calculations
```

#### Right Side (30% width) - Analysis Panels

**Panel 1: Performance Trends (Placeholder for IA Data)**
```
┌─────────────────────────────────────┐
│ 📊 Performance Trends               │
├─────────────────────────────────────┤
│ 📊 Filter Replacement Tendency      │
│                                     │
│ [🔮 PLACEHOLDER]                    │
│ (IA Module Data)                    │
│                                     │
│ Supply Temp Trend                   │
│ Filter Clogging Trend               │
│                                     │
│ 📌 Coming Soon: Real-time graphs    │
└─────────────────────────────────────┘
```

**Panel 2: Active Alerts**
```
┌─────────────────────────────────────┐
│ 🔴 Active Alerts                    │
├─────────────────────────────────────┤
│ ❌ Unit 2: UNIT_FAULT               │
│ ⚠️  Unit 3: HIGH_PRESSURE            │
│ ❌ Unit 4: LOW_DELTA_T               │
│ ✓  All other systems normal         │
└─────────────────────────────────────┘
```

---

### Section 3: PARTS & MALFUNCTION STATUS (Bottom)

#### Left Side (60% width) - Parts Status Table
```
EQUIPMENT PARTS STATUS
═══════════════════════════════════════════════════════════════════

┌──────┬──────────────┬────────────┬────────┬──────────┬────────────┐
│ Unit │ Customer     │ Compressor │ Filter │ Condenser│ Evaporator │
├──────┼──────────────┼────────────┼────────┼──────────┼────────────┤
│ 2    │ Park It      │ ✓ OK       │ ✓ OK   │ ✓ OK     │ ✓ OK       │
│ 3    │ Park It      │ ⚠ Check    │ ✓ OK   │ ✓ OK     │ ✓ OK       │
│ 4    │ Park It      │ ✓ OK       │ ✓ OK   │ ✓ OK     │ ✓ OK       │
│ 5    │ Park It      │ ✓ OK       │ ✓ OK   │ ✓ OK     │ ✓ OK       │
└──────┴──────────────┴────────────┴────────┴──────────┴────────────┘

┌─────────────────┐
│ Next Service    │
├─────────────────┤
│ 30 days         │
│ 30 days         │
│ 30 days         │
│ 30 days         │
└─────────────────┘

📌 Parts status will be auto-updated from maintenance module
```

#### Right Side (40% width) - Maintenance Schedule
```
┌─────────────────────────────────────┐
│ 📅 Maintenance Schedule             │
├─────────────────────────────────────┤
│ 🔵 Unit 2 - Filter Change           │
│    📌 In 15 days                    │
│                                     │
│ 🟡 Unit 3 - Pressure Check          │
│    📌 In 7 days                     │
│                                     │
│ 🟢 Unit 5 - Routine Inspection      │
│    📌 In 30 days                    │
│                                     │
│ 📌 Schedule syncs with maintenance  │
│    module                           │
└─────────────────────────────────────┘
```

---

### Section 4: DETAILED UNIT ANALYSIS (Expandable)
```
VIEW DETAILED UNIT ANALYSIS ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────┬──────────────────────────┬──────────────────────────┐
│ Unit 2 (FAIR)            │ Unit 3 (GOOD)            │ Unit 4 (EXCELLENT)       │
├──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Park It @                │ Park It @                │ Park It @                │
│ 160-162 West 124th St    │ 160-162 West 124th St    │ 160-162 West 124th St    │
│                          │                          │                          │
│ York 12344               │ Trane RTU-Test-2026      │ ggggg ggggg              │
│                          │                          │                          │
│ Health Score: 50/100     │ Health Score: 65/100     │ Health Score: 78/100     │
│                          │                          │                          │
│ Temp: 53.9°F | ΔT: 9.4°F │ Temp: 55°F | ΔT: -24.1°F │ Temp: 59.4°F | ΔT: 0°F   │
│ ⚠ Fault: LOW_DELTA_T     │ ⚠ Fault: PRESSURE_HIGH  │ No Faults                │
│                          │                          │                          │
│ [View Details]           │ [View Details]           │ [View Details]           │
└──────────────────────────┴──────────────────────────┴──────────────────────────┘
```

Each card shows:
- Unit number and health status
- Customer and location
- Equipment model
- Health score (0-100)
- Current temperatures
- Fault codes if any
- Quick action button

---

## Logical Data Hierarchy

```
DASHBOARD
├── 1️⃣ KEY METRICS (System-level overview)
│   ├── Active Units
│   ├── Warnings Count
│   ├── Faults Count
│   └── Average Temperature
│
├── 2️⃣ EQUIPMENT TABLE (Unit-level status)
│   ├── Unit ID
│   ├── Customer Name
│   ├── Location Address
│   ├── Equipment Make/Model
│   ├── Current Status (Mode)
│   ├── Temperatures
│   ├── Faults
│   └── Last Update Time
│
├── 3️⃣ RIGHT ANALYSIS PANELS
│   ├── Performance Trends (Future: IA Data)
│   │   ├── Filter Replacement Tendency
│   │   ├── Supply Temp Trend
│   │   └── Filter Clogging Trend
│   │
│   └── Active Alerts (Real-time)
│       ├── Critical Alerts
│       ├── Warnings
│       └── System Status
│
├── 4️⃣ PARTS & MAINTENANCE (Lower section)
│   ├── Equipment Parts Status
│   │   ├── Compressor Status
│   │   ├── Filter Status
│   │   ├── Condenser Status
│   │   └── Evaporator Status
│   │
│   └── Maintenance Schedule
│       ├── Upcoming Filter Changes
│       ├── Pressure Checks
│       └── Routine Inspections
│
└── 5️⃣ DETAILED ANALYSIS (Expandable)
    ├── Unit 2 Card → [Click for full modal]
    ├── Unit 3 Card → [Click for full modal]
    ├── Unit 4 Card → [Click for full modal]
    └── Unit 5 Card → [Click for full modal]
```

---

## Data Flow & Auto-Updates

```
Database (SQLite)
      ↓
Test Data Generator (60s interval)
      ↓
Dashboard Query (get_unit_stats)
      ↓
Core Modules Processing
├── Equipment Analysis → Health Scores
├── Alert System → Active Alerts
└── Statistics → Trends & Averages
      ↓
UI Rendering
      ↓
JavaScript Auto-Refresh (30s interval)
      ↓
Browser Display
```

---

## Future Enhancements (Ready for Integration)

### 1. **IA Module - Tendency Graphs**
- Location: Right sidebar, Performance Trends panel
- Data needed:
  - Filter replacement predictions
  - Supply temperature trends
  - Filter clogging forecasts
  - Component lifespan estimates
- Implementation: `TODO - IA Module Integration`

### 2. **Maintenance Module - Parts Status**
- Location: Bottom, Parts Malfunction Table
- Data needed:
  - Part condition status
  - Last service date
  - Next service schedule
  - Maintenance history
- Implementation: `TODO - Maintenance Module Integration`

### 3. **Alert System Enhancements**
- Current: Display top 5 alerts
- Future: Customizable alert filters
- Future: Alert history and trends

### 4. **Additional Metrics**
- Energy consumption
- Cost analysis
- Service call history
- Equipment efficiency ratings

---

## File Structure

**Current Dashboard File:**
- `pages/dashboard.py` (560+ lines)
  - Layout sections organized with comments
  - `get_unit_stats()` - Main data gathering function
  - `show_unit_details()` - Detail modal
  - `_metric()` - Metric card component
  - Color coding functions
  - Time formatting utilities

**Core Dependencies:**
- `core.equipment_analysis` - Health scoring
- `core.alert_system` - Alert generation
- `core.db` - Database connection
- `core.auth` - User authentication

---

## Testing Checklist

- [x] All 4 test units display correctly
- [x] Customer and location info showing
- [x] Health scores calculating
- [x] Alerts generating
- [x] Fault codes displaying
- [x] Click-to-expand working
- [x] 30-second auto-refresh functional
- [x] Responsive layout (mobile/desktop)
- [ ] IA module data integration
- [ ] Maintenance module data integration
- [ ] Performance optimization (large data sets)
- [ ] Search/filter functionality

---

## Tomorrow's Work Plan

### Application Logic & Hierarchy
1. **Build IA Module**
   - Filter replacement prediction algorithm
   - Trend analysis functions
   - Forecast models

2. **Build Maintenance Module**
   - Parts tracking database schema
   - Service schedule management
   - Maintenance history logging

3. **Dashboard Integration**
   - Connect IA data to tendency graphs
   - Connect maintenance data to parts table
   - Add alert configuration UI

4. **Reporting Module**
   - Historical data export
   - Trend reports
   - Compliance reporting

---

## Color Scheme Reference

```
System Status:
  Green (#10B981)     - OK / Normal
  Yellow (#FBBF24)    - Warning / Attention
  Red (#EF4444)       - Critical / Error
  Gray (#9CA3AF)      - Offline / Unknown

Mode Colors:
  Cyan (#06B6D4)      - Cooling
  Orange (#FB923C)    - Heating
  Blue (#3B82F6)      - Economizer
  Gray (#6B7280)      - Idle/Off

Background:
  Dark Gray (#1F2937) - Main background
  Darker (#111827)    - Cards
  Accent (#0F172A)    - Headers
```

---

## Notes for Development Team

1. All placeholder sections are ready for module integration
2. Database schema supports all current and planned data
3. Core modules (equipment_analysis, alert_system) are functional and tested
4. Dashboard auto-refreshes every 30 seconds - no manual refresh needed
5. Detailed analysis modal provides deep dive for individual units
6. Parts table currently shows static data - ready for maintenance module
7. All table rows are clickable for detailed drill-down analysis

**Status: DASHBOARD COMPLETE ✓**
**Ready for: Tomorrow's Application Logic Development**
