# Application Logic & Hierarchy - Tomorrow's Development Plan

**Date**: January 18, 2026 | **Status**: Dashboard Complete, Ready for Module Development
**Goal**: Finish the 3 remaining modules (IA, Maintenance, Reporting) and integrate with dashboard

---

## What's Done Today ✓

1. **Dashboard Layout** - Complete redesign with 5 sections
2. **Equipment Status Table** - Shows all customer/location/equipment data
3. **Alert System** - Real-time critical/warning alerts
4. **Health Scoring** - Equipment analysis with 0-100 scale
5. **Detailed Modals** - Click any unit for deep analysis
6. **Auto-Refresh** - Every 30 seconds
7. **Placeholders** - Ready for new module data integration

---

## Tomorrow's Tasks - Priority Order

### Task 1: IA (Intelligent Analytics) Module
**Location**: `core/ia_analytics.py` (NEW)
**Purpose**: Predict maintenance needs and equipment failures
**Data to predict**:
- Filter replacement tendency (days until replacement)
- Supply temperature trends
- Filter clogging forecasts
- Component lifespan estimates
- Efficiency degradation

**Function Requirements**:
```python
def predict_filter_replacement_days(unit_id, supply_temp, delta_t, runtime_hours):
    """Predict when filter needs replacement based on current trends"""
    # Logic: Analyze delta-t decrease rate, return days until critical
    return {"days_until_replacement": 15, "urgency": "medium", "confidence": 0.85}

def get_temperature_trend(unit_id, days=7):
    """Get supply temperature trend over last N days"""
    # Logic: Average temperature trend up/down
    return {"trend": "decreasing", "avg_change": -0.5, "forecast": [55, 54, 53]}

def predict_equipment_failure(unit_id):
    """Predict probability of equipment failure in next 30 days"""
    # Logic: Combine all signals (temps, pressure, faults, etc)
    return {"failure_probability": 0.15, "reason": "High discharge pressure", "urgency": "high"}

def get_efficiency_metrics(unit_id):
    """Calculate current efficiency vs baseline"""
    # Logic: Compare delta-t, power consumption, run time
    return {"efficiency_percent": 78, "trend": "declining", "recommendation": "Clean filter"}
```

**Integration Point**: Dashboard → Right sidebar "Performance Trends" panel

---

### Task 2: Maintenance Module
**Location**: `core/maintenance.py` (NEW)
**Purpose**: Track parts status, schedule services, manage maintenance history
**Schema needs**:
```python
# New tables needed
Maintenance_History
├── history_id
├── unit_id
├── service_date
├── service_type (Filter Change, Pressure Check, etc)
├── parts_replaced
├── technician_notes
└── next_service_date

Parts_Status
├── parts_status_id
├── unit_id
├── part_name (Compressor, Filter, Condenser, etc)
├── status (OK, Warning, Critical)
├── last_service_date
├── next_service_date
└── service_hours_remaining
```

**Function Requirements**:
```python
def get_parts_status(unit_id):
    """Get current status of all parts for a unit"""
    return {
        "compressor": {"status": "OK", "hours_remaining": 8000},
        "filter": {"status": "OK", "days_remaining": 15},
        "condenser": {"status": "OK", "hours_remaining": 12000},
        "evaporator": {"status": "OK", "hours_remaining": 10000}
    }

def get_maintenance_schedule(customer_id=None):
    """Get upcoming maintenance tasks"""
    return [
        {"unit_id": 2, "task": "Filter Change", "days_until": 15, "priority": "medium"},
        {"unit_id": 3, "task": "Pressure Check", "days_until": 7, "priority": "high"},
        {"unit_id": 5, "task": "Routine Inspection", "days_until": 30, "priority": "low"}
    ]

def schedule_maintenance(unit_id, service_type, scheduled_date, notes=""):
    """Schedule a maintenance event"""
    return {"schedule_id": 123, "status": "scheduled"}

def record_service(unit_id, service_type, completed_date, parts_replaced, notes):
    """Record completed maintenance"""
    return {"history_id": 456, "status": "recorded"}
```

**Integration Point**: Dashboard → Bottom section "Parts & Malfunction Status" + "Maintenance Schedule"

---

### Task 3: Reporting Module
**Location**: `pages/reporting.py` (NEW)
**Purpose**: Generate reports, export data, analyze trends
**Report Types**:
1. **Daily Summary Report** - Equipment status, alerts, maintenance
2. **Weekly Trend Report** - Performance analysis, predictions
3. **Monthly Efficiency Report** - Cost analysis, ROI
4. **Equipment History Report** - Full service history
5. **Compliance Report** - Service records for audits

**Functions**:
```python
def generate_daily_report():
    """Create daily summary email/PDF"""
    # Show today's alerts, equipment status, upcoming maintenance

def export_equipment_history(unit_id, date_from, date_to):
    """Export historical data for analysis"""
    # CSV with all readings, alerts, maintenance events

def get_efficiency_analysis(unit_id, days=30):
    """Analyze equipment efficiency over time"""
    # Compare baseline vs current, identify degradation

def generate_maintenance_forecast():
    """Predict maintenance needs for next 90 days"""
    # Use IA module to forecast all upcoming services
```

**Route**: `@ui.page("/reports")` or add tab to dashboard

---

### Task 4: Integration Points

#### Update Dashboard
```python
# In pages/dashboard.py - Right Sidebar

# Instead of placeholder, call IA module:
from core.ia_analytics import predict_filter_replacement_days, get_temperature_trend

# Update Performance Trends section:
def update_trends_panel(unit_id):
    filter_pred = predict_filter_replacement_days(unit_id)
    temp_trend = get_temperature_trend(unit_id)
    return {
        'filter_days': filter_pred['days_until_replacement'],
        'temp_trend': temp_trend['trend'],
        'forecast': temp_trend['forecast']
    }

# Update Parts Status Table:
from core.maintenance import get_parts_status, get_maintenance_schedule

# Replace static parts table with:
parts = get_parts_status(unit_id)
maintenance = get_maintenance_schedule()
```

---

## Database Schema Updates Needed

### New Tables
```sql
-- IA Analytics History
CREATE TABLE Analytics_History (
    history_id INTEGER PRIMARY KEY,
    unit_id INTEGER,
    prediction_date DATETIME,
    filter_days_predicted INTEGER,
    efficiency_percent FLOAT,
    failure_probability FLOAT,
    FOREIGN KEY(unit_id) REFERENCES Units(unit_id)
);

-- Maintenance Tracking
CREATE TABLE Maintenance_History (
    history_id INTEGER PRIMARY KEY,
    unit_id INTEGER,
    service_date DATETIME,
    service_type TEXT,
    parts_replaced TEXT,
    technician_notes TEXT,
    next_service_date DATE,
    FOREIGN KEY(unit_id) REFERENCES Units(unit_id)
);

CREATE TABLE Parts_Status (
    parts_id INTEGER PRIMARY KEY,
    unit_id INTEGER,
    part_name TEXT,
    status TEXT,
    last_service_date DATE,
    next_service_date DATE,
    FOREIGN KEY(unit_id) REFERENCES Units(unit_id)
);

-- Report Generation Log
CREATE TABLE Reports (
    report_id INTEGER PRIMARY KEY,
    report_type TEXT,
    generated_date DATETIME,
    generated_by TEXT,
    file_path TEXT,
    status TEXT
);
```

---

## File Structure After Tomorrow

```
gcc_monitoring/
├── core/
│   ├── equipment_analysis.py    [DONE]
│   ├── alert_system.py          [DONE]
│   ├── statistics.py            [DONE]
│   ├── ia_analytics.py          [NEW - Tomorrow]
│   ├── maintenance.py           [NEW - Tomorrow]
│   └── reporting.py             [NEW - Tomorrow]
│
├── pages/
│   ├── dashboard.py             [UPDATED - Today]
│   ├── reporting.py             [NEW - Tomorrow]
│   └── ...
│
├── data/
│   └── app.db                   [Will add new tables]
│
└── docs/
    ├── DASHBOARD_REDESIGN.md    [NEW - Today]
    ├── IA_MODULE_SPEC.md        [NEW - Tomorrow]
    ├── MAINTENANCE_SPEC.md      [NEW - Tomorrow]
    └── REPORTING_SPEC.md        [NEW - Tomorrow]
```

---

## Development Priority

### Morning Session (2-3 hours)
1. Build IA Module with basic algorithms
2. Add 3 new database tables
3. Integrate IA data into dashboard trends panel

### Afternoon Session (2-3 hours)
4. Build Maintenance Module
5. Create parts tracking logic
6. Integrate maintenance into dashboard bottom section

### Late Afternoon (1-2 hours)
7. Build basic Reporting Module
8. Create first report (Daily Summary)
9. Test full dashboard flow

---

## Testing Strategy Tomorrow

```
1. Unit Tests (per module)
   - IA predictions with test data
   - Maintenance scheduling functions
   - Report generation

2. Integration Tests
   - Dashboard loads all new data
   - Tendency graphs display correctly
   - Maintenance schedule updates
   - Reports generate without errors

3. UI Tests
   - Click unit → modal shows trends
   - Parts table updates
   - Maintenance schedule visible
   - Auto-refresh still working

4. End-to-End
   - Full dashboard flow
   - All sections populated
   - No data conflicts
```

---

## Success Criteria for Tomorrow

✓ IA Module predicting maintenance needs
✓ Tendency graphs showing real data
✓ Parts status table populated from maintenance module
✓ Maintenance schedule displaying upcoming tasks
✓ Dashboard fully integrated with all new modules
✓ Auto-refresh still working
✓ All tests passing
✓ Documentation complete

---

## Notes for Development Team

1. **Reuse existing patterns** - Follow equipment_analysis.py style for new modules
2. **Type conversions** - Remember to use _to_float() for database string values
3. **Error handling** - Wrap all DB queries in try/finally blocks
4. **Testing** - Use test_modules.py as reference for test structure
5. **Documentation** - Comment all new functions like existing modules
6. **Integration** - Use core/db.py get_conn() for database access
7. **UI/UX** - Keep consistent with current color scheme and layout

---

## Git Commit Messages (For tracking)

```
Day 1 (Today):
"Dashboard redesign complete - add sections for IA and maintenance"

Day 2 (Tomorrow):
"Add IA module - filter prediction and efficiency analytics"
"Add maintenance module - parts tracking and scheduling"
"Add reporting module - daily/weekly/monthly reports"
"Integrate all modules with dashboard"
"Complete application logic hierarchy"
```

---

**Status**: ✓ READY FOR TOMORROW'S DEVELOPMENT
**Estimated Duration**: 6-8 hours
**Expected Completion**: End of Day 2 (January 19, 2026)
