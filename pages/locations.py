from nicegui import ui
from core.auth import require_login, is_admin
from ui.layout import layout
from core.customers_repo import list_customers
from core.locations_repo import list_locations, create_location, update_location, delete_location
from core.logger import log_user_action, handle_error

def page():
    if not require_login():
        return

    log_user_action("Viewed Locations Page")
    can_edit = is_admin()

    with layout("Locations", show_logout=True, show_back=True, back_to="/"):

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

        # Toolbar - clean layout with auto-refresh
        with ui.row().classes("gap-3 w-full items-center flex-wrap mb-4"):
            ui.label("Client:").classes("font-semibold")
            customer_id = ui.select(options=options).classes("w-[520px]")
            search = ui.input("Search location (address/city/state/zip/contact)").classes("w-96")
            add_btn = ui.button("Add Location", icon="add", on_click=lambda: open_location_dialog("add")).props("dense color=primary")
            edit_btn = ui.button("Edit", icon="edit", on_click=lambda: open_location_dialog("edit")).props("dense color=green-10")
            delete_btn = ui.button("Delete", icon="delete", on_click=lambda: open_location_dialog("delete")).props("dense color=negative outline")

        # Table with fixed height
        with ui.card().classes("gcc-card").style("height: calc(100vh - 380px); display: flex; flex-direction: column;"):
            table = ui.table(
                columns=[
                    {"name": "ID", "label": "ID", "field": "ID"},
                    {"name": "address1", "label": "Address 1", "field": "address1"},
                    {"name": "city", "label": "City", "field": "city"},
                    {"name": "state", "label": "State", "field": "state"},
                    {"name": "zip", "label": "Zip", "field": "zip"},
                    {"name": "contact", "label": "Contact", "field": "contact"},
                    {"name": "job_phone", "label": "Job Phone", "field": "job_phone"},
                    {"name": "business_name", "label": "Business Name", "field": "business_name"},
                    {"name": "res", "label": "Res", "field": "res"},
                    {"name": "com", "label": "Com", "field": "com"},
                ],
                rows=[],
                row_key="ID",
                selection="single",
                pagination={"rowsPerPage": 15},
            ).classes("w-full").style("flex: 1; min-height: 0;")
            table.props("dense bordered virtual-scroll")

            empty_label = ui.label("Pick a client to load locations").classes("gcc-muted text-sm")

        def update_button_states():
            has_client = bool(customer_id.value)
            if not can_edit:
                add_btn.disable()
                edit_btn.disable()
                delete_btn.disable()
            else:
                if has_client:
                    add_btn.enable()
                    edit_btn.enable()
                    delete_btn.enable()
                else:
                    add_btn.disable()
                    edit_btn.disable()
                    delete_btn.disable()

        def refresh():
            if not customer_id.value:
                table.rows = []
                table.selected = []
                table.update()
                empty_label.visible = True
                empty_label.update()
                update_button_states()
                return

            cid = int(customer_id.value)
            rows = list_locations(search.value or "", cid)
            for r in rows:
                r["res"] = "✔" if int(r.get("residential") or 0) == 1 else ""
                r["com"] = "✔" if int(r.get("commercial") or 0) == 1 else ""
                # Show business name for commercial properties
                if int(r.get("commercial") or 0) == 1 and r.get("business_name"):
                    r["business_name"] = r.get("business_name", "")
                else:
                    r["business_name"] = ""
            table.rows = rows
            table.update()
            empty_label.visible = len(rows) == 0
            empty_label.update()
            update_button_states()

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
                    location_id = int(selected["ID"])
                    location_address = selected.get("address1", "Unknown")
                    delete_location(location_id)
                    dialog.close()
                    refresh()
                    ui.notify(f"✓ Location deleted: {location_address}", type="positive", timeout=3000)

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
                "business_name": selected.get("business_name", "") if selected else "",
            }

            def do_save():
                data["custid"] = int(customer_id.value)
                try:
                    if mode == "add":
                        new_id = create_location(data)
                        msg = f"✓ Location #{new_id} created successfully"
                        if data.get("commercial") and data.get("business_name"):
                            msg += f" - Business: {data['business_name']}"
                        ui.notify(msg, type="positive", timeout=3000)
                    else:
                        update_location(int(selected["ID"]), data)
                        msg = f"✓ Location #{selected['ID']} updated successfully"
                        if data.get("commercial") and data.get("business_name"):
                            msg += f" - Business: {data['business_name']}"
                        ui.notify(msg, type="positive", timeout=3000)
                    dialog.close()
                    refresh()
                except Exception as e:
                    ui.notify(f"✗ Save failed: {str(e)}", type="negative", timeout=5000)

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
                        commercial_check = ui.checkbox("Commercial").bind_value(data, "commercial")

                    # Business name for commercial properties (LLC name)
                    business_name_input = ui.input("Business Name (LLC/Corporation)").bind_value(data, "business_name").classes("w-full")
                    business_name_input.set_visibility(data.get("commercial", 0) == 1)
                    
                    def toggle_business_name():
                        business_name_input.set_visibility(data.get("commercial", 0) == 1)
                        business_name_input.update()
                    
                    commercial_check.on_value_change(lambda: toggle_business_name())

                    ui.textarea("Notes").bind_value(data, "notes").classes("w-full min-h-[180px] resize-y mt-4")
                    ui.textarea("Extended Notes").bind_value(data, "extendednotes").classes("w-full min-h-[240px] resize-y")

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        ui.button("Save", on_click=do_save).props("color=primary")

            dialog.open()

        # Auto-refresh when customer or search changes
        customer_id.on("update:model-value", lambda e: refresh())
        search.on("update:model-value", lambda e: refresh())
        
        # Start with no selection; wait for explicit client choice
        update_button_states()