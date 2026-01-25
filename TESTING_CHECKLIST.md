# Testing Checklist: Module-by-Module

Use this checklist to track what functions need tests and prioritize implementation.

---

## 🔴 CRITICAL (Priority 1 - Week 1)

### core/auth.py
- [ ] `login(email, password)` - Success path
- [ ] `login(email, password)` - Invalid password
- [ ] `login(email, password)` - Nonexistent user
- [ ] `login(email, password)` - Inactive user
- [ ] `current_user()` - Returns None when not logged in
- [ ] `current_user()` - Returns user dict when logged in
- [ ] `current_user()` - Invalidates on server restart
- [ ] `is_admin()` - Returns True for hierarchy 1-2
- [ ] `is_admin()` - Returns False for hierarchy 3-5
- [ ] `is_admin()` - Returns False when not logged in
- [ ] `require_login()` - Returns False and navigates to /login when not logged in
- [ ] `require_login()` - Returns True when logged in
- [ ] `logout()` - Clears storage
- [ ] `ensure_admin(email, password)` - Creates admin if not exists
- [ ] `ensure_admin(email, password)` - Skips if already exists
- [ ] `HIERARCHY` dict - All mappings correct

### core/security.py
- [ ] `hash_password(password)` - Creates Argon2 hash
- [ ] `hash_password("")` - Empty password handling
- [ ] `verify_password(password, hash)` - Valid password returns True
- [ ] `verify_password(password, hash)` - Invalid password returns False
- [ ] `verify_password(password, "plaintext")` - Plaintext fallback works
- [ ] Exception handling - Malformed hash doesn't crash

---

## 🟠 HIGH (Priority 2 - Weeks 2-3)

### core/db.py
- [ ] `get_conn()` - Returns sqlite3.Connection
- [ ] `get_conn()` - Sets row_factory to sqlite3.Row
- [ ] `get_conn()` - Enables PRAGMA foreign_keys
- [ ] `get_conn()` - Creates data/ directory if missing
- [ ] `init_db()` - Can be called without errors

### core/customers_repo.py
- [ ] `list_customers()` - Empty search returns all
- [ ] `list_customers(search="test")` - Filters by company
- [ ] `list_customers(search="test")` - Filters by first_name
- [ ] `list_customers(search="test")` - Filters by email
- [ ] `list_customers(search="test")` - Case-insensitive search
- [ ] `get_customer(id)` - Returns customer dict
- [ ] `get_customer(99999)` - Returns None for invalid ID
- [ ] `create_customer(data)` - Inserts new customer
- [ ] `create_customer(data)` - Returns new customer ID
- [ ] `create_customer(missing_fields)` - Handles partial data
- [ ] `update_customer(id, data)` - Updates fields
- [ ] `update_customer(99999, data)` - Handles invalid ID
- [ ] `delete_customer(id)` - Removes customer
- [ ] `delete_customer(id)` - Cascades delete to locations/units

### core/locations_repo.py
- [ ] `list_locations()` - Empty search returns all
- [ ] `list_locations(search="123 Main")` - Filters by address
- [ ] `list_locations(customer_id=1)` - Filters by customer
- [ ] `get_location(id)` - Returns location dict
- [ ] `get_location(99999)` - Returns None
- [ ] `create_location(data)` - Inserts new location
- [ ] `create_location(invalid_customer_id)` - Foreign key violation
- [ ] `update_location(id, data)` - Updates fields
- [ ] `delete_location(id)` - Cascades to units

### core/units_repo.py
- [ ] `list_units()` - Returns all units
- [ ] `list_units(search="UNIT-001")` - Filters by tag
- [ ] `list_units(location_id=1)` - Filters by location
- [ ] `get_unit_by_id(unit_id)` - Returns unit dict
- [ ] `get_unit_by_id(99999)` - Returns None
- [ ] `create_unit(data)` - Inserts new unit
- [ ] `create_unit(invalid_location)` - Foreign key violation
- [ ] `update_unit(unit_id, data)` - Updates fields
- [ ] `delete_unit(unit_id)` - Removes unit

### core/tickets_repo.py
- [ ] `create_service_call(data)` - Inserts ticket
- [ ] `get_service_call(id)` - Returns ticket dict
- [ ] `get_service_call(99999)` - Returns None
- [ ] `list_service_calls()` - Returns all
- [ ] `list_service_calls(customer_id=1)` - Filters by customer
- [ ] `list_service_calls(status="Open")` - Filters by status
- [ ] `list_service_calls(priority="High")` - Filters by priority
- [ ] `update_service_call(id, data)` - Updates fields
- [ ] `close_service_call(id)` - Sets status to closed

### core/issues_repo.py
- [ ] `list_issue_types()` - Returns all types
- [ ] `list_issue_types(enabled_only=True)` - Filters inactive
- [ ] `get_issue_type_by_code(code)` - Returns type dict
- [ ] `get_issue_type_by_code("INVALID")` - Returns None

### core/setpoints_repo.py
- [ ] `get_unit_setpoint(unit_id)` - Returns setpoint dict
- [ ] `create_or_update_setpoint(unit_id, data)` - Inserts or updates
- [ ] [ ] Test all CRUD operations

### core/settings_repo.py
- [ ] `get_setting(key)` - Returns value
- [ ] `set_setting(key, value)` - Stores value
- [ ] `list_settings()` - Returns all settings

---

## 🟡 MEDIUM (Priority 3 - Weeks 3-4)

### core/issue_rules.py
- [ ] `can_create_ticket(issue_id, unit_id, is_admin=False)` - Success
- [ ] `can_create_ticket()` - Detects duplicate open ticket
- [ ] `can_create_ticket()` - Enforces 24h cooldown for clients
- [ ] `can_create_ticket()` - Bypasses cooldown for admin
- [ ] `can_create_ticket()` - Cooldown expiration

### core/alert_system.py
- [ ] `check_temperature_alerts()` - Freezing alert (< 32°F)
- [ ] `check_temperature_alerts()` - High supply temp alert
- [ ] `check_temperature_alerts()` - Low delta T alert
- [ ] `check_temperature_alerts()` - None input handling
- [ ] `check_pressure_alerts()` - Low suction alert
- [ ] `check_pressure_alerts()` - High discharge alert
- [ ] `check_pressure_alerts()` - None input handling
- [ ] `check_electrical_alerts()` - Phase imbalance alert
- [ ] `check_electrical_alerts()` - Overload alert
- [ ] `check_electrical_alerts()` - None input handling
- [ ] `evaluate_all_alerts(reading)` - Combines all alert types
- [ ] `_to_float(value)` - Converts string to float
- [ ] `_to_float("invalid")` - Returns None
- [ ] `_ensure_dict(row)` - Converts Row to dict

### core/equipment_analysis.py
- [ ] `calculate_equipment_health_score(unit_data)` - Valid inputs
- [ ] `calculate_equipment_health_score()` - Edge cases (all None)
- [ ] `calculate_equipment_health_score()` - Weighting algorithm
- [ ] Health score between 0-100

### core/stats.py
- [ ] `get_summary_counts()` - Returns dict with clients/locations/equipment
- [ ] `get_summary_counts()` - Correct counts
- [ ] `_table_exists(conn, table_name)` - True when exists
- [ ] `_table_exists(conn, "nonexistent")` - False when missing
- [ ] `_count(conn, table_name)` - Returns correct count

### core/logger.py
- [ ] `log_info(message, context)` - Creates log entry
- [ ] `log_error(message, context)` - Creates error entry
- [ ] `log_user_action(user_id, action, details)` - Creates action log
- [ ] `with_error_handling(label)` - Wraps function
- [ ] `with_error_handling()` - Catches exceptions

---

## 🟠 MEDIUM-HIGH (Priority 4 - Weeks 4+)

### pages/login.py
- [ ] `page()` - Renders login form
- [ ] Login button click triggers `login(email, password)`
- [ ] Successful login navigates to "/"
- [ ] Failed login shows error message
- [ ] Current user auto-logged out on page access

### pages/dashboard.py
- [ ] `page()` - Requires login
- [ ] Admin sees all equipment
- [ ] Client (hierarchy 4) sees only their equipment
- [ ] Unit stats display correctly
- [ ] Alert indicators show for critical issues
- [ ] "Create ticket" button enabled for open issues
- [ ] Thermostat dialog triggers on button click

### pages/admin.py
- [ ] `page()` - Requires admin access
- [ ] Non-admins redirected
- [ ] List logins displays all users
- [ ] Edit login updates hierarchy/customer
- [ ] Create login inserts new user
- [ ] Delete login removes user
- [ ] Search logins filters results

### pages/clients.py
- [ ] `page()` - Requires login
- [ ] List customers displays all (for admins)
- [ ] Create customer inserts new
- [ ] Edit customer updates
- [ ] Delete customer removes
- [ ] Search filters results

### pages/locations.py
- [ ] `page()` - Requires login
- [ ] List locations for customer
- [ ] Admin sees all locations
- [ ] Create location inserts
- [ ] Edit location updates
- [ ] Delete location removes

### pages/equipment.py
- [ ] `page()` - Requires login
- [ ] List units for location
- [ ] Create unit inserts
- [ ] Edit unit updates
- [ ] Delete unit removes
- [ ] Search filters results

### pages/tickets.py
- [ ] `page()` - Requires login
- [ ] List service calls
- [ ] Create ticket follows business rules
- [ ] Client sees cooldown message
- [ ] Admin bypasses cooldown
- [ ] Update ticket status
- [ ] Close/complete ticket

### pages/thermostat.py
- [ ] `page()` - Requires login
- [ ] Display unit control interface
- [ ] Set temperature submits value
- [ ] Feedback message displays
- [ ] Invalid input rejected

### pages/settings.py
- [ ] `page()` - Requires admin access
- [ ] Update settings stores values
- [ ] Read settings retrieves values
- [ ] Settings persist across sessions

### pages/profile.py
- [ ] `page()` - Requires login
- [ ] Display user info
- [ ] Update profile saves changes
- [ ] Change password validates

---

## 🟡 API/INTEGRATION (Priority 5)

### app.py Endpoints
- [ ] `POST /api/logout-on-close` - Logs out user
- [ ] `POST /api/set-unit` - Validates unit_id parameter
- [ ] `POST /api/set-unit` - Returns unit ID
- [ ] `POST /api/open-thermostat-dialog` - Opens dialog
- [ ] Invalid parameters return error
- [ ] Unauthenticated access blocked

### End-to-End Scenarios
- [ ] User login → view dashboard → create ticket → logout
- [ ] Admin create customer → location → units
- [ ] Client view own equipment → create ticket with cooldown
- [ ] Tech view all equipment → no modification
- [ ] Server restart invalidates session

---

## Progress Tracking

Copy this template to track your progress:

```
Week 1: Auth & Security
[████░░░░░░] 40% - Completed test_auth.py (10/25 assertions)

Week 2: Repositories - Part 1
[░░░░░░░░░░] 0% - Starting test_customers_repo.py

Week 3: Repositories - Part 2 + Business Rules
[░░░░░░░░░░] 0% - Starting test_locations_repo.py

Week 4: Extended Coverage
[░░░░░░░░░░] 0% - Starting test_stats.py

Overall Coverage: X%
Critical Modules: Y%
```

---

## Legend

- 🔴 **CRITICAL** - Security/auth (test first, 0-tolerance for gaps)
- 🟠 **HIGH** - Data integrity/CRUD (frequent use, high impact)
- 🟡 **MEDIUM** - Business logic/UI (important but less critical)
- ⬜ **LOW** - Utility functions (test if time permits)

---

## Tips

1. **Group by module**: Test all functions in one module before moving to next
2. **Build fixtures first**: Invest time in `conftest.py` to reuse across tests
3. **Use parametrization**: Test multiple inputs with `@pytest.mark.parametrize`
4. **Document your tests**: Add docstrings explaining what each test validates
5. **Run tests frequently**: `pytest tests/` after each module completion
6. **Monitor coverage**: `pytest --cov=core` to see which lines untested
7. **Refactor as you go**: Move common test code into fixtures/helpers

