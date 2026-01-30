# pages/client_home.py
# Client portal: Responsive card-based thermostat control
# - Client sees all their Locations → Units → Thermostats
# - Responsive design: works on phone, tablet, desktop, smart screens
# - Hierarchy: Client → Location → Unit → Thermostat (setpoints)

from typing import Dict, Any, List

from nicegui import ui

from core.auth import current_user, require_login
from ui.layout import layout
from core.customers_repo import list_customers, get_customer
from core.locations_repo import list_locations
from core.units_repo import list_units
from core.setpoints_repo import get_unit_setpoint


def page():
    if not require_login():
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)

    # 1 (Master) and 2 (Administrator) use main dashboard
    if hierarchy in (1, 2):
        ui.navigate.to("/")
        return

    with layout("Client Portal", hierarchy=hierarchy):

        # TECH (3): can select any customer
        if hierarchy == 3:
            customers = list_customers("")
            if not customers:
                ui.label("No customers found").classes("text-yellow-500")
                return

            customer_options = {
                int(c["ID"]): (
                    c.get("company")
                    or f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
                    or f"Customer {c['ID']}"
                )
                for c in customers
            }

            with ui.row().classes("w-full items-center gap-4 mb-6"):
                customer_select = ui.select(customer_options, label="Select Customer").classes("flex-1 max-w-sm")
                customer_select.value = list(customer_options.keys())[0]

            @ui.refreshable
            def render_portal():
                cid = customer_select.value
                if cid:
                    render_client_portal(int(cid), hierarchy=3)

            customer_select.on_value_change(lambda _: render_portal.refresh())
            render_portal()
            return

        # CLIENT (4): only own customer
        if hierarchy == 4:
            customer_id = user.get("customer_id")
            if not customer_id:
                ui.label("Error: No customer assigned to your account").classes("text-red-500 text-xl")
                return
            render_client_portal(int(customer_id), hierarchy=4)
            return

        ui.label("Access denied: invalid hierarchy").classes("text-red-500 font-bold")


def render_client_portal(customer_id: int, hierarchy: int):
    """
    Responsive client portal: Location → Unit → Thermostat hierarchy
    Displays as responsive cards (tall, narrow) for phone/tablet/desktop/smart screens
    """
    # Security check: clients can only view their own data
    if hierarchy == 4:
        user_customer_id = (current_user() or {}).get("customer_id")
        if int(customer_id) != int(user_customer_id or 0):
            ui.notify("Access denied: you can only view your own data", type="negative")
            return

    customer = get_customer(customer_id)
    if not customer:
        ui.label("Customer not found").classes("text-red-500")
        return

    customer_name = (
        customer.get("company")
        or f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        or f"Customer {customer_id}"
    )

    # ============================================
    # HEADER CARD - Customer info
    # ============================================
    with ui.card().classes("gcc-card p-6 w-full max-w-2xl"):
        ui.label(customer_name).classes("text-3xl font-bold")
        
        # Contact info in grid
        with ui.grid(columns=2).classes("w-full gap-4 mt-4"):
            if customer.get("email"):
                ui.label("Email").classes("text-sm font-semibold gcc-muted")
                ui.label(customer["email"]).classes("text-sm")
            
            if customer.get("phone1"):
                ui.label("Phone").classes("text-sm font-semibold gcc-muted")
                ui.label(customer["phone1"]).classes("text-sm")
            
            if customer.get("address1"):
                ui.label("Address").classes("text-sm font-semibold gcc-muted")
                ui.label(customer["address1"]).classes("text-sm")
            
            if customer.get("city"):
                ui.label("City").classes("text-sm font-semibold gcc-muted")
                city_state = f"{customer.get('city', '')}, {customer.get('state', '')}".strip(", ")
                ui.label(city_state).classes("text-sm")

    ui.separator().classes("my-4")

    # ============================================
    # LOCATIONS & THERMOSTATS - Main content
    # ============================================
    locations = safe_list_locations(customer_id)
    if not locations:
        ui.label("No locations found").classes("text-yellow-500 p-6")
        return

    for location in locations:
        location_id = int(location.get("ID") or 0)
        location_name = location.get("PropertyName") or location.get("address1") or f"Location {location_id}"
        
        units = list_units(location_id=location_id) or []
        if not units:
            continue
        
        # LOCATION HEADER
        with ui.card().classes("gcc-card p-6 w-full max-w-2xl"):
            ui.label(location_name).classes("text-2xl font-bold text-blue-400")
            
            # Location address
            addr_parts = []
            if location.get("address1"):
                addr_parts.append(location["address1"])
            if location.get("city"):
                addr_parts.append(location["city"])
            if location.get("state"):
                addr_parts.append(location["state"])
            if location.get("zip"):
                addr_parts.append(location["zip"])
            
            if addr_parts:
                ui.label(" | ".join(addr_parts)).classes("text-sm gcc-muted mt-2")
            
            # Equipment count badge
            with ui.row().classes("mt-3 gap-2"):
                ui.badge(f"{len(units)} Unit{'s' if len(units) != 1 else ''}").props("color=primary")
        
        # UNITS & THERMOSTATS - One card per unit
        for unit in units:
            unit_id = int(unit.get("unit_id") or 0)
            unit_tag = unit.get("unit_tag") or f"Unit {unit_id}"
            unit_name = unit.get("unit_tag") or f"Unit {unit_id}"
            eq_type = unit.get("equipment_type") or "RTU"
            make = unit.get("make") or ""
            model = unit.get("model") or ""
            
            # Get thermostat info
            setpoint = get_unit_setpoint(unit_id) or {}
            thermostat_name = setpoint.get("thermostat_name") or f"{unit_name} Thermostat"
            mode = setpoint.get("mode", "Auto")
            cool_sp = setpoint.get("cooling_setpoint", 72)
            heat_sp = setpoint.get("heating_setpoint", 68)
            fan = setpoint.get("fan", "Auto")
            
            # Status indicator
            status = unit.get("status", "unknown")
            status_color = {
                "active": "green",
                "warning": "orange",
                "error": "red",
                "unknown": "gray"
            }.get(status, "gray")
            status_icons = {
                "active": "✓ Active",
                "warning": "⚠ Warning",
                "error": "✗ Error",
                "unknown": "? Unknown"
            }
            
            # UNIT CARD
            with ui.card().classes("gcc-card p-6 w-full max-w-2xl"):
                # Header: Unit name + Status
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    ui.label(unit_name).classes("text-xl font-bold")
                    ui.badge(status_icons.get(status, status)).props(f"color={status_color}")
                
                # Equipment details
                ui.label(f"{eq_type} • {make} {model}".strip(" •")).classes("text-sm gcc-muted mb-3")
                
                ui.separator().classes("my-3")
                
                # ============================================
                # THERMOSTAT CONTROL - Main focus
                # ============================================
                ui.label(thermostat_name).classes("text-lg font-semibold text-blue-400 mb-2")
                
                # Current setpoints in grid (2x2)
                with ui.grid(columns=2).classes("w-full gap-4 mb-4"):
                    # Cooling
                    with ui.column().classes("items-center gap-2 p-3 bg-blue-900/20 rounded"):
                        ui.label("COOL").classes("text-xs font-bold gcc-muted")
                        ui.label(f"{cool_sp}°F").classes("text-2xl font-bold text-blue-400")
                    
                    # Heating
                    with ui.column().classes("items-center gap-2 p-3 bg-red-900/20 rounded"):
                        ui.label("HEAT").classes("text-xs font-bold gcc-muted")
                        ui.label(f"{heat_sp}°F").classes("text-2xl font-bold text-red-400")
                    
                    # Mode
                    with ui.column().classes("items-center gap-2 p-3 bg-gray-700/20 rounded"):
                        ui.label("MODE").classes("text-xs font-bold gcc-muted")
                        ui.label(mode).classes("text-lg font-bold")
                    
                    # Fan
                    with ui.column().classes("items-center gap-2 p-3 bg-gray-700/20 rounded"):
                        ui.label("FAN").classes("text-xs font-bold gcc-muted")
                        ui.label(fan).classes("text-lg font-bold")
                
                # Additional details
                with ui.grid(columns=2).classes("w-full gap-3 text-sm mb-4"):
                    ui.label("Serial:").classes("font-semibold gcc-muted")
                    ui.label(unit.get("serial") or "N/A")
                    
                    ui.label("Voltage:").classes("font-semibold gcc-muted")
                    ui.label(str(unit.get("voltage") or "—"))
                    
                    ui.label("Capacity:").classes("font-semibold gcc-muted")
                    tonnage = unit.get("tonnage") or "—"
                    ui.label(f"{tonnage} Ton" if tonnage != "—" else "—")
                    
                    ui.label("Refrigerant:").classes("font-semibold gcc-muted")
                    ui.label(unit.get("refrigerant_type") or "—")
                
                ui.separator().classes("my-3")
                
                # Control button
                from pages.thermostat import open_thermostat_dialog
                
                def open_thermostat(uid=unit_id):
                    open_thermostat_dialog(uid, on_saved=None)
                
                ui.button("Adjust Thermostat", on_click=open_thermostat).classes("w-full").props("color=blue")
        
        ui.separator().classes("my-6")

    render_client_portal(int(customer_id), hierarchy)


def safe_list_locations(customer_id: int) -> List[Dict[str, Any]]:
    """
    Safely fetch locations with flexible repo signatures.
    Some repos use list_locations(customer_id=...), others use list_locations(search="", customer_id=...).
    """
    try:
        return list_locations(customer_id=customer_id)
    except TypeError:
        return list_locations(search="", customer_id=customer_id)
