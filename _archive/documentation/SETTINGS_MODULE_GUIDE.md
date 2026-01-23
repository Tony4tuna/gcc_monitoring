# Settings Module Guide

## Overview

The Settings Module provides a comprehensive configuration and administration dashboard for the GCC Monitoring System. It includes five main management areas:

1. **Company Profile** - Organization information
2. **Email Settings** - SMTP/Email configuration
3. **Employee Profile** - Employee directory management
4. **Service Call Settings** - Service request configuration
5. **Ticket Sequence** - Ticket numbering format management

## Module Structure

```
gcc_monitoring/
├── core/
│   └── settings_repo.py          # Data access layer for all settings
├── pages/
│   └── settings.py               # Main UI page with all tabs
├── ui/
│   └── settings_dialogs.py       # Reusable dialog components
└── app.py                         # Updated with settings route
```

## Components

### 1. Core Settings Repository (`core/settings_repo.py`)

**Functions:**

#### Company Profile
- `get_company_profile()` - Retrieve company information
- `update_company_profile(data: Dict)` - Update company details

#### Email Settings
- `get_email_settings()` - Retrieve SMTP configuration
- `update_email_settings(data: Dict)` - Update email settings

#### Employee Profile
- `list_employees(search: str, status: str)` - List employees with filtering
- `get_employee(employee_id: int)` - Get single employee
- `create_employee(data: Dict)` - Create new employee
- `update_employee(employee_id: int, data: Dict)` - Update employee
- `delete_employee(employee_id: int)` - Delete employee

#### Service Call Settings
- `get_service_call_settings()` - Retrieve service call configuration
- `update_service_call_settings(data: Dict)` - Update settings

#### Ticket Sequence
- `list_ticket_sequences()` - List all sequence types
- `get_ticket_sequence(sequence_id: int)` - Get specific sequence
- `create_ticket_sequence(data: Dict)` - Create new sequence
- `update_ticket_sequence(sequence_id: int, data: Dict)` - Update sequence
- `delete_ticket_sequence(sequence_id: int)` - Delete sequence
- `get_next_ticket_number(sequence_type: str)` - Generate next ticket number

### 2. Settings UI Page (`pages/settings.py`)

**Features:**
- Tabbed interface for different settings areas
- Modal dialogs for CRUD operations
- Form validation and error handling
- Real-time notifications

**Functions:**
- `page()` - Main page renderer
- `create_company_profile_tab()` - Company settings tab
- `create_email_settings_tab()` - Email configuration tab
- `create_employee_profile_tab()` - Employee directory tab
- `create_service_call_settings_tab()` - Service call configuration
- `create_ticket_sequence_tab()` - Ticket sequence management

### 3. Dialog Components (`ui/settings_dialogs.py`)

**Classes:**

#### SettingsDialog
Base class for creating consistent modal dialogs
```python
dialog = SettingsDialog("Edit Settings", modal_size="md")
dialog.add_field("name", "Company Name", "text", "Current Name")
dialog.add_row_fields([...])
dialog.create(on_save=save_handler)
dialog.open()
```

#### FormDialog
Generic form dialog for create/edit operations
```python
fields = [
    {"name": "first_name", "label": "First Name", "type": "text", "value": ""},
    {"name": "email", "label": "Email", "type": "text", "value": ""},
]
form = FormDialog("Add Employee", fields, modal_size="md")
form.create_form(on_save=save_handler)
form.open()
```

#### ConfirmDialog
Confirmation dialog for destructive operations
```python
confirm = ConfirmDialog(
    "Delete Employee?",
    "This action cannot be undone.",
    on_confirm=delete_handler
)
confirm.show()
```

#### TableWithActions
Table component with built-in action buttons
```python
table = TableWithActions(
    columns=[...],
    rows=data,
    on_edit=edit_handler,
    on_delete=delete_handler
)
table.create()
```

#### NotificationBanner
Notification system for user feedback
```python
NotificationBanner.success("Changes saved successfully")
NotificationBanner.error("An error occurred")
NotificationBanner.info("This is informational")
NotificationBanner.warning("Be careful with this action")
```

## Database Tables

### CompanyInfo
```sql
id INTEGER PRIMARY KEY
name TEXT
address1, address2 TEXT
city, state, zip TEXT
phone TEXT
email TEXT
website TEXT
service_email TEXT
owner_email TEXT
```

### EmailSettings
```sql
id INTEGER PRIMARY KEY
smtp_host TEXT
smtp_port INTEGER (default: 587)
use_tls INTEGER (default: 1)
smtp_user TEXT
smtp_pass TEXT
smtp_from TEXT
```

### EmployeeProfile
```sql
id INTEGER PRIMARY KEY
employee_id TEXT UNIQUE
first_name, last_name TEXT
photo_path TEXT
department TEXT
position TEXT
email, phone, mobile TEXT
address1, address2, city, state, zip TEXT
start_date TEXT
end_date TEXT
status TEXT (Active/Inactive/Leave/Terminated)
emergency_contact TEXT
emergency_phone TEXT
notes TEXT
```

### ServiceCallSettings
```sql
id INTEGER PRIMARY KEY (1)
default_priority TEXT
auto_assign INTEGER
assignment_method TEXT
priority_colors TEXT (JSON)
status_workflow TEXT (JSON)
notification_on_create INTEGER
notification_on_close INTEGER
sla_hours_* INTEGER (for each priority level)
```

### TicketSequenceSettings
```sql
id INTEGER PRIMARY KEY
sequence_type TEXT UNIQUE
prefix TEXT
starting_number INTEGER
current_number INTEGER
increment_by INTEGER
format_pattern TEXT
reset_period TEXT (none/daily/monthly/yearly)
last_reset TEXT
is_active INTEGER
```

## Usage Examples

### Example 1: Add New Employee
```python
from core.settings_repo import create_employee

data = {
    "employee_id": "EMP001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@company.com",
    "position": "Technician",
    "department": "Service",
    "start_date": "2024-01-15",
    "status": "Active"
}

employee_id = create_employee(data)
if employee_id:
    print(f"Employee created with ID: {employee_id}")
```

### Example 2: Update Company Profile
```python
from core.settings_repo import update_company_profile

data = {
    "name": "GCC Monitoring Inc.",
    "email": "contact@gcc-monitoring.com",
    "phone": "555-123-4567",
    "address1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001"
}

if update_company_profile(data):
    print("Company profile updated successfully")
```

### Example 3: Create Ticket Sequence
```python
from core.settings_repo import create_ticket_sequence, get_next_ticket_number

# Create a new sequence
seq_data = {
    "sequence_type": "service_ticket",
    "prefix": "SVR",
    "starting_number": 1000,
    "current_number": 1000,
    "increment_by": 1,
    "format_pattern": "{prefix}-{year}{month}-{seq:05d}",
    "reset_period": "monthly",
    "is_active": 1
}

seq_id = create_ticket_sequence(seq_data)

# Generate next ticket number
next_num = get_next_ticket_number("service_ticket")
print(f"Next ticket: {next_num}")
```

### Example 4: Get Employee List
```python
from core.settings_repo import list_employees

# All employees
all_employees = list_employees()

# Active employees
active = list_employees(status="Active")

# Search by name
search_results = list_employees(search="John")

# Combined
results = list_employees(search="tech", status="Active")
```

## Accessing the Settings Module

1. **Navigate to Settings:**
   - URL: `/settings`
   - Only accessible to admin users (hierarchy 1-2)

2. **Tabs Available:**
   - Company Profile - View/Edit company information
   - Email Settings - Configure SMTP and email
   - Employee Profile - Manage employee directory
   - Service Call Settings - Configure service requests
   - Ticket Sequence - Manage ticket numbering

## Design Principles

### Dialog Consistency
- All dialogs use consistent grid layout (12-column)
- Standard padding: 16px/24px
- Cancel button on left, primary action on right
- Close button (X) in top-right corner

### Modal Sizes
- **sm** (400px) - Simple forms
- **md** (600px) - Standard forms (default)
- **lg** (800px) - Complex multi-section forms
- **xl** (1000px) - Large data entry forms

### Color Scheme
- Primary: Blue (#3b82f6)
- Success: Green (#22c55e)
- Danger: Red (#ef4444)
- Warning: Yellow (#eab308)
- Background: Dark theme (#1f2937)

### Responsive Behavior
- Desktop: 2-column layouts in dialogs
- Tablet: Adaptive 1-2 column
- Mobile: Single column, full-width

## Error Handling

All CRUD operations include try-except blocks with logging:

```python
def update_employee(employee_id, data):
    try:
        # Update logic
        return True
    except Exception as e:
        print(f"Error updating employee: {e}")
        return False
```

Errors are notified to users via notification system:
```python
if update_employee(emp_id, data):
    show_notification("Employee updated successfully", "success")
else:
    show_notification("Error updating employee", "error")
```

## Security Considerations

1. **Authentication:** Settings page requires login
2. **Authorization:** Admin-only access (hierarchy levels 1-2)
3. **Password Storage:** Email passwords stored securely in database
4. **Audit:** Consider adding audit logging for sensitive changes

## Future Enhancements

1. **Batch Operations:** Import/export employee data via CSV
2. **Email Templates:** Create custom email notification templates
3. **Alert Thresholds:** Configurable equipment alert parameters
4. **Maintenance Schedules:** Schedule preventive maintenance tasks
5. **Audit Logging:** Track all settings changes with timestamps
6. **Backup/Restore:** System configuration backup functionality
7. **Multi-language:** Internationalization support
8. **API Integration:** REST API for settings management

## Troubleshooting

### Issue: Settings page shows "Access Denied"
**Solution:** Verify user has admin privileges (hierarchy 1 or 2)

### Issue: Email settings not saving
**Solution:** Check database permissions and SMTP credentials

### Issue: Employee not appearing in list
**Solution:** Verify employee has status="Active" or adjust filter

### Issue: Ticket numbers not incrementing
**Solution:** Check TicketSequenceSettings table for correct sequence_type

## Support

For issues or questions about the Settings Module:
1. Check this documentation
2. Review function docstrings in settings_repo.py
3. Check database schema in schema/schema.sql
4. Review error logs in logs/app.log
