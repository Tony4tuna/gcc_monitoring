# pages/thermostat.py
from __future__ import annotations

from nicegui import ui
from typing import Optional, Callable

from core.auth import require_login, current_user
from core.version import get_version, get_build_info
from core.db import get_conn
from core.setpoints_repo import get_unit_setpoint, create_or_update_setpoint
from ui.layout import layout


def open_thermostat_dialog(unit_id: int, on_saved: Optional[Callable[[], None]] = None) -> None:
    """Grid-style symmetric thermostat dialog with CREDS actions."""
    sp = get_unit_setpoint(unit_id) or {}
    user = current_user() or {}
    
    # Determine title: use thermostat name if exists, otherwise default
    thermostat_title = sp.get("thermostat_name", "") or "Thermostat Control"

    with ui.dialog() as dlg, ui.card().classes("gcc-card p-6 w-full max-h-screen overflow-y-auto"):
        # Header placeholder (will be populated after form fields exist)
        header_row = ui.row().classes("w-full items-center mb-4 pb-3 border-b justify-between sticky top-0")
        
        # CREDS Section - Create form fields FIRST so buttons can reference them
        ui.label("CREDS").classes("text-base font-bold mb-2")
        with ui.grid(columns=3).classes("w-full gap-4 mb-6"):
            # Thermostat name section
            with ui.column().classes("gap-2"):
                ui.label("Thermostat Name").classes("text-sm font-semibold gcc-muted")
                name = ui.input(
                    value=sp.get("thermostat_name", ""),
                    placeholder="Enter name"
                ).classes("w-full").props("outlined dense standout")
            
            # Mode section
            with ui.column().classes("gap-2"):
                ui.label("Operating Mode").classes("text-sm font-semibold gcc-muted")
                mode = ui.select(
                    {"Off": "Off", "Auto": "Auto", "Cooling": "Cooling", "Heating": "Heating", "Dry": "Dry"},
                    value=sp.get("mode", "Auto"),
                ).classes("w-full").props("outlined dense standout")
            
            # Fan section
            with ui.column().classes("gap-2"):
                ui.label("Fan").classes("text-sm font-semibold gcc-muted")
                fan = ui.select(
                    {"Auto": "Auto", "On": "On"},
                    value=sp.get("fan", "Auto"),
                ).classes("w-full").props("outlined dense standout")
            
            # Deadband section
            with ui.column().classes("gap-2"):
                ui.label("Deadband").classes("text-sm font-semibold gcc-muted")
                dead = ui.number(
                    value=sp.get("deadband", 2.0), 
                    min=0.5, 
                    max=5.0,
                    step=0.5,
                    suffix="F"
                ).classes("w-full").props("outlined dense standout")
            
            # Cooling setpoint section
            with ui.column().classes("gap-2"):
                ui.label("Cooling Setpoint").classes("text-sm font-semibold gcc-muted")
                cool = ui.number(
                    value=sp.get("cooling_setpoint", 72.0), 
                    min=60, 
                    max=85,
                    step=1,
                    suffix="F"
                ).classes("w-full").props("outlined dense standout")
            
            # Heating setpoint section
            with ui.column().classes("gap-2"):
                ui.label("Heating Setpoint").classes("text-sm font-semibold gcc-muted")
                heat = ui.number(
                    value=sp.get("heating_setpoint", 68.0), 
                    min=55, 
                    max=80,
                    step=1,
                    suffix="F"
                ).classes("w-full").props("outlined dense standout")
        
        ui.separator().classes("my-4")
        
        # Schedule Section
        ui.label("Schedule").classes("text-base font-bold mb-2")
        with ui.grid(columns=3).classes("w-full gap-4 mb-4"):
            # Enable schedule
            with ui.column().classes("gap-2"):
                ui.label("Enable Schedule").classes("text-sm font-semibold gcc-muted")
                schedule_enabled = ui.checkbox("Active", value=bool(sp.get("schedule_enabled", 0))).classes("w-full")
            
            # Schedule day
            with ui.column().classes("gap-2"):
                ui.label("Day").classes("text-sm font-semibold gcc-muted")
                schedule_day = ui.select(
                    {"Daily": "Daily", "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", 
                     "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"},
                    value=sp.get("schedule_day", "Daily"),
                ).classes("w-full").props("outlined dense standout")
            
            # Schedule mode
            with ui.column().classes("gap-2"):
                ui.label("Schedule Mode").classes("text-sm font-semibold gcc-muted")
                schedule_mode = ui.select(
                    {"Off": "Off", "Auto": "Auto", "Cooling": "Cooling", "Heating": "Heating", "Dry": "Dry"},
                    value=sp.get("schedule_mode", "Auto"),
                ).classes("w-full").props("outlined dense standout")
            
            # Start time
            with ui.column().classes("gap-2"):
                ui.label("Start Time").classes("text-sm font-semibold gcc-muted")
                schedule_start = ui.input(
                    value=sp.get("schedule_start_time", "09:00"),
                    placeholder="HH:MM"
                ).classes("w-full").props("outlined dense standout")
            
            # End time
            with ui.column().classes("gap-2"):
                ui.label("End Time").classes("text-sm font-semibold gcc-muted")
                schedule_end = ui.input(
                    value=sp.get("schedule_end_time", "17:00"),
                    placeholder="HH:MM"
                ).classes("w-full").props("outlined dense standout")
            
            # Schedule temperature
            with ui.column().classes("gap-2"):
                ui.label("Schedule Temp").classes("text-sm font-semibold gcc-muted")
                schedule_temp = ui.number(
                    value=sp.get("schedule_temp", 72.0), 
                    min=55, 
                    max=85,
                    step=1,
                    suffix="F"
                ).classes("w-full").props("outlined dense standout")
        
        ui.separator().classes("my-4")
        
        # NOW define CREDS actions (after form fields exist in scope)
        # Record - Save current values explicitly
        def _record():
            try:
                create_or_update_setpoint(
                    unit_id=unit_id,
                    mode=str(mode.value),
                    cooling_setpoint=float(cool.value),
                    heating_setpoint=float(heat.value),
                    deadband=float(dead.value),
                    fan=str(fan.value),
                    thermostat_name=str(name.value),
                    schedule_enabled=1 if schedule_enabled.value else 0,
                    schedule_day=str(schedule_day.value),
                    schedule_start_time=str(schedule_start.value),
                    schedule_end_time=str(schedule_end.value),
                    schedule_mode=str(schedule_mode.value),
                    schedule_temp=float(schedule_temp.value),
                    updated_by_login_id=user.get("id"),
                )
                ui.notify("Configuration recorded", type="positive")
                if on_saved:
                    on_saved()
            except Exception as e:
                ui.notify(f"Error recording: {e}", type="negative")
        
        # Delete - Clear and delete setpoint
        def _delete():
            try:
                conn = get_conn()
                conn.execute("DELETE FROM UnitSetpoints WHERE unit_id = ?", (unit_id,))
                conn.commit()
                conn.close()
                ui.notify("Setpoint deleted", type="positive")
                dlg.close()
                if on_saved:
                    on_saved()
            except Exception as e:
                ui.notify(f"Error deleting: {e}", type="negative")
        
        # Print - Export setpoint
        def _print():
            try:
                print_data = {
                    "unit_id": unit_id,
                    "name": name.value,
                    "mode": mode.value,
                    "fan": fan.value,
                    "cooling_setpoint": cool.value,
                    "heating_setpoint": heat.value,
                    "deadband": dead.value,
                    "schedule_enabled": schedule_enabled.value,
                    "schedule_day": schedule_day.value,
                    "schedule_mode": schedule_mode.value,
                    "schedule_start": schedule_start.value,
                    "schedule_end": schedule_end.value,
                    "schedule_temp": schedule_temp.value,
                }
                import json
                config_json = json.dumps(print_data, indent=2)
                ui.notify(f"Config exported: {config_json}", type="positive")
            except Exception as e:
                ui.notify(f"Error printing: {e}", type="negative")
        
        # Now populate header with CREDS buttons
        with header_row:
            # Title section with dynamic thermostat name
            with ui.row().classes("items-center gap-3"):
                ui.icon("thermostat").classes("text-2xl").style("color:#4db8ff;")
                ui.label(f"RTU-{unit_id}").classes("text-xl font-bold")
                ui.label(name.value if name.value else thermostat_title).classes("text-lg gcc-muted")
            
            # CREDS Action buttons
            with ui.row().classes("gap-1"):
                ui.button(icon="add", on_click=lambda: ui.notify("Create new config", type="info")).props("flat dense size=md").tooltip("Create")
                ui.button(icon="save", on_click=_record).props("flat dense size=md").tooltip("Record")
                ui.button(icon="edit", on_click=lambda: ui.notify("Edit mode", type="info")).props("flat dense size=md").tooltip("Edit")
                ui.button(icon="delete", on_click=_delete).props("flat dense size=md color=negative").tooltip("Delete")
                ui.button(icon="search", on_click=lambda: ui.notify("Search configs", type="info")).props("flat dense size=md").tooltip("Search")
                ui.button(icon="print", on_click=_print).props("flat dense size=md").tooltip("Print")
        
        # Auto-save function
        def _auto_save() -> None:
            try:
                create_or_update_setpoint(
                    unit_id=unit_id,
                    mode=str(mode.value),
                    cooling_setpoint=float(cool.value),
                    heating_setpoint=float(heat.value),
                    deadband=float(dead.value),
                    fan=str(fan.value),
                    thermostat_name=str(name.value),
                    schedule_enabled=1 if schedule_enabled.value else 0,
                    schedule_day=str(schedule_day.value),
                    schedule_start_time=str(schedule_start.value),
                    schedule_end_time=str(schedule_end.value),
                    schedule_mode=str(schedule_mode.value),
                    schedule_temp=float(schedule_temp.value),
                    updated_by_login_id=user.get("id"),
                )
            except Exception:
                pass  # Silent auto-save to avoid notification spam
        
        # Bind auto-save to all value changes
        name.on_value_change(lambda: _auto_save())
        mode.on_value_change(lambda: _auto_save())
        fan.on_value_change(lambda: _auto_save())
        dead.on_value_change(lambda: _auto_save())
        cool.on_value_change(lambda: _auto_save())
        heat.on_value_change(lambda: _auto_save())
        schedule_enabled.on_value_change(lambda: _auto_save())
        schedule_day.on_value_change(lambda: _auto_save())
        schedule_start.on_value_change(lambda: _auto_save())
        schedule_end.on_value_change(lambda: _auto_save())
        schedule_mode.on_value_change(lambda: _auto_save())
        schedule_temp.on_value_change(lambda: _auto_save())
        
        # Bottom action buttons
        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Back", on_click=dlg.close).props("color=primary unelevated")

    dlg.open()


def open_bulk_thermostat_dialog(unit_ids: list[int], on_saved: Optional[Callable[[], None]] = None) -> None:
    """Bulk thermostat settings dialog for multiple units."""
    user = current_user() or {}
    
    # Get first unit's settings as defaults
    sp = get_unit_setpoint(unit_ids[0]) or {}

    with ui.dialog() as dlg, ui.card().classes("gcc-card p-6 w-full max-h-screen overflow-y-auto"):
        # Header
        with ui.row().classes("w-full items-center mb-4 pb-3 border-b justify-between sticky top-0"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("thermostat").classes("text-2xl").style("color:#4db8ff;")
                ui.label(f"Bulk Set: {len(unit_ids)} Units").classes("text-xl font-bold")
                ui.label(f"RTU-{', '.join(str(u) for u in unit_ids[:5])}{'...' if len(unit_ids) > 5 else ''}").classes("text-sm gcc-muted")
        
        # Settings Grid
        ui.label("Apply Settings to All Selected Units").classes("text-base font-bold mb-2")
        with ui.grid(columns=3).classes("w-full gap-4 mb-6"):
            # Mode section
            with ui.column().classes("gap-2"):
                ui.label("Operating Mode").classes("text-sm font-semibold gcc-muted")
                mode = ui.select(
                    {"Off": "Off", "Auto": "Auto", "Cooling": "Cooling", "Heating": "Heating", "Dry": "Dry"},
                    value=sp.get("mode", "Auto"),
                ).classes("w-full").props("outlined dense standout")
            
            # Fan section
            with ui.column().classes("gap-2"):
                ui.label("Fan").classes("text-sm font-semibold gcc-muted")
                fan = ui.select(
                    {"Auto": "Auto", "On": "On"},
                    value=sp.get("fan", "Auto"),
                ).classes("w-full").props("outlined dense standout")
            
            # Deadband section
            with ui.column().classes("gap-2"):
                ui.label("Deadband").classes("text-sm font-semibold gcc-muted")
                dead = ui.number(
                    value=sp.get("deadband", 2.0), 
                    min=0.5, 
                    max=5.0,
                    step=0.5,
                    suffix="°F"
                ).classes("w-full").props("outlined dense standout")
            
            # Cooling setpoint section
            with ui.column().classes("gap-2"):
                ui.label("Cooling Setpoint").classes("text-sm font-semibold gcc-muted")
                cool = ui.number(
                    value=sp.get("cooling_setpoint", 72.0), 
                    min=60, 
                    max=85,
                    step=1,
                    suffix="°F"
                ).classes("w-full").props("outlined dense standout")
            
            # Heating setpoint section
            with ui.column().classes("gap-2"):
                ui.label("Heating Setpoint").classes("text-sm font-semibold gcc-muted")
                heat = ui.number(
                    value=sp.get("heating_setpoint", 68.0), 
                    min=55, 
                    max=80,
                    step=1,
                    suffix="°F"
                ).classes("w-full").props("outlined dense standout")
        
        ui.separator().classes("my-4")
        
        # Schedule Section
        ui.label("Schedule (Applied to All)").classes("text-base font-bold mb-2")
        with ui.grid(columns=3).classes("w-full gap-4 mb-4"):
            # Enable schedule
            with ui.column().classes("gap-2"):
                ui.label("Enable Schedule").classes("text-sm font-semibold gcc-muted")
                schedule_enabled = ui.checkbox("Active", value=bool(sp.get("schedule_enabled", 0))).classes("w-full")
            
            # Schedule day
            with ui.column().classes("gap-2"):
                ui.label("Day").classes("text-sm font-semibold gcc-muted")
                schedule_day = ui.select(
                    {"Daily": "Daily", "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", 
                     "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"},
                    value=sp.get("schedule_day", "Daily"),
                ).classes("w-full").props("outlined dense standout")
            
            # Schedule mode
            with ui.column().classes("gap-2"):
                ui.label("Schedule Mode").classes("text-sm font-semibold gcc-muted")
                schedule_mode = ui.select(
                    {"Off": "Off", "Auto": "Auto", "Cooling": "Cooling", "Heating": "Heating", "Dry": "Dry"},
                    value=sp.get("schedule_mode", "Auto"),
                ).classes("w-full").props("outlined dense standout")
            
            # Start time
            with ui.column().classes("gap-2"):
                ui.label("Start Time").classes("text-sm font-semibold gcc-muted")
                schedule_start = ui.input(
                    value=sp.get("schedule_start_time", "09:00"),
                    placeholder="HH:MM"
                ).classes("w-full").props("outlined dense standout")
            
            # End time
            with ui.column().classes("gap-2"):
                ui.label("End Time").classes("text-sm font-semibold gcc-muted")
                schedule_end = ui.input(
                    value=sp.get("schedule_end_time", "17:00"),
                    placeholder="HH:MM"
                ).classes("w-full").props("outlined dense standout")
            
            # Schedule temperature
            with ui.column().classes("gap-2"):
                ui.label("Schedule Temp").classes("text-sm font-semibold gcc-muted")
                schedule_temp = ui.number(
                    value=sp.get("schedule_temp", 72.0), 
                    min=55, 
                    max=85,
                    step=1,
                    suffix="°F"
                ).classes("w-full").props("outlined dense standout")
        
        ui.separator().classes("my-4")
        
        # Action buttons
        def apply_to_all():
            try:
                success_count = 0
                for unit_id in unit_ids:
                    create_or_update_setpoint(
                        unit_id=unit_id,
                        mode=str(mode.value),
                        cooling_setpoint=float(cool.value),
                        heating_setpoint=float(heat.value),
                        deadband=float(dead.value),
                        fan=str(fan.value),
                        thermostat_name="",  # Bulk set doesn't change name
                        schedule_enabled=1 if schedule_enabled.value else 0,
                        schedule_day=str(schedule_day.value),
                        schedule_start_time=str(schedule_start.value),
                        schedule_end_time=str(schedule_end.value),
                        schedule_mode=str(schedule_mode.value),
                        schedule_temp=float(schedule_temp.value),
                        updated_by_login_id=user.get("id"),
                    )
                    success_count += 1
                ui.notify(f"Applied settings to {success_count} unit(s)", type="positive")
                if on_saved:
                    on_saved()
                dlg.close()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")
        
        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dlg.close).props("flat")
            ui.button("Apply to All", on_click=apply_to_all).props("color=primary unelevated")

    dlg.open()


def _fetch_units_by_location(customer_id: int, location_id: int) -> list[dict]:
    """Fetch latest unit status rows for a specific customer and location."""
    conn = get_conn()
    try:
        # Ensure the installed_location column exists (idempotent)
        try:
            conn.execute("ALTER TABLE Units ADD COLUMN installed_location TEXT")
            conn.commit()
        except Exception:
            pass

        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT
                u.unit_id,
                ur.mode,
                ur.supply_temp,
                pl.address1 AS location,
                COALESCE(u.installed_location, '') AS installed_at,
                c.company AS customer,
                c.ID as customer_id,
                pl.ID as location_id
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            WHERE ur.reading_id IN (
                SELECT MAX(reading_id) FROM UnitReadings GROUP BY unit_id
            )
            AND c.ID = ?
            AND pl.ID = ?
            ORDER BY u.unit_id
            LIMIT 15
            """,
            (customer_id, location_id),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def page():
    """Thermostat management page."""
    if not require_login():
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5))
    customer_filter = user.get("customer_id") if hierarchy == 4 else None
    
    from core.customers_repo import list_customers
    from core.locations_repo import list_locations

    with layout("Thermostat", show_logout=True, show_back=True, back_to="/"):
        # CSS for grid styling with borders
        ui.add_head_html("""
        <style>
            .gcc-thermostat-container {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 280px);
                gap: 0.75rem;
            }
            
            .gcc-crudsp-grid {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 0.5rem;
                margin-bottom: 0.75rem;
                width: 100%;
            }
            
            .gcc-crudsp-btn {
                min-height: 40px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: center;
                gap: 4px;
                transition: all 0.2s;
                white-space: nowrap;
            }
            
            .gcc-crudsp-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            
            .gcc-thermostat-table .q-table__middle table td,
            .gcc-thermostat-table .q-table__middle table th {
                border: 1px solid rgba(255,255,255,0.12) !important;
            }
            
            body.light .gcc-thermostat-table .q-table__middle table td,
            body.light .gcc-thermostat-table .q-table__middle table th {
                border: 1px solid rgba(0,0,0,0.12) !important;
            }
            
            .gcc-thermostat-table .loc-col {
                max-width: 260px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .inst-col {
                max-width: 200px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .gcc-selector-grid {
                display: grid;
                grid-template-columns: auto 1fr auto 1fr;
                gap: 0.75rem;
                align-items: center;
                padding: 0.75rem;
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 8px;
                flex-shrink: 0;
            }
        </style>
        """)
        
        # Load customers
        customers = list_customers("") if not customer_filter else list_customers("", customer_filter)
        customer_opts = {}
        if customer_filter:
            # Client users see only their customer
            for c in customers:
                if int(c["ID"]) == customer_filter:
                    customer_opts[int(c["ID"])] = f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip()
        else:
            customer_opts = {
                int(c["ID"]): f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip()
                for c in customers
            }

        with ui.element("div").classes("gcc-thermostat-container"):
            # Client and Location selectors
            with ui.element("div").classes("gcc-selector-grid"):
                ui.label("Client:").classes("font-bold text-sm")
                customer_sel = ui.select(customer_opts).classes("w-full")
                if customers:
                    customer_sel.value = int(customers[0]["ID"])
                
                ui.label("Location:").classes("font-bold text-sm")
                location_sel = ui.select({}).classes("w-full")
                
                def update_locations():
                    if not customer_sel.value:
                        location_sel.options = {}
                        location_sel.value = None
                        location_sel.update()
                        return
                    
                    locations = list_locations("", int(customer_sel.value))
                    location_sel.options = {
                        int(loc["ID"]): f"{loc.get('address1','')} — {loc.get('city','')}, {loc.get('state','')}".strip()
                        for loc in locations
                    }
                    if locations:
                        location_sel.value = int(locations[0]["ID"])
                    else:
                        location_sel.value = None
                    location_sel.update()
                    refresh_table()
                
                customer_sel.on_value_change(lambda: update_locations())
                location_sel.on_value_change(lambda: refresh_table())
            
            # CRUDSP buttons
            with ui.element("div").classes("gcc-crudsp-grid"):
                ui.button(icon="add", on_click=lambda: ui.notify("Create - Coming soon", type="info")).props("outline dense").classes("gcc-crudsp-btn").style("color: #4ade80;")
                ui.button(icon="save", on_click=lambda: ui.notify("Check a unit or use header checkbox for bulk", type="info")).props("outline dense").classes("gcc-crudsp-btn").style("color: #60a5fa;")
                ui.button(icon="update", on_click=lambda: ui.notify("Check a unit to update", type="info")).props("outline dense").classes("gcc-crudsp-btn").style("color: #fbbf24;")
                ui.button(icon="delete", on_click=lambda: ui.notify("Check a unit to delete", type="info")).props("outline dense").classes("gcc-crudsp-btn").style("color: #ef4444;")
                ui.button(icon="search", on_click=lambda: ui.notify("Search - Coming soon", type="info")).props("outline dense").classes("gcc-crudsp-btn").style("color: #a78bfa;")
                ui.button(icon="print", on_click=lambda: ui.notify("Print - Coming soon", type="info")).props("outline dense").classes("gcc-crudsp-btn").style("color: #f472b6;")

            # Header info
            with ui.card().classes("gcc-card").style("flex-shrink: 0;"):
                with ui.row().classes("items-center gap-3 p-2"):
                    ui.icon("thermostat").classes("text-2xl").style("color:#4db8ff;")
                    ui.label("Thermostat Control").classes("text-xl font-bold")
                    ui.label("Check a unit or use header checkbox for bulk settings").classes("gcc-muted ml-auto")

            # Table container with fixed height and borders
            with ui.card().classes("gcc-card gcc-thermostat-table").style("height: calc(100vh - 480px); display: flex; flex-direction: column;"):
                columns = [
                    {"name": "client", "label": "Client", "field": "client", "align": "right"},
                    {"name": "location", "label": "Location", "field": "location", "align": "right", "classes": "loc-col", "headerClasses": "loc-col"},
                    {"name": "installed", "label": "Installed @", "field": "installed", "align": "right", "classes": "inst-col", "headerClasses": "inst-col"},
                    {"name": "unit", "label": "Tag", "field": "unit", "align": "right"},
                    {"name": "temp", "label": "Temp", "field": "temp", "align": "right"},
                    {"name": "mode", "label": "Mode", "field": "mode", "align": "right"},
                ]

                table = ui.table(
                    columns=columns,
                    rows=[],
                    row_key="unit_id",
                    selection="multiple",  # use multiple to show header checkbox
                    pagination={"rowsPerPage": 15}
                ).classes("w-full").style("flex: 1; min-height: 0;")
                table.props("dense bordered virtual-scroll")

                # Right-align all cell content with ellipsis on location column
                table.add_slot("body-cell", """
                    <q-td :props="props" :class="['text-right', props.col.name === 'location' ? 'loc-col' : '', props.col.name === 'installed' ? 'inst-col' : '']">
                        {{ props.value }}
                    </q-td>
                """)
                
                # Handle selection changes
                def on_selection_change():
                    if not table.selected:
                        return
                    selected_now = list(table.selected)
                    total_rows = len(table.rows)

                    # Header checkbox selects all rows -> bulk dialog
                    if total_rows > 0 and len(selected_now) == total_rows:
                        table.selected = []
                        table.update()
                        unit_ids = [int(row["unit_id"]) for row in table.rows]
                        open_bulk_thermostat_dialog(unit_ids, refresh_table)
                        return

                    # Single checkbox -> open dialog for that thermostat
                    selected_row = selected_now[0]
                    unit_id = int(selected_row["unit_id"])
                    table.selected = []
                    table.update()
                    open_thermostat_dialog(unit_id, refresh_table)

                # Bind selection event (covers row checkbox and header checkbox)
                table.on("selection", lambda: on_selection_change())
                
                def refresh_table():
                    if not customer_sel.value or not location_sel.value:
                        table.rows = []
                        table.update()
                        return
                    
                    # Fetch units for selected customer and location (max 15)
                    units = _fetch_units_by_location(int(customer_sel.value), int(location_sel.value))[:15]
                    rows = []
                    for u in units:
                        rows.append({
                            "client": u.get("customer") or "",
                            "location": u.get("location") or "",
                            "installed": (u.get("installed_at") or "")[:30],
                            "unit": f"RTU-{u['unit_id']}",
                            "temp": f"{u.get('supply_temp')}F" if u.get('supply_temp') is not None else "",
                            "mode": u.get("mode") or "",
                            "unit_id": u["unit_id"],
                        })
                    table.rows = rows
                    table.update()
                
                # Initial load
                update_locations()

        with ui.row().classes("text-xs gcc-muted mt-6 justify-center"):
            ui.label(f"GCC Monitoring v{get_version()}  Built {get_build_info().get('build_date','')}")