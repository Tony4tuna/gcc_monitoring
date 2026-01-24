# System Improvements - Logging, Error Handling, and UX Enhancements

## Overview

This document describes the comprehensive improvements made to the GCC Monitoring System for better reliability, user experience, and maintainability.

## 1. Centralized Logging System

### Location
`core/logger.py`

### Features
- **Daily log files** stored in `logs/app_YYYYMMDD.log`
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Dual output**: Console and file logging
- **Structured format** with timestamps, level, and module info

### Usage Examples

```python
from core.logger import log_info, log_error, log_user_action, handle_error

# Log informational messages
log_info("User logged in successfully", "auth")

# Log errors with exception details
try:
    risky_operation()
except Exception as e:
    log_error("Operation failed", "module_name", exc_info=e)

# Log user actions for audit trail
log_user_action("Created new ticket", "Ticket #123, Customer XYZ")

# Handle errors with automatic logging and user notification
try:
    process_data()
except Exception as e:
    handle_error(e, "data processing", notify_user=True)
```

### Error Handling Decorator

```python
from core.logger import with_error_handling

@with_error_handling("user creation")
def create_user(data):
    # Any exception will be caught, logged, and user notified
    # Function returns None on error
    save_to_database(data)
```

## 2. Navigation Improvements

### Back Buttons

All major pages now include back buttons for easier navigation:

**In Header** (small icon):
- Appears in top navigation bar
- Quick way to go back without scrolling

**In Page Title** (button with icon):
- Larger, more visible
- Shows tooltip indicating destination

### Usage in Pages

```python
from ui.layout import layout

# Add back button that goes to dashboard
with layout("Page Title", show_logout=True, show_back=True, back_to="/"):
    # Page content here
```

### Parameters
- `show_back`: Enable/disable back button
- `back_to`: URL to navigate to (default: "/" dashboard)

## 3. Visual Indicators & Tooltips

### Clickable Rows
Tables with interactive rows now show:
- **Hover effect**: Light green highlight on mouseover
- **Cursor change**: Pointer cursor indicates clickability
- **Helper text**: "Click any row to..." instructions above tables

### Button Icons
All action buttons now include:
- **Material Icons**: Clear visual representation
- **Tooltips**: Hover to see what the button does
- **Color coding**:
  - Green: Add/Create actions
  - Blue: Edit actions
  - Red: Delete actions
  - Orange: Print/Export actions

### Example Button Definitions

```python
# Add button with icon and tooltip
ui.button("Add Client", icon="add", on_click=add_handler)\
    .props("dense color=positive")\
    .tooltip("Create a new client")

# Edit button
ui.button("Edit", icon="edit", on_click=edit_handler)\
    .props("dense color=primary")\
    .tooltip("Edit selected client")

# Delete button  
ui.button("Delete", icon="delete", on_click=delete_handler)\
    .props("dense color=negative")\
    .tooltip("Delete selected client")
```

## 4. User Action Audit Trail

All significant user actions are logged:

### Logged Actions
- Page views
- Record creation (clients, locations, units, tickets)
- Record updates
- Record deletions
- Ticket status changes
- Login/logout events
- Failed actions (e.g., duplicate ticket attempts)

### Log Format
```
2026-01-24 10:30:15 | INFO | audit | USER_ACTION: Created ticket #123 | User: admin@example.com | Details: Unit 5, Symptom: Not cooling
```

### Viewing Logs
Logs are stored in `logs/` directory:
```
logs/
├── app_20260124.log    # Today's log
├── app_20260123.log    # Yesterday's log
└── ...
```

## 5. Error Recovery

### Graceful Degradation
- Errors don't crash the app
- User gets friendly notification
- Error details logged for debugging
- Function returns `None` or empty data on error

### User Notifications
- **Success**: Green notification with checkmark
- **Warning**: Amber notification with alert icon
- **Error**: Red notification with error icon
- **Info**: Blue notification with info icon

### Example Flow
```
User Action → Error Occurs → System Response
1. Click "Create Ticket"
2. Database connection fails
3. System:
   - Logs full error with stack trace
   - Shows user: "An error occurred during ticket creation"
   - Returns to safe state
   - User can retry
```

## 6. Page-by-Page Enhancements

### Dashboard
- ✅ Error handling on data loading
- ✅ Tooltips on clickable unit rows
- ✅ Tooltips on ticket grid rows
- ✅ User action logging

### Clients Page
- ✅ Back button to dashboard
- ✅ Icons on all action buttons
- ✅ Tooltips explaining each button
- ✅ Action logging (create, edit, delete)
- ✅ Error handling on all operations

### Locations Page
- ✅ Back button to dashboard
- ✅ Action logging
- ✅ Error handling

### Equipment Page
- ✅ Back button to dashboard  
- ✅ Action logging
- ✅ Error handling

### Service Tickets Page
- ✅ Unit dialog with error handling
- ✅ Duplicate prevention logging
- ✅ Ticket creation logging
- ✅ User-friendly error messages

### Settings Page
- ✅ Error handling imports
- ✅ Prepared for action logging

## 7. CSS Enhancements

### New CSS Classes

```css
/* Clickable rows */
.clickable-row {
    cursor: pointer;
    transition: background-color 0.2s;
}
.clickable-row:hover {
    background-color: rgba(22, 163, 74, 0.1);
}

/* Tooltips */
.gcc-tooltip {
    font-size: 12px;
    background: rgba(0, 0, 0, 0.9);
    padding: 6px 10px;
    border-radius: 4px;
}
```

## 8. Best Practices for Developers

### When Adding New Pages

```python
from nicegui import ui
from core.auth import require_login
from core.logger import log_user_action, handle_error
from ui.layout import layout

def page():
    if not require_login():
        return
    
    # Log page view
    log_user_action("Viewed My New Page")
    
    # Use layout with back button
    with layout("My Page", show_logout=True, show_back=True, back_to="/"):
        # Add helper text for interactive elements
        ui.label("Click any row to edit").classes("text-xs gcc-muted mb-2")
        
        # Add tooltips to buttons
        ui.button("Save", icon="save", on_click=save_handler)\
            .tooltip("Save changes")
```

### When Adding New Features

```python
@with_error_handling("saving customer data")
def save_customer(data):
    # Log the action
    log_user_action("Created customer", f"Company: {data['company']}")
    
    # Your code here
    result = database.save(data)
    
    # Success notification
    ui.notify("Customer saved successfully", type="positive")
    
    return result
```

## 9. Troubleshooting

### Viewing Logs
1. Navigate to `logs/` folder
2. Open today's log file: `app_YYYYMMDD.log`
3. Search for ERROR or CRITICAL entries
4. Check timestamp and user email for context

### Common Log Patterns

**Successful Action:**
```
2026-01-24 10:30:15 | INFO | audit | USER_ACTION: Created ticket #123
```

**Error:**
```
2026-01-24 10:30:20 | ERROR | error_handler | Error in ticket creation: Database connection failed
Traceback (most recent call last):
  ...
```

**User Action with Details:**
```
2026-01-24 10:30:25 | INFO | audit | USER_ACTION: Viewed Dashboard | User: admin@example.com | Details: 
```

## 10. Future Enhancements

Recommended additions:
- [ ] Log rotation (automatic cleanup of old logs)
- [ ] Admin page to view recent logs
- [ ] Email notifications for critical errors
- [ ] Performance monitoring (slow queries, long page loads)
- [ ] User session analytics
- [ ] Export logs to CSV for analysis

## Summary

These improvements significantly enhance:
- **Reliability**: Errors don't crash the system
- **Debugging**: Comprehensive logs for troubleshooting  
- **User Experience**: Clear navigation, tooltips, visual feedback
- **Security**: Audit trail of all user actions
- **Maintainability**: Centralized error handling and logging

All pages now follow consistent patterns for error handling, logging, and user interaction.
