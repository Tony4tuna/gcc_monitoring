from nicegui import ui
from core.auth import require_login, is_admin
from ui.layout import layout
from core.customers_repo import list_customers
from core.locations_repo import list_locations, create_location, update_location, delete_location

def page():
    if not require_login():
        return

    can_edit = is_admin()

    with layout("Locations"):

        ui.add_head_html("""
        <style>
          .gcc-soft-grid .q-table__middle table td,
          .gcc-soft-grid .q-table__middle table th {
            border-color: rgba(255,255,255,0.12) !important;
          }
          body.light .gcc-soft-grid .q-table__middle table td,
          body.light .gcc-soft-grid .q-table__middle table th {
            border-color: rgba(0,0,0,0.12) !important;
          }
        </style>
        """)

        customers = list_customers("")
        options = {
            int(c["ID"]): f"{c.get('company','')} — {c.get('first_name','')} {c.get('last_name','')}".strip()
            for c in customers
        }

        with ui.row().classes("gap-3 w-full items-center flex-wrap"):
            ui.label("Client:").classes("font-semibold")
            customer_id = ui.select(options=options).classes("w-[520px]")
            if customers:
                customer_id.value = int(customers[0]["ID"])
            search = ui.input("Search location (address/city/state/zip/contact)").classes("w-96")
            ui.button("Refresh", on_click=lambda: refresh()).props("outline dense")
            ui.space()
            ui.button("Add Location", on_click=lambda: open_location_dialog("add")).props(f"dense color=primary {'disable' if not can_edit else ''}")
            ui.button("Edit", on_click=lambda: open_location_dialog("edit")).props(f"dense {'disable' if not can_edit else ''}")
            ui.button("Delete", on_click=lambda: open_location_dialog("delete")).props(f"dense color=negative outline {'disable' if not can_edit else ''}")

        table = ui.table(
            columns=[
                {"name": "ID", "label": "ID", "field": "ID"},
                {"name": "address1", "label": "Address 1", "field": "address1"},
                {"name": "city", "label": "City", "field": "city"},
                {"name": "state", "label": "State", "field": "state"},
                {"name": "zip", "label": "Zip", "field": "zip"},
                {"name": "contact", "label": "Contact", "field": "contact"},
                {"name": "job_phone", "label": "Job Phone", "field": "job_phone"},
                {"name": "res", "label": "Res", "field": "res"},
                {"name": "com", "label": "Com", "field": "com"},
            ],
            rows=[],
            row_key="ID",
            selection="single",
            pagination={"rowsPerPage": 25, "options": [10, 25, 50, 100]},
        ).classes("w-full gcc-card rounded-lg overflow-hidden gcc-soft-grid")
        table.props("dense bordered separator-cell")

        def refresh():
            if not customer_id.value:
                table.rows = []
                table.update()
                return

            cid = int(customer_id.value)
            rows = list_locations(search.value or "", cid)
            for r in rows:
                r["res"] = "✔" if int(r.get("residential") or 0) == 1 else ""
                r["com"] = "✔" if int(r.get("commercial") or 0) == 1 else ""
            table.rows = rows
            table.update()

        def open_location_dialog(mode: str):
            if not customer_id.value:
                ui.notify("Pick a client first", type="warning")
                return

            selected = table.selected[0] if table.selected else None
            if mode in ("edit", "delete") and not selected:
                ui.notify("Select a location first", type="warning")
                return

            if mode == "delete":
                def do_delete():
                    delete_location(int(selected["ID"]))
                    dialog.close()
                    refresh()
                    ui.notify("Deleted", type="positive")

                with ui.dialog() as dialog:
                    with ui.card().classes("p-6 gcc-card"):
                        ui.label("Delete Location?").classes("text-lg font-bold")
                        with ui.row().classes("justify-end gap-3 mt-4"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")
                            ui.button("Delete", on_click=do_delete).props("color=negative")
                dialog.open()
                return

            data = {
                "custid": int(customer_id.value),
                "address1": selected.get("address1", "") if selected else "",
                "address2": selected.get("address2", "") if selected else "",
                "city": selected.get("city", "") if selected else "",
                "state": selected.get("state", "") if selected else "",
                "zip": selected.get("zip", "") if selected else "",
                "contact": selected.get("contact", "") if selected else "",
                "job_phone": selected.get("job_phone", "") if selected else "",
                "job_phone2": selected.get("job_phone2", "") if selected else "",
                "notes": selected.get("notes", "") if selected else "",
                "extendednotes": selected.get("extendednotes", "") if selected else "",
                "residential": int(selected.get("residential") or 0) if selected else 0,
                "commercial": int(selected.get("commercial") or 0) if selected else 0,
            }

            def do_save():
                data["custid"] = int(customer_id.value)
                if mode == "add":
                    create_location(data)
                else:
                    update_location(int(selected["ID"]), data)
                dialog.close()
                refresh()
                ui.notify("Saved", type="positive")

            with ui.dialog() as dialog:
                with ui.card().classes("w-[920px] max-w-[95vw] p-6 gcc-card"):
                    ui.label("Add Location" if mode == "add" else "Edit Location").classes("text-xl font-bold mb-4")

                    ui.input("Address 1").bind_value(data, "address1").classes("w-full")
                    ui.input("Address 2").bind_value(data, "address2").classes("w-full")

                    with ui.row().classes("gap-4 wrap"):
                        ui.input("City").bind_value(data, "city").classes("flex-1 min-w-[220px]")
                        ui.input("State").bind_value(data, "state").classes("w-28")
                        ui.input("Zip").bind_value(data, "zip").classes("w-32")

                    with ui.row().classes("gap-4 wrap"):
                        ui.input("Contact").bind_value(data, "contact").classes("flex-1 min-w-[220px]")
                        ui.input("Job Phone").bind_value(data, "job_phone").classes("flex-1 min-w-[200px]")
                        ui.input("Job Phone 2").bind_value(data, "job_phone2").classes("flex-1 min-w-[200px]")

                    with ui.row().classes("gap-6 mt-2"):
                        ui.checkbox("Residential").bind_value(data, "residential")
                        ui.checkbox("Commercial").bind_value(data, "commercial")

                    ui.textarea("Notes").bind_value(data, "notes").classes("w-full min-h-[180px] resize-y mt-4")
                    ui.textarea("Extended Notes").bind_value(data, "extendednotes").classes("w-full min-h-[240px] resize-y")

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        ui.button("Save", on_click=do_save).props("color=primary")

            dialog.open()

        customer_id.on("update:model-value", lambda e: refresh())
        refresh()