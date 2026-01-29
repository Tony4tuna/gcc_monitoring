"""
Shared ticket action handlers
Used by both dashboard.py and tickets.py to avoid code duplication
"""

from typing import Dict, Any, Optional


def get_selected_ticket_id(selected: Dict[str, Any]) -> int:
    """
    Extract numeric ticket ID from selected table row
    Handles both raw ID and HTML-formatted ID display
    
    Args:
        selected: Selected row dict from UI table
        
    Returns:
        Numeric ticket ID
    """
    # Use _id_raw if available (HTML-formatted tables)
    # Otherwise fall back to ID field
    return selected.get("_id_raw", selected.get("ID"))


def open_ticket_dialog(
    mode: str,
    selected_row: Optional[Dict[str, Any]],
    user: Dict[str, Any],
    hierarchy: int,
    customer_id: Optional[int] = None
):
    """
    Open ticket dialog based on mode
    Shared logic for dashboard and tickets page
    
    Args:
        mode: "new", "view", "edit", "close", "delete", "print", "email"
        selected_row: Selected table row (None for "new" mode)
        user: Current user dict
        hierarchy: User hierarchy level
        customer_id: Customer ID (for client users)
    """
    from nicegui import ui
    from pages.tickets import (
        show_ticket_detail, 
        show_edit_dialog, 
        show_close_dialog, 
        confirm_delete, 
        show_print_call, 
        send_ticket_email
    )
    
    if mode == "new":
        # Create empty call structure for new service call
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
            "labor_description": "",
        }
        show_edit_dialog(new_call, mode="create", user=user, hierarchy=hierarchy)
        return
    
    if not selected_row:
        ui.notify("Select a service call first", type="warning")
        return
    
    # Extract data from selected row
    full_data = selected_row.get("_full_data", selected_row)
    call_id = get_selected_ticket_id(selected_row)
    
    # Route to appropriate handler
    if mode == "view":
        show_ticket_detail(full_data)
    elif mode == "edit":
        show_edit_dialog(full_data, mode="edit", user=user, hierarchy=hierarchy)
    elif mode == "close":
        show_close_dialog(call_id)
    elif mode == "delete":
        confirm_delete(call_id)
    elif mode == "print":
        show_print_call(full_data)
    elif mode == "email":
        send_ticket_email(call_id)
