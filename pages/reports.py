"""
Reports Page - Generate and view various system reports
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from nicegui import ui, app

from core.auth import current_user, require_login, is_admin
from ui.layout import layout
from core.reports_repo import (
    get_company_profile,
    get_hierarchical_company_report,
    get_equipment_inventory_report,
    get_equipment_by_age_report,
    get_equipment_maintenance_history,
    get_tickets_by_status_report,
    get_ticket_resolution_analysis,
    get_open_tickets_summary,
    get_customer_summary_report,
    get_customer_activity_report,
    get_location_inventory_report,
    get_alert_history_report,
    get_current_alerts_report,
    get_temperature_trend_report,
    get_system_overview_report,
    get_available_report_types
)
from core.customers_repo import list_customers
from core.locations_repo import list_locations
from core.units_repo import list_units


def page():
    """Reports page - accessible by admins and techs"""
    if not require_login():
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)
    
    # Only admins (1,2) and techs (3) can access reports
    if hierarchy not in (1, 2, 3):
        ui.notify("Access denied: Reports are only available to administrators and technicians", type="negative")
        ui.navigate.to("/")
        return

    with layout("Reports", hierarchy=hierarchy):
        ui.label("Report Center").classes("text-3xl font-bold mb-2")
        ui.label("Generate comprehensive reports across all system data").classes("text-sm text-gray-400 mb-8")
        
        # Report category selector
        categories = get_available_report_types()
        
        with ui.tabs().classes("w-full") as tabs:
            hierarchical_tab = ui.tab("🏢 Hierarchical View")
            equipment_tab = ui.tab("Equipment")
            tickets_tab = ui.tab("Service Tickets")
            customers_tab = ui.tab("Customers")
            locations_tab = ui.tab("Locations")
            alerts_tab = ui.tab("Alerts")
            overview_tab = ui.tab("Overview")
        
        with ui.tab_panels(tabs, value=hierarchical_tab).classes("w-full"):
            # HIERARCHICAL COMPANY REPORT
            with ui.tab_panel(hierarchical_tab):
                render_hierarchical_report()
            
            # EQUIPMENT REPORTS
            with ui.tab_panel(equipment_tab):
                render_equipment_reports()
            
            # SERVICE TICKET REPORTS
            with ui.tab_panel(tickets_tab):
                render_ticket_reports()
            
            # CUSTOMER REPORTS
            with ui.tab_panel(customers_tab):
                render_customer_reports()
            
            # LOCATION REPORTS
            with ui.tab_panel(locations_tab):
                render_location_reports()
            
            # ALERT REPORTS
            with ui.tab_panel(alerts_tab):
                render_alert_reports()
            
            # OVERVIEW REPORTS
            with ui.tab_panel(overview_tab):
                render_overview_reports()


# ============================================
# HIERARCHICAL COMPANY REPORT
# ============================================

def render_hierarchical_report():
    """Hierarchical report showing Company → Customers → Locations → Equipment"""
    ui.label("Company Report").classes("text-2xl font-bold mb-4")
    ###ui.label("Complete organizational structure: Company Profile → Customers → Locations → Equipment").classes("text-sm text-gray-400 mb-6")
    
    with ui.card().classes("w-full gcc-card"):
        with ui.row().classes("w-full gap-4 items-end mb-4"):
            # Customer filter
            customer_options = {0: "All Customers"}
            customers = list_customers("")
            for c in customers:
                customer_options[c["ID"]] = c.get("company") or f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            
            customer_filter = ui.select(customer_options, label="Filter by Customer", value=0).classes("flex-1")
            
            with ui.row().classes("gap-2"):
                ui.button("Generate Report", icon="analytics", 
                         on_click=lambda: show_hierarchical_report(customer_filter.value)).props("color=green-10")
                ui.button("Export PDF", icon="picture_as_pdf",
                         on_click=lambda: export_hierarchical_pdf(customer_filter.value)).props("color=blue-10")


def show_hierarchical_report(customer_id: int):
    """Display hierarchical report in a dialog"""
    cust_id = None if customer_id == 0 else customer_id
    data = get_hierarchical_company_report(cust_id)
    
    if not data or not data.get("customers"):
        ui.notify("No data found", type="warning")
        return
    
    with ui.dialog().props("maximized") as dialog, ui.card().classes("w-full"):
        # Header with company profile
        company = data.get("company_profile", {})
        with ui.card().classes("w-full gcc-card mb-6 bg-blue-900"):
            ui.label(company.get("company", "Company Profile")).classes("text-3xl font-bold mb-2")
            with ui.row().classes("w-full gap-8"):
                with ui.column():
                    ui.label(f"📍 {company.get('address1', 'N/A')}").classes("text-sm")
                    if company.get("address2"):
                        ui.label(f"   {company.get('address2')}").classes("text-sm")
                    ui.label(f"   {company.get('city', '')}, {company.get('state', '')} {company.get('zip', '')}").classes("text-sm")
                with ui.column():
                    ui.label(f"📞 {company.get('phone', 'N/A')}").classes("text-sm")
                    ui.label(f"📧 {company.get('email', 'N/A')}").classes("text-sm")
                    if company.get("website"):
                        ui.label(f"🌐 {company.get('website')}").classes("text-sm")
        
        # Summary statistics
        with ui.card().classes("w-full gcc-card mb-6"):
            ui.label("Summary Statistics").classes("text-xl font-bold mb-3")
            with ui.row().classes("w-full gap-6"):
                with ui.card().classes("gcc-card bg-green-900 flex-1"):
                    ui.label(str(data.get("total_customers", 0))).classes("text-4xl font-bold")
                    ui.label("Total Customers").classes("text-sm text-gray-400")
                with ui.card().classes("gcc-card bg-blue-900 flex-1"):
                    ui.label(str(data.get("total_locations", 0))).classes("text-4xl font-bold")
                    ui.label("Total Locations").classes("text-sm text-gray-400")
                with ui.card().classes("gcc-card bg-purple-900 flex-1"):
                    ui.label(str(data.get("total_equipment", 0))).classes("text-4xl font-bold")
                    ui.label("Total Equipment Units").classes("text-sm text-gray-400")
        
        # Customers with nested locations and equipment
        ui.label("Customers & Equipment Details").classes("text-xl font-bold mb-4")
        
        for customer in data.get("customers", []):
            with ui.expansion(
                f"🏢 {customer.get('company', 'N/A')} ({customer.get('location_count', 0)} locations, {customer.get('equipment_count', 0)} units)",
                icon="business"
            ).classes("w-full mb-2 gcc-card"):
                # Customer details
                with ui.card().classes("w-full gcc-card mb-4 bg-gray-800"):
                    ui.label("Customer Information").classes("text-lg font-bold mb-2")
                    with ui.grid(columns=3).classes("w-full gap-4"):
                        with ui.column():
                            ui.label("Contact").classes("font-bold text-gray-400 text-xs")
                            ui.label(f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "N/A")
                        with ui.column():
                            ui.label("Email").classes("font-bold text-gray-400 text-xs")
                            ui.label(customer.get("email") or "N/A")
                        with ui.column():
                            ui.label("Phone").classes("font-bold text-gray-400 text-xs")
                            ui.label(customer.get("phone") or "N/A")
                
                # Locations for this customer
                for location in customer.get("locations", []):
                    with ui.expansion(
                        f"📍 {location.get('address1', 'N/A')} ({location.get('equipment_count', 0)} units)",
                        icon="location_on"
                    ).classes("w-full mb-2"):
                        # Location details
                        with ui.card().classes("w-full gcc-card mb-3 bg-gray-900"):
                            ui.label("Location Details").classes("text-md font-bold mb-2")
                            with ui.grid(columns=2).classes("w-full gap-4"):
                                with ui.column():
                                    ui.label("Address").classes("font-bold text-gray-400 text-xs")
                                    addr = location.get('address1', 'N/A')
                                    if location.get('address2'):
                                        addr += f", {location.get('address2')}"
                                    ui.label(addr)
                                    ui.label(f"{location.get('city', '')}, {location.get('state', '')} {location.get('zip', '')}".strip())
                                with ui.column():
                                    ui.label("Contact").classes("font-bold text-gray-400 text-xs")
                                    ui.label(location.get("contact") or "N/A")
                                    ui.label(location.get("phone") or "N/A")
                        
                        # Equipment table for this location
                        equipment = location.get("equipment", [])
                        if equipment:
                            ui.label(f"Equipment at this Location ({len(equipment)} units)").classes("text-md font-bold mb-2")
                            
                            # Equipment table
                            columns = [
                                {"name": "unit_tag", "label": "Unit Tag", "field": "unit_tag", "align": "left", "sortable": True},
                                {"name": "make", "label": "Make", "field": "make", "align": "left", "sortable": True},
                                {"name": "model", "label": "Model", "field": "model", "align": "left", "sortable": True},
                                {"name": "type", "label": "Type", "field": "type", "align": "left", "sortable": True},
                                {"name": "refrigerant", "label": "Refrigerant", "field": "refrigerant", "align": "left"},
                                {"name": "tonnage", "label": "Tonnage", "field": "tonnage", "align": "right"},
                                {"name": "serial", "label": "Serial #", "field": "serial", "align": "left"},
                            ]
                            
                            ui.table(
                                columns=columns,
                                rows=equipment,
                                row_key="unit_id",
                                pagination={"rowsPerPage": 10, "sortBy": "unit_tag"}
                            ).classes("w-full").props("dense flat")
                        else:
                            ui.label("No equipment at this location").classes("text-sm text-gray-500 italic")
        
        with ui.row().classes("w-full justify-end mt-6"):
            ui.button("Close", on_click=dialog.close).props("flat")
    
    dialog.open()


def export_hierarchical_pdf(customer_id: int):
    """Export hierarchical report as PDF"""
    from core.report_document import generate_hierarchical_company_pdf
    
    cust_id = None if customer_id == 0 else customer_id
    data = get_hierarchical_company_report(cust_id)
    
    if not data or not data.get("customers"):
        ui.notify("No data to export", type="warning")
        return
    
    try:
        filepath, pdf_bytes = generate_hierarchical_company_pdf(data)
        import os
        ui.download(pdf_bytes, filename=os.path.basename(filepath))
        ui.notify("PDF generated successfully", type="positive")
    except Exception as e:
        ui.notify(f"PDF generation failed: {e}", type="negative")


# ============================================
# EQUIPMENT REPORTS
# ============================================

def render_equipment_reports():
    """Equipment report section"""
    ui.label("Equipment Reports").classes("text-2xl font-bold mb-4")
    
    with ui.expansion("Equipment Inventory Report", icon="inventory").classes("w-full mb-4"):
        ui.label("Complete list of all equipment with specifications").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("w-full gap-4 items-end mb-4"):
            customer_options = {0: "All Customers"}
            customers = list_customers("")
            for c in customers:
                customer_options[c["ID"]] = c.get("company") or f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            
            customer_filter = ui.select(customer_options, label="Customer", value=0).classes("flex-1")
            location_filter = ui.select({0: "All Locations"}, label="Location", value=0).classes("flex-1")
            
            def on_customer_change():
                if customer_filter.value == 0:
                    location_filter.options = {0: "All Locations"}
                else:
                    locations = list_locations(customer_id=customer_filter.value)
                    location_filter.options = {0: "All Locations"}
                    for loc in locations:
                        location_filter.options[loc["ID"]] = loc.get("address1") or f"Location {loc['ID']}"
                location_filter.update()
            
            customer_filter.on_value_change(lambda: on_customer_change())
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=lambda: show_equipment_inventory(
                customer_filter.value if customer_filter.value != 0 else None,
                location_filter.value if location_filter.value != 0 else None
            )).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=lambda: export_equipment_inventory_pdf(
                customer_filter.value if customer_filter.value != 0 else None,
                location_filter.value if location_filter.value != 0 else None
            )).props("flat")
    
    with ui.expansion("Equipment Age Analysis", icon="schedule").classes("w-full mb-4"):
        ui.label("Equipment grouped by installation date and warranty status").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=show_equipment_age_report).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=export_equipment_age_pdf).props("flat")
    
    with ui.expansion("Maintenance History", icon="build").classes("w-full mb-4"):
        ui.label("Service history for equipment units").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("w-full gap-4 items-end mb-4"):
            units = list_units("")
            unit_options = {0: "All Units"}
            for u in units:
                unit_options[u["unit_id"]] = u.get("unit_tag") or f"Unit {u['unit_id']}"
            
            unit_filter = ui.select(unit_options, label="Unit", value=0).classes("flex-1")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=lambda: show_maintenance_history(
                unit_filter.value if unit_filter.value != 0 else None
            )).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=lambda: export_maintenance_pdf(
                unit_filter.value if unit_filter.value != 0 else None
            )).props("flat")


def show_equipment_inventory(customer_id: Optional[int], location_id: Optional[int]):
    """Display equipment inventory report"""
    data = get_equipment_inventory_report(customer_id, location_id)
    
    if not data:
        ui.notify("No equipment found", type="warning")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        ui.label(f"Equipment Inventory Report ({len(data)} units)").classes("text-2xl font-bold mb-4")
        ui.label("Crew Guide: Customer, Location & Equipment Details").classes("text-sm text-gray-400 mb-4")
        
        # Build formatted location strings
        for row in data:
            location_parts = [row.get("location_address", "")]
            if row.get("location_city"):
                location_parts.append(row["location_city"])
            if row.get("location_state"):
                location_parts.append(row["location_state"])
            row["full_location"] = ", ".join(filter(None, location_parts))
        
        columns = [
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "full_location", "label": "Location Address", "field": "full_location", "sortable": True, "align": "left"},
            {"name": "unit_tag", "label": "Unit Tag", "field": "unit_tag", "sortable": True, "align": "left"},
            {"name": "make", "label": "Make", "field": "make", "sortable": True, "align": "left"},
            {"name": "model", "label": "Model", "field": "model", "sortable": True, "align": "left"},
            {"name": "serial", "label": "Serial #", "field": "serial", "sortable": True, "align": "left"},
            {"name": "inst_date", "label": "Install Date", "field": "inst_date", "sortable": True, "align": "left"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="unit_id",
            pagination={"rowsPerPage": 50, "sortBy": "customer_name", "descending": False}
        ).classes("w-full").props("dense")
        
        with ui.row().classes("w-full justify-between mt-4"):
            ui.label(f"Total: {len(data)} units").classes("text-sm text-gray-400")
            ui.button("Close", on_click=dialog.close).props("flat")
    
    dialog.open()


def show_equipment_age_report():
    """Display equipment age analysis"""
    data = get_equipment_by_age_report()
    
    if not data:
        ui.notify("No equipment found", type="warning")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-6xl p-6"):
        ui.label(f"Equipment Age Analysis ({len(data)} units)").classes("text-2xl font-bold mb-4")
        
        # Summary stats
        total = len(data)
        under_warranty = sum(1 for d in data if d.get("warranty_status") == "Under Warranty")
        out_warranty = sum(1 for d in data if d.get("warranty_status") == "Out of Warranty")
        
        with ui.row().classes("w-full gap-6 mb-6 p-4 bg-gray-800 rounded"):
            with ui.column().classes("items-center"):
                ui.label(str(total)).classes("text-3xl font-bold text-blue-400")
                ui.label("Total Units").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(under_warranty)).classes("text-3xl font-bold text-green-400")
                ui.label("Under Warranty").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(out_warranty)).classes("text-3xl font-bold text-yellow-400")
                ui.label("Out of Warranty").classes("text-xs text-gray-400")
        
        columns = [
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "unit_tag", "label": "Unit", "field": "unit_tag", "sortable": True, "align": "left"},
            {"name": "make", "label": "Make", "field": "make", "sortable": True, "align": "left"},
            {"name": "model", "label": "Model", "field": "model", "sortable": True, "align": "left"},
            {"name": "inst_date", "label": "Install Date", "field": "inst_date", "sortable": True, "align": "center"},
            {"name": "age_group", "label": "Age", "field": "age_group", "sortable": True, "align": "center"},
            {"name": "warranty_status", "label": "Warranty", "field": "warranty_status", "sortable": True, "align": "center"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="unit_id",
            pagination={"rowsPerPage": 20, "sortBy": "inst_date", "descending": True}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


def show_maintenance_history(unit_id: Optional[int]):
    """Display maintenance history report"""
    data = get_equipment_maintenance_history(unit_id=unit_id)
    
    if not data:
        ui.notify("No maintenance history found", type="warning")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        ui.label(f"Maintenance History ({len(data)} service records)").classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "service_date", "label": "Date", "field": "service_date", "sortable": True, "align": "center"},
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "unit_tag", "label": "Unit", "field": "unit_tag", "sortable": True, "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
            {"name": "priority", "label": "Priority", "field": "priority", "sortable": True, "align": "center"},
            {"name": "title", "label": "Description", "field": "title", "sortable": True, "align": "left"},
            {"name": "technician", "label": "Technician", "field": "technician", "sortable": True, "align": "left"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="ticket_id",
            pagination={"rowsPerPage": 20, "sortBy": "service_date", "descending": True}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


# ============================================
# SERVICE TICKET REPORTS
# ============================================

def render_ticket_reports():
    """Service ticket report section"""
    ui.label("Service Ticket Reports").classes("text-2xl font-bold mb-4")
    
    with ui.expansion("Tickets by Status", icon="receipt_long").classes("w-full mb-4"):
        ui.label("Service tickets filtered by status and date range").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("w-full gap-4 items-end mb-4"):
            status_filter = ui.select(
                {None: "All Statuses", "Open": "Open", "In Progress": "In Progress", "Closed": "Closed"},
                label="Status",
                value=None
            ).classes("flex-1")
            
            start_date = ui.input("Start Date", placeholder="YYYY-MM-DD").classes("flex-1")
            end_date = ui.input("End Date", placeholder="YYYY-MM-DD").classes("flex-1")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=lambda: show_tickets_by_status(
                status_filter.value,
                start_date.value or None,
                end_date.value or None
            )).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=lambda: export_tickets_pdf(
                status_filter.value,
                start_date.value or None,
                end_date.value or None
            )).props("flat")
    
    with ui.expansion("Resolution Time Analysis", icon="timer").classes("w-full mb-4"):
        ui.label("Average resolution time by priority and customer").classes("text-sm text-gray-400 mb-4")
        
        days_select = ui.select({7: "Last 7 days", 30: "Last 30 days", 90: "Last 90 days"}, label="Period", value=30).classes("w-64 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=lambda: show_resolution_analysis(days_select.value)).props("color=primary")
    
    with ui.expansion("Open Tickets Summary", icon="pending_actions").classes("w-full mb-4"):
        ui.label("All currently open service tickets").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=show_open_tickets).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=export_open_tickets_pdf).props("flat")


def show_tickets_by_status(status: Optional[str], start_date: Optional[str], end_date: Optional[str]):
    """Display tickets by status report"""
    data = get_tickets_by_status_report(status=status, start_date=start_date, end_date=end_date)
    
    if not data:
        ui.notify("No tickets found", type="warning")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        title = f"Service Tickets Report ({len(data)} tickets)"
        if status:
            title += f" - Status: {status}"
        ui.label(title).classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "ticket_id", "label": "ID", "field": "ticket_id", "sortable": True, "align": "center"},
            {"name": "created", "label": "Created", "field": "created", "sortable": True, "align": "center"},
            {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
            {"name": "priority", "label": "Priority", "field": "priority", "sortable": True, "align": "center"},
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "title", "label": "Description", "field": "title", "sortable": True, "align": "left"},
            {"name": "resolution_hours", "label": "Hrs to Close", "field": "resolution_hours", "sortable": True, "align": "right"},
        ]
        
        # Format resolution hours
        for row in data:
            if row.get("resolution_hours"):
                row["resolution_hours"] = f"{row['resolution_hours']:.1f}"
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="ticket_id",
            pagination={"rowsPerPage": 25, "sortBy": "created", "descending": True}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


def show_resolution_analysis(days: int):
    """Display resolution time analysis"""
    data = get_ticket_resolution_analysis(days)
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-5xl p-6"):
        ui.label(f"Resolution Time Analysis - Last {days} Days").classes("text-2xl font-bold mb-6")
        
        # Overall stats
        overall = data.get("overall", {})
        with ui.row().classes("w-full gap-6 mb-6 p-4 bg-gray-800 rounded"):
            with ui.column().classes("items-center"):
                ui.label(str(overall.get("total_tickets", 0))).classes("text-3xl font-bold text-blue-400")
                ui.label("Total Tickets").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(overall.get("closed_tickets", 0))).classes("text-3xl font-bold text-green-400")
                ui.label("Closed").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                avg_hours = overall.get("avg_resolution_hours", 0) or 0
                ui.label(f"{avg_hours:.1f}h").classes("text-3xl font-bold text-yellow-400")
                ui.label("Avg Resolution Time").classes("text-xs text-gray-400")
        
        # By priority
        ui.label("Resolution Time by Priority").classes("text-lg font-semibold mb-3 mt-6")
        by_priority = data.get("by_priority", [])
        if by_priority:
            columns = [
                {"name": "priority", "label": "Priority", "field": "priority", "align": "left"},
                {"name": "count", "label": "Count", "field": "count", "align": "right"},
                {"name": "avg_resolution_hours", "label": "Avg Hours", "field": "avg_resolution_hours", "align": "right"},
            ]
            for row in by_priority:
                if row.get("avg_resolution_hours"):
                    row["avg_resolution_hours"] = f"{row['avg_resolution_hours']:.1f}"
            ui.table(columns=columns, rows=by_priority).classes("w-full mb-6")
        
        # By customer
        ui.label("Top 10 Customers by Ticket Volume").classes("text-lg font-semibold mb-3 mt-6")
        by_customer = data.get("by_customer", [])
        if by_customer:
            columns = [
                {"name": "customer_name", "label": "Customer", "field": "customer_name", "align": "left"},
                {"name": "ticket_count", "label": "Tickets", "field": "ticket_count", "align": "right"},
                {"name": "avg_resolution_hours", "label": "Avg Hours", "field": "avg_resolution_hours", "align": "right"},
            ]
            for row in by_customer:
                if row.get("avg_resolution_hours"):
                    row["avg_resolution_hours"] = f"{row['avg_resolution_hours']:.1f}"
            ui.table(columns=columns, rows=by_customer).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


def show_open_tickets():
    """Display open tickets summary"""
    data = get_open_tickets_summary()
    
    if not data:
        ui.notify("No open tickets", type="positive")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-6xl p-6"):
        ui.label(f"Open Tickets Summary ({len(data)} tickets)").classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "ticket_id", "label": "ID", "field": "ticket_id", "sortable": True, "align": "center"},
            {"name": "priority", "label": "Priority", "field": "priority", "sortable": True, "align": "center"},
            {"name": "title", "label": "Description", "field": "title", "sortable": True, "align": "left"},
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "location_address", "label": "Location", "field": "location_address", "sortable": True, "align": "left"},
            {"name": "days_open", "label": "Days Open", "field": "days_open", "sortable": True, "align": "right"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="ticket_id",
            pagination={"rowsPerPage": 25, "sortBy": "days_open", "descending": True}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


# ============================================
# CUSTOMER REPORTS
# ============================================

def render_customer_reports():
    """Customer report section"""
    ui.label("Customer Reports").classes("text-2xl font-bold mb-4")
    
    with ui.expansion("Customer Summary", icon="people").classes("w-full mb-4"):
        ui.label("Overview of all customers with statistics").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=show_customer_summary).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=export_customer_summary_pdf).props("flat")


def show_customer_summary():
    """Display customer summary report"""
    data = get_customer_summary_report()
    
    if not data:
        ui.notify("No customers found", type="warning")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        ui.label(f"Customer Summary ({len(data)} customers)").classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "customer_name", "label": "Company", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "customer_email", "label": "Email", "field": "customer_email", "sortable": True, "align": "left"},
            {"name": "customer_phone", "label": "Phone", "field": "customer_phone", "sortable": True, "align": "left"},
            {"name": "location_count", "label": "Locations", "field": "location_count", "sortable": True, "align": "right"},
            {"name": "equipment_count", "label": "Equipment", "field": "equipment_count", "sortable": True, "align": "right"},
            {"name": "open_tickets", "label": "Open Tickets", "field": "open_tickets", "sortable": True, "align": "right"},
            {"name": "total_tickets", "label": "Total Tickets", "field": "total_tickets", "sortable": True, "align": "right"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="customer_id",
            pagination={"rowsPerPage": 25, "sortBy": "customer_name", "descending": False}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


# ============================================
# LOCATION REPORTS
# ============================================

def render_location_reports():
    """Location report section"""
    ui.label("Location Reports").classes("text-2xl font-bold mb-4")
    
    with ui.expansion("Location Inventory", icon="location_on").classes("w-full mb-4"):
        ui.label("All locations with equipment counts and status").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=show_location_inventory).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=export_location_inventory_pdf).props("flat")


def show_location_inventory():
    """Display location inventory report"""
    data = get_location_inventory_report()
    
    if not data:
        ui.notify("No locations found", type="warning")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        ui.label(f"Location Inventory ({len(data)} locations)").classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "address1", "label": "Address", "field": "address1", "sortable": True, "align": "left"},
            {"name": "city", "label": "City", "field": "city", "sortable": True, "align": "left"},
            {"name": "state", "label": "State", "field": "state", "sortable": True, "align": "center"},
            {"name": "equipment_count", "label": "Total Units", "field": "equipment_count", "sortable": True, "align": "right"},
            {"name": "active_units", "label": "Active", "field": "active_units", "sortable": True, "align": "right"},
            {"name": "alert_units", "label": "Alerts", "field": "alert_units", "sortable": True, "align": "right"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="location_id",
            pagination={"rowsPerPage": 25, "sortBy": "customer_name", "descending": False}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


# ============================================
# ALERT REPORTS
# ============================================

def render_alert_reports():
    """Alert and monitoring report section"""
    ui.label("Alert & Monitoring Reports").classes("text-2xl font-bold mb-4")
    
    with ui.expansion("Current Alerts", icon="warning").classes("w-full mb-4"):
        ui.label("Units with active alerts right now").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=show_current_alerts).props("color=primary")
            ui.button("Export PDF", icon="picture_as_pdf", on_click=export_current_alerts_pdf).props("flat")
    
    with ui.expansion("Alert History", icon="history").classes("w-full mb-4"):
        ui.label("Historical alerts from telemetry data").classes("text-sm text-gray-400 mb-4")
        
        days_select = ui.select({7: "Last 7 days", 30: "Last 30 days", 90: "Last 90 days"}, label="Period", value=30).classes("w-64 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=lambda: show_alert_history(days_select.value)).props("color=primary")


def show_current_alerts():
    """Display current alerts report"""
    data = get_current_alerts_report()
    
    if not data:
        ui.notify("No active alerts - all systems normal!", type="positive")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        ui.label(f"Current Alerts ({len(data)} units)").classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "location_address", "label": "Location", "field": "location_address", "sortable": True, "align": "left"},
            {"name": "unit_tag", "label": "Unit", "field": "unit_tag", "sortable": True, "align": "left"},
            {"name": "make", "label": "Make", "field": "make", "sortable": True, "align": "left"},
            {"name": "mode", "label": "Mode", "field": "mode", "sortable": True, "align": "center"},
            {"name": "fault_code", "label": "Fault", "field": "fault_code", "sortable": True, "align": "center"},
            {"name": "last_reading", "label": "Last Reading", "field": "last_reading", "sortable": True, "align": "center"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="unit_id",
            pagination={"rowsPerPage": 25, "sortBy": "status", "descending": False}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


def show_alert_history(days: int):
    """Display alert history report"""
    data = get_alert_history_report(days=days)
    
    if not data:
        ui.notify(f"No alerts found in last {days} days", type="positive")
        return
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-7xl p-6"):
        ui.label(f"Alert History - Last {days} Days ({len(data)} alerts)").classes("text-2xl font-bold mb-4")
        
        columns = [
            {"name": "timestamp", "label": "Time", "field": "timestamp", "sortable": True, "align": "center"},
            {"name": "customer_name", "label": "Customer", "field": "customer_name", "sortable": True, "align": "left"},
            {"name": "unit_tag", "label": "Unit", "field": "unit_tag", "sortable": True, "align": "left"},
            {"name": "mode", "label": "Mode", "field": "mode", "sortable": True, "align": "center"},
            {"name": "fault_code", "label": "Fault", "field": "fault_code", "sortable": True, "align": "center"},
            {"name": "alarm_status", "label": "Alarm", "field": "alarm_status", "sortable": True, "align": "center"},
            {"name": "alert_message", "label": "Message", "field": "alert_message", "sortable": True, "align": "left"},
        ]
        
        ui.table(
            columns=columns,
            rows=data,
            row_key="reading_id",
            pagination={"rowsPerPage": 25, "sortBy": "timestamp", "descending": True}
        ).classes("w-full")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")
    
    dialog.open()


# ============================================
# OVERVIEW REPORTS
# ============================================

def render_overview_reports():
    """System overview report section"""
    ui.label("System Overview").classes("text-2xl font-bold mb-4")
    
    with ui.expansion("Complete System Overview", icon="dashboard").classes("w-full mb-4"):
        ui.label("High-level statistics for entire system").classes("text-sm text-gray-400 mb-4")
        
        with ui.row().classes("gap-2"):
            ui.button("Generate Report", icon="assessment", on_click=show_system_overview).props("color=primary")


def show_system_overview():
    """Display system overview report"""
    data = get_system_overview_report()
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-6xl p-6"):
        ui.label("System Overview Report").classes("text-3xl font-bold mb-6")
        
        # Customer stats
        customer_stats = data.get("customer_stats", {})
        ui.label("Customers").classes("text-xl font-semibold mb-3 text-blue-400")
        with ui.row().classes("w-full gap-6 mb-6 p-4 bg-gray-800 rounded"):
            with ui.column().classes("items-center"):
                ui.label(str(customer_stats.get("total_customers", 0))).classes("text-3xl font-bold text-blue-400")
                ui.label("Total Customers").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(customer_stats.get("new_customers_30d", 0))).classes("text-3xl font-bold text-green-400")
                ui.label("New (30 days)").classes("text-xs text-gray-400")
        
        # Location stats
        location_stats = data.get("location_stats", {})
        ui.label("Locations").classes("text-xl font-semibold mb-3 mt-6 text-blue-400")
        with ui.row().classes("w-full gap-6 mb-6 p-4 bg-gray-800 rounded"):
            with ui.column().classes("items-center"):
                ui.label(str(location_stats.get("total_locations", 0))).classes("text-3xl font-bold text-blue-400")
                ui.label("Total Locations").classes("text-xs text-gray-400")
        
        # Equipment stats
        equipment_stats = data.get("equipment_stats", {})
        ui.label("Equipment").classes("text-xl font-semibold mb-3 mt-6 text-blue-400")
        with ui.row().classes("w-full gap-6 mb-6 p-4 bg-gray-800 rounded"):
            with ui.column().classes("items-center"):
                ui.label(str(equipment_stats.get("total_units", 0))).classes("text-3xl font-bold text-blue-400")
                ui.label("Total Units").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(equipment_stats.get("active_units", 0))).classes("text-3xl font-bold text-green-400")
                ui.label("Active").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(equipment_stats.get("warning_units", 0))).classes("text-3xl font-bold text-yellow-400")
                ui.label("Warnings").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(equipment_stats.get("error_units", 0))).classes("text-3xl font-bold text-red-400")
                ui.label("Errors").classes("text-xs text-gray-400")
        
        # Ticket stats
        ticket_stats = data.get("ticket_stats", {})
        ui.label("Service Tickets").classes("text-xl font-semibold mb-3 mt-6 text-blue-400")
        with ui.row().classes("w-full gap-6 mb-6 p-4 bg-gray-800 rounded"):
            with ui.column().classes("items-center"):
                ui.label(str(ticket_stats.get("total_tickets", 0))).classes("text-3xl font-bold text-blue-400")
                ui.label("Total Tickets").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(ticket_stats.get("open_tickets", 0))).classes("text-3xl font-bold text-yellow-400")
                ui.label("Open").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(ticket_stats.get("closed_tickets", 0))).classes("text-3xl font-bold text-green-400")
                ui.label("Closed").classes("text-xs text-gray-400")
            with ui.column().classes("items-center"):
                ui.label(str(ticket_stats.get("tickets_7d", 0))).classes("text-3xl font-bold text-gray-400")
                ui.label("Last 7 Days").classes("text-xs text-gray-400")
        
        ui.button("Close", on_click=dialog.close).props("flat").classes("mt-6")
    
    dialog.open()


# ============================================
# PDF EXPORT FUNCTIONS
# ============================================

def export_equipment_inventory_pdf(customer_id: Optional[int], location_id: Optional[int]):
    from core.report_document import generate_equipment_inventory_pdf
    try:
        data = get_equipment_inventory_report(customer_id, location_id)
        if not data:
            ui.notify("No data to export", type="warning")
            return
        
        filepath, pdf_bytes = generate_equipment_inventory_pdf(data, customer_id)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")

def export_equipment_age_pdf():
    from core.report_document import generate_equipment_age_pdf
    try:
        data = get_equipment_by_age_report()
        if not data:
            ui.notify("No data to export", type="warning")
            return
        
        filepath, pdf_bytes = generate_equipment_age_pdf(data)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")

def export_maintenance_pdf(unit_id: Optional[int]):
    ui.notify("PDF export coming soon", type="info")

def export_tickets_pdf(status: Optional[str], start_date: Optional[str], end_date: Optional[str]):
    from core.report_document import generate_tickets_report_pdf
    try:
        data = get_tickets_by_status_report(status=status, start_date=start_date, end_date=end_date)
        if not data:
            ui.notify("No data to export", type="warning")
            return
        
        filepath, pdf_bytes = generate_tickets_report_pdf(data, status)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")

def export_open_tickets_pdf():
    from core.report_document import generate_open_tickets_pdf
    try:
        data = get_open_tickets_summary()
        if not data:
            ui.notify("No open tickets to export", type="positive")
            return
        
        filepath, pdf_bytes = generate_open_tickets_pdf(data)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")

def export_customer_summary_pdf():
    from core.report_document import generate_customer_summary_pdf
    try:
        data = get_customer_summary_report()
        if not data:
            ui.notify("No data to export", type="warning")
            return
        
        filepath, pdf_bytes = generate_customer_summary_pdf(data)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")

def export_location_inventory_pdf():
    from core.report_document import generate_location_inventory_pdf
    try:
        data = get_location_inventory_report()
        if not data:
            ui.notify("No data to export", type="warning")
            return
        
        filepath, pdf_bytes = generate_location_inventory_pdf(data)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")

def export_current_alerts_pdf():
    from core.report_document import generate_current_alerts_pdf
    try:
        data = get_current_alerts_report()
        if not data:
            ui.notify("No alerts to export - all systems normal!", type="positive")
            return
        
        filepath, pdf_bytes = generate_current_alerts_pdf(data)
        ui.download(pdf_bytes, filename=filepath.split("/")[-1].split("\\")[-1])
        ui.notify("PDF exported successfully", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")
