# Quick Reference: System Improvements

## For Operators/Users

### Navigation
- **Back Button** (← icon): Returns to previous page (usually dashboard)
- **Sidebar Menu**: Quick navigation to any section
- **Tooltips**: Hover over buttons to see what they do

### Visual Cues
- **Hover Effect**: Rows that turn light green are clickable
- **Button Colors**:
  - 🟢 Green = Add/Create
  - 🔵 Blue = Edit
  - 🔴 Red = Delete
  - 🟠 Orange = Print/Export
- **Pointer Cursor**: Indicates clickable items

### Notifications
- ✅ **Green** = Success
- ⚠️ **Amber** = Warning
- ❌ **Red** = Error
- ℹ️ **Blue** = Information

### Dashboard
- **Units Table**: Click any faulty unit to view details or create ticket
- **Tickets Table**: Click any ticket to view full details
- **Status Badges**:
  - 🎫 Green badge = Open ticket exists
  - ⚠️ Red badge = No ticket (action needed)
  - 🟡 AMBER badge = Created by client
  - 🔵 BLUE badge = Created by tech/admin

## For Developers

### Adding Logging
```python
from core.logger import log_user_action, log_error, handle_error

# Log user actions
log_user_action("Action description", "Optional details")

# Log errors
try:
    risky_code()
except Exception as e:
    log_error("What failed", "module", exc_info=e)

# Or use handle_error for automatic user notification
try:
    risky_code()
except Exception as e:
    handle_error(e, "operation name", notify_user=True)
```

### Using Error Decorator
```python
from core.logger import with_error_handling

@with_error_handling("operation description")
def my_function():
    # Automatically catches and logs errors
    # Returns None on error
    pass
```

### Adding Back Buttons
```python
from ui.layout import layout

with layout("Page Title", show_back=True, back_to="/"):
    # Page content
```

### Adding Tooltips
```python
ui.button("Text", icon="icon_name", on_click=handler)\
    .tooltip("Helpful description")
```

### Adding Clickable Tables
```python
# 1. Add helper text
ui.label("Click any row to view details").classes("text-xs gcc-muted mb-2")

# 2. Create table
table = ui.table(columns=cols, rows=rows)

# 3. Add click handler
def on_row_click(e):
    row = e.args[1] if len(e.args) >= 2 else None
    if row:
        # Handle click
        open_detail_dialog(row['id'])

table.on("row-click", on_row_click)
```

## Viewing Logs

### Location
`logs/app_YYYYMMDD.log`

### What's Logged
- User actions (page views, create/edit/delete)
- Errors with stack traces
- System startup/shutdown
- Authentication events

### Log Format
```
TIMESTAMP | LEVEL | MODULE | MESSAGE
```

### Example
```
2026-01-24 00:06:43 | INFO | audit | USER_ACTION: Created ticket #5 | User: admin@test.com | Details: Unit 2, Symptom: Not cooling
```

## Error Handling Flow

```
User Action
    ↓
Try Operation
    ↓
Success? → Log action → Notify user (green)
    ↓
Error? → Log error → Notify user (red) → Return safe state
```

## Icon Reference

Common Material Icons used in the app:

- `arrow_back` - Back navigation
- `add` - Create new
- `edit` - Edit existing
- `delete` - Delete
- `refresh` - Reload data
- `save` - Save changes
- `close` - Close dialog
- `print` - Print/Export
- `info` - Information
- `warning` - Warning
- `error` - Error
- `check_circle` - Success/Complete
- `cancel` - Cancel action

## Testing Checklist

When adding new features, verify:

- [ ] Back button works (if applicable)
- [ ] All buttons have icons
- [ ] All buttons have tooltips
- [ ] Clickable items show hover effect
- [ ] User actions are logged
- [ ] Errors are caught and logged
- [ ] User gets friendly error messages
- [ ] Success actions show green notification
- [ ] Errors don't crash the page

## Common Patterns

### Creating a New Page
1. Import layout and logger
2. Check authentication
3. Log page view
4. Use layout with back button
5. Add tooltips to all buttons
6. Add error handling to all operations
7. Log all user actions

### Handling Forms
1. Validate input
2. Try operation in try/except
3. Log the action (success or failure)
4. Notify user (green for success, red for error)
5. Close dialog/refresh data on success
6. Keep dialog open on error (so user can retry)

### Updating Data
1. Confirm with dialog (for destructive actions)
2. Try operation with error handling
3. Log the update with details
4. Refresh the table/view
5. Notify user of outcome
