"""
Service Calls Page
Full CRUD interface for service call management
"""

from nicegui import ui, app
import os
import base64
from typing import Optional, Dict, Any
from core.auth import current_user, require_login
from core.tickets_repo import (
    create_service_call, get_service_call, list_service_calls, update_service_call, delete_service_call,
    get_service_call_stats, search_service_calls
)
from core.customers_repo import list_customers, get_customer
from core.locations_repo import list_locations
from core.units_repo import list_units
from ui.layout import layout


@ui.page("/tickets")
def tickets_page():
    """Service Calls page"""
    if not require_login():
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy") or 5)
    customer_id = user.get("customer_id")
    
    with layout("Service Calls", show_logout=True, hierarchy=hierarchy):
        # Stats cards
        render_stats(customer_id if hierarchy == 4 else None)
        
        # Main content
        with ui.tabs().classes("w-full") as tabs:
            ui.tab("All Calls")
            ui.tab("Create New")
        
        with ui.tab_panels(tabs, value="All Calls").classes("w-full"):
            with ui.tab_panel("All Calls"):
                render_calls_list(customer_id if hierarchy == 4 else None, hierarchy)
            
            with ui.tab_panel("Create New"):
                render_call_form(customer_id if hierarchy == 4 else None, user, hierarchy)


def render_stats(customer_id: Optional[int] = None):
    """Display service call statistics"""
    stats = get_service_call_stats(customer_id)
    
    with ui.row().classes("w-full gap-4 mb-4"):
        # Total
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Total Calls").classes("text-sm gcc-muted")
            ui.label(str(stats.get("total", 0))).classes("text-3xl font-bold")
        
        # Open
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Open").classes("text-sm gcc-muted")
            ui.label(str(stats.get("open", 0))).classes("text-3xl font-bold text-blue-400")
        
        # In Progress
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("In Progress").classes("text-sm gcc-muted")
            ui.label(str(stats.get("in_progress", 0))).classes("text-3xl font-bold text-yellow-400")
        
        # Closed
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Closed").classes("text-sm gcc-muted")
            ui.label(str(stats.get("closed", 0))).classes("text-3xl font-bold text-green-400")
        
        # Emergency
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Emergency").classes("text-sm gcc-muted")
            ui.label(str(stats.get("emergency", 0))).classes("text-3xl font-bold text-red-400")


def render_calls_list(customer_id: Optional[int] = None, hierarchy: int = 5):
    """Display service calls list with search and filters"""
    
    with ui.card().classes("gcc-card p-4 mb-4"):
        with ui.row().classes("w-full gap-4 items-center"):
            search_input = ui.input("Search", placeholder="ID, Title, Description").classes("flex-1")
            status_filter = ui.select(
                ["All", "Open", "In Progress", "Closed"],
                value="All",
                label="Status"
            ).classes("w-40")
            priority_filter = ui.select(
                ["All", "Low", "Normal", "High", "Emergency"],
                value="All",
                label="Priority"
            ).classes("w-40")
            ui.button("Search", icon="search", on_click=lambda: refresh_calls())
            ui.button("Print All", icon="print", on_click=lambda: show_print_all(search_input.value, status_filter.value, priority_filter.value, customer_id))
    
    # Calls container
    calls_container = ui.column().classes("w-full gap-3")
    
    def refresh_calls():
        calls_container.clear()
        with calls_container:
            search_term = search_input.value
            status = None if status_filter.value == "All" else status_filter.value
            priority = None if priority_filter.value == "All" else priority_filter.value
            
            if search_term:
                calls = search_service_calls(search_term, customer_id)
            else:
                calls = list_service_calls(customer_id=customer_id, status=status, priority=priority, limit=50)
            
            if not calls:
                ui.label("No service calls found").classes("text-gray-400 italic")
                return
            
            for call in calls:
                render_call_card(call, hierarchy)
    
    refresh_calls()


def render_call_card(call: Dict[str, Any], hierarchy: int):
    """Display single service call card"""
    call_id = call.get("ID")
    status = call.get("status", "Open")
    priority = call.get("priority", "Normal")
    
    # Status colors
    status_colors = {
        "Open": "border-blue-500",
        "In Progress": "border-yellow-500",
        "Closed": "border-green-500"
    }
    
    # Priority badges
    priority_colors = {
        "Low": "bg-gray-700",
        "Normal": "bg-blue-700",
        "High": "bg-orange-700",
        "Emergency": "bg-red-700"
    }
    
    border_class = status_colors.get(status, "border-gray-500")
    priority_class = priority_colors.get(priority, "bg-gray-700")
    
    with ui.card().classes(f"gcc-card p-4 border-l-4 {border_class}"):
        with ui.row().classes("w-full items-start justify-between mb-2"):
            # Left: Call ID and title
            with ui.column().classes("gap-1 flex-1"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"#{call_id}").classes("font-mono text-sm gcc-muted")
                    ui.badge(priority.upper()).classes(f"{priority_class} text-xs")
                    ui.badge(status.upper()).classes("bg-gray-800 text-xs")
                
                ui.label(call.get("title", "Untitled")).classes("text-lg font-bold")
            
            # Right: Actions
            if hierarchy <= 3:  # Admin/Tech can edit
                with ui.row().classes("gap-2"):
                    ui.button(icon="visibility", on_click=lambda c=call: show_ticket_detail(c)).props("flat dense")
                    ui.button(icon="print", on_click=lambda c=call: show_print_call(c)).props("flat dense color=blue").tooltip("Print")
                    ui.button(icon="edit", on_click=lambda c=call: show_edit_dialog(c)).props("flat dense").tooltip("Edit")
                    if status != "Closed":
                        ui.button(icon="check_circle", on_click=lambda cid=call_id: show_close_dialog(cid)).props("flat dense color=green").tooltip("Close with reason")
                    else:
                        ui.button(icon="delete", on_click=lambda cid=call_id: confirm_delete(cid)).props("flat dense color=red").tooltip("Delete")
        
        # Details
        with ui.grid(columns=4).classes("gap-2 text-sm gcc-muted"):
            with ui.column():
                ui.label("Customer")
                ui.label(call.get("customer_name", "N/A")).classes("font-semibold")
            
            with ui.column():
                ui.label("Location")
                ui.label(call.get("location_address", "N/A"))
            
            with ui.column():
                ui.label("Equipment")
                eq_type = call.get('equipment_type', 'Unit')
                unit_txt = f"{eq_type}-{call.get('unit_id')}" if call.get('unit_id') else (call.get("unit_name", "N/A"))
                ui.label(unit_txt or "N/A")

            with ui.column():
                ui.label("Specs")
                specs = []
                if call.get('tonnage'):
                    specs.append(f"{call.get('tonnage')}T")
                if call.get('refrigerant_type'):
                    specs.append(call.get('refrigerant_type'))
                ui.label(" | ".join(specs) or "N/A")
        
        if call.get("description"):
            ui.separator().classes("my-2")
            ui.label(call.get("description", "")).classes("text-sm")

        if call.get("materials_services") or call.get("labor_description"):
            ui.separator().classes("my-2")
            if call.get("materials_services"):
                ui.label("Materials & Services").classes("text-xs font-semibold")
                ui.label(call.get("materials_services", "")).classes("text-xs")
            if call.get("labor_description"):
                ui.label("Labor Description").classes("text-xs font-semibold mt-1")
                ui.label(call.get("labor_description", "")).classes("text-xs")
        
        # Footer: dates
        with ui.row().classes("text-xs gcc-muted mt-2 gap-4"):
            ui.label(f"Created: {call.get('created', '')[:16]}")
            if call.get("closed"):
                ui.label(f"Closed: {call.get('closed')[:16]}")


def show_ticket_detail(ticket: Dict[str, Any]) -> None:
    """Read-only detail dialog for service tickets (matches dashboard view)."""
    with ui.dialog() as dlg, ui.card().classes("gcc-card p-4 w-full max-w-4xl"):
        ui.label(f"Service Ticket #{ticket.get('ID','—')}").classes("text-lg font-bold")
        ui.label(
            f"Status: {ticket.get('status','—')} | Priority: {ticket.get('priority','—')} | Created: {(ticket.get('created') or '')[:19]}"
        ).classes("text-sm gcc-muted")

        ui.separator().classes("my-2")

        ui.label(f"Customer: {ticket.get('customer_name') or ticket.get('customer','—')}").classes("text-sm")
        ui.label(f"Location: {ticket.get('location_address') or ticket.get('location','—')}").classes("text-sm")
        eq_type = ticket.get('equipment_type', 'RTU')
        unit_txt = f"{eq_type}-{ticket.get('unit_id')}" if ticket.get('unit_id') else "—"
        ui.label(f"Unit: {unit_txt}").classes("text-sm")

        specs = []
        if ticket.get('make'):
            specs.append(f"Make: {ticket.get('make')}")
        if ticket.get('model'):
            specs.append(f"Model: {ticket.get('model')}")
        if ticket.get('refrigerant_type'):
            specs.append(f"Refrig: {ticket.get('refrigerant_type')}")
        if ticket.get('tonnage'):
            specs.append(f"Capacity: {ticket.get('tonnage')} Ton")
        if specs:
            ui.label(" | ".join(specs)).classes("text-sm gcc-muted")

        ui.separator().classes("my-2")

        ui.label("Title").classes("text-sm font-bold")
        ui.label(ticket.get("title") or "—").classes("text-sm")

        ui.separator().classes("my-2")

        ui.label("General Description").classes("text-sm font-bold")
        ui.textarea(value=ticket.get("description") or "").props("readonly autogrow").classes("w-full")

        ui.separator().classes("my-2")

        ui.label("Materials & Services").classes("text-sm font-bold")
        ui.textarea(value=ticket.get("materials_services") or "").props("readonly autogrow").classes("w-full")

        ui.separator().classes("my-2")

        ui.label("Labor Description").classes("text-sm font-bold")
        ui.textarea(value=ticket.get("labor_description") or "").props("readonly autogrow").classes("w-full")

        with ui.row().classes("justify-end mt-3 gap-2"):
            ui.button("Close", on_click=dlg.close).props("dense")

    dlg.open()


def show_close_dialog(call_id: int):
    """Show dialog to close ticket with reason"""
    close_reasons = [
        "Fixed - Issue Resolved",
        "Customer Cancelled",
        "No Access to Equipment",
        "Parts on Order",
        "Warranty Work",
        "Duplicate Call",
        "Unable to Reproduce",
        "Other"
    ]
    
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-6"):
        ui.label("Close Service Call").classes("text-xl font-bold mb-4")
        ui.label("Select a reason for closing this ticket:").classes("text-sm gcc-muted mb-3")
        
        reason_select = ui.select(close_reasons, label="Closing Reason *").classes("w-full")
        notes_input = ui.textarea("Additional Notes").classes("w-full").props("outlined rows=3")
        
        def on_confirm():
            if not reason_select.value:
                ui.notify("Please select a closing reason", type="negative")
                return
            
            # Update status and add reason to description
            conn = get_conn()
            try:
                current_desc = conn.execute(
                    "SELECT description FROM ServiceCalls WHERE ID = ?", (call_id,)
                ).fetchone()
                
                new_desc = f"{current_desc[0] or ''}\n\n[CLOSED: {reason_select.value}]"
                if notes_input.value:
                    new_desc += f"\n{notes_input.value}"
                
                conn.execute(
                    "UPDATE ServiceCalls SET status = ?, description = ?, closed = datetime('now') WHERE ID = ?",
                    ("Closed", new_desc, call_id)
                )
                conn.commit()
                ui.notify(f"✓ Service Call #{call_id} closed successfully", type="positive")
                dialog.close()
                ui.navigate.reload()
            except Exception as e:
                ui.notify(f"Error closing call: {e}", type="negative")
            finally:
                conn.close()
        
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Close Call", icon="check_circle", on_click=on_confirm).props("color=green")
    
    dialog.open()


def confirm_delete(call_id: int):
    """Confirm and delete service call"""
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-6"):
        ui.label("Delete Service Call?").classes("text-xl font-bold mb-2 text-red-400")
        ui.label(f"Ticket #{call_id}").classes("text-sm gcc-muted mb-4")
        ui.label("This action cannot be undone. All associated data will be permanently deleted.").classes("text-sm text-orange-300 mb-4")
        
        confirm_check = ui.checkbox("Yes, I confirm deletion")
        
        def on_confirm():
            if not confirm_check.value:
                ui.notify("Please check the confirmation box", type="negative")
                return
            
            try:
                if delete_service_call(call_id):
                    ui.notify(f"✓ Service Call #{call_id} permanently deleted", type="positive")
                    dialog.close()
                    ui.navigate.reload()
                else:
                    ui.notify("Failed to delete service call", type="negative")
            except Exception as e:
                ui.notify(f"Error deleting call: {e}", type="negative")
        
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Delete Permanently", icon="delete", on_click=on_confirm).props("color=red")
    
    dialog.open()


def show_print_call(call: Dict[str, Any]):
    """Use the same PDF generator as dashboard for consistency."""
    try:
        # Lazy import to avoid circulars
        from pages.dashboard import generate_service_order_pdf, _generate_ticket_no

        # Build data payload expected by generator
        data = {
            "customer": call.get('customer') or call.get('customer_name') or '—',
            "location": call.get('location') or call.get('location_address') or '—',
            "customer_phone": "—",
            "customer_email": "—",
            "unit_id": call.get('unit_id', 0),
            "equipment_type": call.get('equipment_type', 'RTU'),
            "make": call.get('make', '—'),
            "model": call.get('model', '—'),
            "serial": call.get('serial', '—'),
            "refrigerant_type": call.get('refrigerant_type', '—'),
            "voltage": call.get('voltage', '—'),
            "amperage": call.get('amperage', '—'),
            "btu_rating": call.get('btu_rating', '—'),
            "tonnage": call.get('tonnage', '—'),
            "breaker_size": call.get('breaker_size', '—'),
            "inst_date": call.get('unit_inst_date') or call.get('inst_date') or '—',
            "warranty_end_date": call.get('warranty_end_date', '—'),
            "status": call.get('status', '—'),
            "priority": call.get('priority', '—'),
            "title": call.get('title', '—'),
            "description": call.get('description', '—'),
            "materials_services": call.get('materials_services', '—'),
            "labor_description": call.get('labor_description', '—'),
            "created": call.get('created', ''),
        }

        # Dummy health/alerts placeholders (match dashboard behavior)
        health = {"score": 85, "status": "Good"}
        alerts = {"alerts": []}

        # Company profile lookup (shared with dashboard logic)
        company = {
            "company": "GCC TECHNOLOGY",
            "address1": "123 Tech Street",
            "address2": "",
            "city": "Tech City",
            "state": "TC",
            "zip": "12345",
            "phone": "(555) 123-4567",
            "email": "support@gcc.com",
            "website": "www.gcc.com"
        }
        conn = get_conn()
        try:
            row = conn.execute("SELECT * FROM CompanyProfile LIMIT 1").fetchone()
            if row is None:
                row = conn.execute("SELECT * FROM CompanyInfo LIMIT 1").fetchone()
            if row:
                row = dict(row)
                company = {
                    "company": row.get("company_name") or row.get("name") or row.get("company") or company["company"],
                    "address1": row.get("address1") or "",
                    "address2": row.get("address2") or "",
                    "city": row.get("city") or "",
                    "state": row.get("state") or "",
                    "zip": row.get("zip") or "",
                    "phone": row.get("phone") or row.get("fax") or company.get("phone"),
                    "email": row.get("email") or company.get("email"),
                    "service_email": row.get("service_email") or row.get("email") or "",
                    "business_license": row.get("business_license") or "",
                    "website": row.get("website") or company.get("website"),
                }
        except Exception:
            pass
        finally:
            conn.close()

        ticket_no = _generate_ticket_no(call.get('ID', 0))
        pdf_path, pdf_bytes = generate_service_order_pdf(ticket_no, data, health, alerts, company)

        # Offer user choice: preview/print or download
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

        with ui.dialog() as dlg, ui.card().classes("gcc-card p-4 max-w-xl"):
            ui.label(f"Service Ticket #{call.get('ID', '—')} PDF Ready").classes("text-lg font-bold")
            ui.label(os.path.basename(pdf_path)).classes("text-sm gcc-muted mb-2")

            with ui.row().classes("gap-2 mt-2 justify-end"):
                ui.button("Open & Print", icon="print", on_click=lambda: ui.run_javascript(
                    "(function(){const b64='" + pdf_b64 + "';"+
                    "const byteChars=atob(b64);const byteNums=new Array(byteChars.length);"+
                    "for(let i=0;i<byteChars.length;i++){byteNums[i]=byteChars.charCodeAt(i);}"+
                    "const byteArray=new Uint8Array(byteNums);const blob=new Blob([byteArray],{type:'application/pdf'});"+
                    "const url=URL.createObjectURL(blob);window.open(url,'_blank');})();"
                )).props("color=blue")
                ui.button("Download PDF", icon="download", on_click=lambda: ui.download(pdf_bytes, filename=os.path.basename(pdf_path))).props("color=green")
                ui.button("Close", on_click=dlg.close).props("flat")

        dlg.open()
        ui.notify("PDF generated", type="positive")
    except Exception as e:
        ui.notify(f"PDF generation failed: {e}", type="negative")


def show_print_form(title: str, description: str, materials: str, labor: str, priority: str, status: str):
    """Show printable version of form before submission - matching PDF format"""
    from datetime import datetime
    
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-8 max-w-4xl bg-white text-black"):
        # Header
        ui.label("GCC TECHNOLOGY").classes("text-sm font-bold")
        ui.label("HVAC Service Order Invoice").classes("text-lg font-bold mb-1")
        
        # Ticket Info Row
        with ui.grid(columns=3).classes("gap-4 mb-4 w-full"):
            with ui.column():
                ui.label("Date").classes("text-xs font-bold gcc-muted")
                ui.label(datetime.now().strftime("%m/%d/%Y")).classes("font-mono text-sm")
            with ui.column():
                ui.label("Time").classes("text-xs font-bold gcc-muted")
                ui.label(datetime.now().strftime("%H:%M:%S")).classes("font-mono text-sm")
            with ui.column():
                ui.label("Status").classes("text-xs font-bold gcc-muted")
                ui.label(status).classes("font-mono text-sm")
        
        ui.separator().classes("my-3")
        
        # Priority
        ui.label("Priority").classes("text-xs font-bold")
        ui.label(priority).classes("text-sm mb-3")
        
        ui.separator().classes("my-3")
        
        # Title
        ui.label("Title").classes("text-xs font-bold")
        ui.label(title or "(Not filled)").classes("text-sm mb-3 whitespace-pre-wrap")
        
        # Description
        if description:
            ui.separator().classes("my-3")
            ui.label("General Description").classes("text-xs font-bold")
            with ui.element().classes("bg-gray-100 p-3 rounded text-xs mb-3"):
                ui.label(description).classes("text-xs whitespace-pre-wrap")
        
        # Materials
        if materials:
            ui.separator().classes("my-3")
            ui.label("Materials & Services").classes("text-xs font-bold")
            with ui.element().classes("bg-gray-100 p-3 rounded text-xs mb-3"):
                ui.label(materials).classes("text-xs whitespace-pre-wrap")
        
        # Labor
        if labor:
            ui.separator().classes("my-3")
            ui.label("Labor Description").classes("text-xs font-bold")
            with ui.element().classes("bg-gray-100 p-3 rounded text-xs mb-3"):
                ui.label(labor).classes("text-xs whitespace-pre-wrap")
        
        ui.separator().classes("my-4")
        
        # Signature area
        ui.label("Customer Signature: _______________________     Date: __________").classes("text-xs font-mono")
        
        with ui.row().classes("justify-end gap-2 mt-6"):
            ui.button("Close", on_click=dialog.close).props("flat")
            ui.button("Print", icon="print", on_click=lambda: ui.run_javascript("window.print()")).props("color=blue")
    
    dialog.open()


def show_print_all(search_term: str, status: str, priority: str, customer_id: Optional[int]):
    """Show printable list of all service calls - matching PDF format"""
    status_filter = None if status == "All" else status
    priority_filter = None if priority == "All" else priority
    
    if search_term:
        calls = search_service_calls(search_term, customer_id)
    else:
        calls = list_service_calls(customer_id=customer_id, status=status_filter, priority=priority_filter, limit=100)
    
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-6 max-w-5xl max-h-[80vh] overflow-auto bg-white text-black"):
        # Header
        ui.label("GCC TECHNOLOGY").classes("text-sm font-bold")
        ui.label("SERVICE CALLS REPORT").classes("text-lg font-bold")
        ui.label(f"Generated: {datetime.now().strftime('%m/%d/%Y %H:%M')}").classes("text-xs gcc-muted mb-4")
        
        ui.separator().classes("my-2")
        
        if not calls:
            ui.label("No service calls to print").classes("text-gray-400")
        else:
            with ui.column().classes("gap-3 w-full"):
                for call in calls:
                    with ui.card().classes("p-3 border-l-4 border-blue-500 bg-gray-50"):
                        # Header row
                        with ui.row().classes("items-center justify-between mb-2"):
                            ui.label(f"#{call['ID']} - {call.get('title', 'Untitled')}").classes("text-sm font-bold flex-1")
                            ui.label(f"{call.get('status', '—')} | {call.get('priority', '—')}").classes("text-xs")

                        # Details row
                        with ui.grid(columns=5).classes("gap-2 text-xs"):
                            ui.label(f"Customer: {call.get('customer_name') or call.get('customer') or 'N/A'}")
                            ui.label(f"Location: {call.get('location_address') or call.get('location') or 'N/A'}")
                            eq_type = call.get('equipment_type', 'RTU')
                            unit_txt = f"{eq_type}-{call.get('unit_id')}" if call.get("unit_id") else (call.get('unit_name') or "—")
                            ui.label(f"Unit: {unit_txt}")
                            specs = []
                            if call.get('tonnage'):
                                specs.append(f"{call.get('tonnage')}T")
                            if call.get('refrigerant_type'):
                                specs.append(call.get('refrigerant_type'))
                            ui.label(f"Specs: {' | '.join(specs) if specs else '—'}")
                            ui.label(f"Created: {(call.get('created') or '')[:10]}")
        
        ui.separator().classes("my-4")
        
        with ui.row().classes("justify-end gap-2"):
            ui.button("Close", on_click=dialog.close).props("flat")
            ui.button("Print", icon="print", on_click=lambda: ui.run_javascript("window.print()")).props("color=blue")
    
    dialog.open()


from datetime import datetime
from core.db import get_conn


def render_call_form(customer_id: Optional[int], user: Dict[str, Any], hierarchy: int):
    """Form to create new service call - Professional Service Order Layout"""
    
    from datetime import datetime
    
    with ui.card().classes("gcc-card p-6 max-w-5xl"):
        # ===== HEADER SECTION =====
        ui.label("SERVICE ORDER").classes("text-2xl font-bold mb-1")
        ui.label("GCC Technology HVAC Service").classes("text-sm gcc-muted mb-4")
        
        ui.separator().classes("my-3")
        
        # Ticket info row (top right)
        with ui.grid(columns=3).classes("gap-8 mb-4 w-full"):
            with ui.column():
                ui.label("Ticket #").classes("text-xs font-bold gcc-muted")
                ui.label("(Auto-generated)").classes("text-sm font-mono")
            
            with ui.column():
                ui.label("Date").classes("text-xs font-bold gcc-muted")
                ui.label(datetime.now().strftime("%m/%d/%Y")).classes("text-sm font-mono")
            
            with ui.column():
                ui.label("Time").classes("text-xs font-bold gcc-muted")
                ui.label(datetime.now().strftime("%H:%M:%S")).classes("text-sm font-mono")
        
        ui.separator().classes("my-4")
        
        # ===== CONTACT INFORMATION & SERVICE STATUS (Two columns) =====
        with ui.row().classes("w-full gap-6"):
            # LEFT: CONTACT INFORMATION
            with ui.column().classes("w-1/2"):
                ui.label("CONTACT INFORMATION").classes("text-sm font-bold border-b pb-2 mb-3")
                
                # Customer selection (admin/tech only)
                if hierarchy <= 3 and not customer_id:
                    customers = list_customers(search="")
                    customer_options = {c["ID"]: c.get("company") or f"{c.get('first_name','')} {c.get('last_name','')}" for c in customers}
                    customer_select = ui.select(customer_options, label="Customer *").classes("w-full mb-2").props("outlined dense")
                else:
                    customer_select = None
                
                # Location
                location_select = ui.select({}, label="Location").classes("w-full mb-2").props("outlined dense")
                
                # Unit/Equipment
                unit_select = ui.select({}, label="Equipment Unit").classes("w-full mb-2").props("outlined dense")
                
                # Dynamic helper info (read-only display)
                info_label = ui.label("").classes("text-xs gcc-muted mt-2 p-2 bg-gray-800 rounded")
            
            # RIGHT: SERVICE STATUS
            with ui.column().classes("w-1/2"):
                ui.label("SERVICE STATUS").classes("text-sm font-bold border-b pb-2 mb-3")
                
                with ui.grid(columns=2).classes("gap-3"):
                    status_select = ui.select(
                        {"Open": "Open", "In Progress": "In Progress", "Closed": "Closed"},
                        value="Open",
                        label="Status"
                    ).classes("w-full").props("outlined dense")
                    
                    priority_select = ui.select(
                        {"Low": "Low", "Normal": "Normal", "High": "High", "Emergency": "Emergency"},
                        value="Normal",
                        label="Priority"
                    ).classes("w-full").props("outlined dense")
                
                ui.label("ALERT SUMMARY").classes("text-xs font-bold mt-3 mb-1")
                alert_display = ui.textarea(value="No alerts").classes("w-full text-xs").props("readonly rows=3")
        
        ui.separator().classes("my-4")
        
        # ===== TITLE / BRIEF DESCRIPTION =====
        title_input = ui.input("Work Order Title *", placeholder="Brief description of the service issue").classes("w-full mb-2").props("outlined")
        
        # ===== GENERAL DESCRIPTION =====
        description_input = ui.textarea("GENERAL DESCRIPTION [TECH TO FILL]", placeholder="Detailed description of the issue and findings").classes("w-full mb-4").props("outlined autogrow")
        
        ui.separator().classes("my-4")
        
        # ===== MATERIALS & SERVICES (Large section) =====
        ui.label("MATERIALS & SERVICES [TECH TO FILL]").classes("text-sm font-bold mb-2")
        materials_input = ui.textarea(
            value="",
            placeholder="List all materials and services provided (one per line or as needed)"
        ).classes("w-full").props("outlined rows=6 autogrow")
        
        ui.separator().classes("my-4")
        
        # ===== LABOR DESCRIPTION (Large section) =====
        ui.label("LABOR DESCRIPTION [TECH TO FILL]").classes("text-sm font-bold mb-2")
        labor_input = ui.textarea(
            value="",
            placeholder="Describe labor performed, time spent, and any recommendations"
        ).classes("w-full").props("outlined rows=6 autogrow")
        
        ui.separator().classes("my-4")
        
        # ===== SIGNATURE SECTION =====
        ui.label("SIGN-OFF").classes("text-sm font-bold border-b pb-2 mb-3")
        with ui.grid(columns=2).classes("gap-6"):
            with ui.column():
                ui.label("Customer Signature ________________").classes("text-xs gcc-muted")
                ui.label("Date ________").classes("text-xs gcc-muted mt-4")
            
            with ui.column():
                ui.label("Technician: " + (user.get("name") or user.get("username") or "—")).classes("text-xs")
                ui.label("User ID: " + str(user.get("ID") or "—")).classes("text-xs gcc-muted")
        
        # ===== DYNAMIC CASCADING SELECTS =====
        def on_customer_change():
            if customer_select:
                cust_id = customer_select.value
                if cust_id:
                    locations = list_locations(customer_id=cust_id)
                    location_select.options = {loc["ID"]: loc.get("PropertyName") or loc.get("address1", "Unknown") for loc in locations}
                    location_select.value = None
                    location_select.update()
                    update_info_display()
        
        def on_location_change():
            loc_id = location_select.value
            if loc_id:
                units = list_units(location_id=loc_id)
                unit_select.options = {u["unit_id"]: u.get("unit_tag") or f"RTU-{u['unit_id']}" for u in units}
                unit_select.value = None
                unit_select.update()
                update_info_display()
        
        def update_info_display():
            """Update info label with location/unit details"""
            text_parts = []
            if location_select.value:
                locs = list_locations(customer_id=customer_select.value if customer_select else customer_id)
                loc = next((l for l in locs if l["ID"] == location_select.value), None)
                if loc:
                    addr = loc.get("address1") or "—"
                    city = loc.get("city") or ""
                    state = loc.get("state") or ""
                    text_parts.append(f"📍 {addr}")
                    if city or state:
                        text_parts.append(f"   {city}, {state}")
            
            if unit_select.value:
                units = list_units(location_id=location_select.value)
                unit = next((u for u in units if u["unit_id"] == unit_select.value), None)
                if unit:
                    eq_type = unit.get('equipment_type', 'Unit')
                    make = unit.get('make', '?')
                    model = unit.get('model', '?')
                    tonnage = unit.get('tonnage', '')
                    refrig = unit.get('refrigerant_type', '')
                    details = f"{make} {model}"
                    if tonnage:
                        details += f" ({tonnage} Ton)"
                    if refrig:
                        details += f" - {refrig}"
                    text_parts.append(f"🔧 {eq_type}: {details}")
            
            info_label.text = "\n".join(text_parts) if text_parts else "(Select location & unit)"
        
        if customer_select:
            customer_select.on_value_change(on_customer_change)
        location_select.on_value_change(on_location_change)
        unit_select.on_value_change(lambda: update_info_display())
        
        # ===== SUBMIT BUTTON =====
        def on_submit():
            # Validation
            if not title_input.value:
                ui.notify("Work Order Title is required", type="negative")
                return
            
            final_customer_id = customer_select.value if customer_select else customer_id
            if not final_customer_id:
                ui.notify("Customer is required", type="negative")
                return
            
            # Create service call
            data = {
                "customer_id": final_customer_id,
                "location_id": location_select.value,
                "unit_id": unit_select.value,
                "title": title_input.value,
                "description": description_input.value,
                "priority": priority_select.value,
                "status": status_select.value,
                "requested_by_login_id": user.get("login_id") or user.get("ID"),
                "materials_services": materials_input.value,
                "labor_description": labor_input.value
            }
            
            try:
                call_id = create_service_call(data)
                ui.notify(f"✓ Service Order #{call_id} created successfully!", type="positive")
                # Clear form
                title_input.value = ""
                description_input.value = ""
                ui.navigate.to("/tickets")
            except Exception as e:
                ui.notify(f"Error creating service call: {e}", type="negative")
        
        with ui.row().classes("justify-between gap-2 mt-6"):
            ui.button("Print Form", icon="print", on_click=lambda: show_print_form(
                title_input.value, description_input.value, materials_input.value, 
                labor_input.value, priority_select.value, status_select.value
            )).props("outline")
            ui.button("Create Service Order", icon="add", on_click=on_submit).props("color=green size=md")


def show_edit_dialog(call: Dict[str, Any]):
    """Show dialog to edit service call"""
    call_id = call.get("ID")
    
    # Sanitize status and priority values from database
    status_val = call.get("status") or "Open"
    if status_val not in ["Open", "In Progress", "Closed"]:
        status_val = "Open"
    
    priority_val = call.get("priority") or "Normal"
    if priority_val not in ["Low", "Normal", "High", "Emergency"]:
        priority_val = "Normal"
    
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-6 min-w-[600px]"):
        ui.label(f"Edit Service Call #{call_id}").classes("text-xl font-bold mb-4")
        
        title_input = ui.input("Title", value=call.get("title", "")).classes("w-full")
        
        with ui.grid(columns=2).classes("gap-4 w-full"):
            status_select = ui.select(
                {"Open": "Open", "In Progress": "In Progress", "Closed": "Closed"},
                value=status_val,
                label="Status"
            ).props("outlined dense")
            
            priority_select = ui.select(
                {"Low": "Low", "Normal": "Normal", "High": "High", "Emergency": "Emergency"},
                value=priority_val,
                label="Priority"
            ).props("outlined dense")
        
        description_input = ui.textarea("Description", value=call.get("description", "")).classes("w-full").props("rows=4")
        
        ui.separator().classes("my-2")
        ui.label("Materials & Labor").classes("text-sm font-semibold mb-2")
        
        materials_input = ui.textarea("Materials/Services", value=call.get("materials_services", "")).classes("w-full").props("rows=3")
        labor_input = ui.textarea("Labor Description", value=call.get("labor_description", "")).classes("w-full").props("rows=3")
        
        def on_save():
            data = {
                "title": title_input.value,
                "description": description_input.value,
                "status": status_select.value,
                "priority": priority_select.value,
                "materials_services": materials_input.value,
                "labor_description": labor_input.value
            }
            
            if update_service_call(call_id, data):
                ui.notify("Service call updated", type="positive")
                dialog.close()
                ui.navigate.reload()
            else:
                ui.notify("Failed to update service call", type="negative")
        
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", icon="save", on_click=on_save).props("color=green")
    
    dialog.open()




def render_ticket_stats(customer_id: Optional[int] = None):
    """Display ticket statistics"""
    stats = get_ticket_stats(customer_id)
    
    with ui.row().classes("w-full gap-4 mb-4"):
        # Total
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Total Tickets").classes("text-sm gcc-muted")
            ui.label(str(stats.get("total", 0))).classes("text-3xl font-bold")
        
        # Open
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Open").classes("text-sm gcc-muted")
            ui.label(str(stats.get("open", 0))).classes("text-3xl font-bold text-blue-400")
        
        # In Progress
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("In Progress").classes("text-sm gcc-muted")
            ui.label(str(stats.get("in_progress", 0))).classes("text-3xl font-bold text-yellow-400")
        
        # Resolved
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Resolved").classes("text-sm gcc-muted")
            ui.label(str(stats.get("resolved", 0))).classes("text-3xl font-bold text-green-400")
        
        # Urgent
        with ui.card().classes("gcc-card p-4 flex-1"):
            ui.label("Urgent").classes("text-sm gcc-muted")
            ui.label(str(stats.get("urgent", 0))).classes("text-3xl font-bold text-red-400")


def render_tickets_list(customer_id: Optional[int] = None, hierarchy: int = 5):
    """Display tickets list with search and filters"""
    
    with ui.card().classes("gcc-card p-4 mb-4"):
        with ui.row().classes("w-full gap-4 items-center"):
            search_input = ui.input("Search", placeholder="Ticket #, Title, Description").classes("flex-1")
            status_filter = ui.select(
                ["All", "open", "in_progress", "on_hold", "resolved", "closed"],
                value="All",
                label="Status"
            ).classes("w-40")
            ui.button("Search", icon="search", on_click=lambda: refresh_tickets())
    
    # Tickets container
    tickets_container = ui.column().classes("w-full gap-3")
    
    def refresh_tickets():
        tickets_container.clear()
        with tickets_container:
            search_term = search_input.value
            status = None if status_filter.value == "All" else status_filter.value
            
            if search_term:
                tickets = search_tickets(search_term, customer_id)
            else:
                tickets = list_tickets(customer_id=customer_id, status=status, limit=50)
            
            if not tickets:
                ui.label("No tickets found").classes("text-gray-400 italic")
                return
            
            for ticket in tickets:
                render_ticket_card(ticket, hierarchy)
    
    refresh_tickets()


def render_ticket_card(ticket: Dict[str, Any], hierarchy: int):
    """Display single ticket card"""
    ticket_id = ticket.get("ticket_id")
    status = ticket.get("status", "open")
    priority = ticket.get("priority", "medium")
    
    # Status colors
    status_colors = {
        "open": "border-blue-500",
        "in_progress": "border-yellow-500",
        "on_hold": "border-orange-500",
        "resolved": "border-green-500",
        "closed": "border-gray-500",
        "cancelled": "border-red-500"
    }
    
    # Priority badges
    priority_colors = {
        "low": "bg-gray-700",
        "medium": "bg-blue-700",
        "high": "bg-orange-700",
        "urgent": "bg-red-700"
    }
    
    border_class = status_colors.get(status, "border-gray-500")
    priority_class = priority_colors.get(priority, "bg-gray-700")
    
    with ui.card().classes(f"gcc-card p-4 border-l-4 {border_class}"):
        with ui.row().classes("w-full items-start justify-between mb-2"):
            # Left: Ticket number and title
            with ui.column().classes("gap-1 flex-1"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(ticket.get("ticket_number", "")).classes("font-mono text-sm gcc-muted")
                    ui.badge(priority.upper()).classes(f"{priority_class} text-xs")
                    ui.badge(status.replace("_", " ").upper()).classes("bg-gray-800 text-xs")
                
                ui.label(ticket.get("title", "Untitled")).classes("text-lg font-bold")
            
            # Right: Actions
            if hierarchy <= 3:  # Admin/Tech can edit
                with ui.row().classes("gap-2"):
                    ui.button(icon="edit", on_click=lambda t=ticket: show_edit_dialog(t)).props("flat dense")
                    ui.button(icon="delete", on_click=lambda tid=ticket_id: confirm_delete(tid)).props("flat dense color=red")
        
        # Details
        with ui.grid(columns=3).classes("gap-2 text-sm gcc-muted"):
            with ui.column():
                ui.label("Customer")
                ui.label(ticket.get("customer_name", "N/A")).classes("font-semibold")
            
            with ui.column():
                ui.label("Location")
                ui.label(ticket.get("location_address", "N/A"))
            
            with ui.column():
                ui.label("Assigned To")
                ui.label(ticket.get("assigned_to_name", "Unassigned"))
        
        if ticket.get("description"):
            ui.separator().classes("my-2")
            ui.label(ticket.get("description", "")).classes("text-sm")
        
        # Footer: dates
        with ui.row().classes("text-xs gcc-muted mt-2 gap-4"):
            ui.label(f"Created: {ticket.get('created_at', '')[:16]}")
            if ticket.get("scheduled_date"):
                ui.label(f"Scheduled: {ticket.get('scheduled_date')}")


def render_my_tickets(employee_id: int):
    """Display tickets assigned to current user"""
    tickets = get_my_tickets(employee_id)
    
    if not tickets:
        ui.label("You have no assigned tickets").classes("text-gray-400 italic")
        return
    
    for ticket in tickets:
        render_ticket_card(ticket, hierarchy=3)


def render_ticket_form(customer_id: Optional[int], user: Dict[str, Any], hierarchy: int):
    """Form to create new ticket"""
    
    with ui.card().classes("gcc-card p-6 max-w-4xl"):
        ui.label("Create Service Ticket").classes("text-xl font-bold mb-4")
        
        # Customer selection (admin/tech only)
        if hierarchy <= 3 and not customer_id:
            customers = list_customers(search="", limit=100)
            customer_options = {c["ID"]: c.get("company") or f"{c.get('first_name','')} {c.get('last_name','')}" for c in customers}
            customer_select = ui.select(customer_options, label="Customer *").classes("w-full")
        else:
            customer_select = None
        
        with ui.grid(columns=2).classes("gap-4 w-full"):
            title_input = ui.input("Title *", placeholder="Brief description of issue").classes("col-span-2")
            
            priority_select = ui.select(
                ["low", "medium", "high", "urgent"],
                value="medium",
                label="Priority"
            )
            
            category_input = ui.input("Category", placeholder="e.g., Maintenance, Repair, Installation")
            
            scheduled_date = ui.input("Scheduled Date", placeholder="YYYY-MM-DD HH:MM")
            
            # Location and Unit selects (dynamically populated)
            location_select = ui.select({}, label="Location").classes("w-full")
            unit_select = ui.select({}, label="Equipment Unit").classes("w-full")
        
        description_input = ui.textarea("Description", placeholder="Detailed description of the issue").classes("w-full").props("rows=4")
        notes_input = ui.textarea("Internal Notes", placeholder="Notes for technicians").classes("w-full").props("rows=2")
        
        def on_customer_change():
            if customer_select:
                cust_id = customer_select.value
                if cust_id:
                    # Load locations
                    locations = list_locations(customer_id=cust_id)
                    location_select.options = {loc["ID"]: loc.get("PropertyName") or loc.get("address1", "Unknown") for loc in locations}
                    location_select.update()
        
        def on_location_change():
            loc_id = location_select.value
            if loc_id:
                # Load units
                units = list_units(location_id=loc_id)
                unit_select.options = {u["unit_id"]: u.get("unit_tag") or f"Unit {u['unit_id']}" for u in units}
                unit_select.update()
        
        if customer_select:
            customer_select.on_value_change(on_customer_change)
        location_select.on_value_change(on_location_change)
        
        def on_submit():
            # Validation
            if not title_input.value:
                ui.notify("Title is required", type="negative")
                return
            
            final_customer_id = customer_select.value if customer_select else customer_id
            if not final_customer_id:
                ui.notify("Customer is required", type="negative")
                return
            
            # Create ticket
            data = {
                "customer_id": final_customer_id,
                "location_id": location_select.value,
                "unit_id": unit_select.value,
                "title": title_input.value,
                "description": description_input.value,
                "priority": priority_select.value,
                "status": "open",
                "category": category_input.value,
                "scheduled_date": scheduled_date.value if scheduled_date.value else None,
                "created_by": user.get("employee_id") or 1,
                "notes": notes_input.value
            }
            
            try:
                ticket_id = create_ticket(data)
                ui.notify(f"Ticket created successfully!", type="positive")
                # Clear form
                title_input.value = ""
                description_input.value = ""
                notes_input.value = ""
                ui.navigate.to("/tickets")
            except Exception as e:
                ui.notify(f"Error creating ticket: {e}", type="negative")
        
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Create Ticket", icon="add", on_click=on_submit).props("color=green")

