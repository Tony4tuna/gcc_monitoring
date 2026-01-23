# AI Copilot Instructions for GCC Monitoring System

## Project Overview
**GCC Monitoring System** is a NiceGUI-based web application for HVAC/equipment monitoring. It manages customer data, property locations, equipment units, and telemetry readings with role-based access control (admin/client/tech).

### Tech Stack
- **Framework**: NiceGUI 3.5.0 (Python web UI)
- **Database**: SQLite (data/app.db)
- **Auth**: Custom role-based system (hierarchy 1-5: GOD → client)
- **Backend**: FastAPI, Starlette, Uvicorn
- **Environment**: Python venv, dark-mode UI

---

## Architecture & Components

### Directory Structure
```
gcc_monitoring/
├── app.py                 # Entry point; defines routes (/login, /, /clients, /locations, /equipment, /admin)
├── core/                  # Business logic & data access
│   ├── auth.py           # Authentication, session management, role hierarchy
│   ├── db.py             # SQLite connection factory (data/app.db, foreign keys ON)
│   ├── customers_repo.py # Customer CRUD operations
│   ├── locations_repo.py # Property locations CRUD
│   ├── units_repo.py     # Equipment units CRUD
│   ├── stats.py          # Aggregation/statistics queries
│   └── security.py       # Password hashing (Argon2 + fallback plaintext)
├── pages/                # Page handlers (NiceGUI page functions)
│   ├── login.py          # Login form
│   ├── dashboard.py      # Admin dashboard (metrics, units table, alerts)
│   ├── clients.py        # Client management CRUD
│   ├── locations.py      # Location management CRUD
│   ├── equipment.py      # Equipment/units management
│   ├── admin.py          # Admin panel
│   └── client_home.py    # Non-admin user homepage
├── ui/                   # UI components & styling
│   ├── layout.py         # Global layout wrapper, CSS variables, dark theme
│   └── buttons.py        # Shared button components
├── schema/               # Database schema definition
│   └── schema.sql        # Tables: Customers, PropertyLocations, Logins, Units, UnitReadings, etc.
└── utility/              # Setup & migration scripts
```

### Data Flow
1. **Request** → NiceGUI page handler (`pages/*.py`)
2. **Auth Check** → `current_user()`, `require_login()`, role checks
3. **Data Access** → Repository layer (`core/*_repo.py`)
4. **DB Queries** → SQLite via `get_conn()` from `core/db.py`
5. **Render** → NiceGUI UI components with `layout()` wrapper
6. **Session** → Stored in `app.storage.user[SESSION_KEY]`

---

## Critical Workflows

### Running the Application
```bash
# From workspace root
python app.py
# Starts NiceGUI server (usually http://localhost:8000)
# Requires venv activated: venv\Scripts\activate
```

### Key Environment Variables
- `ADMIN_EMAIL` (default: "admin") - initial admin account
- `ADMIN_PASSWORD` (default: "1931") - initial admin password

### Database Initialization
- Schema: `schema/schema.sql`
- Utility scripts in `utility/` handle migrations/imports
- Foreign keys enforced (`PRAGMA foreign_keys = ON`)
- Connection factory: `core/db.py:get_conn()`

---

## Code Patterns & Conventions

### Authentication & Authorization
```python
# Session storage (all pages check this)
from core.auth import current_user, require_login, is_admin

def page():
    if not require_login():
        return  # Redirects to /login if missing
    
    user = current_user()  # Returns dict: {id, email, hierarchy, role, customer_id, location_id}
    if not is_admin():     # hierarchy in (1, 2) = GOD or admin
        ui.navigate.to("/")
```

**Hierarchy Codes** (`core/auth.py:HIERARCHY`):
- 1: GOD (full access)
- 2: Administrator (full access)
- 3: tech_gcc (technician)
- 4: client (customer)
- 5: client_mngs (client manager)

### Data Access Pattern (Repository Layer)
```python
# Example: core/customers_repo.py
from .db import get_conn

def list_customers(search: str = "") -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM Customers WHERE ...", params).fetchall()
        return [dict(r) for r in rows]  # Convert Row objects to dicts
    finally:
        conn.close()  # Always close connection
```

**Pattern**: Get conn → execute query → close in finally block

### Page Structure (NiceGUI)
```python
# pages/example.py
from nicegui import ui
from core.auth import require_login
from ui.layout import layout

def page():
    if not require_login():
        return
    
    with layout("Page Title"):  # Global header + nav
        # UI elements here
        ui.button("Action", on_click=handler).props("color=green-10")
```

**Pattern**: Always wrap content in `layout()` context manager; use `.props()` for Quasar styling

### Styling Convention
- **Dark theme** enforced via `ui/layout.py` CSS variables
- **CSS classes**: `gcc-card` (styled card), `gcc-muted` (dim text), `gcc-soft-grid` (table grid)
- **Quasar props**: `.props("dense flat color=negative")` for buttons
- **Tailwind colors**: Inline classes like `text-green-400`, `text-yellow-400` for alerts

---

## Database Schema Essentials

### Key Tables & Relationships
- **Customers** ← primary entity (company, contact info)
- **PropertyLocations** ← many-to-one to Customers (sites/branches)
- **Units** ← many-to-one to PropertyLocations (equipment at each site)
- **UnitReadings** ← many-to-one to Units (time-series telemetry)
- **Logins** ← separate auth table (1 customer → N logins with different roles)

### Foreign Key Strategy
- `ON DELETE CASCADE` for Units/UnitReadings (cascade deletes with location/unit)
- `ON DELETE SET NULL` for Logins.customer_id (preserve auth records)
- Indexes on join keys: `idx_units_location_id`, `idx_readings_unit_ts`, etc.

---

## Common Tasks

### Adding a New Page
1. Create `pages/new_feature.py` with `def page():`
2. Wrap content in `layout("Title")`
3. Add route in `app.py`: `@ui.page("/new-feature")`
4. Import and register page handler

### Adding a Repository Function
1. Add method to `core/*_repo.py`
2. Use `get_conn()` → execute → close pattern
3. Return `List[Dict[str, Any]]` or single dict
4. Use named parameters (?) for SQL safety

### Updating UI Colors/Theme
- Edit `ui/layout.py` CSS variables (`:root { --bg, --card, --accent }`)
- Changes apply globally via head HTML injection
- Avoid hardcoding colors; use CSS vars or `gcc-*` classes

---

## Important Notes

### Security
- Passwords: Argon2 hashes preferred; plain text fallback in dev only
- Role checks: Always use `is_admin()` or hierarchy values before exposing admin features
- Input: Use parameterized queries (?) to prevent SQL injection

### Performance
- `UnitReadings` table indexed on `(unit_id, ts)` for time-range queries
- Close DB connections promptly (use finally blocks)
- Avoid loading all readings at once; use pagination for large datasets

### Known Quirks
- Storage format: `app.storage.user[SESSION_KEY]` (per-browser session)
- NiceGUI JavaScript integration via `.props()` and `.add_slot()` for Quasar templates
- Windows path handling: Use `Path()` from pathlib for cross-platform DB paths

---

## AI Agent Guidelines

**When adding features:**
- Always call `require_login()` and check roles before exposing data
- Use existing repository functions; create new ones for reusable queries
- Follow the layout wrapper + page function pattern
- Test with at least two roles (admin and client)
- Update `.props()` styling to match dark theme conventions

**When debugging:**
- Check `app.storage.user` for session state
- Verify foreign key constraints in schema
- Use `conn.row_factory = sqlite3.Row` for dict-like access
- Confirm `.close()` is called in all finally blocks
