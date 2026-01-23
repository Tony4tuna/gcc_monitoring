# ui/layout.py
from nicegui import ui
from core.auth import current_user, logout


def layout(title: str = "HVAC Dashboard", show_logout: bool = False, hierarchy: int = None):
    user = current_user() or {}
    if hierarchy is None:
        hierarchy = user.get("hierarchy", 5)

    # Force dark mode
    ui.run_javascript('document.body.classList.remove("light")')

    ui.add_head_html("""
    <style>
      :root {
        --bg: #07150f;
        --card: #0b231a;
        --text: #f0f0f0;
        --muted: #aaaaaa;
        --accent: #16a34a;
        --line: rgba(255,255,255,0.14);
      }
      body { background: var(--bg); color: var(--text); }
      .gcc-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 16px;
      }
      .gcc-muted { color: var(--muted); }
      .menu-link { width: 100%; text-align: left; justify-content: flex-start; }
    </style>
    """)

    def confirm_logout():
        with ui.dialog() as d:
            with ui.card().classes("gcc-card"):
                ui.label("Logout?").classes("text-lg font-bold")
                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=d.close)
                    ui.button(
                        "Logout",
                        on_click=lambda: (d.close(), logout(), ui.navigate.to("/login")),
                        color="negative",
                    )
        d.open()

    # ------------------------------------------------------------
    # LEFT DRAWER (created ONCE)
    # ------------------------------------------------------------
    drawer = ui.left_drawer(value=True).props(
        "bordered width=260 show-if-above breakpoint=900"
    ).classes("p-4").style("background: var(--bg);")

    with drawer:
        # Title row WITH burger (desktop-friendly)
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(title).classes("text-xl font-bold")
            ui.button("☰", on_click=drawer.toggle).props("flat dense")

        ui.separator().classes("my-2")

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
            ui.button("🏠 Dashboard", on_click=lambda: ui.navigate.to("/")).classes("menu-link")
            ui.button("👥 Clients", on_click=lambda: ui.navigate.to("/clients")).classes("menu-link")
            ui.button("📍 Locations", on_click=lambda: ui.navigate.to("/locations")).classes("menu-link")
            ui.button("📦 Equipment", on_click=lambda: ui.navigate.to("/equipment")).classes("menu-link")
            ui.button("🎫 Service Tickets", on_click=lambda: ui.navigate.to("/tickets")).classes("menu-link")
            ui.button("⚙️ Settings", on_click=lambda: ui.navigate.to("/settings")).classes("menu-link")

            if show_logout:
                ui.separator().classes("my-2")
                ui.button("🚪 Logout", on_click=confirm_logout, color="negative").classes("menu-link")

    # ------------------------------------------------------------
    # HEADER (mobile-friendly burger)
    # ------------------------------------------------------------
    with ui.header().style("background: var(--card); border-bottom: 1px solid var(--line);"):
        with ui.row().classes("items-center gap-3"):
            # SECOND burger (same drawer, safe)
            ui.button("☰", on_click=drawer.toggle).props("flat dense")
            ui.label("GCC Monitoring System").classes("font-bold")

        with ui.row().classes("ml-auto items-center gap-2"):
            if user:
                ui.label(user.get("email", "")).classes("gcc-muted")

    # ------------------------------------------------------------
    # PAGE CONTENT
    # ------------------------------------------------------------
    return ui.column().classes("p-6 w-full mx-auto gap-6")
