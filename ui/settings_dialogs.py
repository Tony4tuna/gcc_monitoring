# ui/settings_dialogs.py
# Reusable dialog components for settings module

from nicegui import ui
from typing import Callable, Dict, Any, List, Optional


class SettingsDialog:
    """Base class for settings dialogs with consistent styling and layout"""
    
    def __init__(self, title: str, modal_size: str = "md"):
        """
        Initialize settings dialog
        
        Args:
            title: Dialog title
            modal_size: Dialog size - sm (400px), md (600px), lg (800px), xl (1000px)
        """
        self.title = title
        self.modal_size = modal_size
        self.dialog = None
        self.fields: Dict[str, ui.input] = {}
        self.size_map = {
            "sm": "min-w-96 max-w-sm",
            "md": "min-w-full max-w-2xl",
            "lg": "min-w-full max-w-4xl",
            "xl": "min-w-full max-w-6xl",
        }
    
    def create(self, on_save: Callable, on_cancel: Optional[Callable] = None):
        """Create the dialog structure"""
        self.dialog = ui.dialog()
        
        with self.dialog:
            with ui.card().classes(f"{self.size_map.get(self.modal_size, self.size_map['md'])} gap-4"):
                # Header with close button
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(self.title).classes("text-lg font-bold")
                    ui.button(icon="close", on_click=self.close).props("flat dense")
                
                # Content area
                with ui.column().classes("w-full gap-4") as self.content_area:
                    pass
                
                # Footer with action buttons
                with ui.row().classes("w-full gap-2 justify-end"):
                    ui.button("Cancel", on_click=on_cancel or self.close).classes("bg-gray-400 hover:bg-gray-500")
                    ui.button("Save", on_click=on_save).classes("bg-blue-600 hover:bg-blue-700")
        
        return self.dialog
    
    def add_field(self, name: str, label: str, input_type: str = "text", 
                  value: Any = "", options: List[str] = None):
        """Add input field to dialog"""
        with self.content_area:
            if input_type == "select":
                field = ui.select(label=label, options=options or [], value=value)
            elif input_type == "checkbox":
                field = ui.checkbox(text=label, value=bool(value))
            elif input_type == "number":
                field = ui.number(label=label, value=value)
            elif input_type == "textarea":
                field = ui.textarea(label=label, value=value)
            elif input_type == "password":
                field = ui.input(label=label, password=True, value=value)
            else:
                field = ui.input(label=label, value=value)
            
            self.fields[name] = field
        
        return field
    
    def add_row_fields(self, fields: List[Dict[str, Any]]):
        """Add multiple fields in a row"""
        with self.content_area:
            with ui.row().classes("w-full gap-4"):
                for field_config in fields:
                    name = field_config.get("name", "")
                    label = field_config.get("label", "")
                    input_type = field_config.get("type", "text")
                    value = field_config.get("value", "")
                    options = field_config.get("options", None)
                    
                    if input_type == "select":
                        field = ui.select(label=label, options=options or [], value=value).classes("flex-1")
                    elif input_type == "checkbox":
                        field = ui.checkbox(text=label, value=bool(value))
                    elif input_type == "number":
                        field = ui.number(label=label, value=value).classes("flex-1")
                    else:
                        field = ui.input(label=label, value=value).classes("flex-1")
                    
                    self.fields[name] = field
    
    def add_section(self, title: str):
        """Add a section title/divider"""
        with self.content_area:
            ui.label(title).classes("text-md font-semibold mt-4")
    
    def get_values(self) -> Dict[str, Any]:
        """Get all field values"""
        return {name: field.value for name, field in self.fields.items()}
    
    def open(self):
        """Open the dialog"""
        if self.dialog:
            self.dialog.open()
    
    def close(self):
        """Close the dialog"""
        if self.dialog:
            self.dialog.close()


class FormDialog(SettingsDialog):
    """Generic form dialog for create/edit operations"""
    
    def __init__(self, title: str, fields_config: List[Dict[str, Any]], modal_size: str = "md"):
        """
        Initialize form dialog
        
        Args:
            title: Dialog title
            fields_config: List of field configurations
            modal_size: Dialog size
        """
        super().__init__(title, modal_size)
        self.fields_config = fields_config
    
    def create_form(self, on_save: Callable, on_cancel: Optional[Callable] = None):
        """Create form with configured fields"""
        self.create(on_save, on_cancel)
        
        for field_config in self.fields_config:
            if "row" in field_config and field_config["row"]:
                # This field is part of a row - skip individual creation
                continue
            
            name = field_config.get("name", "")
            label = field_config.get("label", "")
            input_type = field_config.get("type", "text")
            value = field_config.get("value", "")
            options = field_config.get("options", None)
            
            self.add_field(name, label, input_type, value, options)
        
        return self.dialog


class ConfirmDialog:
    """Reusable confirmation dialog"""
    
    def __init__(self, title: str, message: str, on_confirm: Callable, on_cancel: Optional[Callable] = None):
        """Initialize confirmation dialog"""
        self.title = title
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
    
    def show(self):
        """Show the confirmation dialog"""
        with ui.dialog() as dialog:
            with ui.card().classes("min-w-96"):
                ui.label(self.title).classes("text-lg font-bold")
                ui.label(self.message)
                
                with ui.row().classes("w-full gap-2 justify-end mt-4"):
                    ui.button("Cancel", on_click=lambda: (
                        self.on_cancel() if self.on_cancel else None,
                        dialog.close()
                    )).classes("bg-gray-400 hover:bg-gray-500")
                    ui.button("Confirm", on_click=lambda: (
                        self.on_confirm(),
                        dialog.close()
                    )).classes("bg-red-600 hover:bg-red-700")
        
        dialog.open()


class TableWithActions:
    """Reusable table component with action buttons"""
    
    def __init__(self, columns: List[Dict], rows: List[Dict], on_edit: Callable, 
                 on_delete: Callable, row_key: str = "id"):
        """Initialize table with actions"""
        self.columns = columns
        self.rows = rows
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.row_key = row_key
    
    def create(self) -> ui.table:
        """Create table with action buttons"""
        # Add actions column
        self.columns.append({
            'name': 'actions',
            'label': 'Actions',
            'field': 'actions',
            'align': 'center'
        })
        
        table = ui.table(columns=self.columns, rows=self.rows, row_key=self.row_key).classes("w-full")
        
        return table


class NotificationBanner:
    """Reusable notification banner"""
    
    @staticmethod
    def success(message: str):
        """Show success notification"""
        ui.notify(message, position="top", type="positive")
    
    @staticmethod
    def error(message: str):
        """Show error notification"""
        ui.notify(message, position="top", type="negative")
    
    @staticmethod
    def info(message: str):
        """Show info notification"""
        ui.notify(message, position="top", type="info")
    
    @staticmethod
    def warning(message: str):
        """Show warning notification"""
        ui.notify(message, position="top", type="warning")
