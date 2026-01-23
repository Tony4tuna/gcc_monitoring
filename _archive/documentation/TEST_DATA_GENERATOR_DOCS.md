# Test Data Generator Documentation

## Overview
The **test_data_generator.py** script simulates realistic HVAC/R equipment monitoring data for development and testing purposes. It continuously generates sensor readings that mimic real equipment behavior, including normal operation, faults, and efficiency issues.

**Created**: January 18, 2026  
**Purpose**: Enable full-stack testing without real hardware  
**Status**: Active development tool

---

## How It Works

### 1. Data Generation Process

```
Start Generator → Loop Every 60 Seconds → Generate Data for Each Unit → Insert to DB
                                              ↓
                                     Choose Operating Mode
                                     (Off/Idle/Cooling/Heating/Economizer/Fault)
                                              ↓
                                     Generate Realistic Parameters
                                     Based on Mode & Environmental Conditions
                                              ↓
                                     3-5% Chance of Injecting Faults
                                     (Low ΔT, High Discharge Temp, etc.)
                                              ↓
                                     Insert Complete Row to UnitReadings
```

### 2. Operating Modes & Probabilities

| Mode | Probability | Supply Temp | Characteristics |
|------|-------------|------------|-----------------|
| **Cooling** | 45% | 52-60°F | High fan speed, pressure cycling |
| **Heating** | 20% | 95-115°F | Lower fan speed, heat rise |
| **Idle** | 15% | Ambient ±2°F | No compressor, minimal fan |
| **Off** | 10% | Ambient | Zero power draw |
| **Economizer** | 7% | Outdoor ±5°F | Free cooling, low energy |
| **Fault** | 3% | Varies | Abnormal readings, fault codes |

### 3. Fault Injection

~3% of readings include faults for testing alarm/alert systems:

```
Fault Codes:
  - LOW_PRESSURE: Suction PSI drops to 15-35 (charge loss)
  - HIGH_DISCHARGE_TEMP: Pressure spikes to 380-450 PSI (restriction)
  - LOW_DELTA_T: ΔT only 8-12°F (efficiency issue)
  - MOTOR_FAULT: Motor issues
  - COMPRESSOR_FAULT: Compressor problems
  - SENSOR_ERROR: Sensor malfunction
```

When fault is triggered:
- `unit_status` → "Error"
- `fault_code` → Specific code
- `alarm_status` → "Active"
- `alert_message` → Description
- Related readings reflect the fault condition

### 4. Realistic Parameter Ranges

**Temperature:**
```
Cooling Mode:
  Supply: 52-60°F (target 55°F)
  Return: 70-80°F (typical indoor)
  ΔT: 12-20°F (normal 15-18°F)

Heating Mode:
  Supply: 95-115°F (furnace output)
  Return: 65-75°F
  ΔT: 30-50°F (heat rise)
```

**Pressure (R-410A Reference):**
```
Cooling @ 95°F outdoor:
  Suction: 60-100 PSI
  Discharge: 250-350 PSI
  Superheat: 8-15°F (target 10°F)
  Subcooling: 8-12°F (target 10°F)
```

**Electrical (Three-Phase):**
```
Voltage: 235-245V per phase (nominal 240V)
Amperage: 15-45A per phase (varies by load)
Imbalance: ±2V between phases (simulates real wiring)
```

---

## Running the Generator

### Quick Start
```bash
cd c:\Users\Public\GCC_Monitoring\gcc_monitoring
.\venv\Scripts\python.exe test_data_generator.py
```

**Output:**
```
======================================================================
HVAC/R TEST DATA GENERATOR
======================================================================
Target database: data/app.db
Units: [1, 2, 3, 4]
Generating realistic HVAC monitoring data for testing

======================================================================
Generating batch #1 at 2026-01-18 14:32:15
======================================================================
✅ Unit 1: Reading inserted (total: 1)
✅ Unit 2: Reading inserted (total: 1)
✅ Unit 3: Reading inserted (total: 1)
✅ Unit 4: Reading inserted (total: 1)
Batch complete. Total readings: 4
Unit breakdown: {1: 1, 2: 1, 3: 1, 4: 1}
Next batch in 60 seconds...
```

### Configuration Options

Edit `test_data_generator.py`, line ~350:

```python
# Run for specified duration (in minutes)
generator.run_continuous(interval_seconds=60, duration_minutes=60)  # 1 hour

# Run indefinitely (until Ctrl+C)
generator.run_continuous(interval_seconds=60, duration_minutes=None)

# Change interval to every 15 seconds for faster testing
generator.run_continuous(interval_seconds=15, duration_minutes=None)

# Quick test: 5 minutes
generator.run_continuous(interval_seconds=60, duration_minutes=5)
```

### Stop the Generator
Press **Ctrl+C** in terminal. It will gracefully shutdown and print summary:

```
======================================================================
GENERATION STOPPED BY USER
======================================================================
Total readings generated: 240
Readings per unit:
  Unit 1: 60 readings
  Unit 2: 60 readings
  Unit 3: 60 readings
  Unit 4: 60 readings
Average: 60 per unit
======================================================================
```

---

## Log Files

All operations are logged to `logs/test_data_generator_YYYYMMDD_HHMMSS.log`

**Log Levels:**
- **INFO**: Batch start/complete, summary statistics
- **DEBUG**: Individual reading inserts (verbose, includes all sensor values)
- **WARNING**: Skipped readings
- **ERROR**: Insert failures, database issues

### Viewing Logs
```bash
# View latest log
Get-Content -Path "logs\test_data_generator_*.log" -Tail 100

# Tail log in real-time
Get-Content -Path "logs\test_data_generator_*.log" -Wait
```

---

## Data Verification

### Check How Many Readings Exist
```bash
.\venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM UnitReadings')
print(f'Total readings: {cursor.fetchone()[0]}')
cursor.execute('SELECT unit_id, COUNT(*) FROM UnitReadings GROUP BY unit_id')
for unit_id, count in cursor.fetchall():
    print(f'  Unit {unit_id}: {count}')
conn.close()
"
```

### Sample Recent Reading
```bash
.\venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM UnitReadings ORDER BY reading_id DESC LIMIT 1')
row = cursor.fetchone()
print('Latest reading:')
for key in row.keys():
    val = row[key]
    if val is not None:
        print(f'  {key}: {val}')
conn.close()
"
```

### Check Fault Injection Rate
```bash
.\venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as total FROM UnitReadings')
total = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) as faults FROM UnitReadings WHERE fault_code IS NOT NULL')
faults = cursor.fetchone()[0]
if total > 0:
    rate = (faults / total) * 100
    print(f'Total readings: {total}')
    print(f'Readings with faults: {faults}')
    print(f'Fault injection rate: {rate:.1f}%')
conn.close()
"
```

---

## Integration with Application

### 1. Display in Dashboard
The test data will automatically appear in your monitoring dashboard when you run the app:

```python
# pages/dashboard.py will query:
SELECT * FROM UnitReadings 
ORDER BY ts DESC LIMIT 4  # Latest reading per unit
```

### 2. Test Alarm Logic
Create alerts based on readings:

```python
# Example: Alert when ΔT is low
if reading['delta_t'] and float(reading['delta_t']) < 14.0 and reading['mode'] == 'Cooling':
    # Trigger "Low Delta T" alert
```

### 3. Test Real-time Updates
NiceGUI pages will see live data as readings are inserted.

---

## Transitioning to Real Data

When ready to use actual equipment data:

### Option 1: Replace Insert Logic
Modify `insert_reading()` to read from real equipment API/sensor instead of generator:

```python
def insert_reading(self, unit_id: int):
    # Instead of:
    data = self.get_realistic_data(unit_id, mode)
    
    # Use real data:
    data = fetch_from_real_equipment(unit_id)  # Your API call
    # ... rest of code remains same
```

### Option 2: Import CSV Data
Create a separate import script to load CSV files from equipment loggers.

### Option 3: Hybrid Approach
Keep generator for units without real hardware, use real data for others.

---

## Debugging & Troubleshooting

### Issue: Generator Runs But No Data Appears

**Check:**
1. Is database writable?
   ```bash
   Test-Path -Path "data/app.db"
   ```

2. Are there connection errors?
   ```bash
   Get-Content "logs/test_data_generator_*.log" | Select-String "ERROR"
   ```

3. Verify foreign key exists:
   ```bash
   .\venv\Scripts\python.exe -c "
   import sqlite3
   conn = sqlite3.connect('data/app.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM Units')
   print(f'Units in database: {cursor.fetchone()[0]}')
   conn.close()
   "
   ```

### Issue: Want to Clear Test Data

**Safe approach (keeps backup):**
```bash
# Stop generator (Ctrl+C)

# Backup current test data
Copy-Item data/app.db data/app.db.test_backup

# Restore from clean backup
Copy-Item data/app.db.backup data/app.db

# Restart generator
.\venv\Scripts\python.exe test_data_generator.py
```

### Issue: Modify Generation Parameters

**Edit in test_data_generator.py:**
```python
# Line 64: Change mode probabilities
MODE_WEIGHTS = {
    "Off": 0.05,          # More cooling, less idle
    "Idle": 0.05,
    "Cooling": 0.70,      # ← Increased from 0.45
    "Heating": 0.10,
    "Economizer": 0.05,
    "Fault": 0.05,        # ← More faults for testing alerts
}

# Line 80: Adjust temperature ranges
if mode == "Cooling":
    supply_temp = random.uniform(48.0, 62.0)  # ← Wider range for testing
```

---

## Performance Notes

### Data Volume
- **4 units × 1 reading/minute** = 5,760 readings/day
- **4 units × 1 reading/10 seconds** = 34,560 readings/day
- **1 week**: ~40,000 readings (small database, <5MB)
- **1 month**: ~170,000 readings (~20MB)

### Database Optimization
- Indexed queries are fast on `(unit_id, ts)`
- For large archives, consider:
  - Monthly partitioning
  - Archive old readings to separate table
  - Aggregate historical data

### Dashboard Impact
- Latest 4 readings (one per unit) = minimal load
- Historical charts (1 week) = scan index, very fast
- Year-long trend = may need aggregation

---

## Reference Data

### Unit Configuration (from database)
```
Unit 1: Carrier 50XC (Cooling) @ Location 1
Unit 2: Trane XR15 (Heat Pump) @ Location 2
Unit 3: Lennox XC21 (Cooling) @ Location 3
Unit 4: York YVAA (Cooling) @ Location 4
```

### Column Mapping
See [HVAC_PARAMETERS.md](HVAC_PARAMETERS.md) for complete field descriptions.

---

## Future Enhancements

Potential improvements when transitioning to production:

- [ ] API integration for real equipment communication
- [ ] Batch import from CSV/Excel
- [ ] Data validation rules before insert
- [ ] Automatic fault detection algorithms
- [ ] Time-series compression for archived data
- [ ] Multi-facility load balancing simulation

---

## Support & Questions

When debugging data issues, check:
1. **Log file** (`logs/test_data_generator_*.log`)
2. **Database schema** (PRAGMA table_info(UnitReadings))
3. **Sample data** (SELECT * FROM UnitReadings LIMIT 5)
4. **Unit count** (SELECT COUNT(*) FROM Units)

All test data uses realistic ranges matching EPA 608 HVAC standards.
