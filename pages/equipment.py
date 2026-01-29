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
        # Load customers
        # ---------------------------------------------------------
        customers = list_customers("")
        customer_opts = {
            int(c["ID"]): f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip()
            for c in customers
        }

        # Wrap page content in flex column to allow table to grow + scroll
        with ui.column().classes("w-full h-full flex-1 min-h-0 gap-3").style("display: flex; flex-direction: column;"):

            # -----------------------------------------------------
            # Selectors and toolbar - compact single-line layout
            # -----------------------------------------------------
            if not from_dashboard:
                with ui.row().classes("gap-3 w-full items-center flex-wrap mb-2"):
                    ui.label("Client:").classes("font-semibold")
                    customer_sel = ui.select(customer_opts).classes("w-[420px]")
                    ui.label("Location:").classes("font-semibold")
                    location_sel = ui.select({}).classes("w-[320px]")
                    search = ui.input("Search...").classes("w-[200px]")
                    unit_count_label = ui.label("").classes("font-bold text-green-500")
            else:
                # placeholders (dashboard auto-selects)
                customer_sel = ui.select({})
                location_sel = ui.select({})
                unit_count_label = ui.label("")
                search = ui.input()

            # -----------------------------------------------------
            # CRUD BUTTONS - Horizontal layout
            # -----------------------------------------------------
            with ui.row().classes("gap-2 flex-wrap items-center mb-2"):
                ui.button("Add", icon="add_circle", on_click=lambda: open_unit_dialog("add")).props("dense color=positive")
                ui.button("Edit", icon="edit", on_click=lambda: open_unit_dialog("edit")).props("dense color=green-10")
                ui.button("Delete", icon="delete", on_click=lambda: open_unit_dialog("delete")).props("dense color=negative outline")
                ui.button(icon="refresh", on_click=lambda: refresh()).props("flat dense")

            # -----------------------------------------------------
            # Table - flex grows to fill, scrolls internally
            # -----------------------------------------------------
            with ui.card().classes("gcc-card w-full flex-1 min-h-0") \
                    .style("display: flex; flex-direction: column; overflow: hidden; max-height: 55vh"):
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
                    pagination={"rowsPerPage": 15},
                ).classes("w-full") \
                 .style("flex: 1; min-height: 0; overflow: hidden;")
                main_table.props("dense bordered virtual-scroll")

            # Invisible footer card to prevent overflow (keeps container boundaries)
            with ui.card().classes("gcc-card p-3 flex-shrink-0").style("opacity: 0; pointer-events: none; height: 1px; min-height: 1px; padding: 0;"):
                ui.label("").classes("text-xs")

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
