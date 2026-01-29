from nicegui import ui
from core.auth import require_login, is_admin, current_user
from core.logger import log_user_action, handle_error
from core.settings_repo import (
    get_company_profile,
    update_company_profile,
    get_email_settings,
    update_email_settings,
    list_employees,
    get_employee,
    create_employee,
    update_employee,
    delete_employee,
    get_service_call_settings,
    update_service_call_settings,
    list_ticket_sequences,
    get_ticket_sequence,
    create_ticket_sequence,
    update_ticket_sequence,
    delete_ticket_sequence,
)
from ui.layout import layout
from core.db import get_conn
from core.security import hash_password
from core.customers_repo import list_customers
from core.version import get_version_info
import json
from pathlib import Path


def show_notification(message: str, notification_type: str = "info"):
    """Show notification banner"""
    if notification_type == "success":
        ui.notify(message, position="top", type="positive")
    elif notification_type == "error":
        ui.notify(message, position="top", type="negative")
    else:
        ui.notify(message, position="top", type="info")


def create_company_profile_tab() -> ui.card:
    """Create company profile settings tab"""
    with ui.card().style("width: 60%; max-width: 60%;") as card:
        with ui.column().classes("w-full gap-2"):
            ui.label("Company Profile").classes("text-xl font-bold")

            company = get_company_profile()
            fields = {}

            with ui.row().classes("w-full gap-2"):
                fields["name"] = ui.input(label="Company Name", value=company.get("name", "")).classes("flex-1")
                fields["website"] = ui.input(label="Website", value=company.get("website", "")).classes("flex-1")

            fields["logo_path"] = ui.input(label="Logo URL", value=company.get("logo_path", "")).classes("w-full")

            logo_preview = ui.image("").classes("w-20 h-20 object-contain border border-gray-700 rounded mt-1")
            logo_preview.visible = bool(company.get("logo_path"))
            if logo_preview.visible:
                logo_preview.source = company.get("logo_path")

            def update_logo_preview():
                url = (fields["logo_path"].value or "").strip()
                if url:
                    logo_preview.source = url
                    logo_preview.visible = True
                else:
                    logo_preview.visible = False

            fields["logo_path"].on_value_change(lambda _: update_logo_preview())

            with ui.row().classes("w-full gap-2"):
                fields["phone"] = ui.input(label="Phone", value=company.get("phone", "")).classes("flex-1")
                fields["fax"] = ui.input(label="Fax", value=company.get("fax", "")).classes("flex-1")

            with ui.row().classes("w-full gap-2"):
                fields["email"] = ui.input(label="Email", value=company.get("email", "")).classes("flex-1")
                fields["service_email"] = ui.input(label="Service Email", value=company.get("service_email", "")).classes("flex-1")

            fields["owner_email"] = ui.input(label="Owner Email", value=company.get("owner_email", "")).classes("w-full")

            with ui.row().classes("w-full gap-2"):
                fields["address1"] = ui.input(label="Address 1", value=company.get("address1", "")).classes("flex-1")
                fields["address2"] = ui.input(label="Address 2", value=company.get("address2", "")).classes("flex-1")

            with ui.row().classes("w-full gap-2"):
                fields["city"] = ui.input(label="City", value=company.get("city", "")).classes("flex-1")
                fields["state"] = ui.input(label="State", value=company.get("state", "")).classes("flex-1")
                fields["zip"] = ui.input(label="Zip", value=company.get("zip", "")).classes("flex-1")

            with ui.row().classes("gap-3 mt-3"):
                ui.button("Save Changes", on_click=lambda: save_company_profile(fields)).classes("bg-blue-600 hover:bg-blue-700")
                ui.button("Cancel", on_click=lambda: ui.navigate.to('/settings')).classes("bg-gray-500 hover:bg-gray-600")
def show_employee_view_dialog(employee_id: int):
    """Show employee record view (read-only)"""
    employee = get_employee(employee_id) if employee_id else {}
    
    role_options = {
        1: "1 - GOD",
        2: "2 - Administrator",
        3: "3 - Tech_GCC",
        4: "4 - Client",
        5: "5 - Client_Mngs",
    }
    
    # Handle security_clearance as either string or int
    clearance = employee.get('security_clearance', 4)
    if isinstance(clearance, str):
        try:
            clearance = int(clearance)
        except ValueError:
            clearance = 4  # Default to Client if conversion fails
    role = role_options.get(clearance, 'N/A')

    with ui.dialog() as dialog:
        with ui.card().style("width: 80%; max-width: 80%;").props("flat bordered"):
            ui.label(f"Employee Record - {employee.get('first_name', '')} {employee.get('last_name', '')}").classes("text-lg font-bold")

            with ui.column().classes("w-full gap-3 mt-3"):
                # Personal Information
                ui.label("PERSONAL INFORMATION").classes("text-md font-bold text-blue-400")
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Record ID:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('id', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Employee #:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('employee_id', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("First Name:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('first_name', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Last Name:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('last_name', 'N/A'))).classes("text-sm")
                
                with ui.column().classes("w-full"):
                    ui.label("Email:").classes("text-sm font-semibold")
                    ui.label(str(employee.get('email', 'N/A'))).classes("text-sm")

                # Address (if available)
                ui.label("ADDRESS").classes("text-md font-bold text-blue-400 mt-2")
                with ui.column().classes("w-full gap-2"):
                    ui.label(f"Address 1: {employee.get('address1', 'N/A')}").classes("text-sm")
                    ui.label(f"Address 2: {employee.get('address2', 'N/A')}").classes("text-sm")
                    ui.label(f"City: {employee.get('city', 'N/A')}  State: {employee.get('state', 'N/A')}  Zip: {employee.get('zip', 'N/A')}").classes("text-sm")

                # Contact Information
                ui.label("CONTACT INFORMATION").classes("text-md font-bold text-blue-400 mt-2")
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Phone:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('phone', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Mobile:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('mobile', 'N/A'))).classes("text-sm")
                
                # Employment Information
                ui.label("EMPLOYMENT INFORMATION").classes("text-md font-bold text-blue-400 mt-2")
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Department:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('department', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Position:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('position', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Start Date:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('start_date', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Status:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('status', 'N/A'))).classes("text-sm")
                
                # Security & Access
                ui.label("SECURITY & ACCESS").classes("text-md font-bold text-blue-400 mt-2")
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("User Role:").classes("text-sm font-semibold")
                        ui.label(role).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Access Scope:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('access_scope', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    login_status = "Yes" if employee.get('can_login') else "No"
                    mfa_status = "Yes" if employee.get('mfa_enabled') else "No"
                    with ui.column().classes("flex-1"):
                        ui.label("Can Log In:").classes("text-sm font-semibold")
                        ui.label(login_status).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("MFA Enabled:").classes("text-sm font-semibold")
                        ui.label(mfa_status).classes("text-sm")
                
                with ui.column().classes("w-full"):
                    ui.label("Password Last Reset:").classes("text-sm font-semibold")
                    ui.label(str(employee.get('password_last_reset', 'Never'))).classes("text-sm")

                # Dialog buttons
                with ui.row().classes("w-full gap-2 justify-end mt-4"):
                    ui.button("Close", on_click=dialog.close).classes("bg-gray-400 hover:bg-gray-500 text-white font-semibold").props("unelevated")

    dialog.open()

    return card


def save_company_profile(fields: dict):
    """Save company profile changes"""
    data = {key: field.value for key, field in fields.items() if hasattr(field, "value")}

    if update_company_profile(data):
        show_notification("Company profile updated successfully", "success")
        ui.navigate.to('/settings')  # Reload settings page after save
    else:
        show_notification("Error updating company profile", "error")


# ==============================================
# EMAIL SETTINGS TAB
# ==============================================

def create_email_settings_tab() -> ui.card:
    """Create email/SMTP settings tab"""
    with ui.card().style("width: 60%; max-width: 60%;") as card:
        with ui.column().classes("w-full gap-2"):
            ui.label("Email Settings").classes("text-xl font-bold")

            email_settings = get_email_settings()

            with ui.column().classes("w-full gap-4"):
                fields = {}
                
                # Email provider toggle
                with ui.row().classes("w-full gap-4 items-center mb-4"):
                    ui.label("Email Provider:").classes("font-bold")
                    fields["use_sendgrid"] = ui.checkbox(
                        text="Use SendGrid API (recommended for cloud servers)",
                        value=bool(email_settings.get("use_sendgrid", 0))
                    ).classes("mt-0")
                
                ui.separator()
                
                # SendGrid API settings
                with ui.column().classes("w-full gap-2 mt-4") as sendgrid_section:
                    ui.label("SendGrid API Settings").classes("text-lg font-bold text-blue-400")
                    ui.label("No SMTP ports needed - works on all servers").classes("text-sm gcc-muted")
                    
                    fields["sendgrid_api_key"] = ui.input(
                        label="SendGrid API Key",
                        value=email_settings.get("sendgrid_api_key", ""),
                        password=True,
                        password_toggle_button=True
                    ).classes("w-full")
                    
                    fields["sendgrid_from"] = ui.input(
                        label="From Email Address (must be verified in SendGrid)",
                        value=email_settings.get("smtp_from", "")
                    ).classes("w-full")
                
                ui.separator().classes("my-4")
                
                # SMTP settings
                with ui.column().classes("w-full gap-2") as smtp_section:
                    ui.label("SMTP Settings (Custom Email Server)").classes("text-lg font-bold text-yellow-400")
                    ui.label("Requires open SMTP ports on your server").classes("text-sm gcc-muted")
                    
                    with ui.row().classes("w-full gap-2"):
                        fields["smtp_host"] = ui.input(label="SMTP Host", value=email_settings.get("smtp_host", "")).classes("flex-1")
                        fields["smtp_port"] = ui.number(label="SMTP Port (2525/587/465)", value=email_settings.get("smtp_port", 2525)).classes("flex-1")

                    with ui.row().classes("w-full gap-2"):
                        fields["smtp_user"] = ui.input(label="SMTP Username", value=email_settings.get("smtp_user", "")).classes("flex-1")
                        fields["smtp_pass"] = ui.input(
                            label="SMTP Password",
                            password=True,
                            password_toggle_button=True,
                            value=email_settings.get("smtp_pass", "")
                        ).classes("flex-1")

                    fields["use_tls"] = ui.checkbox(text="Use TLS/STARTTLS", value=bool(email_settings.get("use_tls", 1))).classes("mt-2")

                # Action buttons
                with ui.row().classes("gap-4 mt-4"):
                    ui.button("Save Settings", on_click=lambda: save_email_settings(fields)).classes("bg-blue-600 hover:bg-blue-700")
                    ui.button("Test Connection", on_click=lambda: test_email_connection(fields)).classes("bg-green-600 hover:bg-green-700")
                
                # Toggle visibility based on provider selection
                def toggle_sections():
                    use_sg = fields["use_sendgrid"].value
                    sendgrid_section.set_visibility(use_sg)
                    smtp_section.set_visibility(not use_sg)
                
                fields["use_sendgrid"].on_value_change(lambda: toggle_sections())
                toggle_sections()  # Initial state

    return card


def save_email_settings(fields: dict):
    """Save email settings"""
    use_sendgrid = fields["use_sendgrid"].value
    
    data = {
        "use_sendgrid": 1 if use_sendgrid else 0,
        "sendgrid_api_key": fields["sendgrid_api_key"].value if use_sendgrid else "",
        "smtp_host": fields["smtp_host"].value,
        "smtp_port": int(fields["smtp_port"].value),
        "smtp_user": fields["smtp_user"].value,
        "smtp_pass": fields["smtp_pass"].value,
        "smtp_from": fields["sendgrid_from"].value if use_sendgrid else fields["smtp_host"].value,
        "use_tls": fields["use_tls"].value,
    }

    if update_email_settings(data):
        show_notification("Email settings updated successfully", "success")
        ui.navigate.to('/settings')
    else:
        show_notification("Error updating email settings", "error")


def test_email_connection(fields: dict):
    """Test email connection"""
    import smtplib
    
    show_notification("Testing email connection...", "info")
    
    try:
        host = fields["smtp_host"].value
        port = int(fields["smtp_port"].value)
        username = fields["smtp_user"].value
        password = fields["smtp_pass"].value
        use_tls = fields["use_tls"].value
        
        if not host:
            show_notification("SMTP Host is required", "error")
            return
        
        # Test connection
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        
        if username and password:
            server.login(username, password)
        
        server.quit()
        show_notification("✓ Connection successful!", "success")
        
    except smtplib.SMTPAuthenticationError:
        show_notification("Authentication failed - check username/password", "error")
    except smtplib.SMTPConnectError:
        show_notification("Could not connect to SMTP server", "error")
    except Exception as e:
        show_notification(f"Connection failed: {str(e)}", "error")


# ==============================================
# EMPLOYEE PROFILE TAB
# ==============================================

def create_employee_profile_tab() -> ui.card:
    """Create employee profile management tab"""
    
    state = {"selected_row": None}
    
    with ui.card() as card:
        with ui.column().classes("w-full gap-2"):
            ui.label("Employee Directory").classes("text-xl font-bold")

            # Search bar
            with ui.row().classes("w-full gap-1 items-center"):
                search_input = ui.input(placeholder="Search employees...").classes("flex-1")

            # Employee table with row selection
            with ui.card().classes("gcc-card gcc-scrollable-card mt-4"):
                employees_table = ui.table(
                    columns=[
                        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                        {'name': 'employee_id', 'label': 'Employee ID', 'field': 'employee_id'},
                        {'name': 'first_name', 'label': 'First Name', 'field': 'first_name'},
                        {'name': 'last_name', 'label': 'Last Name', 'field': 'last_name'},
                        {'name': 'position', 'label': 'Position', 'field': 'position'},
                        {'name': 'email', 'label': 'Email', 'field': 'email'},
                        {'name': 'security_clearance', 'label': 'Role', 'field': 'security_clearance'},
                        {'name': 'can_login', 'label': 'Login', 'field': 'can_login'},
                        {'name': 'status', 'label': 'Status', 'field': 'status'},
                    ],
                    rows=list_employees(),
                    row_key='id',
                    selection="single",
                    pagination={"rowsPerPage": 10}
                ).classes("gcc-fixed-table")

            # Action buttons
            with ui.row().classes("w-full gap-2 mt-2"):
                def add_employee():
                    show_employee_dialog(None, card)
                
                def view_selected():
                    if not employees_table.selected:
                        show_notification("Select an employee to view", "error")
                        return
                    row = employees_table.selected[0]
                    show_employee_view_dialog(row['id'])
                
                def print_selected():
                    if not employees_table.selected:
                        show_notification("Select an employee to print", "error")
                        return
                    row = employees_table.selected[0]
                    print_employee_record(row['id'])
                
                def edit_selected():
                    if employees_table.selected:
                        row = employees_table.selected[0]
                        show_employee_dialog(row['id'], card)
                
                def delete_selected():
                    if not employees_table.selected:
                        show_notification("Select an employee to delete", "error")
                        return
                    
                    row = employees_table.selected[0]
                    with ui.dialog() as confirm_dialog:
                        with ui.card():
                            ui.label("Confirm Delete").classes("text-lg font-bold")
                            ui.label(f"Delete {row.get('first_name', '')} {row.get('last_name', '')}?").classes("mt-2")
                            with ui.row().classes("gap-2 mt-4"):
                                ui.button("Cancel", on_click=confirm_dialog.close).classes("bg-gray-600 hover:bg-gray-700")
                                ui.button("Delete", on_click=lambda: (
                                    delete_employee(row['id']),
                                    confirm_dialog.close(),
                                    refresh_employees()
                                )).classes("bg-red-600 hover:bg-red-700")
                    confirm_dialog.open()
                
                def refresh_employees():
                    employees_table.rows = list_employees(search=search_input.value)
                    employees_table.selected = []
                    employees_table.update()

                ui.button("+ Add Employee", icon="person_add", on_click=add_employee).classes("bg-green-600 hover:bg-green-700 text-white font-semibold").props("unelevated")
                ui.button("View", icon="visibility", on_click=view_selected).classes("bg-indigo-600 hover:bg-indigo-700 text-white font-semibold").props("unelevated")
                ui.button("Edit", icon="edit", on_click=edit_selected).classes("bg-blue-600 hover:bg-blue-700 text-white font-semibold").props("unelevated")
                ui.button("Print", icon="print", on_click=print_selected).classes("bg-purple-600 hover:bg-purple-700 text-white font-semibold").props("unelevated")
                ui.button("Delete", icon="delete", on_click=delete_selected).classes("bg-red-600 hover:bg-red-700 text-white font-semibold").props("unelevated")
                ui.button("Refresh", icon="refresh", on_click=refresh_employees).classes("bg-gray-600 hover:bg-gray-700 text-white font-semibold").props("unelevated")

            # Search function
            def on_search():
                employees_table.rows = list_employees(search=search_input.value)
                employees_table.selected = []
                employees_table.update()

            search_input.on_value_change(lambda _: on_search())
            
            # Store card reference for later use
            card.employees_table = employees_table

    return card


def show_employee_dialog(employee_id: int | None, card):
    """Show employee create/edit dialog as floating modal"""
    employee = get_employee(employee_id) if employee_id else {}
    
    # Role options for security clearance (same as Logins)
    role_options = {
        1: "1 - GOD",
        2: "2 - Administrator",
        3: "3 - Tech_GCC",
        4: "4 - Client",
        5: "5 - Client_Mngs",
    }

    with ui.dialog() as dialog:
        with ui.card().style("width: 60%; max-width: 60%;").props("flat bordered"):
            ui.label(f"{'Edit' if employee_id else 'Add'} Employee").classes("text-lg font-bold")

            with ui.column().classes("w-full gap-2 mt-2"):
                # Form fields
                fields = {}
                fields["emp_id"] = ui.input(label="Employee ID", value=employee.get("employee_id", "")).classes("w-full")
                fields["first_name"] = ui.input(label="First Name", value=employee.get("first_name", "")).classes("w-full")
                fields["last_name"] = ui.input(label="Last Name", value=employee.get("last_name", "")).classes("w-full")
                fields["department"] = ui.input(label="Department", value=employee.get("department", "")).classes("w-full")
                fields["position"] = ui.input(label="Position", value=employee.get("position", "")).classes("w-full")
                fields["email"] = ui.input(label="Email", value=employee.get("email", "")).classes("w-full")
                
                with ui.row().classes("w-full gap-2"):
                    fields["phone"] = ui.input(label="Phone", value=employee.get("phone", "")).classes("flex-1")
                    fields["mobile"] = ui.input(label="Mobile", value=employee.get("mobile", "")).classes("flex-1")
                
                fields["start_date"] = ui.input(label="Start Date", value=employee.get("start_date", "")).classes("w-full")
                
                with ui.row().classes("w-full gap-2"):
                    fields["status"] = ui.select(label="Status",
                        options=["Active", "Inactive", "Leave", "Terminated"],
                        value=employee.get("status", "Active")).classes("flex-1")
                    
                    # Handle security_clearance as either string or int for display
                    clearance = employee.get("security_clearance", 4)
                    if isinstance(clearance, str):
                        try:
                            clearance = int(clearance)
                        except ValueError:
                            clearance = 4
                    
                    fields["security_clearance"] = ui.select(label="User Role",
                        options=role_options,
                        value=clearance).classes("flex-1")
                
                fields["access_scope"] = ui.input(label="Access Scope", placeholder="Comma-separated areas",
                    value=employee.get("access_scope", "")).classes("w-full")
                
                with ui.row().classes("w-full gap-4"):
                    fields["can_login"] = ui.checkbox(text="Can log in", value=bool(employee.get("can_login", 0)))
                    fields["mfa_enabled"] = ui.checkbox(text="MFA enabled", value=bool(employee.get("mfa_enabled", 0)))
                
                fields["password_last_reset"] = ui.input(label="Password Last Reset",
                    placeholder="YYYY-MM-DD", value=employee.get("password_last_reset", "")).classes("w-full")

                # Dialog buttons
                with ui.row().classes("w-full gap-2 justify-end mt-4"):
                    ui.button("Cancel", on_click=dialog.close).classes("bg-gray-400 hover:bg-gray-500 text-white font-semibold").props("unelevated")
                    ui.button("Save", on_click=lambda: save_employee_data(
                        employee_id, fields, dialog, card
                    )).classes("bg-blue-600 hover:bg-blue-700 text-white font-semibold").props("unelevated")

    dialog.open()


def show_employee_view_dialog(employee_id: int):
    """Show employee record view (read-only)"""
    employee = get_employee(employee_id) if employee_id else {}
    
    role_options = {
        1: "1 - GOD",
        2: "2 - Administrator",
        3: "3 - Tech_GCC",
        4: "4 - Client",
        5: "5 - Client_Mngs",
    }
    
    # Handle security_clearance as either string or int
    clearance = employee.get('security_clearance', 4)
    if isinstance(clearance, str):
        try:
            clearance = int(clearance)
        except ValueError:
            clearance = 4  # Default to Client if conversion fails
    role = role_options.get(clearance, 'N/A')

    with ui.dialog() as dialog:
        with ui.card().style("width: 70%; max-width: 70%;").props("flat bordered"):
            ui.label(f"Employee Record - {employee.get('first_name', '')} {employee.get('last_name', '')}").classes("text-lg font-bold")

            with ui.column().classes("w-full gap-2 mt-2"):
                # Display fields as read-only
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Employee ID:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('employee_id', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Status:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('status', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("First Name:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('first_name', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Last Name:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('last_name', 'N/A'))).classes("text-sm")
                
                with ui.column().classes("w-full"):
                    ui.label("Email:").classes("text-sm font-semibold")
                    ui.label(str(employee.get('email', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Department:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('department', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Position:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('position', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Phone:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('phone', 'N/A'))).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Mobile:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('mobile', 'N/A'))).classes("text-sm")
                
                with ui.column().classes("w-full"):
                    ui.label("Start Date:").classes("text-sm font-semibold")
                    ui.label(str(employee.get('start_date', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("User Role:").classes("text-sm font-semibold")
                        ui.label(role).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("Access Scope:").classes("text-sm font-semibold")
                        ui.label(str(employee.get('access_scope', 'N/A'))).classes("text-sm")
                
                with ui.row().classes("w-full gap-4"):
                    login_status = "Yes" if employee.get('can_login') else "No"
                    mfa_status = "Yes" if employee.get('mfa_enabled') else "No"
                    with ui.column().classes("flex-1"):
                        ui.label("Can Log In:").classes("text-sm font-semibold")
                        ui.label(login_status).classes("text-sm")
                    with ui.column().classes("flex-1"):
                        ui.label("MFA Enabled:").classes("text-sm font-semibold")
                        ui.label(mfa_status).classes("text-sm")
                
                with ui.column().classes("w-full"):
                    ui.label("Password Last Reset:").classes("text-sm font-semibold")
                    ui.label(str(employee.get('password_last_reset', 'Never'))).classes("text-sm")

                # Dialog buttons
                with ui.row().classes("w-full gap-2 justify-end mt-4"):
                    ui.button("Close", on_click=dialog.close).classes("bg-gray-400 hover:bg-gray-500 text-white font-semibold").props("unelevated")

    dialog.open()


def print_employee_record(employee_id: int):
    """Print employee record in letter format"""
    employee = get_employee(employee_id) if employee_id else {}
    
    role_options = {
        1: "1 - GOD",
        2: "2 - Administrator",
        3: "3 - Tech_GCC",
        4: "4 - Client",
        5: "5 - Client_Mngs",
    }
    
    # Handle security_clearance as either string or int
    clearance = employee.get('security_clearance', 4)
    if isinstance(clearance, str):
        try:
            clearance = int(clearance)
        except ValueError:
            clearance = 4  # Default to Client if conversion fails
    role = role_options.get(clearance, 'N/A')
    
    login_status = "Yes" if employee.get('can_login') else "No"
    mfa_status = "Yes" if employee.get('mfa_enabled') else "No"

    with ui.dialog() as dialog:
        with ui.card().style("width: 8.5in; max-width: 100%; overflow: auto;").props("flat"):
            # Letter header
            with ui.column().classes("w-full gap-4 p-8").style("font-family: Arial, sans-serif;"):
                ui.label("EMPLOYEE RECORD").classes("text-2xl font-bold text-center")
                ui.label(f"{employee.get('first_name', '')} {employee.get('last_name', '')}").classes("text-xl text-center font-semibold")
                ui.separator()
                
                # Employee details
                with ui.column().classes("w-full gap-2 text-sm"):
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Record ID:").classes("font-semibold")
                        ui.label(str(employee.get('id', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Employee #:").classes("font-semibold")
                        ui.label(str(employee.get('employee_id', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Status:").classes("font-semibold")
                        ui.label(str(employee.get('status', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Email:").classes("font-semibold")
                        ui.label(str(employee.get('email', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Department:").classes("font-semibold")
                        ui.label(str(employee.get('department', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Position:").classes("font-semibold")
                        ui.label(str(employee.get('position', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Phone:").classes("font-semibold")
                        ui.label(str(employee.get('phone', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Mobile:").classes("font-semibold")
                        ui.label(str(employee.get('mobile', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Start Date:").classes("font-semibold")
                        ui.label(str(employee.get('start_date', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("User Role:").classes("font-semibold")
                        ui.label(role)
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Access Scope:").classes("font-semibold")
                        ui.label(str(employee.get('access_scope', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Can Log In:").classes("font-semibold")
                        ui.label(login_status)
                    with ui.row().classes("w-full gap-8"):
                        ui.label("MFA Enabled:").classes("font-semibold")
                        ui.label(mfa_status)
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Password Last Reset:").classes("font-semibold")
                        ui.label(str(employee.get('password_last_reset', 'Never')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Address 1:").classes("font-semibold")
                        ui.label(str(employee.get('address1', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("Address 2:").classes("font-semibold")
                        ui.label(str(employee.get('address2', 'N/A')))
                    with ui.row().classes("w-full gap-8"):
                        ui.label("City/State/Zip:").classes("font-semibold")
                        ui.label(f"{employee.get('city', 'N/A')} / {employee.get('state', 'N/A')} / {employee.get('zip', 'N/A')}")
                
                ui.separator()
                ui.label(f"Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").classes("text-xs text-gray-500 mt-8")

            # Print buttons
            with ui.row().classes("w-full gap-2 justify-end p-4"):
                ui.button("Print", icon="print", on_click=lambda: ui.run_javascript(
                    "window.print();"
                )).classes("bg-blue-600 hover:bg-blue-700 text-white font-semibold").props("unelevated")
                ui.button("Close", on_click=dialog.close).classes("bg-gray-400 hover:bg-gray-500 text-white font-semibold").props("unelevated")

    dialog.open()


def save_employee_data(employee_id, fields: dict, dialog, card):
    """Save employee data and refresh table"""
    data = {
        "employee_id": fields["emp_id"].value,
        "first_name": fields["first_name"].value,
        "last_name": fields["last_name"].value,
        "department": fields["department"].value,
        "position": fields["position"].value,
        "email": fields["email"].value,
        "phone": fields["phone"].value,
        "mobile": fields["mobile"].value,
        "start_date": fields["start_date"].value,
        "status": fields["status"].value,
        # Keep as string to match repo expectations and avoid strip errors
        "security_clearance": str(fields["security_clearance"].value),
        "access_scope": fields["access_scope"].value,
        "can_login": fields["can_login"].value,
        "mfa_enabled": fields["mfa_enabled"].value,
        "password_last_reset": fields["password_last_reset"].value,
    }

    if employee_id:
        if update_employee(employee_id, data):
            show_notification("Employee updated successfully", "success")
        else:
            show_notification("Error updating employee", "error")
    else:
        if create_employee(data):
            show_notification("Employee created successfully", "success")
        else:
            show_notification("Error creating employee", "error")

    dialog.close()
    # Refresh table
    if hasattr(card, 'employees_table'):
        card.employees_table.rows = list_employees()
        card.employees_table.selected = []
        card.employees_table.update()


# ==============================================
# SERVICE CALL SETTINGS TAB
# ==============================================

def create_service_call_settings_tab() -> ui.card:
    """Create service call settings tab"""
    with ui.card() as card:
        with ui.column().classes("w-full gap-1"):
            ui.label("Service Call Settings").classes("text-lg font-bold")

            sc_settings = get_service_call_settings()

            with ui.column().classes("w-full gap-1"):
                ui.select(label="Default Priority",
                    options=["Low", "Normal", "High", "Emergency"],
                    value=sc_settings.get("default_priority", "Normal")).classes("w-full")

                ui.checkbox(text="Auto-Assign Service Calls",
                    value=bool(sc_settings.get("auto_assign", 0)))

                ui.select(label="Assignment Method",
                    options=["round_robin", "by_location", "manual"],
                    value=sc_settings.get("assignment_method", "manual")).classes("w-full")

                ui.label("SLA Response Times (hours)").classes("font-semibold text-sm mt-1 mb-1")
                with ui.row().classes("w-full gap-1"):
                    ui.number(label="Low", value=sc_settings.get("sla_hours_low", 72)).classes("flex-1")
                    ui.number(label="Normal", value=sc_settings.get("sla_hours_normal", 48)).classes("flex-1")
                    ui.number(label="High", value=sc_settings.get("sla_hours_high", 24)).classes("flex-1")
                    ui.number(label="Emergency", value=sc_settings.get("sla_hours_emergency", 4)).classes("flex-1")

                ui.checkbox(text="Notify on creation", value=bool(sc_settings.get("notification_on_create", 1)))
                ui.checkbox(text="Notify on closure", value=bool(sc_settings.get("notification_on_close", 1)))

                ui.button("Save Changes", on_click=lambda: save_service_call_settings(card)).classes("mt-2 bg-blue-600 hover-bg-blue-700 w-40")

    return card


def save_service_call_settings(card):
    """Save service call settings"""
    # TODO: Extract form data and save
    show_notification("Service call settings updated successfully", "success")


# ==============================================
# TICKET SEQUENCE TAB
# ==============================================

def create_ticket_sequence_tab() -> ui.card:
    """Create ticket sequence management tab"""
    with ui.card() as card:
        with ui.column().classes("w-full gap-4"):
            ui.label("Ticket Sequence Configuration").classes("text-xl font-bold")

            # Search and action
            with ui.row().classes("w-full gap-2 items-center"):
                ui.label("Manage ticket numbering formats and sequences").classes("flex-1")
                ui.button("+ Add Sequence", on_click=lambda: show_ticket_sequence_dialog(card, None)).classes("bg-green-600 hover:bg-green-700")

            # Sequences table
            sequences = list_ticket_sequences()
            with ui.card().classes("gcc-card gcc-scrollable-card mt-4"):
                sequences_table = ui.table(
                    columns=[
                        {'name': 'id', 'label': 'ID', 'field': 'id'},
                        {'name': 'sequence_type', 'label': 'Type', 'field': 'sequence_type'},
                        {'name': 'prefix', 'label': 'Prefix', 'field': 'prefix'},
                        {'name': 'current_number', 'label': 'Current #', 'field': 'current_number'},
                        {'name': 'format_pattern', 'label': 'Format', 'field': 'format_pattern'},
                        {'name': 'reset_period', 'label': 'Reset', 'field': 'reset_period'},
                        {'name': 'is_active', 'label': 'Active', 'field': 'is_active'},
                    ],
                    rows=sequences,
                    row_key='id',
                    pagination={"rowsPerPage": 10}
                ).classes("gcc-fixed-table")

    return card


def show_ticket_sequence_dialog(card, sequence_id: int | None):
    """Show ticket sequence create/edit dialog"""
    sequence = get_ticket_sequence(sequence_id) if sequence_id else {}

    with ui.dialog() as dialog:
        with ui.card().classes("min-w-96"):
            ui.label(f"{'Edit' if sequence_id else 'Add'} Ticket Sequence").classes("text-lg font-bold")

            with ui.column().classes("w-full gap-3"):
                seq_type = ui.input(label="Sequence Type", value=sequence.get("sequence_type", ""))
                prefix = ui.input(label="Prefix (e.g., SVR)", value=sequence.get("prefix", ""))
                starting = ui.number(label="Starting Number", value=sequence.get("starting_number", 1000))
                current = ui.number(label="Current Number", value=sequence.get("current_number", 1000))
                increment = ui.number(label="Increment By", value=sequence.get("increment_by", 1))
                pattern = ui.input(label="Format Pattern", value=sequence.get("format_pattern", "{prefix}-{seq:05d}"))
                reset = ui.select(label="Reset Period",
                    options=["none", "daily", "monthly", "yearly"],
                    value=sequence.get("reset_period", "none"))
                active = ui.checkbox(text="Active", value=bool(sequence.get("is_active", 1)))

                with ui.row().classes("w-full gap-2 justify-end mt-4"):
                    ui.button("Cancel", on_click=dialog.close).classes("bg-gray-400 hover:bg-gray-500")
                    ui.button("Save", on_click=lambda: save_ticket_sequence(
                        sequence_id, seq_type.value, prefix.value, int(starting.value),
                        int(current.value), int(increment.value), pattern.value, reset.value,
                        active.value, dialog, card
                    )).classes("bg-blue-600 hover:bg-blue-700")

    dialog.open()


def save_ticket_sequence(sequence_id, seq_type, prefix, starting, current, increment,
                        pattern, reset, active, dialog, card):
    """Save ticket sequence"""
    data = {
        "sequence_type": seq_type,
        "prefix": prefix,
        "starting_number": starting,
        "current_number": current,
        "increment_by": increment,
        "format_pattern": pattern,
        "reset_period": reset,
        "is_active": active,
    }

    if sequence_id:
        if update_ticket_sequence(sequence_id, data):
            show_notification("Ticket sequence updated successfully", "success")
        else:
            show_notification("Error updating ticket sequence", "error")
    else:
        if create_ticket_sequence(data):
            show_notification("Ticket sequence created successfully", "success")
        else:
            show_notification("Error creating ticket sequence", "error")

    dialog.close()


# ==============================================
# ADMIN / USERS TAB
# ==============================================

# Role options (hierarchy integers)
ROLE_OPTIONS = [
    (1, "1 - GOD"),
    (2, "2 - Administrator"),
    (3, "3 - Tech_GCC"),
    (4, "4 - Client"),
    (5, "5 - Client_Mngs"),
]


def create_admin_tab() -> ui.card:
    """Create admin/users management tab"""

    def fetch_clients_map():
        rows = list_customers("")
        out = {}
        for c in rows:
            cid = int(c["ID"])
            company = (c.get("company") or "").strip()
            first = (c.get("first_name") or "").strip()
            last = (c.get("last_name") or "").strip()
            label = company or (" ".join([first, last]).strip()) or f"Client {cid}"
            out[cid] = label
        return out

    clients_map = fetch_clients_map()

    state = {
        "selected_login_id": None,
        "selected_row": None,
    }

    def list_logins(search_text: str = ""):
        s = (search_text or "").strip().lower()
        like = f"%{s}%"

        sql = """
        SELECT
            L.ID AS login_db_id,
            L.login_id,
            L.hierarchy,
            L.is_active,
            L.customer_id,
            COALESCE(C.company, '') AS company,
            COALESCE(C.first_name, '') AS first_name,
            COALESCE(C.last_name, '') AS last_name
        FROM Logins L
        LEFT JOIN Customers C ON C.ID = L.customer_id
        """
        params = ()
        if s:
            sql += """
            WHERE
                LOWER(L.login_id) LIKE ?
                OR LOWER(C.company) LIKE ?
                OR LOWER(C.first_name) LIKE ?
                OR LOWER(C.last_name) LIKE ?
                OR LOWER(L.hierarchy) LIKE ?
            """
            params = (like, like, like, like, like)

        sql += " ORDER BY L.ID DESC;"

        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        out = []
        for r in rows:
            company = (r["company"] or "").strip()
            fname = (r["first_name"] or "").strip()
            lname = (r["last_name"] or "").strip()

            belongs = company
            if not belongs:
                nm = f"{fname} {lname}".strip()
                belongs = nm if nm else "(unassigned)"

            out.append({
                "login_db_id": int(r["login_db_id"]),
                "login_id": r["login_id"],
                "belongs_to": belongs,
                "role": r["hierarchy"],
                "active": int(r["is_active"] or 0),
                "customer_id": r["customer_id"],
            })
        return out

    with ui.card() as card:
        with ui.column().classes("w-full gap-2"):
            ui.label("Admin - Users & Logins").classes("text-xl font-bold")

            with ui.row().classes("w-full items-center gap-4"):
                search = ui.input("Search logins / client / role").classes("flex-1")

            with ui.row().classes("w-full gap-6"):
                # Left: Users list
                with ui.column().classes("flex-1"):
                    with ui.card().classes("gcc-card gcc-scrollable-card mt-1").style("max-height: 350px; padding: 8px;"):
                        logins_table = ui.table(
                            columns=[
                                {"name": "login_id", "label": "Login", "field": "login_id"},
                                {"name": "belongs_to", "label": "Belongs To", "field": "belongs_to"},
                                {"name": "role", "label": "Role", "field": "role"},
                                {"name": "active", "label": "Active", "field": "active"},
                            ],
                            rows=[],
                            row_key="login_db_id",
                            selection="single",
                            pagination={"rowsPerPage": 5},
                        ).classes("gcc-fixed-table text-sm")

                # Right: Edit panel
                with ui.column().classes("flex-1"):
                    ui.label("Edit Selected Login").classes("font-bold text-sm")

                    selected_title = ui.label("Selected: (none)").classes("text-xs mb-1")

                    login_id_readonly = ui.input("Login ID").props("readonly dense").classes("w-full")
                    role_sel = ui.select({k: v for k, v in ROLE_OPTIONS}, label="Role").props("dense").classes("w-full")
                    client_sel = ui.select(clients_map, label="Belongs To").props("dense").classes("w-full")
                    active_chk = ui.checkbox("Active")
                    new_pass = ui.input("Reset Password (opt)", password=True).props("dense").classes("w-full")

            # Action buttons below - NOT in a nested card
            with ui.row().classes("w-full gap-2 mt-4"):
                btn_add = ui.button("+ Add Login", icon="person_add").classes("bg-green-600 hover:bg-green-700 text-white font-semibold").props("unelevated")
                btn_delete = ui.button("Delete", icon="delete").classes("bg-red-600 hover:bg-red-700 text-white font-semibold").props("unelevated")
                btn_update = ui.button("Update", icon="save").classes("bg-blue-600 hover:bg-blue-700 text-white font-semibold").props("unelevated")
                btn_clear = ui.button("Clear", icon="clear").classes("bg-gray-600 hover:bg-gray-700 text-white font-semibold").props("unelevated")
                btn_creds = ui.button("CRED SP", icon="key").classes("bg-purple-600 hover:bg-purple-700 text-white font-semibold").props("unelevated")

            def set_buttons_enabled():
                has_sel = bool(state["selected_login_id"])
                btn_delete.enabled = has_sel
                btn_update.enabled = has_sel
                btn_clear.enabled = has_sel

            def refresh_logins():
                rows = list_logins(search.value or "")
                logins_table.rows = rows
                logins_table.update()

            def clear_selection():
                state["selected_login_id"] = None
                state["selected_row"] = None
                selected_title.text = "Selected: (none)"
                login_id_readonly.value = ""
                role_sel.value = None
                client_sel.value = None
                active_chk.value = False
                new_pass.value = ""
                logins_table.selected = []
                logins_table.update()
                set_buttons_enabled()

            def load_selected(row: dict):
                state["selected_login_id"] = int(row["login_db_id"])
                state["selected_row"] = row
                selected_title.text = f"Selected: {row.get('login_id')}"
                login_id_readonly.value = row.get("login_id") or ""
                role_sel.value = row.get("role")
                client_sel.value = row.get("customer_id") if row.get("customer_id") is not None else None
                active_chk.value = bool(int(row.get("active") or 0))
                new_pass.value = ""
                set_buttons_enabled()

            def on_table_select(_):
                if not logins_table.selected:
                    clear_selection()
                    return
                row = logins_table.selected[0]
                load_selected(row)

            logins_table.on("selection", on_table_select)

            def delete_login():
                if not state["selected_login_id"]:
                    show_notification("Select a login first", "error")
                    return

                with ui.dialog() as d:
                    with ui.card():
                        ui.label("Delete Login?").classes("text-lg font-bold")
                        ui.label(f"Delete: {state['selected_row']['login_id']}")
                        with ui.row().classes("gap-2 mt-4"):
                            ui.button("Cancel", on_click=d.close)
                            ui.button("Delete", color="negative", on_click=lambda: (
                                get_conn().__enter__().execute("DELETE FROM Logins WHERE ID = ?", (state["selected_login_id"],)),
                                get_conn().__enter__().commit(),
                                d.close(),
                                show_notification("Login deleted", "success"),
                                clear_selection(),
                                refresh_logins()
                            ))
                d.open()

            def open_add_dialog():
                with ui.dialog() as d:
                    with ui.card().style("width: 60%; max-width: 60%;").props("flat bordered"):
                        ui.label("Add Login").classes("text-lg font-bold")

                        with ui.column().classes("w-full gap-3 mt-2"):
                            with ui.row().classes("w-full gap-2"):
                                login_new = ui.input(label="Login ID (email)").props("dense").classes("flex-1")
                                role_new = ui.select({k: v for k, v in ROLE_OPTIONS}, label="User Role").props("dense").classes("flex-1")

                            with ui.row().classes("w-full gap-2"):
                                client_new = ui.select(clients_map, label="Belongs To").props("dense").classes("flex-1")
                                active_new = ui.checkbox(text="Active").classes("mt-2")
                                active_new.value = True

                            pass_new = ui.input(label="Password", password=True).props("dense").classes("w-full")
                            pass_confirm = ui.input(label="Confirm Password", password=True).props("dense").classes("w-full")

                        def create():
                            login_id = (login_new.value or "").strip().lower()
                            password = pass_new.value or ""
                            confirm = pass_confirm.value or ""
                            role = role_new.value
                            customer_id = client_new.value
                            active = active_new.value

                            if not login_id or not password or role is None:
                                show_notification("Fill Login ID, Password, and Role", "error")
                                return

                            if password != confirm:
                                show_notification("Passwords do not match", "error")
                                return

                            with get_conn() as conn:
                                exists = conn.execute("SELECT ID FROM Logins WHERE login_id = ?", (login_id,)).fetchone()
                                if exists:
                                    show_notification("Login ID already exists", "error")
                                    return

                                conn.execute(
                                    "INSERT INTO Logins (login_id, password_hash, password_salt, hierarchy, is_active, customer_id) VALUES (?, ?, '', ?, ?, ?)",
                                    (login_id, hash_password(password), int(role), 1 if active else 0, customer_id)
                                )
                                conn.commit()

                            d.close()
                            show_notification("Login created", "success")
                            refresh_logins()

                        with ui.row().classes("w-full gap-2 justify-end mt-4"):
                            ui.button("Cancel", on_click=d.close).classes("bg-gray-400 hover:bg-gray-500 text-white font-semibold").props("unelevated")
                            ui.button("Create", color="positive", on_click=create).classes("bg-green-600 hover:bg-green-700 text-white font-semibold").props("unelevated")
                d.open()

            def update_login():
                if not state["selected_login_id"]:
                    show_notification("Select a login first", "error")
                    return

                login_db_id = int(state["selected_login_id"])
                role = role_sel.value
                customer_id = client_sel.value
                is_active = 1 if active_chk.value else 0
                new_password = (new_pass.value or "").strip()

                if role is None:
                    show_notification("Role is required", "error")
                    return

                with get_conn() as conn:
                    if new_password:
                        conn.execute(
                            "UPDATE Logins SET hierarchy = ?, is_active = ?, customer_id = ?, password_hash = ? WHERE ID = ?",
                            (int(role), is_active, customer_id, hash_password(new_password), login_db_id)
                        )
                    else:
                        conn.execute(
                            "UPDATE Logins SET hierarchy = ?, is_active = ?, customer_id = ? WHERE ID = ?",
                            (int(role), is_active, customer_id, login_db_id)
                        )
                    conn.commit()

                show_notification("Login updated", "success")
                refresh_logins()

            def handle_creds():
                if not state["selected_login_id"]:
                    show_notification("Select a login first", "error")
                    return
                show_notification("Credentials management coming soon", "info")

            # Wire buttons
            search.on_value_change(lambda _: refresh_logins())
            btn_add.on_click(open_add_dialog)
            btn_delete.on_click(delete_login)
            btn_update.on_click(update_login)
            btn_clear.on_click(clear_selection)
            btn_creds.on_click(handle_creds)

            # Initial load
            clear_selection()
            refresh_logins()

    return card


def create_version_tab() -> ui.card:
    """
    Create version management tab
    
    NOTE: This is a JSON-based settings pattern that can be reused for other settings.
    Pattern:
    1. Load JSON file with json.load()
    2. Display fields from JSON
    3. Update JSON dict with new values
    4. Save back with json.dump()
    
    This same pattern works for any JSON configuration file (e.g., app_settings.json, feature_flags.json, etc.)
    """
    with ui.card().style("width: 60%; max-width: 60%;") as card:
        with ui.column().classes("w-full gap-2"):
            ui.label("App Version & Branding").classes("text-xl font-bold")
            ui.label("Manage application version and software name (for white-label rebranding)").classes("gcc-muted text-sm mb-2")

            version_info = get_version_info()
            fields = {}

            fields["software_name"] = ui.input(label="Software Name", value=version_info.get("software_name", "GCC Monitoring")).classes("w-full")
            
            with ui.row().classes("w-full gap-2"):
                fields["version"] = ui.input(label="Version Number", value=version_info.get("version", "1.0.0")).classes("flex-1")
                fields["build_date"] = ui.input(label="Build Date (YYYY-MM-DD)", value=version_info.get("build_date", "")).classes("flex-1")

            fields["release_date"] = ui.input(label="Release Date (YYYY-MM-DD)", value=version_info.get("release_date", "")).classes("w-full")
            fields["description"] = ui.textarea(label="Description", value=version_info.get("description", "")).classes("w-full").props("rows=3")

            def save_version():
                """Save version info to VERSION file"""
                try:
                    version_file = Path(__file__).parent.parent / "VERSION"
                    
                    # Load existing data to preserve features array
                    existing_data = {}
                    if version_file.exists():
                        with open(version_file, "r") as f:
                            existing_data = json.load(f)
                    
                    # Update with new values
                    existing_data["software_name"] = fields["software_name"].value.strip()
                    existing_data["version"] = fields["version"].value.strip()
                    existing_data["build_date"] = fields["build_date"].value.strip()
                    existing_data["release_date"] = fields["release_date"].value.strip()
                    existing_data["description"] = fields["description"].value.strip()
                    
                    # Write back
                    with open(version_file, "w") as f:
                        json.dump(existing_data, f, indent=2)
                    
                    show_notification("Version updated - refresh page to see changes", "success")
                    log_user_action("version_update", f"Updated to version {existing_data['version']}")
                    
                    # Force reload to clear cache
                    ui.run_javascript('window.location.reload();')
                except Exception as e:
                    show_notification(f"Error saving version: {str(e)}", "error")
                    handle_error(e, "save_version")

            with ui.row().classes("gap-3 mt-3"):
                ui.button("Save Version", on_click=save_version).classes("bg-blue-600 hover:bg-blue-700")

    return card


# ==============================================
# MAIN PAGE
# ==============================================


def page():
    """Settings/Configuration Dashboard Page"""
    if not require_login():
        return

    if not is_admin():
        ui.label("Access Denied: Admin privileges required").classes("text-red-600")
        return

    with layout("Settings & Configuration", show_logout=True, show_back=True, back_to="/"):
        # Place the main tabs at the top where the quick links used to be
        with ui.tabs().classes("w-full -mt-4 mb-2") as tabs:
            ui.tab("company", label="Company", icon="business")
            ui.tab("email", label="Email", icon="email")
            ui.tab("employees", label="Employees", icon="badge")
            ui.tab("service", label="Service", icon="settings")
            ui.tab("tickets", label="Tickets", icon="confirmation_number")
            ui.tab("version", label="Version", icon="info")
            ui.tab("admin", label="Users", icon="admin_panel_settings")

        with ui.tab_panels(tabs, value="company").classes("w-full"):
            with ui.tab_panel("company"):
                create_company_profile_tab()

            with ui.tab_panel("email"):
                create_email_settings_tab()

            with ui.tab_panel("employees"):
                create_employee_profile_tab()

            with ui.tab_panel("service"):
                create_service_call_settings_tab()

            with ui.tab_panel("tickets"):
                create_ticket_sequence_tab()

            with ui.tab_panel("version"):
                create_version_tab()

            with ui.tab_panel("admin"):
                create_admin_tab()