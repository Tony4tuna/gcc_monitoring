# core/unit_status.py
# Junior module to get current status / sensor data for a HVAC unit
# Fake data generator for development (skeleton phase)
# Later: replace fake logic with real DB queries or hardware reads

import random
from datetime import datetime, timedelta

def get_unit_status(unit_id: int, location_id: int = None):
    """
    Get current monitoring status for one unit.
    Returns: dict with sensor values, mode, alerts — easy to use in UI/tables
    Fake but realistic ranges based on typical RTU/AHU HVAC data
    """
    # Step 1: Pick current operating mode (weighted - cooling more common)
    modes = ["Off", "Idle", "Cooling", "Heating", "Economizer", "Fault"]
    weights = [8, 25, 40, 15, 7, 5]  # Cooling highest probability for now
    mode = random.choices(modes, weights=weights)[0]

    # Step 2: Generate sensor readings based on mode
    outdoor_temp = random.uniform(35.0, 95.0)  # NJ-like outdoor range

    if mode == "Cooling":
        supply_temp = random.uniform(52.0, 60.0)     # Typical target ~55°F
        return_temp = random.uniform(70.0, 80.0)     # Indoor average
        fan_speed = random.randint(75, 100)          # High fan for cooling
    elif mode == "Heating":
        supply_temp = random.uniform(95.0, 115.0)    # Furnace/heat rise
        return_temp = random.uniform(68.0, 74.0)
        fan_speed = random.randint(60, 90)
    elif mode == "Economizer":
        supply_temp = outdoor_temp + random.uniform(-8.0, 2.0)
        return_temp = random.uniform(70.0, 78.0)
        fan_speed = random.randint(70, 100)
    else:
        supply_temp = random.uniform(65.0, 78.0)
        return_temp = supply_temp + random.uniform(-5.0, 5.0)
        fan_speed = 0 if mode == "Off" else random.randint(30, 60)

    delta_t = round(supply_temp - return_temp, 1)
    abs_delta = abs(delta_t)  # Absolute value for diagnostic checks

    # Step 3: Runtime hours (fake cumulative)
    runtime_hours = random.randint(300, 18000)

    # Step 4: Last update time (pretend recent)
    minutes_ago = random.randint(1, 60)
    last_update = datetime.now() - timedelta(minutes=minutes_ago)
    last_update_str = last_update.strftime("%Y-%m-%d %H:%M:%S")

    # Step 5: Alert / fault detection (simple if/else rules)
    status_color = "green"
    alert_message = ""
    alert_level = "normal"

    if mode == "Fault":
        status_color = "red"
        alert_message = "Unit in fault mode"
        alert_level = "critical"

    elif mode == "Cooling":
        if abs_delta < 14.0:
            status_color = "red"
            alert_message = "Low Delta T (cooling fault?) - check refrigerant/airflow/coil"
            alert_level = "critical"
        elif abs_delta < 16.0:
            status_color = "yellow"
            alert_message = "Marginal Delta T - possible low charge or dirty filter"
            alert_level = "warning"
        elif supply_temp > 62.0:
            status_color = "yellow"
            alert_message = "High supply temp - cooling underperforming"
            alert_level = "warning"

    elif mode == "Heating":
        if abs_delta < 30.0:
            status_color = "red"
            alert_message = "Low heat rise - check heat exchanger/fan"
            alert_level = "critical"

    elif fan_speed == 0 and mode not in ["Off", "Idle"]:
        status_color = "red"
        alert_message = "Fan stopped during operation"
        alert_level = "critical"

    # Final return dict - all info in one place
    return {
        "unit_id": unit_id,
        "mode": mode,
        "supply_temp_f": round(supply_temp, 1),
        "return_temp_f": round(return_temp, 1),
        "delta_t_f": delta_t,
        "outdoor_temp_f": round(outdoor_temp, 1),
        "fan_speed_percent": fan_speed,
        "runtime_hours": runtime_hours,
        "last_update": last_update_str,
        "status_color": status_color,
        "alert_message": alert_message,
        "alert_level": alert_level,
    }


# Quick test block - run this file alone to see examples
if __name__ == "__main__":
    print("Example status for unit 101:")
    print(get_unit_status(101))
    print("\nExample status for unit 202:")
    print(get_unit_status(202))