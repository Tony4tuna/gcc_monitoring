"""
Standard table page component - ONE pattern for all CRUD pages.
Uses the EXACT same structure as working dashboard tables.
"""

from contextlib import contextmanager
from typing import Generator, Optional, Callable, List, Dict, Any
from nicegui import ui


@contextmanager
def table_page(
    *,
    title: str,
    columns: List[Dict[str, Any]],
    row_key: str = "ID",
    toolbar_builder: Optional[Callable] = None,
    on_refresh: Callable,
    can_edit: bool = True,
) -> Generator[Any, None, None]:
    """
    Standard CRUD table page layout - matches working dashboard pattern.
    
    Args:
        title: Page section title
        columns: Table column definitions (same as ui.table)
        row_key: Row key field name
        toolbar_builder: Function that builds filter/search controls
        on_refresh: Function that returns table rows
        can_edit: Whether CRUD buttons are enabled
        
    Usage:
        with table_page(
            title="Clients",
            columns=[...],
            toolbar_builder=lambda ctx: build_filters(ctx),
            on_refresh=lambda filters: fetch_data(filters)
        ) as page:
            # Access page.table, page.refresh(), etc.
    """
    
    # Container matching dashboard grid item
    with ui.column().classes("w-full flex-1 min-h-0 overflow-hidden"):
        with ui.column().classes("w-full flex-1 min-h-0 gap-3"):
            
            # Title
            ui.label(title).classes("text-lg font-bold")
            
            # Toolbar area
            toolbar_container = ui.row().classes("gap-3 w-full items-center flex-wrap")
            
            # Action buttons row
            actions_row = ui.row().classes("gap-2 items-center flex-wrap")
            
            ui.separator().classes("opacity-40")
            
            # Table wrapper - EXACT dashboard pattern
            with ui.element("div").classes("gcc-fixed-table w-full flex-1 min-h-0").style(
                "display: flex; flex-direction: column; border: 1px solid var(--border); "
                "border-radius: 12px; background: var(--card); padding: 0;"
            ):
                table = ui.table(
                    columns=columns,
                    rows=[],
                    row_key=row_key,
                    selection="single",
                ).classes("w-full gcc-soft-grid")
                table.props('dense flat bordered virtual-scroll header-align="left"')
    
    # Build context object
    class TablePageContext:
        def __init__(self):
            self.table = table
            self.toolbar_container = toolbar_container
            self.actions_row = actions_row
            self.on_refresh = on_refresh
            self.can_edit = can_edit
            self._filter_state = {}
        
        def refresh(self):
            """Reload table data"""
            rows = self.on_refresh(self._filter_state)
            self.table.rows = rows
            self.table.update()
        
        def add_filter(self, name: str, widget):
            """Register a filter widget"""
            self._filter_state[name] = widget
            return widget
        
        def add_action(self, label: str, icon: str, on_click: Callable, **props):
            """Add an action button"""
            with self.actions_row:
                btn = ui.button(icon=icon, on_click=on_click).props("flat dense").tooltip(label)
                if not self.can_edit and label.lower() in ("add", "edit", "delete"):
                    btn.disable()
                for key, val in props.items():
                    btn.props(f"{key}={val}")
                return btn
        
        def get_selected(self) -> Optional[Dict[str, Any]]:
            """Get selected row or None"""
            return self.table.selected[0] if self.table.selected else None
    
    ctx = TablePageContext()
    
    # Build toolbar if provided
    if toolbar_builder:
        with ctx.toolbar_container:
            toolbar_builder(ctx)
    
    # Initial load
    ctx.refresh()
    
    yield ctx
