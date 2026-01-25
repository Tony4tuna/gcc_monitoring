# Quick Start: Setting Up Tests for GCC Monitoring

This is the **hands-on implementation guide** to accompany [TESTING_ASSESSMENT.md](TESTING_ASSESSMENT.md).

---

## Step 1: Install Testing Dependencies

```bash
cd c:\Users\Public\GCC_Monitoring\gcc_monitoring

# Activate venv
.venv\Scripts\activate

# Install testing packages
pip install pytest==7.4.3 pytest-cov==4.1.0 pytest-mock==3.12.0 faker==22.0.0 freezegun==1.5.0

# Verify installation
pytest --version
```

---

## Step 2: Create Test Directory Structure

```bash
# From workspace root
mkdir tests
mkdir tests\fixtures
mkdir tests\integration
```

---

## Step 3: Create `pytest.ini`

```ini
[pytest]
testpaths = tests/
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=core
    --cov=pages
    --cov-report=html
    --cov-report=term-missing
    -v

# Allow async tests
asyncio_mode = auto
```

**Location**: `c:\Users\Public\GCC_Monitoring\gcc_monitoring\pytest.ini`

---

## Step 4: Create Core Fixtures (`tests/conftest.py`)

```python
# tests/conftest.py
import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from pathlib import Path

# =====================================================
# DATABASE FIXTURES
# =====================================================

@pytest.fixture
def test_db():
    """In-memory SQLite database with schema loaded"""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Load schema
    schema_path = Path(__file__).parent.parent / "schema" / "schema.sql"
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    
    yield conn
    conn.close()

@pytest.fixture
def mock_db_connection(test_db):
    """Mock get_conn() to return test database"""
    with patch('core.db.get_conn') as mock_get_conn:
        mock_get_conn.return_value = test_db
        yield mock_get_conn

# =====================================================
# AUTH & SESSION FIXTURES
# =====================================================

@pytest.fixture
def mock_storage():
    """Mock app.storage.user for session tests"""
    with patch('core.auth.app.storage.user', new_callable=dict) as mock:
        yield mock

@pytest.fixture
def mock_nicegui():
    """Mock NiceGUI ui module"""
    with patch('pages.login.ui') as mock_ui:
        # Setup common mocks
        mock_ui.navigate.to = MagicMock()
        mock_ui.input = MagicMock(return_value=MagicMock(value=''))
        mock_ui.button = MagicMock()
        mock_ui.label = MagicMock()
        yield mock_ui

# =====================================================
# TEST DATA FIXTURES
# =====================================================

@pytest.fixture
def test_customer_data():
    """Valid customer data for INSERT tests"""
    return {
        "company": "Test HVAC Solutions",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@hvac.test",
        "phone1": "555-123-4567",
        "phone2": "555-987-6543",
        "mobile": "555-111-2222",
        "address1": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip": "62701",
    }

@pytest.fixture
def test_location_data(test_db, test_customer_data):
    """Valid location data with customer created first"""
    # Insert customer
    cur = test_db.execute(
        """INSERT INTO Customers 
        (company, first_name, last_name, email, phone1, address1, city, state, zip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (test_customer_data["company"], test_customer_data["first_name"],
         test_customer_data["last_name"], test_customer_data["email"],
         test_customer_data["phone1"], test_customer_data["address1"],
         test_customer_data["city"], test_customer_data["state"],
         test_customer_data["zip"])
    )
    test_db.commit()
    customer_id = cur.lastrowid
    
    return {
        "customer_id": customer_id,
        "custid": str(customer_id),
        "address1": "456 Oak Ave",
        "city": "Springfield",
        "state": "IL",
        "zip": "62702",
        "contact": "Facility Manager",
        "job_phone": "555-222-3333",
    }

@pytest.fixture
def test_unit_data(test_db, test_location_data):
    """Valid unit data with location created first"""
    # Location already exists from fixture
    return {
        "location_id": test_location_data["customer_id"],
        "unit_tag": "UNIT-001",
        "equipment_type": "AC",
        "make": "Lennox",
        "model": "XC21",
        "serial": "ABC123456",
    }

@pytest.fixture
def test_user_hierarchy_levels(test_db):
    """Test users at each hierarchy level"""
    # Create logins for each role
    roles = {
        1: ("god@test.com", "godpass", 1),
        2: ("admin@test.com", "adminpass", 2),
        3: ("tech@test.com", "techpass", 3),
        4: ("client@test.com", "clientpass", 4),
        5: ("mgr@test.com", "mgrpass", 5),
    }
    
    created = {}
    for hierarchy, (email, pwd, h) in roles.items():
        cur = test_db.execute(
            """INSERT INTO Logins 
            (login_id, password_hash, password_salt, hierarchy, is_active)
            VALUES (?, ?, ?, ?, 1)""",
            (email, pwd, "", h)
        )
        test_db.commit()
        created[hierarchy] = {
            "id": cur.lastrowid,
            "email": email,
            "password": pwd,
            "hierarchy": hierarchy,
        }
    
    return created

# =====================================================
# CONTEXTUAL FIXTURES (combine multiple)
# =====================================================

@pytest.fixture
def auth_context(test_db, mock_storage):
    """Setup for auth tests: real DB + mocked storage"""
    with patch('core.auth.get_conn') as mock_get_conn:
        mock_get_conn.return_value = test_db
        yield {
            "db": test_db,
            "storage": mock_storage,
            "get_conn": mock_get_conn,
        }

@pytest.fixture
def repository_context(test_db, mock_db_connection):
    """Setup for repository tests: mocked get_conn returning test DB"""
    yield {
        "db": test_db,
        "mock_get_conn": mock_db_connection,
    }
```

---

## Step 5: Create First Test File (`tests/test_auth.py`)

```python
# tests/test_auth.py
import pytest
from unittest.mock import patch, MagicMock
from core.auth import login, logout, current_user, is_admin, HIERARCHY

class TestLogin:
    """Test authentication"""
    
    def test_login_success_with_valid_credentials(self, test_db, mock_storage):
        """User successfully logs in with valid email and password"""
        with patch('core.auth.get_conn') as mock_get_conn:
            mock_get_conn.return_value = test_db
            with patch('core.security.verify_password', return_value=True):
                # Setup test user
                test_db.execute(
                    """INSERT INTO Logins 
                    (login_id, password_hash, password_salt, hierarchy, is_active)
                    VALUES (?, ?, ?, ?, 1)""",
                    ("test@example.com", "$argon2...", "", 2)  # Admin
                )
                test_db.commit()
                
                # Attempt login
                result = login("test@example.com", "correctpass")
                
                assert result == True
                assert mock_storage.get("user") is not None
                assert mock_storage["user"]["email"] == "test@example.com"
                assert mock_storage["user"]["hierarchy"] == 2

    def test_login_fails_with_invalid_password(self, test_db, mock_storage):
        """User cannot log in with wrong password"""
        with patch('core.auth.get_conn') as mock_get_conn:
            mock_get_conn.return_value = test_db
            with patch('core.security.verify_password', return_value=False):
                test_db.execute(
                    """INSERT INTO Logins 
                    (login_id, password_hash, password_salt, hierarchy, is_active)
                    VALUES (?, ?, ?, ?, 1)""",
                    ("test@example.com", "$argon2...", "", 2)
                )
                test_db.commit()
                
                result = login("test@example.com", "wrongpass")
                
                assert result == False
                assert "user" not in mock_storage

    def test_login_fails_with_nonexistent_email(self, test_db, mock_storage):
        """User cannot log in with email not in database"""
        with patch('core.auth.get_conn') as mock_get_conn:
            mock_get_conn.return_value = test_db
            
            result = login("nonexistent@example.com", "anypass")
            
            assert result == False
            assert "user" not in mock_storage

    def test_login_fails_when_user_inactive(self, test_db, mock_storage):
        """Inactive user cannot log in"""
        with patch('core.auth.get_conn') as mock_get_conn:
            mock_get_conn.return_value = test_db
            test_db.execute(
                """INSERT INTO Logins 
                (login_id, password_hash, password_salt, hierarchy, is_active)
                VALUES (?, ?, ?, ?, 0)""",  # is_active = 0
                ("inactive@example.com", "$argon2...", "", 2)
            )
            test_db.commit()
            
            result = login("inactive@example.com", "anypass")
            
            assert result == False

class TestCurrentUser:
    """Test session state functions"""
    
    def test_current_user_returns_none_when_not_logged_in(self, mock_storage):
        """No user in storage = None"""
        result = current_user()
        assert result is None

    def test_current_user_returns_user_dict_when_logged_in(self, mock_storage):
        """Logged in user returns session dict"""
        mock_storage["user"] = {
            "id": 1,
            "email": "admin@test.com",
            "hierarchy": 2,
        }
        
        result = current_user()
        
        assert result is not None
        assert result["email"] == "admin@test.com"
        assert result["hierarchy"] == 2

class TestIsAdmin:
    """Test admin authorization"""
    
    @pytest.mark.parametrize("hierarchy", [1, 2])
    def test_is_admin_true_for_god_and_admin(self, mock_storage, hierarchy):
        """Hierarchy 1 and 2 are admins"""
        mock_storage["user"] = {"hierarchy": hierarchy}
        
        assert is_admin() == True

    @pytest.mark.parametrize("hierarchy", [3, 4, 5])
    def test_is_admin_false_for_non_admins(self, mock_storage, hierarchy):
        """Hierarchy 3, 4, 5 are not admins"""
        mock_storage["user"] = {"hierarchy": hierarchy}
        
        assert is_admin() == False

    def test_is_admin_returns_false_when_not_logged_in(self, mock_storage):
        """No user = not admin"""
        assert is_admin() == False

class TestLogout:
    """Test session cleanup"""
    
    def test_logout_clears_storage(self, mock_storage):
        """Logout removes user from storage"""
        mock_storage["user"] = {"id": 1, "email": "test@test.com"}
        
        logout()
        
        assert "user" not in mock_storage

class TestHierarchy:
    """Test role mappings"""
    
    def test_all_hierarchies_mapped(self):
        """All hierarchy codes have role names"""
        assert len(HIERARCHY) == 5
        assert HIERARCHY[1] == "GOD"
        assert HIERARCHY[2] == "administrator"
        assert HIERARCHY[3] == "tech_gcc"
        assert HIERARCHY[4] == "client"
        assert HIERARCHY[5] == "client_mngs"
```

---

## Step 6: Run Your First Tests

```bash
# Activate venv
.venv\Scripts\activate

# Run all auth tests
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/test_auth.py --cov=core.auth --cov-report=term-missing

# Run with specific test
pytest tests/test_auth.py::TestLogin::test_login_success_with_valid_credentials -v
```

**Expected Output**:
```
tests/test_auth.py::TestLogin::test_login_success_with_valid_credentials PASSED
tests/test_auth.py::TestLogin::test_login_fails_with_invalid_password PASSED
...
====== 8 passed in 0.23s ======

Name             Stmts   Miss  Cover   Missing
core/auth.py        45      4    91%   98-100
```

---

## Step 7: Add Repository Tests

Create `tests/test_customers_repo.py`:

```python
# tests/test_customers_repo.py
import pytest
from core.customers_repo import (
    list_customers, get_customer, create_customer, update_customer, delete_customer
)

class TestListCustomers:
    """Test customer list retrieval"""
    
    def test_list_customers_empty_database(self, test_db, mock_db_connection):
        """Empty DB returns empty list"""
        result = list_customers()
        assert result == []

    def test_list_customers_returns_all_customers(self, test_db, mock_db_connection, test_customer_data):
        """List returns all created customers"""
        test_db.execute(
            """INSERT INTO Customers 
            (company, first_name, last_name, email)
            VALUES (?, ?, ?, ?)""",
            (test_customer_data["company"], test_customer_data["first_name"],
             test_customer_data["last_name"], test_customer_data["email"])
        )
        test_db.commit()
        
        result = list_customers()
        
        assert len(result) == 1
        assert result[0]["company"] == "Test HVAC Solutions"

    def test_list_customers_filters_by_search(self, test_db, mock_db_connection, test_customer_data):
        """Search term filters results"""
        test_db.execute(
            """INSERT INTO Customers 
            (company, first_name, last_name, email)
            VALUES (?, ?, ?, ?)""",
            ("Test HVAC", "John", "Smith", "john@test.com")
        )
        test_db.execute(
            """INSERT INTO Customers 
            (company, first_name, last_name, email)
            VALUES (?, ?, ?, ?)""",
            ("Other Co", "Jane", "Doe", "jane@test.com")
        )
        test_db.commit()
        
        result = list_customers(search="Test")
        
        assert len(result) == 1
        assert result[0]["company"] == "Test HVAC"

class TestGetCustomer:
    """Test single customer retrieval"""
    
    def test_get_customer_returns_valid_record(self, test_db, mock_db_connection, test_customer_data):
        """Get returns matching customer"""
        cur = test_db.execute(
            """INSERT INTO Customers 
            (company, first_name, last_name, email)
            VALUES (?, ?, ?, ?)""",
            (test_customer_data["company"], test_customer_data["first_name"],
             test_customer_data["last_name"], test_customer_data["email"])
        )
        test_db.commit()
        customer_id = cur.lastrowid
        
        result = get_customer(customer_id)
        
        assert result is not None
        assert result["company"] == "Test HVAC Solutions"

    def test_get_customer_returns_none_for_invalid_id(self, test_db, mock_db_connection):
        """Get returns None for missing ID"""
        result = get_customer(99999)
        assert result is None

class TestCreateCustomer:
    """Test customer creation"""
    
    def test_create_customer_success(self, test_db, mock_db_connection, test_customer_data):
        """New customer inserted successfully"""
        customer_id = create_customer(test_customer_data)
        
        assert customer_id > 0
        
        # Verify it was inserted
        row = test_db.execute("SELECT * FROM Customers WHERE ID = ?", (customer_id,)).fetchone()
        assert row is not None
        assert row["company"] == "Test HVAC Solutions"
```

---

## Step 8: Generate Coverage Report

```bash
pytest tests/ --cov=core --cov=pages --cov-report=html

# Opens in browser: htmlcov/index.html
start htmlcov/index.html
```

---

## Step 9: Continuous Testing (Optional)

For development: auto-run tests on file changes

```bash
pip install pytest-watch

ptw tests/
```

---

## Tips for Success

1. **Start small**: Get `test_auth.py` passing before expanding
2. **Use fixtures**: All tests should use the `test_db` fixture (isolation)
3. **Mock external dependencies**: Mock `get_conn()`, `app.storage.user`, etc.
4. **Test the happy path first**: Then error cases
5. **Aim for assertion clarity**:
   ```python
   # GOOD
   assert result == True
   assert len(result) == 3
   
   # AVOID
   assert result  # Ambiguous
   ```

6. **Use parametrize for multiple scenarios**:
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, "GOD"),
       (2, "administrator"),
       (3, "tech_gcc"),
   ])
   def test_hierarchy(input, expected):
       assert HIERARCHY[input] == expected
   ```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'core'` | Run pytest from workspace root: `cd c:\Users\Public\GCC_Monitoring\gcc_monitoring` |
| `AssertionError: assert None == <obj>` | Mock might not be returning value. Check `mock_get_conn.return_value = test_db` |
| `sqlite3.IntegrityError: FOREIGN KEY constraint failed` | Insert parent record first (customer before location) |
| Test hangs | May be missing `.close()` on DB connection. Ensure fixture closes DB. |
| Coverage < 50% | Run `pytest --cov-report=term-missing` to see what lines aren't covered |

---

## Next Steps

1. Implement `tests/test_auth.py` (this page)
2. Add `tests/test_security.py` (password hashing)
3. Add `tests/test_customers_repo.py` (CRUD operations)
4. Scale to other repositories
5. Add `tests/test_issue_rules.py` and `tests/test_alert_system.py`

See [TESTING_ASSESSMENT.md](TESTING_ASSESSMENT.md) for full strategy.
