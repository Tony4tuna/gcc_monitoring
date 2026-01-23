# Quick Reference - Core Module Usage

## One-Minute Imports

```python
# Equipment Analysis
from core.equipment_analysis import (
    get_temperature_analysis,
    get_pressure_analysis,
    get_electrical_analysis,
    calculate_equipment_health_score
)

# Alert System
from core.alert_system import (
    check_temperature_alerts,
    check_pressure_alerts,
    check_electrical_alerts,
    evaluate_all_alerts
)

# Statistics
from core.statistics import (
    calculate_temperature_statistics,
    calculate_efficiency_metrics,
    get_summary_statistics
)
```

---

## Common Tasks

### Task 1: Check if Equipment is Healthy

```python
# Get latest reading
reading = cursor.execute(
    "SELECT * FROM UnitReadings WHERE unit_id = ? ORDER BY reading_id DESC LIMIT 1",
    (unit_id,)
).fetchone()

# Calculate health
health = calculate_equipment_health_score(reading)

# Use results
if health['score'] >= 80:
    print("Equipment is good")
elif health['score'] >= 60:
    print("Watch for issues:")
    for issue in health['issues']:
        print(f"  - {issue}")
else:
    print("CRITICAL ISSUES:")
    for issue in health['issues']:
        print(f"  - {issue}")
```

### Task 2: Get Latest Alerts for a Unit

```python
# Get latest reading
reading = get_latest_reading(unit_id)

# Evaluate alerts
alerts = evaluate_all_alerts(reading)

# Display by severity
if alerts['critical']:
    print("CRITICAL ALERTS:")
    for alert in alerts['critical']:
        print(f"  {alert['code']}: {alert['message']}")

if alerts['warning']:
    print("WARNINGS:")
    for alert in alerts['warning']:
        print(f"  {alert['code']}: {alert['message']}")
```

### Task 3: Analyze Temperature Trend

```python
# Get readings from last 24 hours
readings = get_readings_from_db(
    unit_id=unit_id,
    hours=24
)

# Calculate statistics
stats = calculate_temperature_statistics(readings)

# Display
print(f"Temperature: {stats['supply']['min']}°F - {stats['supply']['max']}F")
print(f"Average: {stats['supply']['avg']}°F")
print(f"Trend: {stats['trend']}")
```

### Task 4: Check Equipment Efficiency

```python
# Get readings
readings = get_readings_from_db(unit_id=unit_id, hours=12)

# Calculate efficiency
efficiency = calculate_efficiency_metrics(readings, 'Cooling')

# Use
print(f"Cooling Efficiency: {efficiency['score']}/100")
if efficiency['issues']:
    for issue in efficiency['issues']:
        print(f"  Issue: {issue}")
```

### Task 5: Get Complete Equipment Overview

```python
# Get readings (last 100)
readings = get_readings_from_db(unit_id=unit_id, limit=100)

# Get everything
summary = get_summary_statistics(readings)

# Display
print(f"Unit {unit_id}")
print(f"  Total readings: {summary['readings_count']}")
print(f"  Runtime: {summary['runtime']['cumulative_runtime_hours']} hours")
print(f"  Supply temp: {summary['temperature']['supply']['avg']}°F (avg)")
print(f"  Cooling: {summary['cooling_efficiency']['score']}/100")
print(f"  Heating: {summary['heating_efficiency']['score']}/100")
```

---

## Return Value Cheat Sheet

### Health Score
```python
{
    'score': 75,                    # 0-100
    'status': 'Good',               # Good, Fair, Poor, etc
    'issues': ['Low Delta-T', ...], # List of problems
    'temperature': {...},           # Sub-analysis
    'pressure': {...},
    'electrical': {...}
}
```

### Alerts
```python
{
    'severity': 'warning',          # critical, warning, info
    'code': 'LOW_DELTA_T',          # Alert code
    'message': 'Low Delta-T...',    # Human readable
    'parameter': 'delta_t'          # What parameter triggered it
}
```

### Temperature Stats
```python
{
    'supply': {'min': 50, 'max': 60, 'avg': 55, 'count': 20},
    'return': {...},
    'delta_t': {...},
    'trend': 'rising'               # rising, stable, falling
}
```

---

## Thresholds Reference

### Temperature
| Parameter | Good | Warning |
|-----------|------|---------|
| Supply Temp | 32-140°F | <32 or >140°F |
| Delta-T (Cooling) | 10-25°F | <10 or >25°F |
| Delta-T (Heating) | 8-20°F | <8 or >20°F |

### Pressure
| Parameter | Good | Warning |
|-----------|------|---------|
| Discharge PSI | 100-400 | <100 or >400 |
| Suction PSI | 20-150 | <20 or >150 |
| Pressure Ratio | 3-7 | <3 or >7 |

### Electrical
| Parameter | Good | Warning |
|-----------|------|---------|
| Phase Balance | <5% variation | >10% |
| Phase Current | <50A per phase | >50A |
| Compressor Load | ±10% of avg | >20% above avg |

---

## Testing Individual Functions

```bash
# Run full test suite
python test_modules.py

# Test specific analysis
python -c "
from core.equipment_analysis import get_temperature_analysis
result = get_temperature_analysis(55.0, 65.0)
print(result)
"
```

---

## Common Patterns

### Pattern 1: Get Health and Alerts for Dashboard

```python
def get_unit_status(unit_id):
    reading = get_latest_reading(unit_id)
    
    health = calculate_equipment_health_score(reading)
    alerts = evaluate_all_alerts(reading)
    
    return {
        'health_score': health['score'],
        'health_status': health['status'],
        'critical_alerts': len(alerts['critical']),
        'warnings': len(alerts['warning'])
    }
```

### Pattern 2: Generate Equipment Report

```python
def generate_unit_report(unit_id, hours=24):
    readings = get_readings_from_db(unit_id, hours=hours)
    summary = get_summary_statistics(readings)
    
    report = {
        'unit_id': unit_id,
        'period_hours': hours,
        'readings': summary['readings_count'],
        'supply_temp_avg': summary['temperature']['supply']['avg'],
        'cooling_score': summary['cooling_efficiency']['score'],
        'runtime_hours': summary['runtime']['cumulative_runtime_hours'],
        'issues': summary['cooling_efficiency']['issues']
    }
    
    return report
```

### Pattern 3: Real-time Alert Monitoring

```python
def check_reading_for_alerts(reading):
    alerts = evaluate_all_alerts(reading)
    
    # Notify on critical
    if alerts['critical']:
        send_alert_notification(
            unit_id=reading['unit_id'],
            severity='CRITICAL',
            messages=[a['message'] for a in alerts['critical']]
        )
    
    # Log warnings
    if alerts['warning']:
        log_warning(
            unit_id=reading['unit_id'],
            alerts=[a['code'] for a in alerts['warning']]
        )
```

---

## Debugging Tips

### Issue: Wrong Alert Thresholds?
Check `core/alert_system.py` top section:
```python
TEMP_THRESHOLDS = {...}
PRESSURE_THRESHOLDS = {...}
ELECTRICAL_THRESHOLDS = {...}
```

### Issue: Different Health Scores?
Check `calculate_equipment_health_score()` - each category has point deduction.

### Issue: Missing Data Handling?
All functions check for `None` values and return `'no_data'` status safely.

### Run Tests to Verify
```bash
python test_modules.py
```

---

## Next: Integrate into Dashboard

Once you're comfortable with the modules, integrate into `pages/dashboard.py`:

```python
# At top of file
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts

# In get_unit_stats() function
def get_unit_stats():
    # ... existing code ...
    
    for unit in units:
        health = calculate_equipment_health_score(unit)
        alerts = evaluate_all_alerts(unit)
        
        # Use health['score'] for coloring
        # Use alerts['critical'] for notifications
```

Start simple, add features gradually! 🚀
