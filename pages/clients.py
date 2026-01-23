from nicegui import ui
from core.auth import require_login, is_admin
from ui.layout import layout
from core.customers_repo import list_customers, create_customer, update_customer, delete_customer
from core.auth import logout  # ← add this import at top

def page():
    if not require_login():
        return

    can_edit = is_admin()

    with layout("Clients"):
        ui.button("Logout", on_click=lambda: (logout(), ui.navigate.to("/login"))).props("dense flat color=negative")
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

        with ui.row().classes("gap-3 w-full items-center flex-wrap"):
            search = ui.input("Search (company, name, email, phone)").classes("w-96")
            ui.button("Refresh", on_click=lambda: refresh()).props("outline dense")
            ui.space()
            ui.button("Add Client", on_click=lambda: open_customer_dialog("add")).props(f"dense color=primary {'disable' if not can_edit else ''}")
            ui.button("Edit", on_click=lambda: open_customer_dialog("edit")).props(f"dense {'disable' if not can_edit else ''}")
            ui.button("Delete", on_click=lambda: open_customer_dialog("delete")).props(f"dense color=negative outline {'disable' if not can_edit else ''}")

        table = ui.table(
            columns=[
                {"name": "ID", "label": "ID", "field": "ID"},
                {"name": "company", "label": "Company", "field": "company"},
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "phone1", "label": "Phone", "field": "phone1"},
                {"name": "city", "label": "City", "field": "city"},
                {"name": "state", "label": "State", "field": "state"},
            ],
            rows=[],
            row_key="ID",
            selection="single",
            pagination={"rowsPerPage": 25, "options": [10, 25, 50, 100]},
        ).classes("w-full gcc-card rounded-lg overflow-hidden gcc-soft-grid")
        table.props("dense bordered separator-cell")

        def refresh():
            rows = list_customers(search.value or "")
            for r in rows:
                r["name"] = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
            table.rows = rows
            table.update()

        def open_customer_dialog(mode: str):
            selected = table.selected[0] if table.selected else None
            if mode in ("edit", "delete") and not selected:
                ui.notify("Select a client first", type="warning")
                return

            if mode == "delete":
                def do_delete():
                    delete_customer(int(selected["ID"]))
                    dialog.close()
                    refresh()
                    ui.notify("Client deleted", type="positive")

                with ui.dialog() as dialog:
                    with ui.card().classes("w-[520px] p-6 gcc-card"):
                        ui.label("Delete Client").classes("text-xl font-bold mb-2")
                        ui.label(f"Delete: {selected.get('company','')} ({selected.get('ID')}) ?").classes("gcc-muted mb-4")
                        with ui.row().classes("justify-end gap-3"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")
                            ui.button("Delete", on_click=do_delete).props("color=negative")
                dialog.open()
                return

            data = {
                "company": selected.get("company", "") if selected else "",
                "first_name": selected.get("first_name", "") if selected else "",
                "last_name": selected.get("last_name", "") if selected else "",
                "email": selected.get("email", "") if selected else "",
                "phone1": selected.get("phone1", "") if selected else "",
                "phone2": selected.get("phone2", "") if selected else "",
                "address1": selected.get("address1", "") if selected else "",
                "address2": selected.get("address2", "") if selected else "",
                "city": selected.get("city", "") if selected else "",
                "state": selected.get("state", "") if selected else "",
                "zip": selected.get("zip", "") if selected else "",
                "notes": selected.get("notes", "") if selected else "",
            }

            def do_save():
                if mode == "add":
                    create_customer(data)
                else:
                    update_customer(int(selected["ID"]), data)
                dialog.close()
                refresh()
                ui.notify("Saved", type="positive")

            with ui.dialog() as dialog:
                with ui.card().classes("w-[820px] max-w-[95vw] p-6 gcc-card"):
                    ui.label("Add Client" if mode == "add" else "Edit Client").classes("text-xl font-bold mb-4")

                    ui.input("Company").bind_value(data, "company").classes("w-full")

                    with ui.row().classes("gap-4 wrap"):
                        ui.input("First Name").bind_value(data, "first_name").classes("flex-1 min-w-[220px]")
                        ui.input("Last Name").bind_value(data, "last_name").classes("flex-1 min-w-[220px]")

                    with ui.row().classes("gap-4 wrap"):
                        ui.input("Email").bind_value(data, "email").classes("flex-1 min-w-[260px]")
                        ui.input("Phone 1").bind_value(data, "phone1").classes("flex-1 min-w-[200px]")
                        ui.input("Phone 2").bind_value(data, "phone2").classes("flex-1 min-w-[200px]")

                    ui.separator().classes("my-4")

                    with ui.row().classes("gap-4 wrap"):
                        ui.input("Address 1").bind_value(data, "address1").classes("flex-1 min-w-[260px]")
                        ui.input("Address 2").bind_value(data, "address2").classes("flex-1 min-w-[260px]")

                    with ui.row().classes("gap-4 wrap"):
                        ui.input("City").bind_value(data, "city").classes("flex-1 min-w-[220px]")
                        ui.input("State").bind_value(data, "state").classes("w-28")
                        ui.input("Zip").bind_value(data, "zip").classes("w-32")

                    ui.textarea("Notes").bind_value(data, "notes").classes("w-full min-h-[220px] resize-y mt-4")

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        ui.button("Save", on_click=do_save).props("color=primary")

            dialog.open()

        refresh()