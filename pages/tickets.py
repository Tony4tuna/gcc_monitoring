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
from ui.table_page import table_page

@ui.page("/tickets")
def tickets_page():
    """Service Calls page - Dashboard-styled with expanded layout"""
    if not require_login():
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy") or 5)
    customer_id = user.get("customer_id")
    
    with layout("Service Calls", show_logout=True, hierarchy=hierarchy, show_back=True, back_to="/"):
        with ui.column().classes("w-full h-full flex-1 gap-4").style("display: flex; flex-direction: column; overflow: hidden;"):
            # Stats row
            render_stats(customer_id if hierarchy == 4 else None)
            
            # Main content - dashboard-styled card container with overflow control
            with ui.element("div").classes("flex-1 min-h-0 w-full").style("display: flex; flex-direction: column; overflow: hidden;"):
                render_calls_table(customer_id if hierarchy == 4 else None, hierarchy)
            
            # Divider card
            ui.separator().classes("my-2")
            
            # Footer card to prevent grid overflow
            with ui.card().classes("gcc-card p-3 flex-shrink-0"):
                ui.label("Service Calls Management").classes("text-xs gcc-muted")

def render_stats(customer_id: Optional[int] = None):
    """Display service call statistics"""
    stats = get_service_call_stats(customer_id)
    
    with ui.row().classes("w-full gap-4 mb-2 flex-shrink-0"):
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


def render_calls_table(customer_id: Optional[int] = None, hierarchy: int = 5):
    """Display service calls in spacious card layout - dashboard-styled"""
    from core.customers_repo import list_customers as _list_customers
    from core.locations_repo import list_locations as _list_locations
    
    # Main dashboard-styled card container
    with ui.element("div").classes("gcc-dashboard-grid-item flex-shrink-0").style("height: 90%; max-height: 92%; display: flex; flex-direction: column; overflow: hidden;"):
        
        # Title in top left corner
        ui.label("Service Tickets").classes("text-lg font-bold mb-3")
        
        # Header with search
        with ui.row().classes("w-full items-center justify-between mb-4 flex-wrap gap-3"):
            search_input = ui.input("Search...").classes("w-64")
        
        # Filters row - inline and spacious
        with ui.row().classes("gap-4 items-center flex-wrap mb-4 pb-3").style("border-bottom: 1px solid var(--border)"):
            status_filter = ui.select(["All", "Open", "In Progress", "Closed"], value="Open", label="Status").classes("w-40")
            priority_filter = ui.select(["All", "Low", "Normal", "High", "Emergency"], value="All", label="Priority").classes("w-40")

            # Admin filters - customer and location selectors
            customer_sel = None
            location_sel = None
            if hierarchy <= 3:  # Admin/tech users get customer/location filters
                customers = _list_customers("")
                customer_opts = {int(c["ID"]): f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip() for c in customers}
                customer_sel = ui.select(customer_opts, label="Client").classes("w-72")

                location_sel = ui.select({}, label="Location").classes("w-56")
                location_sel.disable()
            
            ui.space()  # Push action buttons to the right
        
        # Action buttons row - professional toolbar
        with ui.row().classes("gap-2 mb-4 pb-3 flex-wrap").style("border-bottom: 1px solid var(--border)"):
            new_btn = ui.button(icon="add_circle", text="New Call").props("flat dense color=positive").tooltip("Create New Service Call")
            view_btn = ui.button(icon="visibility", text="View").props("flat dense").tooltip("View Details")
            edit_btn = ui.button(icon="edit", text="Edit").props("flat dense").tooltip("Edit Service Call")
            close_btn = ui.button(icon="check_circle", text="Close").props("flat dense color=green").tooltip("Close Call with Reason")
            delete_btn = ui.button(icon="delete", text="Delete").props("flat dense color=negative").tooltip("Delete Service Call")
            print_btn = ui.button(icon="print", text="Print").props("flat dense").tooltip("Print Work Order")
            email_btn = ui.button(icon="mail", text="Email").props("flat dense color=blue").tooltip("Send Email to Admin")
            refresh_btn = ui.button(icon="refresh", text="Refresh").props("flat dense").tooltip("Refresh List")
            
            # Wire initial click handlers
            new_btn.on_click(lambda: open_ticket_dialog("new"))
            view_btn.on_click(lambda: open_ticket_dialog("view"))
            edit_btn.on_click(lambda: open_ticket_dialog("edit"))
            close_btn.on_click(lambda: open_ticket_dialog("close"))
            delete_btn.on_click(lambda: open_ticket_dialog("delete"))
            print_btn.on_click(lambda: open_ticket_dialog("print"))
            email_btn.on_click(lambda: open_ticket_dialog("email"))
            refresh_btn.on_click(lambda: refresh_calls())

        # Table definition - 7 columns with more spacing
        columns = [
            {"name": "ID", "label": "ID", "field": "ID", "align": "left", "sortable": True},
            {"name": "title", "label": "Title", "field": "title", "align": "left", "sortable": True},
            {"name": "customer", "label": "Customer", "field": "customer", "align": "left"},
            {"name": "location", "label": "Location", "field": "location", "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "align": "center"},
            {"name": "priority", "label": "Priority", "field": "priority", "align": "center"},
            {"name": "created", "label": "Created", "field": "created", "align": "left"},
        ]

        # Spacious table with more padding - constrained height
        table = ui.table(columns=columns, rows=[], row_key="ID", selection="single") \
            .classes("gcc-dashboard-table w-full") \
            .props('dense flat virtual-scroll')
        
        empty_label = ui.label("No service calls found. Click New Call to create one.").classes("gcc-muted text-center py-8")
        empty_label.visible = False

        def update_button_states():
            """Smart enable/disable based on selection and status"""
            has_selection = bool(table.selected)
            
            # Disable New when a row is selected (same logic as other grids)
            if has_selection:
                new_btn.disable()
            else:
                new_btn.enable()

            if has_selection:
                view_btn.enable()
                edit_btn.enable() if hierarchy <= 3 else edit_btn.disable()
                
                selected = table.selected[0]
                if selected.get("status") != "Closed":
                    close_btn.enable() if hierarchy <= 3 else close_btn.disable()
                    delete_btn.disable()
                else:
                    close_btn.disable()
                    delete_btn.enable() if hierarchy <= 3 else delete_btn.disable()
                print_btn.enable()
            else:
                view_btn.disable()
                edit_btn.disable()
                close_btn.disable()
                delete_btn.disable()
                print_btn.disable()

        def refresh_calls():
            """Load and filter service calls"""
            search_term = (search_input.value or "").strip()
            status = None if status_filter.value == "All" else status_filter.value
            priority = None if priority_filter.value == "All" else priority_filter.value

            # Determine filters based on selectors / role
            effective_customer_id = customer_id
            if customer_sel and customer_sel.value:
                effective_customer_id = int(customer_sel.value)
            
            effective_location_id = None
            if location_sel and location_sel.value:
                effective_location_id = int(location_sel.value)

            # Load from database
            if search_term:
                calls = search_service_calls(search_term, effective_customer_id)
            else:
                calls = list_service_calls(
                    customer_id=effective_customer_id,
                    location_id=effective_location_id,
                    status=status,
                    priority=priority,
                    limit=100,
                )

            rows = []
            for call in calls:
                customer_name = call.get("customer_name") or call.get("customer") or "—"

                rows.append({
                    "ID": call.get("ID"),
                    "title": (call.get("title") or "Untitled")[:60],
                    "customer": customer_name[:40],
                    "location": (call.get("location_address") or call.get("location") or "—")[:60],
                    "status": call.get("status", "—"),
                    "priority": call.get("priority", "—"),
                    "created": (call.get("created") or "")[:16],
                    "_full_data": call,
                })

            table.rows = rows
            table.update()
            empty_label.visible = len(rows) == 0
            empty_label.update()
            update_button_states()

        def update_locations():
            """Cascade customer selection to location filter"""
            if not customer_sel or not location_sel:
                refresh_calls()
                return
            
            if not customer_sel.value:
                location_sel.options = {}
                location_sel.value = None
                location_sel.update()
                location_sel.disable()
                refresh_calls()
                return
            
            locs = _list_locations("", int(customer_sel.value))
            location_sel.options = {int(l["ID"]): f"{l.get('address1','')} — {l.get('city','')}, {l.get('state','')}".strip() for l in locs}
            location_sel.value = None
            location_sel.enable()
            location_sel.update()
            refresh_calls()

        def open_ticket_dialog(mode: str):
            """Open dialog based on mode: new/view/edit/close/delete/print"""
            if mode == "new":
                # Create empty call structure for new service call
                user = current_user() or {}
                new_call = {
                    "ID": None,
                    "customer_id": customer_id if hierarchy == 4 else None,
                    "location_id": None,
                    "unit_id": None,
                    "status": "Open",
                    "priority": "Normal",
                    "title": "Work Order",
                    "description": "",
                    "materials_services": "",
                    "labor_description": ""
                }
                show_edit_dialog(new_call, mode="create", user=user, hierarchy=hierarchy)
                return

            if not table.selected:
                ui.notify("Select a service call first", type="warning")
                return

            selected = table.selected[0]
            full_data = selected.get("_full_data", selected)
            call_id = selected["ID"]

            if mode == "view":
                show_ticket_detail(full_data)
            elif mode == "edit":
                user = current_user() or {}
                show_edit_dialog(full_data, mode="edit", user=user, hierarchy=hierarchy)
            elif mode == "close":
                show_close_dialog(call_id)
            elif mode == "delete":
                confirm_delete(call_id)
            elif mode == "print":
                show_print_call(full_data)
            elif mode == "email":
                send_ticket_email(call_id)

        # Wire up event handlers
        table.on("update:selected", lambda: update_button_states())
        search_input.on("keydown.enter", lambda: refresh_calls())
        status_filter.on_value_change(lambda: refresh_calls())
        priority_filter.on_value_change(lambda: refresh_calls())

        if customer_sel:
            customer_sel.on_value_change(lambda: update_locations())
        if location_sel:
            location_sel.on_value_change(lambda: refresh_calls())

        # Initial load
        update_button_states()
        refresh_calls()


def show_ticket_detail(ticket: Dict[str, Any]) -> None:
    """Read-only detail dialog for service tickets - uses unified edit dialog in view mode."""
    show_edit_dialog(ticket, mode="view")


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
        notes_input = ui.textarea("Additional Notes").classes("w-full bg-gray-900 text-white").props("outlined rows=3")
        
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


def send_ticket_email(call_id: int):
    """Send ticket email with recipient picker dialog"""
    from core.tickets_repo import send_ticket_email as send_email_repo, get_service_call
    from core.email_settings import get_email_settings
    from core.customers_repo import get_customer
    
    # Get ticket details
    call = get_service_call(call_id)
    if not call:
        ui.notify("Ticket not found", type="negative")
        return
    
    # Get available recipients
    settings = get_email_settings()
    admin_email = settings.get("smtp_from", "")
    
    customer_email = ""
    if call.get("customer_id"):
        customer = get_customer(call.get("customer_id"))
        if customer:
            customer_email = customer.get("email", "")
    
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-6 max-w-xl"):
        ui.label(f"Send Ticket #{call_id} via Email").classes("text-xl font-bold mb-4")
        ui.label("PDF will be attached to email").classes("text-sm gcc-muted mb-4")
        
        ui.separator().classes("my-3")
        
        # Recipient options
        ui.label("Select Recipients:").classes("text-sm font-bold mb-2")
        
        admin_check = ui.checkbox(f"Admin: {admin_email if admin_email else '(not configured)'}").classes("mb-2")
        admin_check.value = True if admin_email else False
        admin_check.enabled = bool(admin_email)
        
        customer_check = ui.checkbox(f"Customer: {customer_email if customer_email else '(no email on file)'}").classes("mb-2")
        customer_check.value = False
        customer_check.enabled = bool(customer_email)
        
        # Custom email input
        ui.label("Additional Recipients (comma-separated):").classes("text-sm font-bold mt-3 mb-1")
        custom_input = ui.input(placeholder="email1@example.com, email2@example.com").classes("w-full").props("outlined dense")
        
        ui.separator().classes("my-3")
        
        def on_send():
            recipients = []
            
            if admin_check.value and admin_email:
                recipients.append(admin_email)
            
            if customer_check.value and customer_email:
                recipients.append(customer_email)
            
            if custom_input.value:
                custom_emails = [e.strip() for e in custom_input.value.split(",") if e.strip()]
                recipients.extend(custom_emails)
            
            if not recipients:
                ui.notify("Please select at least one recipient", type="warning")
                return
            
            # Send to all recipients
            success_count = 0
            fail_count = 0
            errors = []
            
            for recipient in recipients:
                success, msg = send_email_repo(call_id, to_email=recipient)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"{recipient}: {msg}")
            
            dialog.close()
            
            if fail_count == 0:
                ui.notify(f"✓ Email sent to {success_count} recipient(s)", type="positive")
            elif success_count > 0:
                ui.notify(f"⚠ Sent to {success_count}, failed {fail_count}", type="warning")
            else:
                ui.notify(f"✗ All emails failed: {'; '.join(errors[:2])}", type="negative")
        
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Send Email", icon="send", on_click=on_send).props("color=blue")
    
    dialog.open()


def confirm_delete(call_id: int):
    """Confirm and delete service call (must be Closed first)"""
    # Check status before allowing delete
    conn = get_conn()
    try:
        row = conn.execute("SELECT status FROM ServiceCalls WHERE ID = ?", (call_id,)).fetchone()
        status = row[0] if row else None
        if status != "Closed":
            ui.notify(f"Cannot delete: Service call must be Closed first (current status: {status})", type="warning")
            return
    finally:
        conn.close()

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
            "customer": call.get('customer') or call.get('customer_name') or (f"Customer #{call.get('customer_id')}") if call.get('customer_id') else '—',
            "location": call.get('location') or call.get('location_address') or (f"Location #{call.get('location_id')}") if call.get('location_id') else '—',
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

        # Use centralized PDF generator
        from core.ticket_document import generate_ticket_pdf
        pdf_path, pdf_bytes = generate_ticket_pdf(call_id)

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
                    "const url=URL.createObjectURL(blob);const w=window.open(url,'_blank');"+
                    "if(w){setTimeout(()=>{w.print();},500);}})();"
                )).props("color=blue")
                ui.button("Download PDF", icon="download", on_click=lambda: ui.download(pdf_bytes, filename=os.path.basename(pdf_path))).props("color=green")
                ui.button("Close", on_click=lambda: dlg.close()).props("flat")

        dlg.open()
        ui.notify("PDF generated", type="positive")
    except Exception as e:
        ui.notify(f"PDF generation failed: {e}", type="negative")


def show_print_form(title: str, description: str, materials: str, labor: str, priority: str, status: str,
                    customer: Optional[Dict[str, Any]] = None,
                    location: Optional[Dict[str, Any]] = None,
                    unit: Optional[Dict[str, Any]] = None,
                    telemetry: Optional[Dict[str, Any]] = None):
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

        # Customer / Location / Unit
        with ui.grid(columns=2).classes("gap-3 mb-3 w-full"):
            if customer:
                cust_name = customer.get("company") or f"{customer.get('first_name','')} {customer.get('last_name','')}" .strip()
                cust_txt = f"Customer: {cust_name}"
            else:
                cust_txt = "Customer: —"
            loc_txt = f"Location: {location.get('address1') or '—'}" if location else "Location: —"
            ui.label(cust_txt).classes("text-xs")
            ui.label(loc_txt).classes("text-xs")
        if unit:
            unit_txt_parts = []
            unit_txt_parts.append(unit.get("unit_tag") or f"Unit {unit.get('unit_id','')}")
            make_model = " ".join(filter(None, [unit.get("make"), unit.get("model")]))
            if make_model:
                unit_txt_parts.append(make_model)
            if unit.get("tonnage"):
                unit_txt_parts.append(f"{unit.get('tonnage')} Ton")
            if unit.get("refrigerant_type"):
                unit_txt_parts.append(unit.get("refrigerant_type"))
            ui.label("Unit: " + " | ".join(unit_txt_parts)).classes("text-xs mb-2")

        if telemetry:
            mode = telemetry.get("mode") or "—"
            sup = telemetry.get("supply_temp") or telemetry.get("supply_temp_f") or "—"
            ret = telemetry.get("return_temp") or telemetry.get("return_temp_f") or "—"
            delta = telemetry.get("delta_t") or telemetry.get("delta_t_f") or "—"
            fan = telemetry.get("fan_speed_percent") or "—"
            stat = telemetry.get("unit_status") or telemetry.get("status_color") or "—"
            ts = telemetry.get("ts") or telemetry.get("last_update") or ""
            alert = telemetry.get("alert_message") or ""
            ui.label(f"Mode: {mode} | Supply: {sup} | Return: {ret} | ΔT: {delta} | Fan: {fan}%").classes("text-xs")
            ui.label(f"Status: {stat} | Updated: {ts}").classes("text-xs")
            if alert:
                ui.label(f"Alert: {alert}").classes("text-xs text-red-500")
        
        ui.separator().classes("my-3")
        
        # Priority
        ui.label("Priority").classes("text-xs font-bold")
        ui.label(priority).classes("text-sm mb-3")
        
        ui.separator().classes("my-3")
        
        # Title
        ui.label("Title").classes("text-xs font-bold")
        ui.label(title or "(Not filled)").classes("text-sm mb-3 whitespace-pre-wrap")
        
        # Description removed (unused)
        
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
                            cust_txt = call.get('customer_name') or call.get('customer') or (f"Customer #{call.get('customer_id')}") if call.get('customer_id') else 'N/A'
                            loc_txt = call.get('location_address') or call.get('location') or (f"Location #{call.get('location_id')}") if call.get('location_id') else 'N/A'
                            ui.label(f"Customer: {cust_txt}")
                            ui.label(f"Location: {loc_txt}")
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
    
    with ui.dialog() as dialog, ui.card().classes("gcc-card p-8 max-w-5xl max-h-[90vh] overflow-auto"):
        # ===== HEADER SECTION =====
        ui.label("WORK ORDER").classes("text-2xl font-bold mb-1")
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
                
                # Customer selection (admin/tech only); client role sees read-only label
                if hierarchy <= 3 and not customer_id:
                    customers = list_customers(search="")
                    customer_options = {c["ID"]: c.get("company") or f"{c.get('first_name','')} {c.get('last_name','')}" for c in customers}
                    customer_select = ui.select(customer_options, label="Customer *").classes("w-full mb-2").props("outlined dense")
                    current_customer_label = None
                else:
                    customer_select = None
                    cust_obj = get_customer(customer_id) if customer_id else None
                    cust_name = cust_obj.get("company") if cust_obj else "—"
                    current_customer_label = ui.label(f"Customer: {cust_name}").classes("text-sm gcc-muted mb-2")
                
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
                alert_display = ui.textarea(value="No alerts").classes("w-full text-xs bg-gray-900 text-white").props("readonly rows=3")
        
        ui.separator().classes("my-4")
        
        # ===== MATERIALS & SERVICES (Large section) =====
        ui.label("MATERIALS & SERVICES [TECH TO FILL]").classes("text-sm font-bold mb-2")
        materials_input = ui.textarea(
            value="",
            placeholder="List all materials and services provided (one per line or as needed)"
        ).classes("w-full mb-2 bg-gray-900 text-white").props("outlined rows=6 autogrow")
        ui.button("Open materials editor", icon="edit_note", on_click=lambda: open_editor_dialog("Materials & Services", materials_input, 900)).props("outline dense")
        
        ui.separator().classes("my-4")
        
        # ===== LABOR DESCRIPTION (Large section) =====
        ui.label("LABOR DESCRIPTION [TECH TO FILL]").classes("text-sm font-bold mb-2")
        labor_input = ui.textarea(
            value="",
            placeholder="Describe labor performed, time spent, and any recommendations"
        ).classes("w-full mb-2 bg-gray-900 text-white").props("outlined rows=6 autogrow")
        ui.button("Open labor editor", icon="edit_note", on_click=lambda: open_editor_dialog("Labor Description", labor_input, 900)).props("outline dense")
        
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
        def open_editor_dialog(label: str, target_input, max_len: int):
            """Popup editor with character limit and counter"""
            with ui.dialog() as edialog, ui.card().classes("gcc-card p-4 max-w-4xl"):
                ui.label(f"{label} (max {max_len} chars)").classes("text-sm font-semibold mb-2")
                counter_label = ui.label("").classes("text-xs gcc-muted mb-2")
                editor = ui.textarea(value=target_input.value or "").classes("w-full bg-gray-900 text-white").props(f"rows=10 maxlength={max_len} counter")

                def update_counter():
                    val = editor.value or ""
                    counter_label.text = f"{len(val)}/{max_len} chars"
                    counter_label.update()
                editor.on_value_change(lambda e: update_counter())
                update_counter()

                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=edialog.close).props("flat")
                    def save_back():
                        target_input.value = editor.value or ""
                        target_input.update()
                        edialog.close()
                    ui.button("Save", on_click=save_back).props("color=green")
            edialog.open()

        def set_locations_for_customer(cust_id: Optional[int]):
            """Populate locations/units when customer is known (includes client role)."""
            locations = list_locations(customer_id=cust_id) if cust_id else []
            location_select.options = {loc["ID"]: loc.get("PropertyName") or loc.get("address1", "Unknown") for loc in locations}
            # Auto-select first location if none chosen yet
            if locations and not location_select.value:
                location_select.value = locations[0]["ID"]
            else:
                location_select.value = location_select.value if location_select.value in location_select.options else None
            location_select.update()
            set_units_for_location(location_select.value)
            update_info_display()

        def set_units_for_location(loc_id: Optional[int]):
            units = list_units(location_id=loc_id) if loc_id else []
            unit_select.options = {u["unit_id"]: u.get("unit_tag") or f"RTU-{u['unit_id']}" for u in units}
            if units and not unit_select.value:
                unit_select.value = units[0]["unit_id"]
            else:
                unit_select.value = unit_select.value if unit_select.value in unit_select.options else None
            unit_select.update()
            update_info_display()

        def on_customer_change():
            if customer_select:
                cust_id = customer_select.value
                set_locations_for_customer(cust_id)
        
        def on_location_change():
            loc_id = location_select.value
            set_units_for_location(loc_id)
        
        def _get_latest_reading(u_id: int):
            """Fetch latest telemetry row for unit"""
            try:
                with get_conn() as conn:
                    row = conn.execute(
                        "SELECT * FROM UnitReadings WHERE unit_id = ? ORDER BY reading_id DESC LIMIT 1",
                        (u_id,),
                    ).fetchone()
                    return dict(row) if row else None
            except Exception:
                return None

        def update_info_display():
            """Update info label with location/unit details and latest telemetry"""
            text_parts = []
            # Location details
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

            latest = None
            # Unit details + telemetry
            if unit_select.value:
                units = list_units(location_id=location_select.value) if location_select.value else []
                unit = next((u for u in units if u["unit_id"] == unit_select.value), None)
                if unit:
                    eq_type = unit.get('equipment_type', 'Unit')
                    make = unit.get('make', '?')
                    model = unit.get('model', '?')
                    tonnage = unit.get('tonnage', '')
                    refrig = unit.get('refrigerant_type', '')
                    serial = unit.get('serial', '')
                    details = f"{make} {model}"
                    if tonnage:
                        details += f" ({tonnage} Ton)"
                    if refrig:
                        details += f" - {refrig}"
                    if serial:
                        details += f" | SN: {serial}"
                    text_parts.append(f"🔧 {eq_type}: {details}")

                    latest = _get_latest_reading(unit_select.value)
                    if latest:
                        mode = latest.get("mode") or "—"
                        sup = latest.get("supply_temp") or latest.get("supply_temp_f") or "—"
                        ret = latest.get("return_temp") or latest.get("return_temp_f") or "—"
                        delta = latest.get("delta_t") or latest.get("delta_t_f") or "—"
                        fan = latest.get("fan_speed_percent") or "—"
                        stat = latest.get("unit_status") or latest.get("status_color") or "—"
                        alert = latest.get("alert_message") or ""
                        ts = latest.get("ts") or latest.get("last_update") or ""
                        text_parts.append(f"📡 Mode: {mode} | Supply: {sup} | Return: {ret} | ΔT: {delta} | Fan: {fan}%")
                        text_parts.append(f"⚙️ Status: {stat} | Updated: {ts}")
                        if alert:
                            text_parts.append(f"⚠️ {alert}")

            info_label.text = "\n".join(text_parts) if text_parts else "(Select location & unit)"
            info_label.update()
        
        if customer_select:
            customer_select.on_value_change(on_customer_change)
        location_select.on_value_change(on_location_change)
        unit_select.on_value_change(lambda: update_info_display())

        # Pre-populate selections and info for client role
        if customer_id and not customer_select:
            set_locations_for_customer(customer_id)
            update_info_display()
        else:
            update_info_display()
        
        # ===== SUBMIT BUTTON =====
        def on_submit():
            final_customer_id = customer_select.value if customer_select else customer_id
            if not final_customer_id:
                ui.notify("Customer is required", type="negative")
                return

            # Derive a short title from materials (fallback to generic)
            title_value = (materials_input.value or "").strip()
            if title_value:
                title_value = title_value.split("\n")[0][:80]
            else:
                title_value = "Work Order"
            
            data = {
                "customer_id": final_customer_id,
                "location_id": location_select.value,
                "unit_id": unit_select.value,
                "title": title_value,
                "description": "",
                "priority": priority_select.value,
                "status": status_select.value,
                "requested_by_login_id": user.get("login_id") or user.get("ID"),
                "materials_services": materials_input.value,
                "labor_description": labor_input.value
            }
            
            try:
                call_id = create_service_call(data)
                ui.notify(f"✓ Service Order #{call_id} created successfully!", type="positive")
                ui.navigate.to("/tickets")
            except Exception as e:
                ui.notify(f"Error creating service call: {e}", type="negative")
        
        with ui.row().classes("justify-end gap-2 mt-6"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            def build_print_context():
                # Resolve effective customer from selection or current user
                eff_customer_id = None
                if customer_select and customer_select.value:
                    eff_customer_id = int(customer_select.value)
                elif customer_id:
                    eff_customer_id = customer_id

                cust_obj = get_customer(eff_customer_id) if eff_customer_id else None

                loc_obj = None
                if location_select.value and eff_customer_id:
                    locs = list_locations(customer_id=eff_customer_id)
                    loc_obj = next((l for l in locs if l["ID"] == location_select.value), None)

                unit_obj = None
                if unit_select.value:
                    units = list_units(location_id=location_select.value) if location_select.value else []
                    unit_obj = next((u for u in units if u["unit_id"] == unit_select.value), None)

                latest = _get_latest_reading(unit_select.value) if unit_select.value else None
                return cust_obj, loc_obj, unit_obj, latest

            ui.button("Print Form", icon="print", on_click=lambda: (
                lambda ctx: show_print_form(
                    (materials_input.value or "Work Order").split("\n")[0][:80] or "Work Order",
                    "", materials_input.value, 
                    labor_input.value, priority_select.value, status_select.value,
                    customer=ctx[0], location=ctx[1], unit=ctx[2], telemetry=ctx[3]
                )
            )(build_print_context())).props("outline")
            ui.button("Create Service Order", icon="add", on_click=on_submit).props("color=green")
    
    dialog.open()


def show_edit_dialog(call: Dict[str, Any], mode: str = "edit", user: Optional[Dict[str, Any]] = None, hierarchy: int = 5):
    """Unified dialog to view, edit, or create service call
    
    Args:
        call: Service call data dict
        mode: 'view' for read-only, 'edit' for editable, 'create' for new
        user: Current user dict (required for create mode)
        hierarchy: User hierarchy level (required for create mode)
    """
    def _safe_int(val):
        try:
            return int(val) if val is not None else None
        except Exception:
            return None

    call_id = call.get("ID")
    existing_customer_id = _safe_int(call.get("customer_id"))
    existing_location_id = _safe_int(call.get("location_id"))
    existing_unit_id = _safe_int(call.get("unit_id"))
    
    is_readonly = (mode == "view")
    is_create = (mode == "create")
    
    # Sanitize status and priority values from database
    status_val = call.get("status") or "Open"
    if status_val not in ["Open", "In Progress", "Closed"]:
        status_val = "Open"
    
    priority_val = call.get("priority") or "Normal"
    if priority_val not in ["Low", "Normal", "High", "Emergency"]:
        priority_val = "Normal"
    
    with ui.dialog() as dialog, ui.card().classes("p-6 min-w-[720px] max-w-5xl bg-gray-900"):
        if is_create:
            dialog_title = "New Service Call"
            title_text = dialog_title
        else:
            dialog_title = "View Service Call" if is_readonly else "Edit Service Call"
            title_text = f"{dialog_title} #{call_id}"
        ui.label(title_text).classes("text-xl font-bold mb-4")

        # readonly_prop must be defined before any inputs use it
        readonly_prop = "readonly" if (is_readonly or (is_create and hierarchy == 4)) else ""

        # Title (editable in edit mode, auto-generated on create)
        if is_create:
            # Auto-generated from materials on create
            with ui.row().classes("w-full mb-3 items-center gap-2"):
                ui.label("Title:").classes("text-sm font-semibold")
                ui.label("Auto-generated from first line of materials").classes("text-sm gcc-muted")
            title_input = None
        else:
            # Editable in edit/view mode
            with ui.row().classes("w-full mb-3"):
                title_input = ui.input(value=call.get("title", "Work Order"), label="Title").classes("w-full bg-gray-800").props(f"outlined dense {readonly_prop}")
        
        # Created date (editable for backdating)
        if not is_create:
            with ui.row().classes("w-full mb-3 items-center gap-2"):
                ui.label("Created:").classes("text-sm font-semibold")
                created_str = call.get("created", "")
                # Extract date portion (YYYY-MM-DD) if timestamp format
                if created_str and " " in created_str:
                    created_str = created_str.split(" ")[0]
                created_input = ui.input(value=created_str, label="Date (YYYY-MM-DD)").classes("w-48 bg-gray-800").props(f"outlined dense {readonly_prop}")
        else:
            created_input = None

        # Contact & equipment selectors
        with ui.grid(columns=3).classes("gap-4 w-full mb-3"):
            # Customer (admin/tech can change, or readonly for client role)
            customers = list_customers(search="")
            customer_options = {c["ID"]: c.get("company") or f"{c.get('first_name','')} {c.get('last_name','')}" for c in customers}
            # Ensure existing value is present for display even if not in options
            if existing_customer_id and existing_customer_id not in customer_options:
                customer_options[existing_customer_id] = call.get("customer") or call.get("customer_name") or "Customer"
            # Readonly for view mode or client role in create mode
            customer_select = ui.select(customer_options, value=existing_customer_id, label="Customer").classes("w-full bg-gray-800").props(f"outlined dense {readonly_prop}")

            # Location (cascades from customer)
            initial_locations = list_locations(customer_id=existing_customer_id) if existing_customer_id else []
            location_options = {loc["ID"]: loc.get("PropertyName") or loc.get("address1", "Unknown") for loc in initial_locations}
            if existing_location_id and existing_location_id not in location_options:
                location_options[existing_location_id] = call.get("location") or call.get("location_address") or "Location"
            location_select = ui.select(location_options, value=existing_location_id, label="Location").classes("w-full bg-gray-800").props(f"outlined dense {readonly_prop}")

            # Unit (cascades from location)
            initial_units = list_units(location_id=existing_location_id) if existing_location_id else []
            unit_options = {u["unit_id"]: u.get("unit_tag") or f"RTU-{u['unit_id']}" for u in initial_units}
            if existing_unit_id and existing_unit_id not in unit_options:
                unit_options[existing_unit_id] = call.get("unit") or call.get("unit_name") or "Unit"
            unit_select = ui.select(unit_options, value=existing_unit_id, label="Equipment Unit").classes("w-full bg-gray-800").props(f"outlined dense {readonly_prop}")

        # Status / Priority
        with ui.grid(columns=2).classes("gap-4 w-full"):
            status_select = ui.select(
                {"Open": "Open", "In Progress": "In Progress", "Closed": "Closed"},
                value=status_val,
                label="Status"
            ).classes("bg-gray-800").props(f"outlined dense {readonly_prop}")
            priority_select = ui.select(
                {"Low": "Low", "Normal": "Normal", "High": "High", "Emergency": "Emergency"},
                value=priority_val,
                label="Priority"
            ).classes("bg-gray-800").props(f"outlined dense {readonly_prop}")

        ui.separator().classes("my-2")
        ui.label("Materials & Labor").classes("text-sm font-semibold mb-2")
        materials_input = ui.textarea("Materials/Services", value=call.get("materials_services", "")).classes("w-full bg-gray-900 text-white").props(f"rows=3 {readonly_prop}")
        labor_input = ui.textarea("Labor Description", value=call.get("labor_description", "")).classes("w-full bg-gray-900 text-white").props(f"rows=3 {readonly_prop}")

        def on_save():
            # Final selections
            final_customer_id = customer_select.value or existing_customer_id
            final_location_id = location_select.value or existing_location_id
            final_unit_id = unit_select.value or existing_unit_id
            
            if not final_customer_id:
                ui.notify("Customer is required", type="negative")
                return
            
            # Derive title from materials if creating
            if is_create:
                title_value = (materials_input.value or "").strip()
                if title_value:
                    title_value = title_value.split("\n")[0][:80]
                else:
                    title_value = "Work Order"
            else:
                title_value = title_input.value if title_input else call.get("title", "Work Order")

            data = {
                "title": title_value,
                "description": call.get("description", ""),
                "status": status_select.value,
                "priority": priority_select.value,
                "customer_id": final_customer_id,
                "location_id": final_location_id,
                "unit_id": final_unit_id,
                "materials_services": materials_input.value,
                "labor_description": labor_input.value
            }
            
            # Add created date if editing and changed
            if not is_create and created_input and created_input.value:
                data["created"] = created_input.value
            
            if is_create:
                data["requested_by_login_id"] = user.get("login_id") or user.get("ID") if user else None
                try:
                    new_id = create_service_call(data)
                    ui.notify(f"✓ Service Call #{new_id} created successfully!", type="positive")
                    dialog.close()
                    ui.navigate.reload()
                except Exception as e:
                    ui.notify(f"Error creating service call: {e}", type="negative")
            else:
                if update_service_call(call_id, data):
                    ui.notify("Service call updated", type="positive")
                    dialog.close()
                    ui.navigate.reload()
                else:
                    ui.notify("Failed to update service call", type="negative")
        
        # Cascading handlers
        def on_customer_change():
            cust_id = customer_select.value
            locs = list_locations(customer_id=cust_id) if cust_id else []
            location_select.options = {loc["ID"]: loc.get("PropertyName") or loc.get("address1", "Unknown") for loc in locs}
            location_select.value = None
            location_select.update()
            unit_select.options = {}
            unit_select.value = None
            unit_select.update()

        def on_location_change():
            loc_id = location_select.value
            units = list_units(location_id=loc_id) if loc_id else []
            unit_select.options = {u["unit_id"]: u.get("unit_tag") or f"RTU-{u['unit_id']}" for u in units}
            if units:
                # keep previous unit if still under this location
                if existing_unit_id and any(u["unit_id"] == existing_unit_id for u in units):
                    unit_select.value = existing_unit_id
            unit_select.update()

        # Only enable cascading handlers in edit mode
        if not is_readonly:
            customer_select.on_value_change(lambda: on_customer_change())
            location_select.on_value_change(lambda: on_location_change())

        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Close", on_click=dialog.close).props("flat")
            if not is_readonly:
                save_label = "Create" if is_create else "Save"
                save_icon = "add" if is_create else "save"
                ui.button(save_label, icon=save_icon, on_click=on_save).props("color=green")
    
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
        
        description_input = ui.textarea("Description", placeholder="Detailed description of the issue").classes("w-full bg-gray-900 text-white").props("rows=4")
        notes_input = ui.textarea("Internal Notes", placeholder="Notes for technicians").classes("w-full bg-gray-900 text-white").props("rows=2")
        
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

