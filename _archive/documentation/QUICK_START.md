# Quick Start - Core Module System

## 🚀 App is Running!

The app is currently running at:
- **Local**: http://localhost:8080
- **Network**: http://192.168.50.29:8080 (or other network addresses shown)

## 📊 What's Working

✓ **Dashboard** - Shows equipment health scores
✓ **Core Modules** - Equipment analysis, alerts, statistics
✓ **Test Data Generator** - Running in background, generating realistic HVAC data
✓ **Database Integration** - Real data from SQLite

## 🎯 What You Can Do Now

### 1. View Dashboard
- Open http://localhost:8080 in your browser
- See equipment status with health scores (0-100)
- Click on units to see detailed analysis
- View alerts and issues

### 2. Test Core Modules
```bash
# Run all tests
python test_modules.py

# Test specific analysis
python -c "from core.equipment_analysis import calculate_equipment_health_score; print(calculate_equipment_health_score({'supply_temp': 55.0, 'return_temp': 65.0, 'mode': 'Cooling'}))"
```

### 3. Modify Thresholds
Edit `core/alert_system.py` to change thresholds:
```python
TEMP_THRESHOLDS = {
    'min': 32,          # Freezing point
    'max_supply': 140,  # Max supply temp
    'low_delta_t': 10,  # Low efficiency threshold
    'high_delta_t': 25,
}
```

## 📁 Key Files to Know

### Core Logic
- `core/equipment_analysis.py` - Equipment health analysis
- `core/alert_system.py` - Alert generation
- `core/statistics.py` - Statistics and aggregation

### Dashboard
- `pages/dashboard.py` - Main dashboard UI (uses core modules)

### Documentation
- `CORE_QUICK_REFERENCE.md` - Quick lookup (start here!)
- `CORE_MODULES_GUIDE.md` - Complete API documentation
- `JUNIOR_ENGINEER_GUIDE.md` - Code style guide

### Testing
- `test_modules.py` - All unit tests

## 💡 Common Tasks

### Get Equipment Health Score
```python
from core.equipment_analysis import calculate_equipment_health_score

reading = {
    'supply_temp': 55.0,
    'return_temp': 65.0,
    'discharge_psi': 280,
    'suction_psi': 75,
    'v_1': 25.0,
    'v_2': 24.0,
    'v_3': 26.0,
    'compressor_amps': 28.0,
    'mode': 'Cooling',
    'fault_code': None
}

health = calculate_equipment_health_score(reading)
print(f"Score: {health['score']}/100 - {health['status']}")
# Output: Score: 70/100 - Good
```

### Get All Alerts
```python
from core.alert_system import evaluate_all_alerts

alerts = evaluate_all_alerts(reading)
print(f"Critical: {len(alerts['critical'])}")
print(f"Warnings: {len(alerts['warning'])}")
print(f"Info: {len(alerts['info'])}")

for alert in alerts['critical']:
    print(f"  {alert['code']}: {alert['message']}")
```

### Get Statistics
```python
from core.statistics import get_summary_statistics

# readings should be a list of reading dicts
summary = get_summary_statistics(readings)
print(f"Avg supply temp: {summary['temperature']['supply']['avg']}°F")
print(f"Cooling efficiency: {summary['cooling_efficiency']['score']}/100")
```

## 🐛 Debugging

### If app won't start:
```bash
# Check Python version
python --version

# Run test modules first
python test_modules.py

# Check imports
python -c "from core.equipment_analysis import calculate_equipment_health_score; print('OK')"
```

### If dashboard is blank:
- Check browser console (F12) for errors
- Verify database has readings: `SELECT COUNT(*) FROM UnitReadings;`
- Check logs for import errors

### If alerts aren't showing:
- Edit thresholds in `core/alert_system.py`
- Run test: `python test_modules.py` to verify alert logic
- Check equipment readings are above minimum

## 📚 Learning Path

1. **Start here**: `CORE_QUICK_REFERENCE.md` (5 min read)
2. **Common patterns**: `CORE_QUICK_REFERENCE.md` - Common Tasks section
3. **Code examples**: Look at `test_modules.py` for usage patterns
4. **Deep dive**: `CORE_MODULES_GUIDE.md` for detailed API
5. **Code style**: `JUNIOR_ENGINEER_GUIDE.md` if you want to add features

## 🔧 Extending the System

### Add a New Analysis Function
1. Add function to appropriate `core/` module
2. Follow existing code pattern (docstrings, error handling)
3. Add test case to `test_modules.py`
4. Document in `CORE_MODULES_GUIDE.md`

### Example:
```python
def analyze_vibration(motor_amps, compressor_amps):
    """
    Analyze compressor vibration indicators.
    
    Args:
        motor_amps (float): Motor current
        compressor_amps (float): Compressor current
    
    Returns:
        dict: Vibration analysis with status
    """
    motor_amps = _to_float(motor_amps)
    compressor_amps = _to_float(compressor_amps)
    
    if motor_amps is None:
        return {'status': 'no_data'}
    
    # Your analysis here...
    return {
        'status': 'normal',
        'warning': None
    }
```

## 🎓 Code Quality Standards

All code follows these principles:

1. **Explicit is Better** - Clear variable names, no abbreviations
2. **Handles Errors** - None values, type conversions handled
3. **Well Documented** - Docstrings for all functions
4. **Testable** - Functions are independent
5. **Debuggable** - Print shows full dicts, not cryptic output

## 📈 What's Next

After understanding the core modules:

1. **Integrate notifications** - Send alerts via email/SMS
2. **Build reports** - Daily/weekly efficiency reports
3. **Add trends** - Track performance over time
4. **Equipment detail pages** - Deep analysis per unit
5. **Historical data** - Archive and analyze old readings

## 🆘 Need Help?

**Error: `'sqlite3.Row' object has no attribute 'get'`**
- Converting Row to dict: `reading_dict = dict(reading)`

**Error: `TypeError: unsupported operand type(s) for -: 'str' and 'str'`**
- Database returns strings, convert to float: `temp = float(value)`

**Error: `Module not found`**
- Check imports match file structure
- Verify venv is activated
- Run `python test_modules.py` first to check imports

**Dashboard shows no data:**
- Verify test data generator is running
- Check database has UnitReadings: `sqlite3 data/app.db "SELECT COUNT(*) FROM UnitReadings;"`
- Check database permissions

## 📞 Support

For detailed help:
- See `CORE_MODULES_GUIDE.md` for API reference
- See `CORE_QUICK_REFERENCE.md` for common tasks
- Check `test_modules.py` for working examples
- Read `JUNIOR_ENGINEER_GUIDE.md` for code patterns

---

## Summary

✓ App is running successfully
✓ Core modules are loaded
✓ Dashboard is working
✓ Test data is generating
✓ Everything is integrated and ready

**Start by viewing the dashboard, then explore the core modules!**
