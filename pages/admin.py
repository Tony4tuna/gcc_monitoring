# pages/admin.py
# Admin: Manage LOGINS + assignment to CLIENTS (Clients CRUD stays in /clients)

from nicegui import ui
from core.auth import require_login, is_admin, logout
try:
    from ui.layout import layout
except Exception:
    from contextlib import contextmanager

    @contextmanager
    def layout(title: str):
        with ui.column().classes("p-4"):
            ui.label(title).classes("text-2xl")
            yield
from core.db import get_conn
from core.security import hash_password
from core.customers_repo import list_customers


# --- Roles (hierarchy integers) ---
# CRITICAL: Store integers in hierarchy column for auth system
ROLE_OPTIONS = [
    (1, "1 - GOD"),
    (2, "2 - Administrator"),
    (3, "3 - Tech_GCC"),
    (4, "4 - Client"),
    (5, "5 - Client_Mngs"),
]


def page():
    if not require_login() or not is_admin():
        ui.label("Access denied").classes("text-red-500 text-xl mt-10")
        return

    with layout("Admin - Users & Logins"):

        # ---------- helpers ----------
        def fetch_clients_map():
            # {id:int -> label:str}
            rows = list_customers("")
            out = {}
            for c in rows:
                cid = int(c["ID"])
                company = (c.get("company") or "").strip()
                first = (c.get("first_name") or "").strip()
                last = (c.get("last_name") or "").strip()
                # Prefer company; fallback to name; fallback to ID
                label = company or (" ".join([first, last]).strip()) or f"Client {cid}"
                out[cid] = label
            return out

        clients_map = fetch_clients_map()

        # state container (simple + junior friendly)
        state = {
            "selected_login_id": None,   # Logins.ID
            "selected_row": None,        # row dict from table
        }

        # ---------- DB queries ----------
        def list_logins(search_text: str = ""):
            s = (search_text or "").strip().lower()
            like = f"%{s}%"

            sql = """
            SELECT
                L.ID AS login_db_id,
                L.login_id,
                L.hierarchy,
                L.is_active,
                L.customer_id,
                COALESCE(C.company, '') AS company,
                COALESCE(C.first_name, '') AS first_name,
                COALESCE(C.last_name, '') AS last_name
            FROM Logins L
            LEFT JOIN Customers C ON C.ID = L.customer_id
            """
            params = ()
            if s:
                sql += """
                WHERE
                    LOWER(L.login_id) LIKE ?
                    OR LOWER(C.company) LIKE ?
                    OR LOWER(C.first_name) LIKE ?
                    OR LOWER(C.last_name) LIKE ?
                    OR LOWER(L.hierarchy) LIKE ?
                """
                params = (like, like, like, like, like)

            sql += " ORDER BY L.ID DESC;"

            with get_conn() as conn:
                rows = conn.execute(sql, params).fetchall()

            out = []
            for r in rows:
                company = (r["company"] or "").strip()
                fname = (r["first_name"] or "").strip()
                lname = (r["last_name"] or "").strip()

                belongs = company
                if not belongs:
                    nm = f"{fname} {lname}".strip()
                    belongs = nm if nm else "(unassigned)"

                out.append({
                    "login_db_id": int(r["login_db_id"]),
                    "login_id": r["login_id"],
                    "belongs_to": belongs,
                    "role": r["hierarchy"],
                    "active": int(r["is_active"] or 0),
                    "customer_id": r["customer_id"],
                })
            return out

        # ---------- UI: top controls ----------
        with ui.row().classes("w-full items-center gap-4"):
            search = ui.input("Search logins / client / role").classes("flex-1")
            btn_refresh = ui.button("REFRESH").props("outline")

        # ---------- main panels (SIDE BY SIDE, SAME SIZE) ----------
        # IMPORTANT: flex-nowrap keeps side-by-side on wide screens.
        # If screen is too small, it may overflow instead of stacking (as requested).
        with ui.row().classes("w-full gap-6 items-stretch flex-nowrap"):

            # ===== LEFT: LOGINS LIST =====
            with ui.card().classes("gcc-card flex-1 p-5 min-h-[640px]"):
                ui.label("Users / Logins").classes("text-xl font-bold")
                ui.label("Select a login. Right side edits ONLY that login.").classes("gcc-muted text-sm mb-3")

                logins_table = ui.table(
                    columns=[
                        {"name": "login_id", "label": "Login", "field": "login_id", "align": "left",
                         "style": "width: 18%;"},
                        {"name": "belongs_to", "label": "Belongs To (Client)", "field": "belongs_to", "align": "left",
                         "style": "width: 52%; white-space: normal;"},
                        {"name": "role", "label": "Role", "field": "role", "align": "left",
                         "style": "width: 18%;"},
                        {"name": "active", "label": "Active", "field": "active", "align": "center",
                         "style": "width: 12%;"},
                    ],
                    rows=[],
                    row_key="login_db_id",
                    selection="single",
                    pagination={"rowsPerPage": 10, "options": [10, 25, 50]},
                ).classes("w-full gcc-soft-grid")

                logins_table.props("dense bordered separator-cell")

                # ---- left panel buttons (for the LIST) ----
                with ui.row().classes("w-full justify-between items-center mt-4"):
                    with ui.row().classes("gap-3"):
                        btn_add = ui.button("ADD").props("color=positive")
                        btn_delete = ui.button("DELETE").props("color=negative outline")
                        btn_print = ui.button("PRINT").props("outline")

                    # Small note area
                    left_hint = ui.label("").classes("gcc-muted text-sm")

            # ===== RIGHT: NOTEBOOK / EDIT SELECTED LOGIN =====
            with ui.card().classes("gcc-card flex-1 p-5 min-h-[640px]"):
                ui.label("Notebook").classes("text-xl font-bold")
                ui.label("Edit the selected login assignment.").classes("gcc-muted text-sm mb-3")

                selected_title = ui.label("Selected Login: (none)").classes("text-lg font-bold mt-2")
                selected_sub = ui.label("Belongs To: (none)").classes("gcc-muted text-sm mb-4")

                # Form fields
                # We keep "login_id" read-only here to reduce mistakes.
                login_id_readonly = ui.input("Login ID").props("readonly").classes("w-full")

                with ui.row().classes("w-full gap-4 items-end"):
                    # Role select
                    role_sel = ui.select(
                        {k: v for k, v in ROLE_OPTIONS},
                        label="Role"
                    ).classes("flex-1")

                    # Client select (LONG / important)
                    client_sel = ui.select(
                        options=clients_map,
                        label="Belongs To (Client)"
                    ).classes("flex-1")

                with ui.row().classes("w-full gap-4 items-center mt-2"):
                    active_chk = ui.checkbox("Active")
                    ui.space()

                new_pass = ui.input("Reset Password (optional)").props("password").classes("w-full")
                ui.label("Leave empty if you don't want to change password.").classes("gcc-muted text-xs")

                # Right panel actions (for selected login only)
                with ui.row().classes("w-full justify-end gap-3 mt-5"):
                    btn_update = ui.button("UPDATE / SAVE").props("color=primary")
                    btn_clear = ui.button("CLEAR").props("outline")

        # ---------- bottom global bar (Logout/Exit) ----------
        ui.separator().classes("my-4 gcc-sep-strong")

        with ui.row().classes("w-full items-center justify-end gap-3"):
            btn_logout = ui.button("LOGOUT").props("outline")
            btn_exit = ui.button("EXIT").props("color=negative outline")

        # ---------- functions ----------
        def set_buttons_enabled():
            has_sel = bool(state["selected_login_id"])
            btn_delete.enabled = has_sel
            btn_print.enabled = has_sel
            btn_update.enabled = has_sel
            btn_clear.enabled = has_sel
            left_hint.text = "" if has_sel else "Select a login to enable DELETE/PRINT and right-side UPDATE."

        def refresh_clients_select():
            nonlocal clients_map
            clients_map = fetch_clients_map()
            client_sel.options = clients_map
            client_sel.update()

        def refresh_logins():
            rows = list_logins(search.value or "")
            logins_table.rows = rows
            logins_table.update()

            # keep selection if possible
            if state["selected_login_id"]:
                still_exists = any(r["login_db_id"] == state["selected_login_id"] for r in rows)
                if not still_exists:
                    clear_selection()

        def clear_selection():
            state["selected_login_id"] = None
            state["selected_row"] = None

            selected_title.text = "Selected Login: (none)"
            selected_sub.text = "Belongs To: (none)"

            login_id_readonly.value = ""
            role_sel.value = None
            client_sel.value = None
            active_chk.value = False
            new_pass.value = ""

            # Clear table selection visually
            logins_table.selected = []
            logins_table.update()

            set_buttons_enabled()

        def load_selected_into_notebook(row: dict):
            state["selected_login_id"] = int(row["login_db_id"])
            state["selected_row"] = row

            selected_title.text = f"Selected Login: {row.get('login_id')}"
            selected_sub.text = f"Belongs To: {row.get('belongs_to')}"

            login_id_readonly.value = row.get("login_id") or ""
            role_sel.value = row.get("role")
            client_sel.value = row.get("customer_id") if row.get("customer_id") is not None else None
            active_chk.value = bool(int(row.get("active") or 0))
            new_pass.value = ""

            set_buttons_enabled()

        def on_table_select(_):
            if not logins_table.selected:
                clear_selection()
                return
            row = logins_table.selected[0]
            load_selected_into_notebook(row)

        logins_table.on("selection", on_table_select)

        def confirm_delete_login():
            if not state["selected_login_id"]:
                ui.notify("Select a login first", type="warning")
                return

            selected_login = state["selected_row"]["login_id"]

            with ui.dialog() as d:
                with ui.card().classes("gcc-card p-5 w-[520px] max-w-[95vw]"):
                    ui.label("Delete Login?").classes("text-lg font-bold")
                    ui.label(f"This will delete login: {selected_login}")
                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=d.close).props("flat")
                        ui.button(
                            "Delete",
                            on_click=lambda: (delete_login(), d.close()),
                        ).props("color=negative")
            d.open()

        def delete_login():
            login_id = int(state["selected_login_id"])
            with get_conn() as conn:
                conn.execute("DELETE FROM Logins WHERE ID = ?", (login_id,))
                conn.commit()

            ui.notify("Login deleted", type="positive")
            clear_selection()
            refresh_logins()

        def open_add_login_dialog():
            refresh_clients_select()

            # small, readable dialog (not huge)
            with ui.dialog() as d:
                with ui.card().classes("gcc-card p-5 w-[650px] max-w-[95vw]"):
                    ui.label("Add Login").classes("text-lg font-bold mb-2")

                    login_new = ui.input("Login ID (email or username)").classes("w-full")
                    pass_new = ui.input("Password").props("password").classes("w-full")

                    with ui.row().classes("w-full gap-4"):
                        role_new = ui.select({k: v for k, v in ROLE_OPTIONS}, label="Role").classes("flex-1")
                        client_new = ui.select(clients_map, label="Belongs To (Client)").classes("flex-1")

                    active_new = ui.checkbox("Active").classes("mt-2")
                    active_new.value = True

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=d.close).props("flat")
                        ui.button(
                            "Create",
                            on_click=lambda: create_login(login_new.value, pass_new.value, role_new.value, client_new.value, active_new.value, d),
                        ).props("color=positive")

            d.open()

        def create_login(login_id: str, password: str, role: int, customer_id, active: bool, dlg):
            login_id = (login_id or "").strip().lower()
            password = password or ""

            if not login_id or not password or role is None:
                ui.notify("Fill Login ID, Password, and Role", type="negative")
                return

            # customer_id can be None (unassigned) if you want
            is_active = 1 if active else 0
            hierarchy_int = int(role)  # Ensure integer for hierarchy column

            with get_conn() as conn:
                # avoid duplicates
                exists = conn.execute("SELECT ID FROM Logins WHERE login_id = ?", (login_id,)).fetchone()
                if exists:
                    ui.notify("That Login ID already exists", type="warning")
                    return

                conn.execute(
                    """
                    INSERT INTO Logins (login_id, password_hash, password_salt, hierarchy, is_active, customer_id)
                    VALUES (?, ?, '', ?, ?, ?)
                    """,
                    (login_id, hash_password(password), hierarchy_int, is_active, customer_id),
                )
                conn.commit()

            dlg.close()
            ui.notify("Login created", type="positive")
            refresh_logins()

        def update_selected_login():
            if not state["selected_login_id"]:
                ui.notify("Select a login first", type="warning")
                return

            login_db_id = int(state["selected_login_id"])

            role = role_sel.value
            customer_id = client_sel.value
            is_active = 1 if active_chk.value else 0
            new_password = (new_pass.value or "").strip()

            if role is None:
                ui.notify("Role is required", type="negative")
                return

            hierarchy_int = int(role)  # Ensure integer for hierarchy column

            with get_conn() as conn:
                if new_password:
                    conn.execute(
                        """
                        UPDATE Logins
                        SET hierarchy = ?, is_active = ?, customer_id = ?, password_hash = ?
                        WHERE ID = ?
                        """,
                        (hierarchy_int, is_active, customer_id, hash_password(new_password), login_db_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE Logins
                        SET hierarchy = ?, is_active = ?, customer_id = ?
                        WHERE ID = ?
                        """,
                        (hierarchy_int, is_active, customer_id, login_db_id),
                    )
                conn.commit()

            ui.notify("Login updated", type="positive")
            refresh_logins()

        def print_selected():
            if not state["selected_row"]:
                ui.notify("Select a login first", type="warning")
                return
            r = state["selected_row"]
            # simple print for now (later you can do PDF)
            ui.notify(f"PRINT: {r['login_id']} -> {r['belongs_to']} ({r['role']})", type="info")

        def confirm_logout():
            with ui.dialog() as d:
                with ui.card().classes("gcc-card p-5 w-[520px] max-w-[95vw]"):
                    ui.label("Logout?").classes("text-lg font-bold")
                    ui.label("You will return to the login screen.")
                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=d.close).props("flat")
                        ui.button(
                            "Logout",
                            on_click=lambda: (d.close(), logout(), ui.navigate.to("/login")),
                        ).props("color=negative")
            d.open()

        def confirm_exit():
            with ui.dialog() as d:
                with ui.card().classes("gcc-card p-5 w-[520px] max-w-[95vw]"):
                    ui.label("Exit Admin?").classes("text-lg font-bold")
                    ui.label("This will return you to the Dashboard.")
                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=d.close).props("flat")
                        ui.button(
                            "Exit",
                            on_click=lambda: (d.close(), ui.navigate.to("/")),
                        ).props("color=negative")
            d.open()

        # ---------- wire buttons ----------
        btn_refresh.on_click(lambda: (refresh_clients_select(), refresh_logins()))
        search.on("keydown.enter", lambda _: refresh_logins())

        btn_add.on_click(open_add_login_dialog)
        btn_delete.on_click(confirm_delete_login)
        btn_print.on_click(print_selected)

        btn_update.on_click(update_selected_login)
        btn_clear.on_click(clear_selection)

        btn_logout.on_click(confirm_logout)
        btn_exit.on_click(confirm_exit)

        # ---------- initial load ----------
        clear_selection()
        refresh_logins()
