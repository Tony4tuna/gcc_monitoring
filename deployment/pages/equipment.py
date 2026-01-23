# pages/equipment.py
# FINAL+ – Paper table (less bright) + consistent buttons + confirm update/delete + print
# Updates requested:
# - Print button moved to the end (before Back)
# - Add a "List" button far away near Back (space in between for future buttons)
# - Print button color = orange (warning)
# - Print output: smaller font, but Unit Tag / Make / Model / Serial show FULL (wrap allowed), trim spaces

from nicegui import ui
from core.auth import require_login, is_admin
from ui.layout import layout
from core.customers_repo import list_customers
from core.locations_repo import list_locations
from core.units_repo import list_units, create_unit, update_unit, delete_unit
from core.unit_status import get_unit_status


def page():
    if not require_login():
        return

    can_edit = is_admin()

    with layout("Equipment / Units"):

        # ---------------------------------------------------------
        # PAPER TABLE CSS (less bright) + consistent button sizes
        # ---------------------------------------------------------
        ui.add_head_html("""
        <style>
          /* PAPER TABLE: softer / less bright */
          .gcc-paper-card {
            background: #f3fbf3 !important;
            border: 1px solid #cfd8e3 !important;
          }

          .gcc-paper-table thead th {
            background: #e3f2e3 !important;
            color: #0f172a !important;
            font-weight: 800 !important;
          }

          .gcc-paper-table td {
            color: #0f172a !important;
          }

          /* Zebra: white + very light green */
          .gcc-paper-table tbody tr:nth-child(odd) td {
            background: #ffffff !important;
          }
          .gcc-paper-table tbody tr:nth-child(even) td {
            background: #eef8ee !important;
          }

          .gcc-paper-table tbody tr:hover td {
            background: #e0f3e0 !important;
          }

          .gcc-paper-table .q-table__middle td,
          .gcc-paper-table .q-table__middle th {
            border-color: #cfd8e3 !important;
          }

          /* Consistent action buttons */
          .gcc-btn {
            min-width: 120px;
            height: 34px;
          }
        </style>
        """)

        customers = list_customers("")
        customer_opts = {
            int(c["ID"]): f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip()
            for c in customers
        }

        # First row: Client + Location + Units count
        with ui.row().classes("gap-6 w-full items-center flex-nowrap"):
            ui.label("Client:").classes("font-semibold min-w-[80px] text-right whitespace-nowrap")
            customer_sel = ui.select(customer_opts).classes("w-[380px] max-w-[380px]").props("dense ellipsis")

            ui.label("Location:").classes("font-semibold min-w-[80px] text-right whitespace-nowrap")
            location_sel = ui.select({}).classes("w-[380px] max-w-[380px]").props("dense ellipsis")

            unit_count_label = ui.label("Units in location: 0").classes(
                "font-medium text-gray-300 ml-8 flex items-center gap-2 whitespace-nowrap"
            )
            ui.icon("group_work", size="sm").classes("text-gray-400")

        # Search
        with ui.row().classes("w-full mt-4"):
            search = ui.input("Search (make/model/serial/unit_tag)").classes("w-full").props("dense")

        def refresh():
            if not location_sel.value:
                main_table.rows = []
                unit_count_label.text = "Units in location: 0"
                details_grid.classes(add="hidden")
                ui.notify("Select a location first", type="warning")
                return

            loading = ui.label("Loading units...").classes("text-primary text-lg mt-3")
            ui.update()

            try:
                units = list_units(search.value or "", int(location_sel.value))
                enhanced = []
                for u in units:
                    status = get_unit_status(u["unit_id"])
                    row = {**u, **status}
                    enhanced.append(row)

                main_table.rows = enhanced
                unit_count_label.text = f"Units in location: {len(enhanced)}"

                if not enhanced:
                    ui.notify("No units yet - add one", type="info")

                details_grid.classes(add="hidden")
            finally:
                loading.delete()
                ui.update()

        # ---------------------------------------------------------
        # PRINT (current rows)
        # ---------------------------------------------------------
        def _clean(v):
            if v is None:
                return ""
            return str(v).strip()

        def print_units():
            if not main_table.rows:
                ui.notify("Nothing to print", type="warning")
                return

            # Keep print font smaller, but show FULL key fields (wrap allowed)
            cols = [
                ("unit_tag", "Unit Tag", True),
                ("make", "Make", True),
                ("model", "Model", True),
                ("serial", "Serial", True),
                ("mode", "Mode", False),
                ("return_temp_f", "Area Temp °F", False),
                ("delta_t_f", "Delta T", False),
                ("fan_speed_percent", "Fan %", False),
                ("runtime_hours", "Runtime Hrs", False),
                ("last_update", "Last Update", False),
                ("alert_message", "Alert", False),
            ]

            rows_html = []
            for r in main_table.rows:
                tds = []
                for key, _label, is_key in cols:
                    val = _clean(r.get(key, ""))
                    cls = "keycol" if is_key else "normcol"
                    tds.append(f'<td class="{cls}">{val}</td>')
                rows_html.append("<tr>" + "".join(tds) + "</tr>")

            client_txt = _clean(customer_sel.options.get(customer_sel.value, "")) if customer_sel.value else ""
            loc_txt = _clean(location_sel.options.get(location_sel.value, "")) if location_sel.value else ""

            # Wider key columns; others smaller
            # (Unit Tag/Make/Model/Serial are the ones that must be readable in full)
            colgroup = """
              <col style="width:12%">
              <col style="width:18%">
              <col style="width:18%">
              <col style="width:18%">
              <col style="width:6%">
              <col style="width:8%">
              <col style="width:5%">
              <col style="width:5%">
              <col style="width:6%">
              <col style="width:8%">
              <col style="width:6%">
            """

            html = f"""
            <html>
            <head>
              <meta charset="utf-8" />
              <title>Equipment Units</title>
              <style>
                body {{ font-family: Arial, sans-serif; margin: 18px; }}
                h1 {{ margin: 0 0 6px 0; font-size: 16px; }}
                .sub {{ margin: 0 0 12px 0; color: #334155; font-size: 11px; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 10px; table-layout: fixed; }}
                th, td {{ border: 1px solid #cbd5e1; padding: 4px 6px; text-align: left; vertical-align: top; }}
                th {{ background: #e3f2e3; font-weight: 700; }}
                tr:nth-child(even) td {{ background: #eef8ee; }}

                /* FULL key fields: allow wrap to show full value */
                td.keycol {{
                  white-space: normal;
                  word-break: break-word;
                }}

                /* Other columns: keep compact */
                td.normcol {{
                  white-space: nowrap;
                  overflow: hidden;
                  text-overflow: ellipsis;
                }}

                @media print {{
                  body {{ margin: 10mm; }}
                }}
              </style>
            </head>
            <body>
              <h1>Equipment / Units</h1>
              <div class="sub"><b>Client:</b> {client_txt} &nbsp;&nbsp; <b>Location:</b> {loc_txt} &nbsp;&nbsp; <b>Total:</b> {len(main_table.rows)}</div>
              <table>
                <colgroup>{colgroup}</colgroup>
                <thead>
                  <tr>
                    {''.join([f"<th>{label}</th>" for _k, label, _is_key in cols])}
                  </tr>
                </thead>
                <tbody>
                  {''.join(rows_html)}
                </tbody>
              </table>
              <script>window.print();</script>
            </body>
            </html>
            """

            ui.run_javascript(f"""
              const w = window.open('', '_blank');
              w.document.open();
              w.document.write({html!r});
              w.document.close();
            """)

        # ---------------------------------------------------------
        # Buttons: same size, consistent colors, Print near end, Back last
        # Add "List" far away near Back for future expansion
        # ---------------------------------------------------------
        with ui.row().classes("gap-3 mt-4 items-center flex-wrap"):
            ui.button("Refresh", icon="refresh", on_click=refresh).props("dense outline").classes("gcc-btn")

            if can_edit:
                ui.button("Add", icon="add", on_click=lambda: open_dialog("add")).props("dense color=positive").classes("gcc-btn")
                ui.button("Edit", icon="edit", on_click=lambda: open_dialog("edit")).props("dense color=primary").classes("gcc-btn")
                ui.button("Delete", icon="delete", on_click=lambda: open_dialog("delete")).props("dense color=negative").classes("gcc-btn")

            # push "List/Print/Back" to the far end
            ui.space()

            # Placeholder navigation/future button slot
            ui.button("List", icon="list", on_click=lambda: ui.notify("List view (future)", type="info")).props("color=info").classes("gcc-btn")

            # Print (orange)
            ui.button("Print", icon="print", on_click=print_units).props("dense color=warning").classes("gcc-btn")

            # Back last
            ui.button("Back", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props("dense outline").classes("gcc-btn")

        # ---------------------------------------------------------
        # MAIN TABLE (paper card wrapper)
        # ---------------------------------------------------------
        with ui.card().classes("w-full mt-4 p-0 overflow-hidden gcc-paper-card"):
            main_table = ui.table(
                columns=[
                    {"name": "unit_tag", "label": "Unit Tag", "field": "unit_tag", "align": "left"},
                    {"name": "make", "label": "Make", "field": "make", "align": "left"},
                    {"name": "serial", "label": "Serial", "field": "serial", "align": "left"},
                    {"name": "mode", "label": "Mode", "field": "mode", "align": "left"},
                    {"name": "area_temp_f", "label": "Area Temp °F", "field": "return_temp_f", "align": "left"},
                    {"name": "status", "label": "Status", "field": "status_color", "align": "left"},
                ],
                rows=[],
                row_key="unit_id",
                selection="single",
                pagination={"rowsPerPage": 25, "options": [10, 25, 50, 100]},
            ).classes("w-full text-sm gcc-paper-table")

            main_table.props("dense bordered separator-cell flat")
            main_table.style("max-height: 40vh; overflow-y: auto; overflow-x: auto;")

            # Mode badge
            main_table.add_slot('body-cell-mode', r'''
                <td :props="props" class="text-left p-3">
                    <q-badge :color="props.row.status_color" text-color="white" outline square>
                        {{ props.value || '-' }}
                    </q-badge>
                    <q-tooltip v-if="props.row.alert_message">
                        {{ props.row.alert_message }}
                    </q-tooltip>
                </td>
            ''')

            # Status: Online/Offline
            main_table.add_slot('body-cell-status', r'''
                <td :props="props" class="text-left p-3">
                    <q-badge :color="props.row.status_color" text-color="white" outline square>
                        {{ props.row.mode === 'Off' || props.row.mode === 'Fault' ? 'Offline' : 'Online' }}
                    </q-badge>
                </td>
            ''')

        # ---------------------------------------------------------
        # DETAILS GRID (paper card wrapper)
        # ---------------------------------------------------------
        details_grid = ui.card().classes("w-full mt-6 p-4 rounded-lg hidden gcc-paper-card")
        with details_grid:
            ui.label("Selected Unit Details").classes("text-lg font-bold mb-3 text-slate-900")

            details_table = ui.table(
                columns=[
                    {"name": "param", "label": "Parameter", "field": "param", "align": "left"},
                    {"name": "value", "label": "Value", "field": "value", "align": "left"},
                ],
                rows=[],
            ).classes("w-full text-sm gcc-paper-table")

            details_table.props("dense bordered separator-cell flat")

        # Update details grid when unit is selected
        def update_details():
            selected = main_table.selected[0] if main_table.selected else None
            if selected:
                details_rows = [
                    {"param": "Unit ID", "value": selected.get('unit_id', '-')},
                    {"param": "Unit Tag", "value": selected.get('unit_tag', '-')},
                    {"param": "Equipment Type", "value": selected.get('equipment_type', '-')},
                    {"param": "Make", "value": selected.get('make', '-')},
                    {"param": "Model", "value": selected.get('model', '-')},
                    {"param": "Serial", "value": selected.get('serial', '-')},
                    {"param": "Refrigerant", "value": selected.get('refrigerant_type', '-')},
                    {"param": "Capacity (Tons)", "value": selected.get('tonnage', '-')},
                    {"param": "BTU Rating", "value": selected.get('btu_rating', '-')},
                    {"param": "Voltage", "value": selected.get('voltage', '-')},
                    {"param": "Amperage", "value": selected.get('amperage', '-')},
                    {"param": "Breaker Size", "value": selected.get('breaker_size', '-')},
                    {"param": "Installation Date", "value": selected.get("inst_date", "-")},
                    {"param": "Warranty End", "value": selected.get("warranty_end_date", "-")},
                    {"param": "Delta T", "value": f"{selected.get('delta_t_f', '-')} °F"},
                    {"param": "Fan Speed", "value": f"{selected.get('fan_speed_percent', '-')} %"},
                    {"param": "Runtime Hours", "value": selected.get("runtime_hours", "-")},
                    {"param": "Note ID", "value": selected.get("note_id", "-")},
                    {"param": "Last Serviced", "value": selected.get("last_update", "-")},
                    {"param": "Alert", "value": selected.get("alert_message", "-")},
                ]
                details_table.rows = details_rows
                details_grid.classes(remove="hidden")
            else:
                details_grid.classes(add="hidden")

        main_table.on("selection", update_details)

        def refresh_locations():
            if not customer_sel.value:
                location_sel.clear()
                return
            locs = list_locations("", int(customer_sel.value))
            opts = {int(l["ID"]): f"{l['address1']} — {l['city']} {l['state']}".strip() for l in locs}
            location_sel.set_options(opts)
            if locs:
                location_sel.value = int(locs[0]["ID"])

        customer_sel.on_value_change(lambda: (refresh_locations(), refresh()))
        location_sel.on_value_change(refresh)
        search.on_value_change(refresh)

        # ---------------------------------------------------------
        # Confirm dialogs (update/delete)
        # ---------------------------------------------------------
        def confirm_dialog(title: str, message: str, confirm_text: str, confirm_color: str, on_confirm):
            with ui.dialog() as d:
                with ui.card().classes("gcc-card p-5 w-[520px] max-w-[95vw]"):
                    ui.label(title).classes("text-lg font-bold")
                    ui.label(message).classes("gcc-muted")
                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=d.close).props("flat")
                        ui.button(confirm_text, on_click=lambda: (on_confirm(), d.close())).props(f"color={confirm_color}")
            d.open()

        def open_dialog(mode: str):
            selected = main_table.selected[0] if main_table.selected else None

            if mode in ["edit", "delete"] and not selected:
                ui.notify("Select a unit first", type="warning")
                return

            if mode == "delete":
                msg = (
                    f"Delete unit {selected['unit_id']} ({selected.get('unit_tag', 'no tag')})?\n"
                    f"This cannot be undone."
                )
                confirm_dialog(
                    title="Confirm Delete",
                    message=msg,
                    confirm_text="Delete",
                    confirm_color="negative",
                    on_confirm=lambda: (delete_unit(int(selected["unit_id"])), refresh(), ui.notify("Deleted", type="positive")),
                )
                return

            if mode == "add" and not location_sel.value:
                ui.notify("Select a location first before adding a unit", type="warning")
                return

            data = {
                "location_id": int(location_sel.value),
                "unit_tag": "" if mode == "add" else selected.get("unit_tag", ""),
                "equipment_type": "RTU" if mode == "add" else selected.get("equipment_type", "RTU"),
                "make": "" if mode == "add" else selected.get("make", ""),
                "model": "" if mode == "add" else selected.get("model", ""),
                "serial": "" if mode == "add" else selected.get("serial", ""),
                "refrigerant_type": "" if mode == "add" else selected.get("refrigerant_type", ""),
                "voltage": "" if mode == "add" else selected.get("voltage", ""),
                "amperage": "" if mode == "add" else selected.get("amperage", ""),
                "btu_rating": "" if mode == "add" else selected.get("btu_rating", ""),
                "tonnage": "" if mode == "add" else selected.get("tonnage", ""),
                "breaker_size": "" if mode == "add" else selected.get("breaker_size", ""),
                "note_id": None if mode == "add" else selected.get("note_id", None),
                "inst_date": "" if mode == "add" else selected.get("inst_date", ""),
                "warranty_end_date": "" if mode == "add" else selected.get("warranty_end_date", ""),
            }

           

            def save_now():
                try:
                    if mode == "add":
                        new_id = create_unit(data)
                        ui.notify(f"Unit added (ID: {new_id})", type="positive")
                    else:
                        update_unit(int(selected["unit_id"]), data)
                        ui.notify("Unit updated", type="positive")

                    d.close()          # ✅ CLOSE the edit dialog after confirmed save
                    refresh()

                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")










            def do_save():
                if mode == "edit":
                    confirm_dialog(
                        title="Confirm Update",
                        message=f"Update unit {selected['unit_id']} ({selected.get('unit_tag', '')}) with these changes?",
                        confirm_text="Update",
                        confirm_color="primary",
                        on_confirm=save_now,
                    )
                else:
                    save_now()
                    d.close()

            with ui.dialog() as d:
                with ui.card().classes("gcc-card p-6 w-[700px] max-w-[95vw]"):
                    ui.label("Add Unit" if mode == "add" else "Edit Unit").classes("text-xl font-bold mb-4")

                    ui.input("Unit Tag (e.g. RTU-01)").bind_value(data, "unit_tag").classes("w-full").props("required")

                    if mode == "edit":
                        ui.input("Unit ID (system)", value=str(selected["unit_id"])).props("readonly").classes("w-full")

                    with ui.row().classes("w-full gap-3"):
                        ui.select(["RTU", "Split", "VRF Indoor", "DOAS", "Freezer", "Chiller", "Boiler", "Other"], label="Equipment Type").bind_value(data, "equipment_type").classes("flex-1")
                        ui.input("Refrigerant (e.g. R-410A)").bind_value(data, "refrigerant_type").classes("flex-1")
                    
                    ui.input("Make").bind_value(data, "make").classes("w-full")
                    ui.input("Model").bind_value(data, "model").classes("w-full")
                    ui.input("Serial").bind_value(data, "serial").classes("w-full")
                    
                    with ui.row().classes("w-full gap-3"):
                        ui.input("Capacity (tons)").bind_value(data, "tonnage").classes("flex-1")
                        ui.input("BTU Rating").bind_value(data, "btu_rating").classes("flex-1")
                    
                    with ui.row().classes("w-full gap-3"):
                        ui.input("Voltage (e.g. 208-230V 3Ph)").bind_value(data, "voltage").classes("flex-1")
                        ui.input("Amperage").bind_value(data, "amperage").classes("flex-1")
                        ui.input("Breaker Size").bind_value(data, "breaker_size").classes("flex-1")
                    
                    with ui.row().classes("w-full gap-3"):
                        ui.input("Inst Date (YYYY-MM-DD)").bind_value(data, "inst_date").classes("flex-1")
                        ui.input("Warranty End (YYYY-MM-DD)").bind_value(data, "warranty_end_date").classes("flex-1")
                    
                    ui.input("Note ID (optional)").bind_value(data, "note_id").classes("w-full")

                    loc_name = location_sel.options.get(location_sel.value, "Unknown")
                    ui.label(f"Location: {loc_name}").classes("text-sm gcc-muted mt-2")

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=d.close).props("flat")
                        ui.button("Save", on_click=do_save).props("color=primary")

            d.open()

        refresh_locations()
        refresh()
