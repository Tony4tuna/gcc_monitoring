# ui/layout.py
from nicegui import ui
from core.auth import current_user, logout
from core.version import get_version, get_build_info


def layout(title: str = "HVAC Dashboard", show_logout: bool = False, hierarchy: int = None, show_back: bool = False, back_to: str = "/"):
    """Common app layout.

    Goals (UI-only):
    - same spacing on every page
    - same table borders
    - same toolbar alignment (filters left, actions right)
    - page title always appears at the top
    - back button navigation when needed
    
    Args:
        title: Page title
        show_logout: Show logout option in sidebar
        hierarchy: User hierarchy level (auto-detected if None)
        show_back: Show back button in header
        back_to: URL to navigate back to (default: dashboard)
    """

    user = current_user() or {}
    if hierarchy is None:
        hierarchy = user.get("hierarchy", 5)

    # Force dark mode
    ui.run_javascript('document.body.classList.remove("light")')

    # Global styles (shared by ALL pages)
    ui.add_head_html("""
    <style>
      :root {
        --bg: #07150f;
        --card: #0b231a;
        --text: #f0f0f0;
        --muted: #aaaaaa;
        --accent: #16a34a;
        --line: rgba(255,255,255,0.14);
        --border: rgba(255,255,255,0.12);
      }
      
      body { 
        background: var(--bg); 
        color: var(--text);
        overflow: hidden; /* Prevent body scroll */
        margin: 0;
        padding: 0;
      }

      /* Cards */
      .gcc-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 16px;
      }
      .gcc-muted { color: var(--muted); }

      /* Fixed layout container */
      .gcc-page-container {
        height: 100vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }
      
      /* Content wrapper - fills remaining space */
      .gcc-content-wrapper {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 1.5rem;
        min-height: 0; /* Critical for flex scrolling */
      }
      
      /* Page with table - fixed layout */
      .gcc-page-with-table {
        display: flex;
        flex-direction: column;
        height: 100%;
        gap: 1rem;
      }
      
      /* Toolbar area - fixed height */
      .gcc-page-toolbar {
        flex-shrink: 0;
      }
      
      /* Table container - grows to fill */
      .gcc-page-table-container {
        flex: 1;
        min-height: 0;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }
      
      /* Grid container with fixed height */
      .gcc-grid-container {
        height: calc(100vh - 280px); /* Adjust based on your header/footer */
        min-height: 500px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }
      
      /* Table wrapper with internal scroll */
      .gcc-table-wrapper {
        flex: 1;
        min-height: 0;
        overflow: hidden;
        border: 1px solid var(--border);
        border-radius: 8px;
        background: var(--card);
        display: flex;
        flex-direction: column;
      }
      
      /* Fixed table with internal scroll */
      .gcc-fixed-table {
        flex: 1;
        min-height: 0;
        overflow: hidden;
      }
      
      .gcc-fixed-table .q-table__container {
        height: 100% !important;
        max-height: none !important;
        display: flex !important;
        flex-direction: column !important;
      }
      
      .gcc-fixed-table .q-table__top {
        flex-shrink: 0;
      }
      
      .gcc-fixed-table .q-table__middle {
        flex: 1 !important;
        min-height: 0 !important;
        max-height: none !important;
        overflow-y: auto !important;
        overflow-x: auto !important;
      }
      
      .gcc-fixed-table .q-table__bottom {
        flex-shrink: 0;
      }

      /* Sidebar buttons */
      .menu-link {
        width: 100%;
        text-align: left;
        justify-content: flex-start;
      }

      /* Tables: subtle grid borders */
      .gcc-soft-grid .q-table__middle table td,
      .gcc-soft-grid .q-table__middle table th {
        border-color: rgba(255,255,255,0.12) !important;
      }
      body.light .gcc-soft-grid .q-table__middle table td,
      body.light .gcc-soft-grid .q-table__middle table th {
        border-color: rgba(0,0,0,0.12) !important;
      }

      /* Toolbars: left filters + right actions */
      .gcc-toolbar {
        width: 100%;
        display: flex;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
        padding: 12px 0;
      }
      .gcc-toolbar-left {
        display: flex;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
        flex: 1;
        min-width: 260px;
      }
      .gcc-toolbar-right {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
        margin-left: auto;
      }

      /* Consistent button sizing */
      .gcc-btn {
        border-radius: 10px;
        font-weight: 600;
      }

      /* Dialog sizing helper */
      .gcc-dialog {
        border-radius: 12px;
      }
      
      /* Clickable row indicator */
      .clickable-row {
        cursor: pointer;
        transition: background-color 0.2s;
      }
      .clickable-row:hover {
        background-color: rgba(22, 163, 74, 0.1) !important;
      }
      
      /* Tooltip style */
      .gcc-tooltip {
        font-size: 12px;
        background: rgba(0, 0, 0, 0.9);
        padding: 6px 10px;
        border-radius: 4px;
      }
      
      /* Consistent spacing */
      .gcc-section {
        margin-bottom: 24px;
      }
      
      .gcc-section-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 12px;
        color: var(--text);
      }
      
      .gcc-helper-text {
        font-size: 12px;
        color: var(--muted);
        margin-bottom: 8px;
      }
      
      /* Grid layout for dashboard */
      .gcc-dashboard-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        width: 100%;
        height: calc(100vh - 380px);
        margin-top: 1rem;
      }
      
      .gcc-dashboard-grid-item {
        background: var(--card);
        border: 1px solid var(--border);
        box-shadow: 0 0 0 1px var(--border);
        border-radius: 8px;
        padding: 1rem;
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      
      .gcc-dashboard-table {
        flex: 1;
        overflow: auto !important;
        width: 100%;
        min-height: 0;
      }
      
      .gcc-dashboard-table .q-table__container {
        max-height: 100% !important;
        overflow: auto !important;
      }
      
      .gcc-dashboard-table .q-table__middle {
        overflow-x: auto !important;
        overflow-y: auto !important;
        max-height: calc(100vh - 420px) !important;
      }
      
      @media (max-width: 1200px) {
        .gcc-dashboard-grid {
          grid-template-columns: 1fr;
          height: auto;
        }
      }
      
      /* Card that fills available height */
      .gcc-fill-card {
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
    </style>
    """)

    def confirm_logout():
        with ui.dialog() as d:
            with ui.card().classes("gcc-card gcc-dialog w-[520px] max-w-[92vw]"):
                ui.label("Logout?").classes("text-lg font-bold")
                ui.label("You will be returned to the login screen.").classes("gcc-muted mt-1")
                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=d.close).props("flat")
                    ui.button(
                        "Logout",
                        on_click=lambda: (d.close(), logout(), ui.navigate.to("/login")),
                        color="negative",
                    )
        d.open()

    # ------------------------------------------------------------
    # LEFT DRAWER
    # ------------------------------------------------------------
    drawer = ui.left_drawer(value=True).props(
      "bordered width=260 show-if-above breakpoint=900"
    ).classes("p-4 flex flex-col").style("background: var(--bg);")

    with drawer:
        with ui.column().classes("gap-2 h-full w-full"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("GCC Monitoring").classes("text-xl font-bold")
                ui.button("☰", on_click=drawer.toggle).props("flat dense")

            # CLIENT (hierarchy 4)
            if hierarchy == 4:
                ui.label("Client Portal").classes("text-sm gcc-muted mb-2")

                ui.button("Dashboard").props("flat dense").disable()
                ui.button("Equipment").props("flat dense").disable()
                ui.button("My Profile").props("flat dense").disable()

                if show_logout:
                    ui.separator().classes("my-2")
                    ui.button("Logout", on_click=confirm_logout).props("outline color=negative")

            # ADMIN / TECH
            else:
                with ui.row().classes("items-center gap-2 text-sm gcc-muted mb-1"):
                    ui.icon("home").classes("text-lg").style("color: var(--text);")
                    ui.label("Home")
                ui.button("👥 Clients", on_click=lambda: ui.navigate.to("/clients")).classes("menu-link")
                ui.button("📍 Locations", on_click=lambda: ui.navigate.to("/locations")).classes("menu-link")
                ui.button("📦 Equipment", on_click=lambda: ui.navigate.to("/equipment")).classes("menu-link")
                ui.button("�️ Thermostat", on_click=lambda: ui.navigate.to("/thermostat")).classes("menu-link")
                ui.button("�🎫 Service Tickets", on_click=lambda: ui.navigate.to("/tickets")).classes("menu-link")
                ui.button("⚙️ Settings", on_click=lambda: ui.navigate.to("/settings")).classes("menu-link")

                if show_logout:
                    ui.separator().classes("my-2")
                    ui.button("🚪 Logout", on_click=confirm_logout, color="negative").classes("menu-link")

            ui.element("div").style("flex: 1 1 auto;")
            ui.separator().classes("my-2")
            build = get_build_info()
            ui.label(f"v{get_version()} • {build.get('build_date', '—')}").classes("text-xs gcc-muted")

    # ------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------
    with ui.header().style("background: var(--card); border-bottom: 1px solid var(--line);"):
        with ui.row().classes("items-center gap-3 w-full"):
            # Burger menu
            ui.button("☰", on_click=drawer.toggle).props("flat dense")
            
            # Back button (if enabled)
            if show_back:
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to(back_to)
                ).props("flat dense").tooltip("Go back")
            
            # Title
            ui.label("GCC Monitoring").classes("font-bold")

        with ui.row().classes("ml-auto items-center gap-2"):
            if user:
                ui.label(user.get("email", "")).classes("gcc-muted")

    # ------------------------------------------------------------
    # PAGE CONTENT
    # ------------------------------------------------------------
    content = ui.column().classes("gcc-page-container w-full")

    with content:
        # Page header (fixed)
        with ui.row().classes("w-full items-center gap-3 px-6 pt-6"):
            if show_back:
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to(back_to)
                ).props("flat dense color=primary").tooltip(f"Back to {back_to.replace('/', '').title() or 'Dashboard'}")
            
            ui.label(title).classes("text-2xl font-bold")
        
        ui.separator().classes("opacity-20 mx-6")
        
        # Scrollable content area
        content_area = ui.column().classes("gcc-content-wrapper w-full")

    return content_area
