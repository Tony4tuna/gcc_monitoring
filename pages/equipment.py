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

    with layout("Equipment / Units", show_logout=True):

        # ---------------------------------------------------------
        # CSS
        # ---------------------------------------------------------
        ui.add_head_html("""
                    <style>
            /* === GCC PAPER THEME (RESTORED) === */

            .gcc-paper-card {
                background: var(--card) !important;
                border: 1px solid var(--border) !important;
                border-radius: 10px;
            }

            .gcc-paper-table thead th {
                background: rgba(22, 163, 74, 0.15) !important;
                color: var(--text) !important;
                font-weight: 700 !important;
            }

            .gcc-paper-table td {
                color: var(--text) !important;
            }

            .gcc-paper-table tbody tr:nth-child(odd) td {
                background: transparent !important;
            }

            .gcc-paper-table tbody tr:nth-child(even) td {
                background: rgba(22, 163, 74, 0.06) !important;
            }

            .gcc-paper-table tbody tr:hover td {
                background: rgba(22, 163, 74, 0.12) !important;
            }

            .gcc-paper-table .q-table__middle td,
            .gcc-paper-table .q-table__middle th {
                border-color: var(--border) !important;
            }

            .gcc-btn {
                min-width: 120px;
                height: 34px;
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
        # Client / Location selectors
        # ---------------------------------------------------------
        if not from_dashboard:
            with ui.row().classes("gap-6 w-full items-center"):
                ui.label("Client:")
                customer_sel = ui.select(customer_opts).props("dense")

                ui.label("Location:")
                location_sel = ui.select({}).props("dense")

                unit_count_label = ui.label("Units: 0")
        else:
            # placeholders (dashboard auto-selects)
            customer_sel = ui.select({})
            location_sel = ui.select({})
            unit_count_label = ui.label("")

        # ---------------------------------------------------------
        # Search
        # ---------------------------------------------------------
        if not from_dashboard:
            search = ui.input("Search").props("dense")
        else:
            search = ui.input()

        # ---------------------------------------------------------
        # Main table
        # ---------------------------------------------------------
        
        with ui.card().classes("gcc-card gcc-scrollable-card mt-4"):
            main_table = ui.table(
                columns=[
                    {"name": "unit_tag", "label": "Unit Tag", "field": "unit_tag"},
                    {"name": "make", "label": "Make", "field": "make"},
                    {"name": "serial", "label": "Serial", "field": "serial"},
                    {"name": "mode", "label": "Mode", "field": "mode"},
                    {"name": "status", "label": "Status", "field": "status_color"},
                ],
                rows=[],
                row_key="unit_id",
                selection="single",
                pagination={"rowsPerPage": 10},
            ).classes("gcc-fixed-table")

        # ---------------------------------------------------------
        # Details
        # ---------------------------------------------------------
        details = ui.card().classes("w-full mt-4 hidden gcc-paper-card")
        with details:
            details_label = ui.label("Selected Unit Details")
            details_table = ui.table(
                columns=[
                    {"name": "k", "label": "Field", "field": "k"},
                    {"name": "v", "label": "Value", "field": "v"},
                ],
                rows=[],
            )

        def update_details():
            sel = main_table.selected
            if not sel:
                details.classes(add="hidden")
                return

            u = sel[0]
            details_table.rows = [
                {"k": "Unit ID", "v": u.get("unit_id")},
                {"k": "Unit Tag", "v": u.get("unit_tag")},
                {"k": "Make", "v": u.get("make")},
                {"k": "Model", "v": u.get("model")},
                {"k": "Serial", "v": u.get("serial")},
                {"k": "Alert", "v": u.get("alert_message")},
            ]
            details.classes(remove="hidden")

        main_table.on("selection", update_details)

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
