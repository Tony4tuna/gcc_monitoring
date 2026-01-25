# GCC Monitoring System: Comprehensive Testing Assessment

**Date**: January 25, 2026  
**Project**: GCC Monitoring (NiceGUI-based HVAC/Equipment Monitoring System)  
**Assessment Scope**: Test coverage gaps, strategy recommendations, and testing priorities

---

## Executive Summary

The GCC Monitoring System currently has **minimal test coverage** with only 2 PDF generation test scripts that are exploratory/manual tests, not proper unit tests. The codebase includes critical business logic across authentication, database access, CRUD operations, and business rules with **zero automated test coverage**. This presents significant risk for:

- **Security regressions** in role-based access control (hierarchy 1-5)
- **Data integrity issues** in database transactions
- **Business rule violations** (e.g., ticket creation cooldowns, duplicate checks)
- **Calculation errors** in alert system and equipment health scoring

---

## 1. Current Test Status

### Existing Test Files

| File | Type | Purpose | Maturity |
|------|------|---------|----------|
| [utility/test_pdf_generation.py](utility/test_pdf_generation.py) | Manual exploration | Query real PDF data from DB | Pre-alpha (no assertions) |
| [utility/test_real_pdf.py](utility/test_real_pdf.py) | Manual exploration | PDF rendering test | Pre-alpha (no assertions) |
| [deployment/utility/test_real_pdf.py](deployment/utility/test_real_pdf.py) | Duplicate | Same as above | Pre-alpha |
| [deployment/utility/test_pdf_generation.py](deployment/utility/test_pdf_generation.py) | Duplicate | Same as above | Pre-alpha |

### Test Framework Status

- **No pytest configuration** (no `pytest.ini`, `pyproject.toml` with test config, or `conftest.py`)
- **No unittest imports** in main codebase
- **No test fixtures or factories** for test data
- **No mocking setup** (no `unittest.mock` or `pytest-mock` usage)
- **No CI/CD integration** for test automation

### Coverage Tools

- **No coverage.py integration** → No coverage reports
- **No coverage thresholds** configured
- **Zero baseline metrics**

---

## 2. Critical Testing Gaps (High-Severity)

### 2.1 Authentication & Security (CRITICAL - 0% coverage)

**Module**: [core/auth.py](core/auth.py)  
**File Size**: 122 lines  
**Criticality**: CRITICAL (controls all access control)

#### Untested Functions:
- `current_user()` - Session validation with server restart detection
- `require_login()` - UI navigation guard (critical for page protection)
- `is_admin()` - Hierarchy-based authorization check
- `login(email, password)` - Authentication with dual hash support (Argon2 + plaintext fallback)
- `logout()` - Session cleanup
- `ensure_admin(email, password)` - Dev bootstrap function
- `HIERARCHY` dict - Role name mapping

#### Risk Examples:
1. **Bug**: Session invalidation on server restart could fail silently
2. **Bug**: Hierarchy 0 or invalid values bypass admin checks
3. **Bug**: Plaintext password fallback could be exploited in production
4. **Security**: No rate limiting on failed login attempts
5. **Security**: Session fixation vulnerability (session_time not validated on every request)

---

### 2.2 Password Security (CRITICAL - 0% coverage)

**Module**: [core/security.py](core/security.py)  
**File Size**: ~15 lines  
**Criticality**: CRITICAL (protects user credentials)

#### Untested Functions:
- `hash_password(password)` - Argon2 hashing
- `verify_password(password, password_hash)` - Hash verification

#### Risk Examples:
1. **Bug**: Exception handling not tested (e.g., malformed hash → `verify_password` crashes)
2. **Security**: Timing attack vulnerability (not constant-time comparison)
3. **Regression**: Passlib context configuration could break on version updates

---

### 2.3 Database Layer (HIGH - 0% coverage)

**Module**: [core/db.py](core/db.py)  
**File Size**: ~30 lines  
**Criticality**: HIGH (all data access goes through this)

#### Untested Functions:
- `get_conn()` - Database connection factory with PRAGMA enforcement
- `init_db()` - (Minimal but should test row factory setup)

#### Risk Examples:
1. **Bug**: Foreign key pragma not enabled → orphaned records possible
2. **Bug**: `sqlite3.Row` row factory not set → dict access fails in repos
3. **Bug**: Connection not closed → connection pool exhaustion
4. **Bug**: Database path initialization fails on permission issues (no error handling)

---

### 2.4 Repository Layer (HIGH - 0% coverage)

**Modules**:
- [core/customers_repo.py](core/customers_repo.py) - 218 lines
- [core/locations_repo.py](core/locations_repo.py) - 158 lines
- [core/units_repo.py](core/units_repo.py) - 171 lines
- [core/tickets_repo.py](core/tickets_repo.py) - 255 lines
- [core/issues_repo.py](core/issues_repo.py) - ~100 lines
- [core/setpoints_repo.py](core/setpoints_repo.py) - (~100 lines, unread)
- [core/settings_repo.py](core/settings_repo.py) - (~100 lines, unread)

**Criticality**: HIGH (core CRUD operations + business logic)

#### Representative Untested Functions (Customers):
- `list_customers(search)` - Search with LIKE across 22 fields
- `get_customer(customer_id)` - Single record fetch
- `create_customer(data)` - INSERT with 23 fields
- `update_customer(customer_id, data)` - UPDATE with validation
- `delete_customer(customer_id)` - DELETE (cascade check)

#### Risk Examples:
1. **Bug**: SQL injection via unsanitized search strings (though parameterized, patterns not tested)
2. **Bug**: Invalid customer_id returns None silently (no validation)
3. **Bug**: create_customer doesn't validate required fields
4. **Bug**: update_customer partial updates could corrupt data
5. **Data integrity**: Foreign key cascades on delete not tested
6. **Bug**: Duplicate email addresses not prevented
7. **Performance**: Search across 22 LIKE clauses not indexed

---

### 2.5 Business Rules Engine (HIGH - 0% coverage)

**Modules**:
- [core/issue_rules.py](core/issue_rules.py) - Ticket creation rules
- [core/alert_system.py](core/alert_system.py) - 304 lines, alert generation

**Criticality**: HIGH (enforces business constraints)

#### [core/issue_rules.py](core/issue_rules.py) Untested:
- `can_create_ticket(issue_id, unit_id, is_admin)` - Returns (bool, reason)
  - Rule 1: No duplicate open ticket
  - Rule 2: 24-hour cooldown for non-admins

#### Risk Examples:
1. **Bug**: `get_open_ticket_for_issue()` not called with correct issue_id → rule bypass
2. **Bug**: UTC datetime comparison could fail in different timezones
3. **Logic error**: Admins bypass cooldown but not tested
4. **Race condition**: Two concurrent requests could both create tickets

#### [core/alert_system.py](core/alert_system.py) Untested:
- `check_temperature_alerts(supply_temp, return_temp, mode)`
- `check_pressure_alerts(discharge, suction, ...)`
- `check_electrical_alerts(a_1, a_2, a_3, ...)`
- Alert threshold configuration (hardcoded in `TEMP_THRESHOLDS`, etc.)

#### Risk Examples:
1. **Logic error**: NaN/None handling (e.g., `supply_temp < 32` when supply_temp is None)
2. **Bug**: Alert thresholds hardcoded with no unit testing
3. **Bug**: `_to_float()` conversion errors not tested
4. **Regression**: Alert message format changes break integrations

---

### 2.6 Statistics & Aggregations (MEDIUM - 0% coverage)

**Module**: [core/stats.py](core/stats.py) - ~50 lines  
**Criticality**: MEDIUM (dashboard metrics)

#### Untested Functions:
- `get_summary_counts()` - Returns {clients, locations, equipment} counts
- `_table_exists(conn, table_name)` - Schema introspection
- `_count(conn, table_name)` - Safe COUNT query

#### Risk Examples:
1. **Bug**: Table name detection fails → wrong counts displayed
2. **Performance**: COUNT on large tables without caching
3. **Bug**: NULL equipment_table returns 0 silently without warning

---

## 3. Medium-Priority Gaps (API Endpoints & Page Handlers)

### 3.1 Page Handlers (MEDIUM - 0% coverage)

**Pages with zero test coverage**:
- [pages/login.py](pages/login.py) - Login form + submission
- [pages/dashboard.py](pages/dashboard.py) - 664 lines, main dashboard (equipment status, alerts, actions)
- [pages/admin.py](pages/admin.py) - 456 lines, user/login management
- [pages/clients.py](pages/clients.py) - Customer CRUD
- [pages/locations.py](pages/locations.py) - Location CRUD
- [pages/equipment.py](pages/equipment.py) - Unit CRUD
- [pages/tickets.py](pages/tickets.py) - Service call management
- [pages/client_home.py](pages/client_home.py) - Non-admin dashboard
- [pages/settings.py](pages/settings.py) - Configuration
- [pages/profile.py](pages/profile.py) - User profile
- [pages/thermostat.py](pages/thermostat.py) - Unit control

#### Risk Examples:
1. **Authorization bypass**: Pages call `require_login()` but no test that non-logged users are blocked
2. **Role-based access**: No tests verify clients only see their data
3. **UI state corruption**: No tests for concurrent access scenarios
4. **NiceGUI integration**: Event handlers (`on_click`, `on_value_changed`) have no isolated tests

---

### 3.2 API Endpoints (MEDIUM - 0% coverage)

**Endpoints in [app.py](app.py)**:
- `POST /api/logout-on-close` - Browser close handler
- `POST /api/set-unit` - Thermostat dialog trigger
- `POST /api/open-thermostat-dialog` - Dialog API

#### Risk Examples:
1. **Bug**: Parameter validation missing (`unit_id` could be non-integer)
2. **Security**: No auth check on `/api/set-unit` endpoint
3. **Exception handling**: Dialog creation failures swallowed silently

---

### 3.3 Equipment Analysis (MEDIUM - 0% coverage)

**Module**: [core/equipment_analysis.py](core/equipment_analysis.py)  
**Criticality**: MEDIUM (health scoring)

#### Likely Untested:
- `calculate_equipment_health_score()` - Composite health metric
- Weighting algorithm for various readings

---

## 4. Testing Strategy Recommendations

### 4.1 Unit vs Integration vs E2E

| Category | Recommendation | Example |
|----------|-----------------|---------|
| **Auth/Security** | **Unit + Integration** | Test login validation (unit), then test with full request flow (integration) |
| **Repositories** | **Unit + Integration** | Test SQL generation (unit), then with real/test DB (integration) |
| **Business Rules** | **Unit** | Test `can_create_ticket()` with mocked repo functions |
| **Alert System** | **Unit** | Test alert logic with various float/None inputs |
| **Page Handlers** | **Integration** | NiceGUI pages need session + UI context; mock NiceGUI client |
| **API Endpoints** | **Integration** | Use FastAPI TestClient |
| **E2E** | **Selective** | Key user journeys: login → create ticket → logout |

### 4.2 Mocking Strategy

#### What to Mock

1. **Database** (for unit tests)
   - Use `unittest.mock.MagicMock` or `pytest-mock`
   - Create `@pytest.fixture(scope="function")` that returns mock connection
   - Mock `get_conn()` globally for unit tests

   Example:
   ```python
   @pytest.fixture
   def mock_db():
       with patch('core.db.get_conn') as mock_get_conn:
           mock_conn = MagicMock()
           mock_get_conn.return_value = mock_conn
           yield mock_conn
   ```

2. **NiceGUI UI** (for page handlers)
   - Mock `ui.navigate.to()` for page redirects
   - Mock `app.storage.user` for session storage
   - Mock `ui.button()`, `ui.input()` for component access

   Example:
   ```python
   @pytest.fixture
   def mock_nicegui():
       with patch('pages.login.ui') as mock_ui:
           yield mock_ui
   ```

3. **External Services** (if present)
   - Email system (core/email_settings.py)
   - File system operations (reports, logs)

#### What NOT to Mock (Integration Tests)

1. **SQLite Database** - Use in-memory or test DB file
2. **Repository Layer** - Test with real SQL queries
3. **Business Rule Logic** - Test with actual data

### 4.3 Test Fixtures & Factories

Create reusable test data:

```python
# tests/fixtures.py
@pytest.fixture
def test_customer():
    """Returns a valid test customer dict"""
    return {
        "company": "Test HVAC Inc",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone1": "555-1234",
        ...
    }

@pytest.fixture
def test_db():
    """In-memory SQLite for integration tests"""
    conn = sqlite3.connect(':memory:')
    # Run schema.sql
    conn.executescript(open('schema/schema.sql').read())
    yield conn
    conn.close()

@pytest.fixture
def test_user_hierarchy_levels():
    """Returns users at each hierarchy level for RBAC testing"""
    return {
        1: {"email": "god@test.com", "hierarchy": 1, ...},
        2: {"email": "admin@test.com", "hierarchy": 2, ...},
        3: {"email": "tech@test.com", "hierarchy": 3, ...},
        4: {"email": "client@test.com", "hierarchy": 4, ...},
        5: {"email": "client_mgr@test.com", "hierarchy": 5, ...},
    }
```

### 4.4 Test Configuration

Create `pytest.ini` and `conftest.py`:

```ini
[pytest]
testpaths = tests/
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=core --cov=pages --cov-report=html --cov-report=term-missing
```

---

## 5. Top 3 Testing Priorities (Impact vs Effort)

### Priority 1: Authentication & Authorization (Week 1)
**Impact**: ⭐⭐⭐⭐⭐ CRITICAL  
**Effort**: ⭐⭐⭐ MEDIUM  
**Time Estimate**: 8-12 hours

**Why first?**
- Highest security risk (all access controlled by auth)
- Relatively small surface area (120 lines in auth.py + security.py)
- Foundation for all other tests (fixtures depend on auth)
- Easy to achieve high coverage (>90%)

**What to test**:
1. Login success/failure scenarios
   - Valid credentials → session created
   - Invalid password → rejection
   - Inactive login → rejection
2. Session validation
   - `current_user()` returns correct hierarchy
   - Server restart invalidates sessions
3. Authorization checks
   - `is_admin()` correctly identifies admins (hierarchy 1-2)
   - Non-admins cannot access admin pages
4. Password hashing
   - `hash_password()` creates Argon2 hash
   - `verify_password()` validates correct password
   - Plaintext fallback still works in dev mode
5. Hierarchy enforcement
   - Client (hierarchy 4) sees only their data
   - Tech (hierarchy 3) has read-only access
   - Admins (hierarchy 1-2) have full access

**Deliverable**: `tests/test_auth.py` (200+ lines, >90% coverage)

---

### Priority 2: Repository Layer - CRUD Operations (Week 2-3)
**Impact**: ⭐⭐⭐⭐ HIGH  
**Effort**: ⭐⭐⭐⭐ HIGH  
**Time Estimate**: 20-30 hours

**Why second?**
- All data persistence depends on these
- Large surface area but repetitive patterns
- Once fixtures in place (Priority 1), faster to implement
- Easy to achieve 80%+ coverage

**What to test** (focus on most critical):

1. **Customers** ([core/customers_repo.py](core/customers_repo.py))
   - `list_customers(search="")` - empty and with filters
   - `get_customer(id)` - valid and invalid ID
   - `create_customer(data)` - valid data, required fields
   - `update_customer(id, data)` - modify fields, invalid ID
   - `delete_customer(id)` - cascade behavior

2. **Locations** ([core/locations_repo.py](core/locations_repo.py))
   - Foreign key enforcement (customer_id must exist)
   - Create with customer_id validation
   - Delete location with units (cascade check)

3. **Units** ([core/units_repo.py](core/units_repo.py))
   - Create unit with required location_id
   - List units with location filter
   - Get single unit by ID

4. **Tickets** ([core/tickets_repo.py](core/tickets_repo.py))
   - Create service call with validation
   - List with filters (status, priority, date)
   - Update status (open → closed)

**Deliverable**: `tests/test_repositories.py` (500+ lines, 80%+ coverage)

---

### Priority 3: Business Rules Engine (Week 3-4)
**Impact**: ⭐⭐⭐⭐ HIGH  
**Effort**: ⭐⭐⭐ MEDIUM  
**Time Estimate**: 12-16 hours

**Why third?**
- Medium-high impact (enforces business constraints)
- Relatively small surface area
- Depends on Priority 2 (repositories)
- Critical for preventing invalid states

**What to test**:

1. **Issue Rules** ([core/issue_rules.py](core/issue_rules.py))
   - `can_create_ticket()` - duplicate check
   - `can_create_ticket()` - cooldown enforcement
   - Admin bypass of cooldown
   - Edge cases (expiring cooldown at boundary)

2. **Alert System** ([core/alert_system.py](core/alert_system.py))
   - Temperature alert thresholds
     - Below freezing → CRITICAL
     - Above max supply → WARNING
     - Poor delta T → WARNING
   - Pressure alerts (discharge/suction)
   - Electrical alerts (imbalance, overload)
   - Null/NaN handling (no crashes)
   - Unit conversion edge cases

3. **Equipment Health** ([core/equipment_analysis.py](core/equipment_analysis.py))
   - Health score calculation with various inputs
   - Weighting algorithm validation

**Deliverable**: `tests/test_business_rules.py` + `tests/test_alerts.py` (300+ lines, 85%+ coverage)

---

## 6. NiceGUI-Specific Testing Challenges

### Challenge 1: Stateful UI Components
**Problem**: NiceGUI components maintain state in closures  
**Example**: 
```python
def page():
    email = ui.input("Email")
    def do_login():
        login(email.value, ...)  # Accesses email.value
```

**Solution**: 
- Mock `ui.input()` to return object with `.value` property
- Use `unittest.mock.PropertyMock` for `.value` accessor
- Extract logic into separate functions testable without UI

### Challenge 2: Session Storage
**Problem**: Authentication stored in `app.storage.user[SESSION_KEY]`  
**Example**: `current_user()` reads from app.storage

**Solution**:
- Mock `app.storage.user` as a dict in fixtures
- Use `@pytest.fixture` to reset storage between tests
- ```python
  @pytest.fixture
  def mock_storage():
      with patch('core.auth.app.storage.user', new_callable=dict) as mock:
          yield mock
  ```

### Challenge 3: Page Navigation
**Problem**: `ui.navigate.to("/path")` triggers navigation  
**Example**: Login redirects to "/" on success

**Solution**:
- Mock `ui.navigate.to()` and assert it was called
- Use `patch('nicegui.ui.navigate.to')`
- Verify navigation happens without actually redirecting

### Challenge 4: FastAPI Integration
**Problem**: API endpoints defined with `@nicegui_app.post()`  
**Example**: `/api/logout-on-close` endpoint

**Solution**:
- Use FastAPI's `TestClient`
- ```python
  from fastapi.testclient import TestClient
  from nicegui import app as nicegui_app
  
  client = TestClient(nicegui_app)
  response = client.post("/api/logout-on-close")
  assert response.status_code == 200
  ```

### Challenge 5: Concurrent Page Access
**Problem**: Multiple users with different roles accessing simultaneously  
**Example**: Client A shouldn't see Client B's data

**Solution**:
- Test with `app.storage.user` mocked per-test
- Simulate different hierarchy levels
- Use parametrized tests for each role level

---

## 7. SQLite-Specific Testing Challenges

### Challenge 1: Foreign Key Enforcement
**Problem**: `PRAGMA foreign_keys = ON` must be set  
**Example**: Deleting customer with locations should cascade or fail

**Solution**:
```python
@pytest.fixture
def test_db():
    conn = sqlite3.connect(':memory:')
    conn.execute("PRAGMA foreign_keys = ON")  # CRITICAL
    # Load schema
    yield conn
```

### Challenge 2: Transaction Isolation
**Problem**: Tests may interfere with each other  
**Example**: Test 1 inserts customer, Test 2 sees it

**Solution**:
- Use `:memory:` database (fresh per test)
- Or wrap each test in `conn.rollback()`
- Use `@pytest.fixture(autouse=True)` for cleanup

### Challenge 3: Row Factory
**Problem**: `conn.row_factory = sqlite3.Row` required for dict-like access  
**Example**: `row["email"]` vs `row[0]`

**Solution**:
```python
@pytest.fixture
def test_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row  # CRITICAL
    yield conn
```

### Challenge 4: DateTime Handling
**Problem**: SQLite `datetime('now')` used in INSERT/UPDATE  
**Example**: `created` timestamp

**Solution**:
- Mock `datetime.now()` for deterministic tests
- Or use actual datetime and assert within tolerance
- Example:
  ```python
  from unittest.mock import patch
  with patch('sqlite3.datetime') as mock_dt:
      mock_dt.now.return_value = '2026-01-25 12:00:00'
      # Test insertion
  ```

---

## 8. Role-Based Authorization Testing Strategy

### Test Matrix: All Hierarchy Levels

Create parameterized tests for each role:

```python
@pytest.mark.parametrize("hierarchy,expected_access", [
    (1, "FULL"),      # GOD - everything
    (2, "FULL"),      # Admin - everything
    (3, "READ_ONLY"), # Tech - view only
    (4, "OWN_DATA"),  # Client - own customer data only
    (5, "OWN_DATA"),  # Client Manager - own customer data only
])
def test_customer_list_access(hierarchy, expected_access):
    """Verify each role sees appropriate data"""
    user = create_test_user(hierarchy=hierarchy)
    # Create multiple customers (user owns one)
    # Test that user sees correct set
```

### Critical Access Control Tests

1. **Customer List Filtering**
   - Admin sees all customers
   - Client (hierarchy 4) sees only their customer
   - Tech cannot filter customers

2. **Location Access**
   - Admin sees all locations
   - Client sees locations for their customer only
   - Tech cannot access locations

3. **Unit Control**
   - Admin can control any unit
   - Tech (hierarchy 3) can view only
   - Client cannot modify units (read-only dashboard)

4. **Ticket Creation**
   - Admin no cooldown
   - Client 24-hour cooldown
   - Tech no tickets

---

## 9. Test File Structure (Recommended)

```
tests/
├── conftest.py                 # Fixtures, mocks (database, auth, nicegui)
├── test_auth.py                # Authentication + session validation
├── test_security.py            # Password hashing
├── test_db.py                  # Database connection + initialization
├── test_customers_repo.py       # Customer CRUD
├── test_locations_repo.py       # Location CRUD
├── test_units_repo.py           # Unit CRUD
├── test_tickets_repo.py         # Ticket/service call CRUD
├── test_issues_repo.py          # Issue type CRUD
├── test_issue_rules.py          # Ticket creation business rules
├── test_alert_system.py         # Alert generation logic
├── test_equipment_analysis.py   # Health scoring
├── test_stats.py                # Aggregation queries
├── test_pages_login.py          # Login page handler
├── test_pages_dashboard.py      # Dashboard page (key user workflow)
├── test_pages_admin.py          # Admin page + authorization
├── test_api_endpoints.py        # /api/* endpoints
├── fixtures/
│   ├── customers.py             # Test customer data
│   ├── locations.py             # Test location data
│   ├── units.py                 # Test unit data
│   └── tickets.py               # Test service call data
└── integration/
    ├── test_user_workflows.py   # End-to-end scenarios
    └── test_rbac_enforcement.py # Multi-role access tests
```

---

## 10. Dependencies to Add

Update `requirements.txt` with testing packages:

```
# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.23.0
pytest-xdist==3.5.0  # Parallel test execution

# Testing utilities
faker==22.0.0  # Generate test data
freezegun==1.5.0  # Mock datetime
responses==0.24.1  # Mock HTTP requests (if needed)

# Code quality (optional but recommended)
black==23.12.0
flake8==6.1.0
mypy==1.7.1
```

---

## 11. Implementation Roadmap

### Week 1: Foundation (Priorities 1)
- [ ] Create `tests/conftest.py` with core fixtures
- [ ] Create `tests/test_auth.py` (200 lines, >90% coverage)
- [ ] Create `pytest.ini` and `.coveragerc`
- [ ] Run first tests: `pytest tests/test_auth.py`
- [ ] Verify coverage: `pytest --cov=core.auth`

**Deliverable**: All auth tests passing, >90% coverage on `core/auth.py`

### Week 2: Repositories (Priority 2 - Part 1)
- [ ] Create `tests/test_customers_repo.py`
- [ ] Create `tests/test_locations_repo.py`
- [ ] Create `tests/test_units_repo.py`
- [ ] Expand fixtures for test data

**Deliverable**: CRUD tests for 3 core repos, 80%+ coverage each

### Week 3: Repositories Continued + Business Rules (Priority 2-3)
- [ ] Create `tests/test_tickets_repo.py`
- [ ] Create `tests/test_issues_repo.py`
- [ ] Create `tests/test_issue_rules.py`
- [ ] Create `tests/test_alert_system.py`

**Deliverable**: 5 repo modules + 2 business rule modules tested, 80%+ coverage

### Week 4: Extend Coverage (Priority 3 + Medium gaps)
- [ ] Create `tests/test_stats.py`
- [ ] Create `tests/test_equipment_analysis.py`
- [ ] Create `tests/test_db.py`
- [ ] Create `tests/test_pages_login.py`

**Deliverable**: 40%+ overall project coverage, critical paths >85%

### Ongoing (After Week 4)
- [ ] Add E2E tests for key user workflows
- [ ] Expand page handler tests (dashboard, admin, clients)
- [ ] Add API endpoint tests
- [ ] Set coverage threshold (e.g., >70% for main code)
- [ ] Integrate into CI/CD pipeline

---

## 12. Quick-Start Test Example

To validate this testing approach, here's a concrete example for `core/auth.py`:

```python
# tests/test_auth.py
import pytest
from unittest.mock import patch, MagicMock
from core.auth import login, logout, current_user, is_admin, HIERARCHY

@pytest.fixture
def mock_storage():
    """Mock NiceGUI storage"""
    with patch('core.auth.app.storage.user', new_callable=dict) as mock:
        yield mock

@pytest.fixture
def mock_db_valid_user():
    """Mock database with valid user"""
    with patch('core.auth.get_conn') as mock_get_conn:
        mock_conn = MagicMock()
        mock_row = {
            'ID': 1,
            'email': 'admin@test.com',
            'password_hash': '$argon2id$v=19$m=65536,t=3,p=4$...',
            'hierarchy': 2,
            'customer_id': None,
            'location_id': None,
            'is_active': 1
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        yield mock_conn

def test_login_success(mock_storage, mock_db_valid_user):
    """Test successful login"""
    with patch('core.security.verify_password', return_value=True):
        result = login('admin@test.com', 'validpass')
        assert result == True
        assert mock_storage['user']['email'] == 'admin@test.com'
        assert mock_storage['user']['hierarchy'] == 2

def test_login_invalid_email(mock_storage, mock_db_valid_user):
    """Test login with non-existent email"""
    mock_db_valid_user.execute.return_value.fetchone.return_value = None
    result = login('nonexistent@test.com', 'anypass')
    assert result == False
    assert 'user' not in mock_storage

def test_current_user_returns_none_when_not_logged_in(mock_storage):
    """Test current_user() with no session"""
    result = current_user()
    assert result is None

def test_is_admin_true_for_hierarchy_1_2(mock_storage):
    """Test is_admin() for GOD and Admin roles"""
    mock_storage['user'] = {'hierarchy': 1}
    assert is_admin() == True
    
    mock_storage['user']['hierarchy'] = 2
    assert is_admin() == True

def test_is_admin_false_for_hierarchy_3_4_5(mock_storage):
    """Test is_admin() for non-admin roles"""
    for hierarchy in [3, 4, 5]:
        mock_storage['user'] = {'hierarchy': hierarchy}
        assert is_admin() == False

@pytest.mark.parametrize("hierarchy,role_name", list(HIERARCHY.items()))
def test_hierarchy_mapping(hierarchy, role_name):
    """Test all hierarchy codes map correctly"""
    assert HIERARCHY[hierarchy] == role_name
```

**Run**: 
```bash
pytest tests/test_auth.py -v --cov=core.auth
```

**Expected Output**:
```
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_invalid_email PASSED
...
====== 8 passed in 0.45s ======
Name                   Stmts   Miss  Cover
core/auth.py              45      4    91%
```

---

## 13. Summary Table: All Modules Ranked by Testing Priority

| Module | Type | Lines | Hierarchy | Current Coverage | Target Coverage | Priority | Est. Hours |
|--------|------|-------|-----------|------------------|-----------------|----------|-----------|
| core/auth.py | Auth | 122 | CRITICAL | 0% | 90%+ | P1 | 4-6 |
| core/security.py | Auth | ~15 | CRITICAL | 0% | 95%+ | P1 | 2 |
| core/db.py | DB | ~30 | HIGH | 0% | 90%+ | P2 | 2-3 |
| core/customers_repo.py | CRUD | 218 | HIGH | 0% | 80%+ | P2 | 6-8 |
| core/locations_repo.py | CRUD | 158 | HIGH | 0% | 80%+ | P2 | 4-5 |
| core/units_repo.py | CRUD | 171 | HIGH | 0% | 80%+ | P2 | 4-5 |
| core/tickets_repo.py | CRUD | 255 | HIGH | 0% | 80%+ | P2 | 6-8 |
| core/issues_repo.py | CRUD | ~100 | HIGH | 0% | 80%+ | P2 | 3-4 |
| core/issue_rules.py | Rules | ~30 | HIGH | 0% | 85%+ | P3 | 3-4 |
| core/alert_system.py | Logic | 304 | MEDIUM | 0% | 85%+ | P3 | 5-8 |
| core/equipment_analysis.py | Logic | ~150 | MEDIUM | 0% | 75%+ | P3 | 4-6 |
| core/stats.py | Agg | ~50 | MEDIUM | 0% | 85%+ | P3 | 2-3 |
| pages/login.py | Handler | ~40 | MEDIUM | 0% | 75%+ | P4 | 3-4 |
| pages/dashboard.py | Handler | 664 | MEDIUM | 0% | 50%+ | P4 | 12-15 |
| pages/admin.py | Handler | 456 | MEDIUM | 0% | 60%+ | P4 | 8-10 |
| **TOTAL** | - | ~2500 | - | **0%** | **75%+** | - | **65-90** |

---

## Conclusion

The GCC Monitoring System is a feature-rich application with zero automated tests, creating significant risk for security regressions, data corruption, and business rule violations. The recommended 3-phase approach focuses on:

1. **Phase 1 (Week 1)**: Secure foundation - Auth & security (P1)
2. **Phase 2 (Weeks 2-3)**: Data integrity - Repository CRUD (P2)
3. **Phase 3 (Weeks 3-4)**: Business logic - Rules & alerts (P3)

By following this roadmap with the provided examples, the project can achieve **75%+ coverage and >85% coverage on critical modules** within 4 weeks, significantly reducing production risks.

