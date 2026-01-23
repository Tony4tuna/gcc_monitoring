# Core Module Documentation - Junior Engineer Guide

## Overview

The `core/` modules provide clean, readable Python functions for analyzing HVAC equipment. All code is written with **clarity first** - easy to read, understand, and debug.

## Module Structure

### 1. `equipment_analysis.py` - Equipment Diagnostics

**Purpose:** Analyze individual parameter readings and identify issues.

**Functions:**

#### `get_temperature_analysis(supply_temp, return_temp)`
Analyzes temperature readings and calculates efficiency.

```python
# Usage:
result = get_temperature_analysis(55.0, 65.0)

# Returns:
{
    'delta_t': -10.0,           # Temperature difference
    'supply_temp': 55.0,
    'return_temp': 65.0,
    'status': 'warning',        # normal, warning, no_data
    'warning': 'Low Delta-T...' # Human-readable message
}
```

**Key Logic:**
- Delta-T (ΔT) = Supply - Return
- Normal cooling: ΔT between 10-25°F
- Low ΔT = poor efficiency or high airflow
- High ΔT = possible blockage/low airflow

#### `get_pressure_analysis(discharge_psi, suction_psi, mode)`
Analyzes refrigerant system pressures.

```python
# Usage:
result = get_pressure_analysis(280, 75, 'Cooling')

# Checks:
- Discharge pressure: 100-400 PSI (typical)
- Suction pressure: 20-150 PSI (typical)
- Pressure ratio: discharge/suction
  - Cooling: ratio should be 4-6
  - Heating: ratio should be 3-5
```

**Returns:** Same structure as temperature analysis

#### `get_electrical_analysis(phase_1, phase_2, phase_3, compressor_amps)`
Analyzes 3-phase electrical system.

```python
# Usage:
result = get_electrical_analysis(25.0, 24.0, 26.0, 28.0)

# Checks:
- Phase balance: All phases within ~5% of average
- Individual overload: Each phase <50A
- Compressor overload: Comp amps vs average phase amps
```

#### `calculate_equipment_health_score(readings)`
Comprehensive health scoring (0-100).

```python
# Usage:
health = calculate_equipment_health_score(reading_dict)

# Returns:
{
    'score': 75,           # 0-100
    'status': 'Good',      # Excellent, Good, Fair, Poor, Critical
    'issues': [...],       # List of problems
    'temperature': {...},  # Sub-analysis
    'pressure': {...},
    'electrical': {...}
}

# Scoring breakdown:
# 100-80: Excellent
# 80-60: Good
# 60-40: Fair
# 40-20: Poor
# 20-0: Critical
```

---

### 2. `alert_system.py` - Alert Generation

**Purpose:** Evaluate readings against thresholds and generate actionable alerts.

**Key Concept:** Alerts have 3 severity levels:
- `ALERT_CRITICAL` - System failure risk, immediate action needed
- `ALERT_WARNING` - Performance issue or developing problem
- `ALERT_INFO` - Informational, monitor but not urgent

**Functions:**

#### `check_temperature_alerts(supply_temp, return_temp, mode)`
Temperature-based alerts.

```python
# Usage:
alerts = check_temperature_alerts(55.0, 65.0, 'Cooling')

# Returns: List of alert dicts
# [
#   {
#       'severity': 'warning',
#       'code': 'LOW_DELTA_T',
#       'message': 'Low Delta-T (5.0°F) - Poor efficiency',
#       'parameter': 'delta_t'
#   },
#   ...
# ]
```

**Thresholds:**
- Freezing: < 32°F (CRITICAL)
- Overheating: > 140°F (WARNING)
- Low ΔT: < 10°F in Cooling/Heating (WARNING)
- High ΔT: > 25°F (INFO)

#### `check_pressure_alerts(discharge_psi, suction_psi, mode)`
Refrigerant pressure alerts.

**Thresholds:**
- Discharge: 100-400 PSI
- Suction: 20-150 PSI
- Ratio: 3-7x (outside indicates imbalance)

#### `check_electrical_alerts(phase_1, phase_2, phase_3, compressor_amps)`
Electrical system alerts.

**Thresholds:**
- Individual phase: < 50A
- Phase imbalance: < 10%
- Compressor overload: < 20% above average

#### `evaluate_all_alerts(reading)`
Comprehensive alert evaluation for one reading.

```python
# Usage:
all_alerts = evaluate_all_alerts(reading_dict)

# Returns:
{
    'critical': [...],    # Critical alerts
    'warning': [...],     # Warnings
    'info': [...],        # Info alerts
    'all': [...],         # All combined
    'count': 3            # Total alert count
}
```

---

### 3. `statistics.py` - Data Aggregation

**Purpose:** Calculate meaningful statistics from multiple readings.

**Functions:**

#### `calculate_temperature_statistics(readings_list)`
Aggregate temperature data.

```python
# Usage:
stats = calculate_temperature_statistics([reading1, reading2, ...])

# Returns:
{
    'supply': {
        'min': 50.0,
        'max': 60.0,
        'avg': 55.2,
        'count': 20
    },
    'return': {...},
    'delta_t': {...},
    'trend': 'rising'      # rising, stable, falling
}
```

#### `calculate_pressure_statistics(readings_list)`
Aggregate pressure data.

Returns min/max/avg for:
- Discharge pressure
- Suction pressure
- Superheat
- Subcooling

#### `calculate_efficiency_metrics(readings_list, mode='Cooling')`
Equipment efficiency scoring.

```python
# Usage:
efficiency = calculate_efficiency_metrics(readings, 'Cooling')

# Returns:
{
    'mode': 'Cooling',
    'readings_count': 20,
    'score': 85,         # 0-100
    'status': 'Good',    # Excellent, Good, Fair, Poor
    'issues': [...]      # What's affecting score
}

# Analyzed for efficiency:
# - Delta-T consistency (should be 12-20°F for cooling)
# - Superheat stability (±5°F is ideal)
# - Compressor load consistency
```

#### `calculate_runtime_statistics(readings_list)`
Operational statistics.

```python
# Returns:
{
    'total_readings': 50,
    'modes': {'Cooling': 30, 'Idle': 20},
    'cumulative_runtime_hours': 1250.5,
    'fault_rate_percent': 2.5,
    'most_common_mode': 'Cooling'
}
```

#### `get_summary_statistics(readings_list)`
Complete statistics package.

```python
# Usage:
summary = get_summary_statistics(readings_list)

# Returns all of above combined:
{
    'readings_count': 100,
    'temperature': {...},
    'pressure': {...},
    'cooling_efficiency': {...},
    'heating_efficiency': {...},
    'runtime': {...},
    'time_span': {
        'first': '2026-01-18T10:00:00',
        'last': '2026-01-18T15:00:00'
    }
}
```

---

## Using Modules in Code

### Example 1: Analyze a Single Reading

```python
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts

# Get reading from database (assume we have this)
reading = get_reading_from_db(unit_id=1)

# Analyze health
health = calculate_equipment_health_score(reading)
print(f"Unit health: {health['score']}/100 - {health['status']}")

# Get alerts
alerts = evaluate_all_alerts(reading)
for alert in alerts['critical']:
    send_notification(alert['message'])
```

### Example 2: Get Equipment Statistics

```python
from core.statistics import get_summary_statistics

# Get last 100 readings for a unit
readings = get_readings_from_db(unit_id=1, limit=100)

# Calculate summary
summary = get_summary_statistics(readings)

# Display results
print(f"Average supply temp: {summary['temperature']['supply']['avg']}°F")
print(f"Cooling efficiency: {summary['cooling_efficiency']['score']}/100")
print(f"Runtime: {summary['runtime']['cumulative_runtime_hours']} hours")
```

### Example 3: Dashboard Display

```python
# For each unit, show health card
for unit_id in unit_list:
    reading = get_latest_reading(unit_id)
    health = calculate_equipment_health_score(reading)
    
    # Display
    color = 'green' if health['score'] >= 80 else 'yellow' if health['score'] >= 60 else 'red'
    print(f"Unit {unit_id}: {health['score']}/100 [{color}]")
    
    for issue in health['issues']:
        print(f"  - {issue}")
```

---

## Testing Modules

Run the test script to verify everything works:

```bash
python test_modules.py
```

This will:
1. Test each function with sample data
2. Display results
3. Confirm all functions work correctly

---

## Understanding the Code Style

All modules follow **junior engineer best practices:**

### 1. **Explicit is Better Than Implicit**
```python
# GOOD: Clear what's happening
delta_t = supply_temp - return_temp
if delta_t < 10:
    status = 'warning'

# Avoid: Magic numbers and unclear logic
if a - b < 10: x = 'w'
```

### 2. **Names Matter**
```python
# GOOD: Names tell the story
supply_temps = [r['supply_temp'] for r in readings]
avg_supply = sum(supply_temps) / len(supply_temps)

# Avoid: Cryptic names
st = [r['st'] for r in rs]
a = sum(st) / len(st)
```

### 3. **Comments for "Why", Not "What"**
```python
# GOOD: Explains reasoning
# Check pressure ratio - normal range is 3-7
# Outside this indicates a system problem
if ratio < 3 or ratio > 7:
    alerts.append(...)

# Avoid: Obvious comments
# Set ratio
ratio = discharge / suction
```

### 4. **Handle Edge Cases**
```python
# GOOD: Explicit handling
if not temps:
    return {'avg': None}

supply_values = [r for r in readings if r.get('supply_temp') is not None]
if supply_values:
    avg = sum(supply_values) / len(supply_values)
```

### 5. **Return Dicts with Keys**
```python
# GOOD: Easy to understand what's in return value
return {
    'score': 75,
    'status': 'Good',
    'issues': ['Low Delta-T']
}

# Avoid: Returning tuples that lose meaning
return (75, 'Good', ['Low Delta-T'])
```

---

## Adding New Functions

When adding functions, follow this template:

```python
def function_name(param1, param2):
    """
    One-line description of what function does.
    
    Args:
        param1 (type): Description
        param2 (type): Description
    
    Returns:
        dict or list: Description of return value
    """
    
    # Initialize return structure
    result = {
        'status': 'normal',
        'value': None,
        'warning': None
    }
    
    # Handle edge cases first
    if param1 is None:
        result['status'] = 'no_data'
        return result
    
    # Do calculation
    value = param1 + param2
    
    # Check against thresholds
    if value > 100:
        result['status'] = 'warning'
        result['warning'] = 'Value exceeded 100'
    else:
        result['value'] = value
    
    return result
```

---

## Next Steps

1. **Integrate into Dashboard** - Import functions and display health scores
2. **Database Integration** - Load readings and calculate statistics
3. **Real-time Alerts** - Check readings as they come in
4. **Historical Reports** - Generate trend reports from statistics

Each module is independent and can be tested separately!
