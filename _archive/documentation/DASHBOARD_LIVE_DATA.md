# What the Dashboard is Reading - Live Data Summary

## Current Dashboard Display

Based on the latest readings from the database:

```
DASHBOARD METRICS (Top 4 Cards)
════════════════════════════════════════════════════════════════

┌─────────────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────────────┐
│ Active Units    │  │ Warnings     │  │ Faults   │  │ Avg Supply Temp   │
│       0         │  │      1       │  │    2     │  │      56.1°F        │
│  Online now     │  │ Need attn.   │  │ Critical │  │   Across site      │
└─────────────────┘  └──────────────┘  └──────────┘  └───────────────────┘
    (GREEN)            (YELLOW)           (RED)          (BLUE)
```

---

## Equipment Status Table

```
┌──────┬──────────────────┬──────────┬────────┬─────────┬────────────────────┐
│ Unit │ Equipment        │ Mode     │ Supply │ ΔT      │ Fault Code        │
├──────┼──────────────────┼──────────┼────────┼─────────┼────────────────────┤
│ 2    │ York 12344       │ Cooling  │ 53.9°F │ 9.4°F   │ LOW_DELTA_T       │
│      │ Health: 50/100   │          │        │ ⚠️ LOW  │                    │
│      │ Status: FAIR     │          │        │         │                    │
├──────┼──────────────────┼──────────┼────────┼─────────┼────────────────────┤
│ 3    │ Trane-4 RTU      │ Cooling  │ 55.0°F │ -24.1°F │ HIGH_DISCHARGE_TEMP│
│      │ Health: 50/100   │          │        │ ⚠️ HIGH │                    │
│      │ Status: FAIR     │          │        │         │                    │
├──────┼──────────────────┼──────────┼────────┼─────────┼────────────────────┤
│ 4    │ ggggg ggggg      │ Idle     │ 59.4°F │ 0.0°F   │ HIGH_DISCHARGE_TEMP│
│      │ Health: 65/100   │          │        │ ⚠️ IDLE │                    │
│      │ Status: GOOD     │          │        │         │                    │
└──────┴──────────────────┴──────────┴────────┴─────────┴────────────────────┘
```

---

## Alerts Sidebar

```
ALERTS & ACTIVITY
═══════════════════════════════════════════════════════════

🔴 CRITICAL ALERTS:
   ├─ Unit 2: UNIT_FAULT - Unit fault: LOW_DELTA_T
   ├─ Unit 3: HIGH_DISCHARGE_PSI - High discharge pressure 425.4 PSI
   └─ Unit 4: HIGH_DISCHARGE_PSI - High discharge pressure 405.2 PSI

🟡 WARNINGS:
   ├─ Unit 2: LOW_DELTA_T - Poor efficiency
   ├─ Unit 2: UNUSUAL_PRESSURE_RATIO - Pressure ratio 2.9 outside normal
   ├─ Unit 3: LOW_DELTA_T - Poor efficiency (-24.1°F)
   ├─ Unit 3: UNUSUAL_PRESSURE_RATIO - Outside normal range
   └─ Unit 4: UNUSUAL_PRESSURE_RATIO - Pressure ratio 10.5
```

---

## What Each Unit is Showing

### Unit 2 - York 12344
```
HEALTH: 50/100 (FAIR)
══════════════════════════════════════════════════════════════

OPERATING CONDITIONS:
  Mode: COOLING
  Supply Temp: 53.9°F
  Return Temp: 70.2°F
  Delta-T: 9.4°F ⚠️ VERY LOW (target: 10-25°F)

PRESSURE SYSTEM:
  Discharge: 256.2 PSI
  Suction: 87.2 PSI
  Ratio: 2.9 (target: 4-6) ⚠️ OUT OF RANGE

ELECTRICAL:
  Phase 1: 235.3A
  Phase 2: 234.0A
  Phase 3: 234.2A
  Compressor: 31.2A
  Balance: Excellent

FAULT: LOW_DELTA_T

ISSUES FOUND:
  ✗ Extremely low Delta-T - Poor cooling efficiency
  ✗ Pressure ratio too low - Possible refrigerant issue
  ✗ Fault code indicates low temperature difference
```

---

### Unit 3 - Trane-4 RTU-Test-2026
```
HEALTH: 50/100 (FAIR)
══════════════════════════════════════════════════════════════

OPERATING CONDITIONS:
  Mode: COOLING
  Supply Temp: 55.0°F
  Return Temp: 79.1°F
  Delta-T: -24.1°F ⚠️ EXTREMELY HIGH (target: 10-25°F)

PRESSURE SYSTEM:
  Discharge: 425.4 PSI ⚠️ CRITICAL (max: 400)
  Suction: 61.0 PSI
  Ratio: 7.0 (target: 4-6) ⚠️ OUT OF RANGE

ELECTRICAL:
  Phase 1: 241.5A
  Phase 2: 242.1A
  Phase 3: 241.1A
  Compressor: 27.9A
  Balance: Good

FAULT: HIGH_DISCHARGE_TEMP

ISSUES FOUND:
  ✗ Extremely high Delta-T - Possible airflow restriction
  ✗ High discharge pressure - System overload condition
  ✗ Unusual pressure ratio - System imbalance
```

---

### Unit 4 - ggggg ggggg
```
HEALTH: 65/100 (GOOD)
══════════════════════════════════════════════════════════════

OPERATING CONDITIONS:
  Mode: IDLE (not actively cooling/heating)
  Supply Temp: 59.4°F
  Return Temp: 60.3°F
  Delta-T: 0.0°F (normal for idle)

PRESSURE SYSTEM:
  Discharge: 405.2 PSI ⚠️ SLIGHTLY HIGH
  Suction: 38.6 PSI
  Ratio: 10.5 (target: 4-6) ⚠️ OUT OF RANGE

ELECTRICAL:
  Phase 1: 244.8A
  Phase 2: 246.3A
  Phase 3: 246.6A
  Compressor: 29.7A
  Balance: Good

FAULT: HIGH_DISCHARGE_TEMP

ISSUES FOUND:
  ✗ High discharge pressure - May need maintenance
  ✗ Unusual pressure ratio - Check system diagnostics
  ⚠️ Note: Unit is idle so some readings are less meaningful
```

---

## Data Integration Points

### Where Dashboard Reads From:
```
Database (SQLite)
    │
    ├─→ Units table
    │   ├─ unit_id
    │   ├─ make/model
    │   └─ location info
    │
    ├─→ UnitReadings table (latest per unit)
    │   ├─ supply_temp
    │   ├─ return_temp
    │   ├─ delta_t
    │   ├─ discharge_psi
    │   ├─ suction_psi
    │   ├─ v_1, v_2, v_3 (phases)
    │   ├─ compressor_amps
    │   └─ fault_code
    │
    └─→ Test Data Generator (continuous updates)
        └─ Adds new readings every 60 seconds per unit
```

### How Dashboard Processes Data:
```
Raw Reading
    ↓
Calculate Equipment Health Score
    ├─→ Temperature analysis
    ├─→ Pressure analysis
    ├─→ Electrical analysis
    └─→ Overall 0-100 score
    ↓
Evaluate All Alerts
    ├─→ Temperature-based alerts
    ├─→ Pressure-based alerts
    ├─→ Electrical-based alerts
    └─→ Grouped by severity
    ↓
Display in Dashboard
    ├─→ Metrics cards (top 4)
    ├─→ Equipment table (all units)
    ├─→ Alerts sidebar (top 5)
    └─→ Click for details modal
```

---

## Key Insights from Current Data

### Performance Status:
- **No units with excellent health** (0/3 scoring 80+)
- **1 unit with good health** (unit 4: 65/100)
- **2 units with fair/poor health** (units 2, 3: 50/100)

### Most Common Issues:
1. **Delta-T problems** - Units not achieving proper temperature differential
2. **High discharge pressure** - System overload conditions
3. **Pressure ratio imbalance** - Indicates refrigerant or compressor issues

### Maintenance Recommendations:
1. **Unit 2**: Check cooling capacity, low Delta-T indicates issue
2. **Unit 3**: High discharge pressure needs immediate investigation
3. **Unit 4**: Monitor while idle, check for refrigerant issues

---

## How the Dashboard Updates

### Real-Time Updates:
- **Every 30 seconds**: Dashboard refreshes from database
- **Test generator**: Adds new reading every 60 seconds per unit
- **Auto-calculation**: Health scores recalculated on each refresh
- **Alert generation**: New alerts from latest readings

### What Triggers Changes:
1. New reading added by test data generator
2. Dashboard refresh occurs (every 30 seconds)
3. Health score changes
4. New alerts generated
5. Metrics update

---

## Summary

The dashboard is **fully operational and displaying real data** from the test data generator. It shows:

✅ **Equipment Health Scores** - Calculated from temperature, pressure, electrical data
✅ **Real-time Alerts** - Generated from actual readings and thresholds
✅ **Equipment Status** - Current mode, temperatures, pressures
✅ **Quick Metrics** - Online/warning/fault counts + average temps
✅ **Detailed Analysis** - Click any unit for comprehensive breakdown

All integrated into the home page (`/`) - admins see this automatically after login!
