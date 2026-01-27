"""Seed fake telemetry into UnitReadings for all units.

Usage (from repo root, venv active):
    python -m utility.seed_unit_readings --per-unit 48 --hours 24

This uses the existing fake generator in core.unit_status.get_unit_status
and writes rows into UnitReadings so dashboards/thermostat can show data.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta

from core.db import get_conn
from core.unit_status import get_unit_status


def seed_unit_readings(per_unit: int, hours: int) -> int:
    """Insert random readings for each unit; returns rows inserted."""
    now = datetime.now()
    inserted = 0
    with get_conn() as conn:
        unit_rows = conn.execute("SELECT unit_id FROM Units").fetchall()
        unit_ids = [int(r[0]) for r in unit_rows]
        for unit_id in unit_ids:
            for _ in range(per_unit):
                status = get_unit_status(unit_id)
                minutes_back = random.randint(0, hours * 60)
                ts = now - timedelta(minutes=minutes_back)
                conn.execute(
                    """
                    INSERT INTO UnitReadings (
                        unit_id, ts,
                        supply_temp, return_temp, delta_t,
                        outdoor_temp, fan_speed_percent, runtime_hours,
                        mode, unit_status, alert_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        unit_id,
                        ts.strftime("%Y-%m-%d %H:%M:%S"),
                        status.get("supply_temp_f"),
                        status.get("return_temp_f"),
                        status.get("delta_t_f"),
                        status.get("outdoor_temp_f"),
                        status.get("fan_speed_percent"),
                        status.get("runtime_hours"),
                        status.get("mode"),
                        status.get("status_color"),
                        status.get("alert_message"),
                    ),
                )
                inserted += 1
        conn.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Seed fake UnitReadings data")
    parser.add_argument("--per-unit", type=int, default=48, help="Rows per unit")
    parser.add_argument("--hours", type=int, default=24, help="Spread readings over past N hours")
    args = parser.parse_args()

    rows = seed_unit_readings(per_unit=args.per_unit, hours=args.hours)
    print(f"Inserted {rows} readings across units")


if __name__ == "__main__":
    main()
