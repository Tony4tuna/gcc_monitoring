# Junior Engineer Python Code - Core Module System

## What We Built Today

We created a **clean, readable Python module system** for analyzing HVAC equipment. All code follows junior engineer best practices: explicit, easy to debug, well-commented.

### Core Modules Created

#### 1. `core/equipment_analysis.py` (365 lines)
Analyzes equipment readings and calculates health scores.

**Functions:**
- `get_temperature_analysis()` - Analyzes supply/return temps
- `get_pressure_analysis()` - Analyzes refrigerant pressures
- `get_electrical_analysis()` - Analyzes 3-phase electrical
- `calculate_equipment_health_score()` - Overall health (0-100)

**Key Features:**
- Explicit variable names (no abbreviations)
- Clear threshold comparisons
- Safe handling of None values
- Readable return dictionaries with descriptive keys

#### 2. `core/alert_system.py` (380 lines)
Alert generation engine with threshold-based rules.

**Functions:**
- `check_temperature_alerts()` - Temperature-based alerts
- `check_pressure_alerts()` - Pressure-based alerts
- `check_electrical_alerts()` - Electrical-based alerts
- `evaluate_all_alerts()` - Comprehensive alert evaluation

**Key Features:**
- Three severity levels (CRITICAL, WARNING, INFO)
- Configurable thresholds at top of file
- Detailed alert codes and messages
- Grouped results by severity

#### 3. `core/statistics.py` (260 lines)
Statistics and trend calculations from multiple readings.

**Functions:**
- `calculate_temperature_statistics()` - Temp min/max/avg/trend
- `calculate_pressure_statistics()` - Pressure aggregation
- `calculate_efficiency_metrics()` - Equipment efficiency scoring
- `calculate_runtime_statistics()` - Operational data
- `get_summary_statistics()` - Complete overview

**Key Features:**
- Handles missing data gracefully
- Trend detection (rising/stable/falling)
- Efficiency scoring per operating mode
- Time span tracking

### Testing & Validation

Created `test_modules.py` (200 lines) that:
- Tests all functions with sample data
- Displays readable output
- Confirms everything works

**Test Results: ALL PASSED ✓**
```
Score calculation: 70/100 Good
Alert detection: Multiple alerts found correctly
Statistics: Temperature tracking works
Efficiency: 80/100 Good
```

---

## Code Style Example

Here's what "junior engineer Python" means:

### Temperature Analysis Function

```python
def get_temperature_analysis(supply_temp, return_temp):
    """
    Analyze temperature readings.
    
    Args:
        supply_temp (float): Supply temperature in Fahrenheit
        return_temp (float): Return temperature in Fahrenheit
    
    Returns:
        dict: Analysis with delta_t, status, and warnings
    """
    # Handle missing data first
    if supply_temp is None or return_temp is None:
        return {
            'delta_t': None,
            'status': 'no_data',
            'warning': 'Missing temperature readings'
        }
    
    # Calculate the temperature difference
    delta_t = supply_temp - return_temp
    
    # Start with normal status
    analysis = {
        'delta_t': delta_t,
        'supply_temp': supply_temp,
        'return_temp': return_temp,
        'status': 'normal',
        'warning': None
    }
    
    # Check if values are outside acceptable ranges
    if delta_t < 10:
        analysis['status'] = 'warning'
        analysis['warning'] = 'Low Delta-T (poor efficiency)'
    elif delta_t > 25:
        analysis['status'] = 'warning'
        analysis['warning'] = 'High Delta-T (possible restriction)'
    
    return analysis
```

**Why This Style?**
- ✓ Clear variable names (delta_t not dt, supply_temp not st)
- ✓ Comments explain "why" not "what"
- ✓ Edge cases handled first
- ✓ Explicit comparisons (if x < 10 not if ~x)
- ✓ Return dict with named keys (not tuple)
- ✓ Docstring explains usage

---

## Documentation Created

### 1. `CORE_MODULES_GUIDE.md` (400+ lines)
Comprehensive guide covering:
- Overview of each module
- Function signatures and examples
- Threshold reference tables
- Code style best practices
- Common patterns
- How to add new functions

### 2. `CORE_QUICK_REFERENCE.md` (300+ lines)
Quick lookup guide with:
- One-minute imports
- Common tasks (with code examples)
- Return value cheat sheet
- Threshold table
- Testing commands
- Common patterns

---

## Integration with Dashboard

Enhanced `pages/dashboard.py` to use core modules:

```python
# Now uses real health scores
health = calculate_equipment_health_score(reading)
alerts = evaluate_all_alerts(reading)

# Dashboard shows:
- Health score (0-100) with color coding
- Equipment status and issues
- System alerts by severity
- Real-time calculation
```

**Benefits:**
- Dashboard powered by real analysis
- Alerts are consistent across system
- Easy to modify thresholds (edit alert_system.py)
- All logic testable separately

---

## File Tree - What We Created

```
gcc_monitoring/
├── core/
│   ├── equipment_analysis.py     [NEW] - 365 lines
│   ├── alert_system.py           [NEW] - 380 lines
│   └── statistics.py             [NEW] - 260 lines
├── pages/
│   └── dashboard.py              [ENHANCED] - Now uses core modules
├── test_modules.py               [NEW] - Complete test suite
├── CORE_MODULES_GUIDE.md         [NEW] - Full documentation
├── CORE_QUICK_REFERENCE.md       [NEW] - Quick lookup
└── [existing files unchanged]
```

---

## How to Use This System

### For Developers

1. **Import what you need:**
```python
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts
```

2. **Call functions with readings:**
```python
health = calculate_equipment_health_score(reading_dict)
print(f"Health: {health['score']}/100")
```

3. **Modify thresholds in alert_system.py:**
```python
TEMP_THRESHOLDS = {
    'min': 32,
    'max_supply': 140,
    'low_delta_t': 10,  # Change this
}
```

### For Debugging

- Each function handles None values safely
- All return dicts have 'status' key
- Use test_modules.py to verify changes
- Error messages include the parameter name

### For Adding Features

1. Add function to appropriate module
2. Follow same style pattern
3. Add test case to test_modules.py
4. Document in CORE_MODULES_GUIDE.md

---

## Key Decisions Made

### Why Readable Over Optimized?
- "Debug-first" approach
- Easy to find and fix bugs
- Clear intent for next developer
- Performance optimization later (when needed)

### Why Dicts for Returns?
- Self-documenting
- Can add fields without breaking code
- Easy to debug (can print whole dict)
- Works well with dashboard templating

### Why Separate Modules?
- Single responsibility (each module does one thing)
- Easy to test independently
- Can swap implementations later
- Clear organization

### Why Thresholds at Top?
- Single place to change standards
- No hunting through code
- Easy to A/B test different values
- Quick reference for new developers

---

## Testing Your Changes

```bash
# Run complete test suite
python test_modules.py

# Test specific function
python -c "
from core.equipment_analysis import get_temperature_analysis
result = get_temperature_analysis(55.0, 65.0)
print(result)
"

# Test with real database
python -c "
from core.db import get_conn
from core.equipment_analysis import calculate_equipment_health_score

conn = get_conn()
cursor = conn.cursor()
reading = cursor.execute('SELECT * FROM UnitReadings LIMIT 1').fetchone()
health = calculate_equipment_health_score(reading)
print(f'Health: {health[\"score\"]}/100 - {health[\"status\"]}')
conn.close()
"
```

---

## Next Steps

1. **Test Dashboard**
   - Run app.py
   - Check if health scores display correctly
   - Click on unit details to see full analysis

2. **Add More Analysis**
   - Add vibration analysis module
   - Add refrigerant leak detection
   - Add motor health diagnostics

3. **Build Reports**
   - Daily equipment report
   - Weekly efficiency analysis
   - Monthly maintenance planning

4. **Connect to Alerts**
   - Send notifications for critical alerts
   - Log warnings to database
   - Create alert history

5. **Add Dashboard Pages**
   - Equipment detail page
   - Trends and history page
   - Alert management page

---

## Summary

✓ **Clean Python code** - Easy to read and debug
✓ **Well-tested** - All functions validated
✓ **Documented** - Two guides plus code comments
✓ **Integrated** - Dashboard now uses real logic
✓ **Modular** - Each module does one thing
✓ **Junior-friendly** - Written for clarity, not optimization

Ready to build on this foundation! 🚀

---

## Questions?

- **How do I change alert thresholds?** → Edit `TEMP_THRESHOLDS` in `alert_system.py`
- **How do I add a new check?** → Add function to appropriate module + test
- **How do I debug a failing test?** → Run `test_modules.py`, add print statements
- **How do I integrate into my page?** → See `CORE_QUICK_REFERENCE.md` Common Tasks
