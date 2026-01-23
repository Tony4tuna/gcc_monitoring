# Settings Module - Quick Reference

## Files Created

| File | Purpose |
|------|---------|
| `core/settings_repo.py` | Data access layer for all settings |
| `pages/settings.py` | Main UI dashboard with tabs |
| `ui/settings_dialogs.py` | Reusable dialog components |
| `SETTINGS_MODULE_GUIDE.md` | Full documentation |

## Main Functions

### Company Profile
```python
from core.settings_repo import get_company_profile, update_company_profile

company = get_company_profile()
update_company_profile({"name": "Company", "email": "email@company.com"})
```

### Employee Management
```python
from core.settings_repo import list_employees, create_employee, update_employee, delete_employee

employees = list_employees(search="John", status="Active")
emp_id = create_employee({"first_name": "Jane", "last_name": "Doe", ...})
update_employee(emp_id, {"position": "Manager"})
delete_employee(emp_id)
```

### Email Configuration
```python
from core.settings_repo import get_email_settings, update_email_settings

settings = get_email_settings()
update_email_settings({
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "email@gmail.com",
    "smtp_pass": "password",
    "smtp_from": "noreply@company.com",
    "use_tls": True
})
```

### Service Call Settings
```python
from core.settings_repo import get_service_call_settings, update_service_call_settings

settings = get_service_call_settings()
update_service_call_settings({
    "default_priority": "Normal",
    "auto_assign": False,
    "sla_hours_low": 72,
    "sla_hours_normal": 48,
    "sla_hours_high": 24,
    "sla_hours_emergency": 4
})
```

### Ticket Sequencing
```python
from core.settings_repo import (
    list_ticket_sequences, 
    create_ticket_sequence, 
    get_next_ticket_number
)

sequences = list_ticket_sequences()
seq_id = create_ticket_sequence({
    "sequence_type": "service_ticket",
    "prefix": "SVR",
    "starting_number": 1000
})
next_ticket = get_next_ticket_number("service_ticket")
```

## Dialog Components

### SettingsDialog (Base Class)
```python
from ui.settings_dialogs import SettingsDialog

dialog = SettingsDialog("Edit Profile", modal_size="md")
dialog.add_field("name", "Full Name", "text", "Current Name")
dialog.add_field("email", "Email", "text", "user@example.com")
dialog.create(on_save=save_handler)
dialog.open()

values = dialog.get_values()  # {"name": "...", "email": "..."}
```

### FormDialog (Pre-configured Forms)
```python
from ui.settings_dialogs import FormDialog

fields = [
    {"name": "first_name", "label": "First Name", "type": "text"},
    {"name": "email", "label": "Email", "type": "text"},
    {"name": "status", "label": "Status", "type": "select", 
     "options": ["Active", "Inactive"]}
]

form = FormDialog("Add Employee", fields)
form.create_form(on_save=save_handler)
form.open()
```

### ConfirmDialog (Confirmation)
```python
from ui.settings_dialogs import ConfirmDialog

confirm = ConfirmDialog(
    "Delete Record?",
    "This action cannot be undone.",
    on_confirm=delete_handler
)
confirm.show()
```

### NotificationBanner (Notifications)
```python
from ui.settings_dialogs import NotificationBanner

NotificationBanner.success("Operation successful!")
NotificationBanner.error("An error occurred")
NotificationBanner.info("Information message")
NotificationBanner.warning("Warning message")
```

## Route

```python
# Access the settings module at:
# http://localhost:8080/settings

# Requires:
# - User authentication (logged in)
# - Admin privileges (hierarchy 1 or 2)
```

## Tab Organization

| Tab | Functions |
|-----|-----------|
| **Company Profile** | View/edit company info (name, address, contact) |
| **Email Settings** | Configure SMTP, email sender, TLS settings |
| **Employee Profile** | CRUD employee directory (create, search, update, delete) |
| **Service Call Settings** | Configure SLA times, priorities, notifications |
| **Ticket Sequence** | Manage ticket numbering formats and sequences |

## Dialog Sizes

- `sm` - 400px (simple forms)
- `md` - 600px (standard forms) ← default
- `lg` - 800px (complex forms)
- `xl` - 1000px (large data entry)

## Status Values for Employees

- `Active` - Currently working
- `Inactive` - Not currently available
- `Leave` - On temporary leave
- `Terminated` - No longer employed

## Service Call Priorities

- `Low` - 72 hour SLA
- `Normal` - 48 hour SLA
- `High` - 24 hour SLA
- `Emergency` - 4 hour SLA

## Ticket Reset Periods

- `none` - Never reset, continuous sequence
- `daily` - Reset every day
- `monthly` - Reset every month
- `yearly` - Reset every year

## Database Connection

All functions use `core/db.py` connection:
```python
from core.db import get_conn

with get_conn() as conn:
    # Execute queries
    pass
```

## Error Messages

Functions return:
- **Success:** `True` or ID (for create operations)
- **Failure:** `False` or `None`

Check error in logs:
```bash
# Watch logs
tail -f logs/app.log
```

## Integration with Other Modules

Settings module integrates with:
- **core/auth.py** - User authentication and authorization
- **core/db.py** - Database connections
- **pages/** - Other dashboard pages
- **ui/** - Shared UI components

## Next Steps

1. Access `/settings` in browser
2. Log in as admin user
3. Navigate through tabs
4. Create/edit company and employee information
5. Configure email and service call settings
6. Set up ticket sequences

## Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check function outputs:
```python
result = create_employee(data)
print(f"Result: {result}")  # Should be employee_id or None
```

Monitor database:
```bash
cd gcc_monitoring
sqlite3 data/app.db "SELECT * FROM EmployeeProfile;"
```
