# pages/client_home.py
# Client portal with role-based access control:
# - Admin/Master: redirected to main dashboard
# - Tech: can select any customer (read-only) and view filtered dashboard
# - Client: only sees their own dashboard + equipment + profile

from typing import Dict, Any, List

from nicegui import ui

from core.auth import current_user, require_login
from ui.layout import layout
from core.customers_repo import list_customers, get_customer, update_customer
from core.locations_repo import list_locations
from core.units_repo import list_units

# IMPORTANT: use the SAME dashboard rendering, but filtered by customer_id
from pages.dashboard import render_dashboard


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

        # TECH (3): can select any customer (read-only dashboard + equipment)
        if hierarchy == 3:
            customers = list_customers("")  # your repo uses list_customers(search)
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

            with ui.row().classes("w-full items-center gap-4 mb-4"):
                customer_select = ui.select(customer_options, label="Select Customer").classes("flex-1")
                customer_select.value = list(customer_options.keys())[0]

            @ui.refreshable
            def render_portal():
                cid = customer_select.value
                if cid:
                    render_portal_for_customer(int(cid), hierarchy=3)

            customer_select.on_value_change(lambda _: render_portal.refresh())
            render_portal()
            return

        # CLIENT (4): only own customer
        if hierarchy == 4:
            customer_id = user.get("customer_id")
            if not customer_id:
                ui.label("Error: No customer assigned to your account").classes("text-red-500 text-xl")
                return
            render_portal_for_customer(int(customer_id), hierarchy=4)
            return

        ui.label("Access denied: invalid hierarchy").classes("text-red-500 font-bold")


def render_portal_for_customer(customer_id: int, hierarchy: int):
    """Tabs for a selected customer.
    Tech: Dashboard + Equipment
    Client: Dashboard + Equipment + My Profile
    """
    # Security guard (client cannot view other customers)
    if hierarchy == 4:
        user_customer_id = (current_user() or {}).get("customer_id")
        if int(customer_id) != int(user_customer_id or 0):
            ui.notify("Access denied: you can only view your own data", type="negative")
            return

    customer = get_customer(customer_id)
    if not customer:
        ui.label("Customer not found").classes("text-red-500")
        return

    # Header
    customer_name = (
        customer.get("company")
        or f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        or f"Customer {customer_id}"
    )

    with ui.card().classes("gcc-card p-4 mb-4"):
        ui.label(customer_name).classes("text-2xl font-bold")
        if customer.get("email"):
            ui.label(f"📧 {customer['email']}").classes("text-sm gcc-muted")
        if customer.get("phone1"):
            ui.label(f"📞 {customer['phone1']}").classes("text-sm gcc-muted")

    # Tabs
    tab_names = ["Dashboard", "Equipment"] if hierarchy == 3 else ["Dashboard", "Equipment", "My Profile"]

    # IMPORTANT: create tabs, then tab panels, and ensure ui.tab() is created inside the tabs context
    with ui.tabs().classes("w-full") as tabs:
        for name in tab_names:
            ui.tab(name)

    with ui.tab_panels(tabs, value=tab_names[0]).classes("w-full") as tab_panels:
        with ui.tab_panel("Dashboard"):
            # SAME dashboard as admin, but filtered for this customer
            render_dashboard(customer_id=int(customer_id))

        with ui.tab_panel("Equipment"):
            render_equipment_by_location(customer_id=int(customer_id), hierarchy=int(hierarchy))

        if hierarchy == 4:
            with ui.tab_panel("My Profile"):
                render_profile_editor(customer_id=int(customer_id), customer=customer)


def safe_list_locations(customer_id: int) -> List[Dict[str, Any]]:
    """
    Some repos use list_locations(customer_id=...), others list_locations(search="", customer_id=...).
    We'll try the simple one first.
    """
    try:
        return list_locations(customer_id=customer_id)  # old signature
    except TypeError:
        return list_locations(search="", customer_id=customer_id)  # alternate signature


def render_equipment_by_location(customer_id: int, hierarchy: int):
    """Equipment displayed as database-style table by location."""
    locations = safe_list_locations(customer_id)
    if not locations:
        ui.label("No locations found for this customer").classes("text-yellow-500")
        return

    for idx, location in enumerate(locations):
        location_id = int(location.get("ID") or 0)
        location_name = location.get("PropertyName") or location.get("address1") or f"Location {location_id}"
        address = location.get("address1") or ""
        city = location.get("city") or ""
        state = location.get("state") or ""

        units = list_units(location_id=location_id) or []

        # Location header
        with ui.row().classes("w-full items-center gap-3 mb-2 mt-4"):
            ui.label(location_name).classes("text-xl font-bold")
            if address or city or state:
                ui.label(f"({address}, {city}, {state})".strip("()")).classes("text-sm gcc-muted")
            ui.label(f"• {len(units)} unit{'s' if len(units) != 1 else ''}").classes("text-sm gcc-muted")

        if not units:
            ui.label("No equipment at this location").classes("text-sm gcc-muted italic mb-4")
        else:
            # Database-style table
            with ui.element("div").classes("gcc-card mb-4 overflow-x-auto"):
                # Table header
                with ui.row().classes("p-3 border-b border-gray-700 font-semibold text-xs uppercase"):
                    ui.label("Status").classes("w-16")
                    ui.label("Unit Name").classes("flex-1 min-w-[140px]")
                    ui.label("Equipment Type").classes("flex-1 min-w-[100px]")
                    ui.label("Capacity").classes("flex-1 min-w-[80px]")
                    ui.label("Refrigerant").classes("flex-1 min-w-[90px]")
                    ui.label("Make/Model").classes("flex-1 min-w-[120px]")
                    ui.label("Voltage").classes("flex-1 min-w-[100px]")
                    ui.label("Install Date").classes("w-28")
                
                # Table rows
                for unit in units:
                    show_unit_table_row(unit)
        
        # Divider between locations
        if idx < len(locations) - 1:
            ui.separator().classes("my-4")


def show_unit_table_row(unit: Dict[str, Any]):
    """Display unit as database table row."""
    unit_id = int(unit.get("unit_id") or 0)
    make = (unit.get("make") or "").strip()
    model = (unit.get("model") or "").strip()
    unit_tag = (unit.get("unit_tag") or "").strip()
    serial = (unit.get("serial") or "N/A").strip()
    inst_date = (unit.get("inst_date") or "N/A").strip()
    eq_type = (unit.get("equipment_type") or "RTU").strip()
    tonnage = (unit.get("tonnage") or "—").strip()
    refrig = (unit.get("refrigerant_type") or "—").strip()
    voltage = (unit.get("voltage") or "—").strip()
    unit_name = unit_tag or f"Unit {unit_id}"
    status = unit.get("status", "unknown")

    status_icons = {"active": "✅", "warning": "⚠️", "error": "🔴", "unknown": "❓"}
    icon = status_icons.get(status, status_icons["unknown"])

    # Table row with hover effect
    with ui.row().classes("p-3 border-b border-gray-800 hover:bg-gray-800/30 text-sm"):
        ui.label(icon).classes("w-16")
        ui.label(unit_name).classes("flex-1 min-w-[140px]")
        ui.label(eq_type).classes("flex-1 min-w-[100px] gcc-muted")
        ui.label(tonnage + (" Ton" if tonnage != "—" else "")).classes("flex-1 min-w-[80px] gcc-muted")
        ui.label(refrig).classes("flex-1 min-w-[90px] gcc-muted")
        ui.label(f"{make} {model}".strip() or "-").classes("flex-1 min-w-[120px] gcc-muted")
        ui.label(voltage).classes("flex-1 min-w-[100px] gcc-muted")
        ui.label(inst_date).classes("w-28 gcc-muted")


def show_unit_details_dialog(unit: Dict[str, Any], hierarchy: int):
    unit_id = int(unit.get("unit_id") or 0)
    unit_name = unit.get("unit_tag") or f"Unit {unit_id}"

    with ui.dialog() as dialog:
        with ui.card().classes("gcc-card p-5 max-w-2xl"):
            ui.label(f"Unit Details: {unit_name}").classes("text-xl font-bold mb-3")

            with ui.grid(columns=2).classes("gap-3 w-full"):
                ui.label("Unit ID:").classes("font-bold")
                ui.label(str(unit.get("unit_id") or "N/A"))

                ui.label("Tag:").classes("font-bold")
                ui.label(unit.get("unit_tag") or "N/A")
                
                ui.label("Equipment Type:").classes("font-bold")
                ui.label(unit.get("equipment_type") or "N/A")

                ui.label("Make/Model:").classes("font-bold")
                ui.label(f"{unit.get('make', 'N/A')} {unit.get('model', 'N/A')}")

                ui.label("Serial:").classes("font-bold")
                ui.label(unit.get("serial") or "N/A")
                
                ui.label("Refrigerant:").classes("font-bold")
                ui.label(unit.get("refrigerant_type") or "N/A")
                
                ui.label("Capacity:").classes("font-bold")
                cap = unit.get("tonnage") or ""
                btu = unit.get("btu_rating") or ""
                ui.label(f"{cap} Ton / {btu} BTU" if cap or btu else "N/A")
                
                ui.label("Voltage/Amperage:").classes("font-bold")
                volt = unit.get("voltage") or ""
                amp = unit.get("amperage") or ""
                ui.label(f"{volt} / {amp}A" if volt or amp else "N/A")
                
                ui.label("Breaker Size:").classes("font-bold")
                ui.label(unit.get("breaker_size") or "N/A")

                ui.label("Status:").classes("font-bold")
                ui.label(unit.get("status") or "unknown")

                ui.label("Location ID:").classes("font-bold")
                ui.label(str(unit.get("location_id") or "N/A"))

                ui.label("Install Date:").classes("font-bold")
                ui.label(unit.get("inst_date") or "N/A")
                
                ui.label("Warranty End:").classes("font-bold")
                ui.label(unit.get("warranty_end_date") or "N/A")

            with ui.row().classes("justify-end gap-2 mt-4"):
                ui.button("Close", on_click=dialog.close).props("flat")
                if hierarchy == 3:
                    ui.button("View History", on_click=lambda: ui.notify("History view coming soon", type="info")).props("outline")

    dialog.open()


def render_profile_editor(customer_id: int, customer: Dict[str, Any]):
    """Client profile editor with comprehensive information."""
    with ui.card().classes("gcc-card p-6 max-w-5xl"):
        ui.label("My Profile").classes("text-2xl font-bold mb-2")
        ui.label("Manage your complete business profile and contact information.").classes("text-sm gcc-muted mb-6")

        # Business Information
        ui.label("Business Information").classes("text-lg font-semibold mb-3 text-blue-400")
        with ui.grid(columns=2).classes("gap-4 w-full mb-6"):
            company = ui.input("Business Name", value=customer.get("company", "")).classes("w-full")
            website = ui.input("Website", value=customer.get("website", "")).classes("w-full")
            idstring = ui.input("Customer ID", value=customer.get("idstring", "")).classes("w-full")
            csr = ui.input("CSR/Account Manager", value=customer.get("csr", "")).classes("w-full")
        
        ui.separator().classes("my-4")
        
        # Contact Person
        ui.label("Primary Contact").classes("text-lg font-semibold mb-3 text-blue-400")
        with ui.grid(columns=2).classes("gap-4 w-full mb-6"):
            first_name = ui.input("First Name", value=customer.get("first_name", "")).classes("w-full")
            last_name = ui.input("Last Name", value=customer.get("last_name", "")).classes("w-full")
            email = ui.input("Email", value=customer.get("email", "")).classes("w-full")
            mobile = ui.input("Mobile", value=customer.get("mobile", "")).classes("w-full")
        
        ui.separator().classes("my-4")
        
        # Phone Numbers
        ui.label("Phone Numbers").classes("text-lg font-semibold mb-3 text-blue-400")
        with ui.grid(columns=2).classes("gap-4 w-full mb-6"):
            phone1 = ui.input("Primary Phone", value=customer.get("phone1", "")).classes("w-full")
            extension1 = ui.input("Extension", value=customer.get("extension1", "")).classes("w-full")
            phone2 = ui.input("Secondary Phone", value=customer.get("phone2", "")).classes("w-full")
            extension2 = ui.input("Extension", value=customer.get("extension2", "")).classes("w-full")
            fax = ui.input("Fax", value=customer.get("fax", "")).classes("w-full")
        
        ui.separator().classes("my-4")
        
        # Business Address
        ui.label("Business Address").classes("text-lg font-semibold mb-3 text-blue-400")
        with ui.grid(columns=1).classes("gap-4 w-full mb-4"):
            address1 = ui.input("Address Line 1", value=customer.get("address1", "")).classes("w-full")
            address2 = ui.input("Address Line 2", value=customer.get("address2", "")).classes("w-full")
        
        with ui.grid(columns=3).classes("gap-4 w-full mb-4"):
            city = ui.input("City", value=customer.get("city", "")).classes("w-full")
            state = ui.input("State", value=customer.get("state", "")).classes("w-full")
            zip_code = ui.input("ZIP Code", value=customer.get("zip", "")).classes("w-full")

        def on_save():
            payload = {
                "company": company.value,
                "website": website.value,
                "idstring": idstring.value,
                "csr": csr.value,
                "first_name": first_name.value,
                "last_name": last_name.value,
                "email": email.value,
                "mobile": mobile.value,
                "phone1": phone1.value,
                "extension1": extension1.value,
                "phone2": phone2.value,
                "extension2": extension2.value,
                "fax": fax.value,
                "address1": address1.value,
                "address2": address2.value,
                "city": city.value,
                "state": state.value,
                "zip": zip_code.value,
            }
            _save_profile(customer_id, payload)

        with ui.row().classes("justify-end gap-2 mt-6"):
            ui.button("Save Changes", on_click=on_save, icon="save").props("color=green")


def _save_profile(customer_id: int, payload: Dict[str, Any]):
    try:
        update_customer(customer_id, payload)
        ui.notify("Profile updated", type="positive")
    except Exception as e:
        ui.notify(f"Error saving profile: {e}", type="negative")
