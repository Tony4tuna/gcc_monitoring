from nicegui import app, ui
from .db import get_conn
from .security import verify_password
import time

SESSION_KEY = "user"
SERVER_START_TIME = time.time()  # Track when server started

# hierarchy codes (your rule)
HIERARCHY = {
    1: "GOD",
    2: "administrator",
    3: "tech_gcc",
    4: "client",
    5: "client_mngs",
}

def current_user():
    user = app.storage.user.get(SESSION_KEY)
    if user:
        # Check if session was created before server restart
        session_time = user.get("session_time", 0)
        if session_time < SERVER_START_TIME:
            # Session is from before server restart - invalidate it
            app.storage.user.pop(SESSION_KEY, None)
            return None
    return user

def require_login() -> bool:
    if not current_user():
        ui.navigate.to("/login")
        return False
    return True

def is_admin() -> bool:
    user = current_user()
    if not user:
        return False
    return user.get("hierarchy") in (1, 2)

def login(email: str, password: str) -> bool:
    email = (email or "").strip().lower()
    password = password or ""

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                ID,
                login_id AS email,
                password_hash,
                hierarchy,
                customer_id,
                location_id,
                is_active
            FROM Logins
            WHERE login_id = ? AND is_active = 1
            """,
            (email,),
        ).fetchone()

    if not row:
        return False

    stored = row["password_hash"] or ""

    # accept argon2 hashes (preferred)
    if stored.startswith("$argon2") or stored.startswith("argon2"):
        if not verify_password(password, stored):
            return False
    else:
        # dev fallback: allow plain text match
        if stored != password:
            return False

    # convert hierarchy to int safely
    h = row["hierarchy"]
    try:
        h = int(h)
    except Exception:
        h = 0

    app.storage.user[SESSION_KEY] = {
        "id": row["ID"],
        "email": row["email"],
        "hierarchy": h,
        "role": HIERARCHY.get(h, "unknown"),
        "customer_id": row["customer_id"],
        "location_id": row["location_id"],
        "session_time": time.time(),  # Store when session was created
    }
    return True

def logout() -> None:
    app.storage.user.pop(SESSION_KEY, None)

def ensure_admin(email: str, password: str) -> None:
    """Create an admin login if it doesn't exist (dev helper)."""
    email = (email or "").strip().lower()
    password = password or ""

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT ID FROM Logins WHERE login_id = ?",
            (email,),
        ).fetchone()

        if existing:
            return

        # hierarchy 2 = Administrator
        # store plain text only if you want dev mode;
        # better: store hashed
        conn.execute(
            """
            INSERT INTO Logins (login_id, password_hash, password_salt, hierarchy, is_active)
            VALUES (?, ?, '', ?, 1)
            """,
            (email, password, 2),
        )
        conn.commit()
