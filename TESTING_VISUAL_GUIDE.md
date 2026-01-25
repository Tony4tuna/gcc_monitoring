# Testing Architecture & Visual Guide

## Testing Pyramid for GCC Monitoring

```
                          /\
                         /  \
                        /  E2E \          End-to-End Tests
                       /   (<5%)  \       - Full user workflows
                      /__________\       - UI + DB + Auth
                      /          \
                     /   Pages &  \      Integration Tests
                    /   Handlers   \     - Page + API tests
                   /      (15%)     \    - Mock external deps
                  /________________\
                  /                 \
                 /    Business Logic  \  Unit Tests (most coverage)
                /       (30%)          \ - Auth/security
               /____________________\   - Repositories
               /                     \  - Business rules
              /    Repositories &    \  - Aggregations
             /      Database          \
            /         (40%)            \
           /___________________________\

Coverage Target:
├── CRITICAL modules (auth):  >90%
├── HIGH modules (repos):     >80%
├── MEDIUM modules (logic):   >85%
└── Overall:                  >75%
```

---

## Test Isolation & Layering

```
┌─────────────────────────────────────────────────────────────┐
│                      E2E Tests                               │
│         (Real browser + real database simulation)            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Integration Tests                             │ │
│  │  (Real DB | In-memory DB + Mocked UI)                  │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │      Unit Tests                                  │ │ │
│  │  │  (Mocked DB | Mocked UI | Mocked External)      │ │ │
│  │  │                                                  │ │ │
│  │  │  Auth | Security | Business Rules | Aggregations │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Dependency & Testing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User (NiceGUI Pages)                     │
│           (TESTED: 50% - Integration/E2E)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┬─────────────────────────────────┐  │
│  │                    │                                 │  │
│  ▼                    ▼                                 ▼  │
│┌──────────────┐ ┌──────────────┐            ┌───────────┐ │
││ Auth Layer   │ │ Dashboard    │  Requires  │  NiceGUI  │ │
││ (CRITICAL)   │ │ Handlers     │  -------► │   Client  │ │
││              │ │ (MEDIUM)     │            │ (Mocked)  │ │
│└──────────────┘ └──────────────┘            └───────────┘ │
│  │                                                          │
│  │   verify_login()                                         │
│  │   current_user()                                         │
│  │   is_admin()                                             │
│  │                                                          │
│  ▼                                                          │
│┌──────────────┐        ┌──────────────────────────────┐   │
││ Business     │────►   │  Repository Layer            │   │
││ Rules Layer  │        │  (HIGH - CRUD + Queries)     │   │
││ (MEDIUM)     │        │                              │   │
│└──────────────┘        │  • Customers                 │   │
│                        │  • Locations                 │   │
│  • Ticket Rules        │  • Units                     │   │
│  • Alert System        │  • Tickets                   │   │
│  • Health Scoring      │  • Issues                    │   │
│                        │  • Settings                  │   │
│                        └──────────────────────────────┘   │
│                                 │                          │
│                                 ▼                          │
│                        ┌──────────────────┐               │
│                        │  Database Layer  │               │
│                        │  (HIGH - SQLite) │               │
│                        │                  │               │
│                        │ • get_conn()     │               │
│                        │ • Row factory    │               │
│                        │ • Foreign keys   │               │
│                        └──────────────────┘               │
│                                 │                          │
│                                 ▼                          │
│                        ┌──────────────────┐               │
│                        │  SQLite DB       │               │
│                        │  /data/app.db    │               │
│                        └──────────────────┘               │
│                                                            │
└────────────────────────────────────────────────────────────┘

Testing Strategy:
✓ Database: Mock for unit tests | Real (:memory:) for integration
✓ Auth: Mock storage | Test login validation
✓ Repos: Mock DB or real | Test SQL + logic
✓ Business Rules: Mock repos | Test constraints
✓ Pages: Mock UI + storage | Test handlers + redirects
```

---

## Test File Organization

```
gcc_monitoring/
│
├── tests/                           # All tests (NEW)
│   │
│   ├── conftest.py                  # Fixtures (database, mocks, auth)
│   │
│   ├── test_auth.py                 # Auth tests (PRIORITY 1)
│   ├── test_security.py             # Password hashing tests
│   ├── test_db.py                   # Database connection tests
│   │
│   ├── test_customers_repo.py       # CRUD tests (PRIORITY 2)
│   ├── test_locations_repo.py       # Location CRUD
│   ├── test_units_repo.py           # Unit CRUD
│   ├── test_tickets_repo.py         # Ticket CRUD
│   ├── test_issues_repo.py          # Issue type CRUD
│   │
│   ├── test_issue_rules.py          # Business rules (PRIORITY 3)
│   ├── test_alert_system.py         # Alert logic
│   ├── test_equipment_analysis.py   # Health scoring
│   ├── test_stats.py                # Aggregations
│   │
│   ├── test_pages_login.py          # Page handlers (PRIORITY 4)
│   ├── test_pages_dashboard.py      # Dashboard logic
│   ├── test_pages_admin.py          # Admin page
│   │
│   ├── test_api_endpoints.py        # FastAPI endpoints
│   │
│   ├── fixtures/                    # Test data factories
│   │   ├── customers.py             # Customer fixtures
│   │   ├── locations.py             # Location fixtures
│   │   ├── units.py                 # Unit fixtures
│   │   └── tickets.py               # Ticket fixtures
│   │
│   └── integration/                 # E2E and multi-component tests
│       ├── test_user_workflows.py   # Full user journeys
│       └── test_rbac_enforcement.py # Role-based access control
│
├── pytest.ini                        # Pytest config (NEW)
├── .coveragerc                       # Coverage config (optional)
│
├── core/                            # Business logic (existing)
├── pages/                           # Page handlers (existing)
├── ui/                              # UI components (existing)
├── schema/                          # Database schema (existing)
└── ...
```

---

## Test Execution & CI/CD Flow

```
Developer commits code
        │
        ▼
┌──────────────────────────────┐
│  Pre-commit Hook (local)     │
│  • Run pytest tests/test_*   │
│  • Check coverage >75%       │
│  • Run linting (optional)    │
└──────────────────────────────┘
        │
        ├─ PASS ──► Can commit
        │
        └─ FAIL ──► Block commit, fix code
        
        ▼
┌──────────────────────────────┐
│  CI/CD Pipeline (GitHub)     │ (future)
│  • Checkout code             │
│  • Install deps              │
│  • pytest tests/ --cov       │
│  • Upload coverage report    │
│  • Block PR if coverage <X%  │
└──────────────────────────────┘
        │
        ├─ PASS ──► Can merge to main
        │
        └─ FAIL ──► PR blocked, review needed
```

---

## Mocking Strategy by Layer

```
┌──────────────────────────────────────────────────────────────┐
│                     Unit Test Mocks                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ core.db.get_conn()                                  │    │
│  │ ├─ Real: Test DB (:memory: SQLite)                 │    │
│  │ ├─ Mock: MagicMock() with .execute()               │    │
│  │ └─ Usage: from unittest.mock import patch          │    │
│  │          with patch('core.db.get_conn') as mock    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ core.auth.app.storage.user (Session)               │    │
│  │ ├─ Real: Fresh dict per test                        │    │
│  │ ├─ Mock: @pytest.fixture with new_callable=dict    │    │
│  │ └─ Usage: mock_storage['user'] = {id, email, ...}  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ nicegui.ui (NiceGUI Components)                     │    │
│  │ ├─ Real: Full NiceGUI server (slow, integration)    │    │
│  │ ├─ Mock: MagicMock() for input/button/navigate      │    │
│  │ └─ Usage: with patch('pages.login.ui') as mock_ui  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ External Services                                   │    │
│  │ ├─ Email: Mock email_settings.send_email()          │    │
│  │ ├─ File System: Mock pathlib/os operations          │    │
│  │ └─ Usage: with patch('core.email_settings.send')    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              Integration Test Approach                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ✓ Real Database: :memory: SQLite with full schema           │
│  ✓ Real Auth: login() with actual password verification      │
│  ✓ Real Repos: SQL queries execute against test DB          │
│  ✗ Mocked UI: Still mock NiceGUI components                 │
│  ✗ Mocked HTTP: Mock FastAPI TestClient calls               │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                 E2E Test Approach                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ✓ Real Database: Live test database or staging DB           │
│  ✓ Real Auth: Full login/logout flow                        │
│  ✓ Real UI: NiceGUI pages rendered in browser               │
│  ✓ Real HTTP: Actual API calls                              │
│  ✗ Minimal Mocking: Only external services (email, etc.)    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Role-Based Access Control (RBAC) Testing Matrix

```
                  Admin    Tech     Client   Viewer   Manager
                  (H=2)    (H=3)    (H=4)    (H=5)    (H=1)
────────────────────────────────────────────────────────────────
View own data      ✓        ✓        ✓        ✓        ✓
View other cust    ✓        ✗        ✗        ✗        ✗
Create customer    ✓        ✗        ✗        ✗        ✓
Edit customer      ✓        ✗        ✗        ✗        ✓
Delete customer    ✓        ✗        ✗        ✗        ✓
────────────────────────────────────────────────────────────────
View location      ✓        ✓        C*       C*       ✓
Create location    ✓        ✗        ✗        ✗        ✓
Edit location      ✓        ✗        ✗        ✗        ✓
Delete location    ✓        ✗        ✗        ✗        ✓
────────────────────────────────────────────────────────────────
View unit          ✓        ✓        C*       C*       ✓
Create unit        ✓        ✗        ✗        ✗        ✓
Edit unit          ✓        ✗        ✗        ✗        ✓
Delete unit        ✓        ✗        ✗        ✗        ✓
Control unit       ✓        ✗        ✗        ✗        ✓
────────────────────────────────────────────────────────────────
Create ticket      ✓        ✓        C**      ✗        ✓
View ticket        ✓        ✓        C*       ✓        ✓
Close ticket       ✓        ✓        ✗        ✗        ✓
────────────────────────────────────────────────────────────────
Manage logins      ✓        ✗        ✗        ✗        ✓
Change hierarchy   ✓        ✗        ✗        ✗        ✓
────────────────────────────────────────────────────────────────

Legend:
✓ = Full access
✗ = No access  
C* = Customer data only
C** = Customer data + 24h cooldown

Test approach:
@pytest.mark.parametrize("hierarchy,action,expected", [
    (1, "view_all_customers", True),  # Admin
    (4, "view_all_customers", False), # Client
    (4, "view_own_customer", True),   # Client sees own
])
```

---

## Coverage Report Timeline

```
Week 1 (Auth Priority)
│
├─ Monday:  Setup pytest, conftest.py
├─ Tuesday: test_auth.py, test_security.py
├─ Wed-Fri: Expand fixtures, get to 90% auth coverage
│
└─ Coverage: 0% → 15% (mostly auth.py + security.py)

            ▓░░░░░░░░░░░░░░░░░░ 15%

────────────────────────────────────────

Week 2-3 (Repositories Priority)
│
├─ Mon-Tue: test_customers_repo.py
├─ Wed:     test_locations_repo.py
├─ Thu:     test_units_repo.py + test_tickets_repo.py
├─ Fri:     test_issues_repo.py
│
└─ Coverage: 15% → 50% (repos + auth)

            ▓▓▓▓▓▓▓▓░░░░░░░░░░░░ 50%

────────────────────────────────────────

Week 3-4 (Business Logic Priority)
│
├─ Mon:     test_issue_rules.py
├─ Tue-Wed: test_alert_system.py
├─ Thu:     test_equipment_analysis.py
├─ Fri:     test_stats.py
│
└─ Coverage: 50% → 75% (logic + previous)

            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░ 75%

────────────────────────────────────────

Week 4+ (Pages & Integration)
│
├─ Ongoing: test_pages_*.py + integration tests
├─ Goal:    Maintain >75% overall, >50% on pages
│
└─ Coverage: 75% → 85%+ (goal)

            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░ 85%
```

---

## How to Read Coverage Reports

```
Terminal Output:
────────────────────────────────────────
Name                   Stmts   Miss  Cover   Missing
────────────────────────────────────────
core/auth.py              45      4    91%    98-100
core/security.py          15      1    93%    42
core/customers_repo.py   218     44    80%    15,17,25-30,45
...
────────────────────────────────────────
TOTAL                   2500    500    80%
────────────────────────────────────────

Translation:
• "Stmts" = Total lines of executable code
• "Miss" = Lines not executed by tests
• "Cover" = Percentage covered (Stmts - Miss) / Stmts
• "Missing" = Line numbers NOT covered

Action Items:
├─ 91% coverage (4 missing lines): Good! Minor edge cases
├─ 80% coverage (44 missing lines): Acceptable, improve later
└─ <50% coverage: URGENT - add tests

HTML Report (htmlcov/index.html):
├─ Red lines: Not executed
├─ Yellow lines: Executed but branch not taken
├─ Green lines: Fully tested
└─ Click module name to drill down

Example:
  33  def login(email, password):       ← Line number
     search = email.lower()             ← Green (tested)
     if not password:                   ← Yellow (tested true, not false)
         return False                   ← Red (not tested)
```

---

## Command Reference

```bash
# Run all tests
pytest tests/

# Run specific file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestLogin::test_login_success

# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run with coverage
pytest tests/ --cov=core --cov=pages

# Generate HTML coverage report
pytest tests/ --cov=core --cov-report=html
start htmlcov/index.html

# Coverage report with missing lines
pytest tests/ --cov=core --cov-report=term-missing

# Run tests matching pattern
pytest tests/ -k "auth"  # Runs test_auth.py + others with "auth" in name

# Run in parallel (requires pytest-xdist)
pytest tests/ -n auto

# Generate test results XML (for CI/CD)
pytest tests/ --junit-xml=test-results.xml

# Show slowest tests
pytest tests/ --durations=10
```

---

**Visual Guide Created**: January 25, 2026  
**For**: GCC Monitoring Testing Initiative
