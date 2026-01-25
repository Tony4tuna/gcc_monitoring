# pages/equipment.py

from nicegui import ui
from core.auth import require_login, is_admin
from ui.layout import layout
from core.customers_repo import list_customers
from core.locations_repo import list_locations
from core.units_repo import list_units, create_unit, update_unit, delete_unit
from core.unit_status import get_unit_status
from core.logger import log_user_action, handle_error


def page():
    if not require_login():
        return

    log_user_action("Viewed Equipment Page")
    can_edit = is_admin()

    # ---------------------------------------------------------
    # Dashboard deep-link flags
    # ---------------------------------------------------------
    
    query = ui.context.client.request.query_params

    from_dashboard = query.get("from") == "dashboard"
    focus_unit_id = query.get("unit")





    try:
        focus_unit_id = int(focus_unit_id) if focus_unit_id else None
    except ValueError:
        focus_unit_id = None

    with layout("Equipment / Units", show_logout=True, show_back=True, back_to="/"):

        # ---------------------------------------------------------
        # CSS for better visual design
        # ---------------------------------------------------------
        ui.add_head_html("""
        <style>
            /* CRUD Button Grid - Horizontal compact */
            .gcc-crud-grid {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 0.5rem;
                margin-bottom: 0.75rem;
                width: 100%;
            }
            
            .gcc-crud-btn {
                min-height: 40px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: center;
                gap: 4px;
                transition: all 0.2s;
                white-space: nowrap;
            }
            
            .gcc-crud-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            
            /* Equipment main container - wider layout */
            .gcc-equipment-container {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 280px);
                gap: 0.75rem;
            }
            
            /* Selector Grid */
            .gcc-selector-grid {
                display: grid;
                grid-template-columns: auto 1fr auto 1fr;
                gap: 0.75rem;
                align-items: center;
                padding: 0.75rem;
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 8px;
                flex-shrink: 0;
            }
            
            @media (max-width: 1024px) {
                .gcc-selector-grid {
                    grid-template-columns: 1fr 1fr;
                }
            }
        </style>
        """)

        # ---------------------------------------------------------
        # Load customers
        # ---------------------------------------------------------
        customers = list_customers("")
        customer_opts = {
            int(c["ID"]): f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip()
            for c in customers
        }

        # ---------------------------------------------------------
        # Main equipment container (wider layout)
        # ---------------------------------------------------------
        with ui.element("div").classes("gcc-equipment-container"):
            
            # Selectors and search
            if not from_dashboard:
                with ui.element("div").classes("gcc-selector-grid"):
                    ui.label("Client:").classes("font-bold text-sm")
                    customer_sel = ui.select(customer_opts).classes("w-full")

                    ui.label("Location:").classes("font-bold text-sm")
                    location_sel = ui.select({}).classes("w-full")
                
                with ui.row().classes("gap-2 w-full items-center"):
                    search = ui.input("Search equipment...").props("dense outlined").classes("flex-1")
                    ui.label("Units: 0").set_text("Units: 0")
                    unit_count_label = ui.label("").classes("font-bold text-green-500 ml-auto")
            else:
                # placeholders (dashboard auto-selects)
                customer_sel = ui.select({})
                location_sel = ui.select({})
                unit_count_label = ui.label("")
                search = ui.input()

            # ---------------------------------------------------------
            # CRUD BUTTONS - Horizontal layout
            # ---------------------------------------------------------
            with ui.element("div").classes("gcc-crud-grid"):
                with ui.button(on_click=lambda: open_unit_dialog("add")).props("no-caps").classes("gcc-crud-btn").style("background: #16a34a; color: white;"):
                    ui.icon("add_circle", size="18px")
                    ui.label("Add")
                
                with ui.button(on_click=lambda: open_unit_dialog("edit")).props("no-caps").classes("gcc-crud-btn").style("background: #2563eb; color: white;"):
                    ui.icon("edit", size="18px")
                    ui.label("Edit")
                
                with ui.button(on_click=lambda: open_unit_dialog("delete")).props("no-caps").classes("gcc-crud-btn").style("background: #dc2626; color: white;"):
                    ui.icon("delete", size="18px")
                    ui.label("Delete")
                
                with ui.button(on_click=lambda: refresh()).props("no-caps outline").classes("gcc-crud-btn").style("border: 2px solid #16a34a; color: #16a34a;"):
                    ui.icon("refresh", size="18px")
                    ui.label("Refresh")
                
                with ui.button(on_click=lambda: main_table.selected.clear() if main_table.selected else None).props("no-caps outline").classes("gcc-crud-btn").style("border: 2px solid #6b7280; color: #6b7280;"):
                    ui.icon("clear", size="18px")
                    ui.label("Clear")

            # ---------------------------------------------------------
            # Table with fixed height - scrolls vertically
            # ---------------------------------------------------------
            with ui.card().classes("gcc-card flex-1").style("display: flex; flex-direction: column; min-height: 0;"):
                main_table = ui.table(
                    columns=[
                        {"name": "unit_tag", "label": "Unit Tag", "field": "unit_tag"},
                        {"name": "make", "label": "Make", "field": "make"},
                        {"name": "model", "label": "Model", "field": "model"},
                        {"name": "serial", "label": "Serial", "field": "serial"},
                        {"name": "mode", "label": "Mode", "field": "mode"},
                        {"name": "status", "label": "Status", "field": "status_color"},
                    ],
                    rows=[],
                    row_key="unit_id",
                    selection="single",
                    pagination={"rowsPerPage": 12},
                ).classes("w-full").style("flex: 1; min-height: 0;")
                main_table.props("dense bordered virtual-scroll")

        # ---------------------------------------------------------
        # CRUD Dialog Functions
        # ---------------------------------------------------------
        def open_unit_dialog(mode: str):
            if not can_edit and mode != "view":
                ui.notify("You don't have permission to edit equipment", type="warning")
                return
                
            selected = main_table.selected[0] if main_table.selected else None
            if mode in ("edit", "delete") and not selected:
                ui.notify("⚠️ Please select a unit first", type="warning")
                return
            
            if mode == "add" and not location_sel.value:
                ui.notify("⚠️ Please select a location first", type="warning")
                return

            if mode == "delete":
                def do_delete():
                    delete_unit(int(selected["unit_id"]))
                    dialog.close()
                    refresh()
                    ui.notify("✅ Unit deleted", type="positive")

                with ui.dialog() as dialog:
                    with ui.card().classes("w-[520px] p-6 gcc-card"):
                        ui.label("Delete Equipment Unit?").classes("text-xl font-bold text-red-500")
                        ui.label(f"Unit: {selected.get('unit_tag','')} - {selected.get('make','')} {selected.get('model','')}").classes("mt-2 mb-4")
                        ui.label("This action cannot be undone.").classes("text-sm gcc-muted")
                        with ui.row().classes("justify-end gap-3 mt-4"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")
                            ui.button("Delete", on_click=do_delete, color="negative").props("icon=delete")
                dialog.open()
                return

            # Add/Edit dialog
            data = {
                "unit_tag": selected.get("unit_tag", "") if selected else "",
                "make": selected.get("make", "") if selected else "",
                "model": selected.get("model", "") if selected else "",
                "serial": selected.get("serial", "") if selected else "",
                "location_id": int(location_sel.value) if location_sel.value else None,
            }

            def do_save():
                if not data["unit_tag"]:
                    ui.notify("⚠️ Unit Tag is required", type="warning")
                    return
                
                if mode == "add":
                    create_unit(data)
                else:
                    update_unit(int(selected["unit_id"]), data)
                dialog.close()
                refresh()
                ui.notify(f"✅ Unit {'added' if mode == 'add' else 'updated'}", type="positive")

            with ui.dialog() as dialog:
                with ui.card().classes("w-[680px] max-w-[95vw] p-6 gcc-card"):
                    title_icon = "add_circle" if mode == "add" else "edit"
                    ui.label(f"{'Add New' if mode == 'add' else 'Edit'} Equipment Unit").props(f"icon={title_icon}").classes("text-xl font-bold mb-4")

                    with ui.row().classes("w-full gap-4"):
                        ui.input("Unit Tag *", placeholder="RTU-1").bind_value(data, "unit_tag").classes("flex-1")
                        ui.input("Make", placeholder="Carrier").bind_value(data, "make").classes("flex-1")

                    with ui.row().classes("w-full gap-4"):
                        ui.input("Model", placeholder="50TCQ").bind_value(data, "model").classes("flex-1")
                        ui.input("Serial Number", placeholder="1234ABC").bind_value(data, "serial").classes("flex-1")

                    with ui.row().classes("justify-end gap-3 mt-6"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        ui.button("Save", on_click=do_save, color="primary").props(f"icon={'add' if mode == 'add' else 'save'}")
            dialog.open()

        # ---------------------------------------------------------
        # Refresh logic
        # ---------------------------------------------------------
        def refresh():
            if not location_sel.value:
                main_table.rows = []
                return

            units = list_units(search.value or "", int(location_sel.value))
            rows = []
            for u in units:
                status = get_unit_status(u["unit_id"])
                rows.append({**u, **status})

            main_table.rows = rows
            unit_count_label.text = f"Units: {len(rows)}"

            if from_dashboard and focus_unit_id:
                for r in rows:
                    if int(r["unit_id"]) == focus_unit_id:
                        main_table.selected = [r]
                        update_details()
                        break

        # ---------------------------------------------------------
        # Load locations
        # ---------------------------------------------------------
        def refresh_locations():
            if not customer_sel.value:
                return
            locs = list_locations("", int(customer_sel.value))
            location_sel.set_options({
                int(l["ID"]): f"{l['address1']} — {l['city']}"
                for l in locs
            })
            if locs:
                location_sel.value = int(locs[0]["ID"])

        customer_sel.on_value_change(lambda: (refresh_locations(), refresh()))
        location_sel.on_value_change(refresh)
        search.on_value_change(refresh)

        # ---------------------------------------------------------
        # Dashboard auto resolve (CRITICAL)
        # ---------------------------------------------------------
        if from_dashboard and focus_unit_id:
            for cid in customer_opts:
                locs = list_locations("", cid)
                for loc in locs:
                    units = list_units("", int(loc["ID"]))
                    for u in units:
                        if int(u["unit_id"]) == focus_unit_id:
                            customer_sel.value = cid
                            refresh_locations()
                            location_sel.value = int(loc["ID"])
                            refresh()
                            break

        refresh_locations()
        refresh()
