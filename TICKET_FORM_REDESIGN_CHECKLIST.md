# Ticket Form Redesign - Complete Change List

**Date**: January 27, 2026  
**Session**: Email Module + Form Layout Redesign

---

## PHASE 1: Foundation (Database & Core)

### 1. Verify/Add Unit Columns
- [ ] Check if `Units` table has `refrigerant_type` column
- [ ] Check if `Units` table has `voltage` column
- [ ] If missing, add via ALTER TABLE
- **Logic**: Need this data before displaying in forms/PDFs

### 2. Multi-Unit Support (Database)
- [ ] **Option A**: Keep 1 unit per ticket (current) — ticket has `unit_id`
- [ ] **Option B**: New junction table `TicketUnits(ticket_id, unit_id)` — many-to-many
- **Decision Needed**: Which approach?
  - A = Simpler, faster implementation
  - B = Scalable, future-proof for multiple units per ticket

### 3. Date Editing (Database)
- [ ] Tickets: Make `created` date editable
- [ ] Other forms: Check if `created`/`updated` columns exist and make editable
- **Logic**: Allow override for backdating/corrections

---

## PHASE 2: Modify PDF Generator (Existing)

### 4. Update PDF Template (dashboard.py: `generate_service_order_pdf()`)
**Current Location**: `pages/dashboard.py` lines ~800-900

**Changes Required**:
- [ ] Company profile → LEFT aligned (margin 0)
- [ ] Ticket # / Date / Time → RIGHT aligned (end at right margin)
- [ ] Divider line
- [ ] Form title ("WORK ORDER") → LEFT aligned
- [ ] Client info (name, address, phone, email) → RIGHT aligned
- [ ] Divider line
- [ ] **"UNITS INFORMATION"** → LEFT aligned, BOLD
- [ ] Units grid → Bordered table with columns:
  - Tag | Type | Make | Model | Tonnage | **Refrigerant** | **Voltage** | Serial
- [ ] Format phone numbers: (XXX) XXX-XXXX
- [ ] Ticket # display: Only show ID number (not control fields)

**Layout Sketch**:
```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  GCC TECHNOLOGY                    Ticket #: 1001         ║
║  123 Tech Street                   Date: 01/27/2026       ║
║  Tech City, TC 12345               Time: 14:30:45         ║
║  Phone: (555) 123-4567                                    ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  WORK ORDER                        Customer: ACME Corp    ║
║                                    123 Main Street        ║
║                                    New York, NY 10001     ║
║                                    Phone: (212) 555-1234  ║
║                                    Email: contact@acme.com║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  **UNITS INFORMATION**                                    ║
║  ┌──────┬───────┬────────┬───────┬──────┬────────┬───┐   ║
║  │ Tag  │ Type  │  Make  │ Model │ Tons │ Refrig │ V │   ║
║  ├──────┼───────┼────────┼───────┼──────┼────────┼───┤   ║
║  │ RTU-1│ Roof  │Carrier │ 25XC  │  5T  │ R410A  │230│   ║
║  ├──────┼───────┼────────┼───────┼──────┼────────┼───┤   ║
║  │ RTU-2│Ground │ Trane  │  YUH  │  3T  │  R22   │460│   ║
║  └──────┴───────┴────────┴───────┴──────┴────────┴───┘   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

**Logic**: This is the master template for print/email

---

## PHASE 3: Ticket Creation/Edit Forms

### 5. Multi-Unit UI (Tickets Page & Dashboard)
**Decision Point**: How to handle multiple units?

**Option A - Single Unit (Keep Current)**:
- [ ] Keep current unit dropdown
- [ ] Display selected unit specs in grid format
- [ ] Add refrigerant + voltage to display

**Option B - Multi-Unit (New Feature)**:
- [ ] Change unit dropdown to multi-select
- [ ] Show all selected units in preview grid
- [ ] Store: comma-separated IDs OR use junction table
- [ ] Update PDF to show all selected units

### 6. Update `render_call_form()` (tickets.py)
**Current Location**: `pages/tickets.py` line ~668

**Changes Required**:
- [ ] Remove "DESCRIPTION (AUTO)" field entirely
- [ ] Apply new PDF layout to form preview
- [ ] Company profile → LEFT
- [ ] Ticket # / Date / Time → RIGHT
- [ ] Client info → RIGHT
- [ ] Units grid → CENTER with borders
- [ ] Add date picker for "Created Date" (optional override)
- [ ] Add refrigerant + voltage to unit display

**Logic**: Form matches print/PDF exactly

### 7. Update `show_edit_dialog()` (tickets.py)
**Current Location**: `pages/tickets.py` line ~982

**Changes Required**:
- [ ] Apply same layout as create form
- [ ] Add date picker for editing `created` date
- [ ] Keep existing customer/location/unit cascading selects
- [ ] Update unit display to show refrigerant + voltage

**Logic**: Allow backdating/corrections, consistent UI

---

## PHASE 4: Email Integration

### 8. Remove Auto-Email on Creation
**Current Location**: `core/tickets_repo.py` line ~100

**Changes Required**:
- [ ] Remove `_send_ticket_email()` call from `create_service_call()`
- [ ] Keep `_send_ticket_email()` function for manual use

**Logic**: User should review ticket before sending email

### 9. Update Manual Email (tickets.py & dashboard.py)
**Locations**: 
- `pages/tickets.py` line ~368 (`send_ticket_email()`)
- `pages/dashboard.py` line ~701 (email handler in `open_ticket_dialog()`)

**Changes Required**:
- [ ] Generate PDF using updated template (`generate_service_order_pdf()`)
- [ ] Attach PDF to email (not plain text body)
- [ ] Add recipient picker dialog:
  - [ ] Admin email (from settings)
  - [ ] Customer email
  - [ ] Custom email input (comma-separated)
- [ ] Show success/failure notification

**Logic**: PDF attachment = professional, configurable recipients

---

## PHASE 5: Apply Date Editing Everywhere

### 10. Add Date Pickers to Other Forms
**Locations**: Various edit dialogs across pages/

**Changes Required**:
- [ ] Customers edit (`pages/clients.py`)
- [ ] Locations edit (`pages/locations.py`)
- [ ] Equipment edit (`pages/equipment.py`)
- [ ] Employees edit (`pages/settings.py`)
- [ ] Add "Created Date" and "Updated Date" fields
- [ ] Make editable with date pickers

**Logic**: Consistency across entire application

---

## CRITICAL DECISIONS NEEDED:

### Q1: Multi-Unit Approach?
- [ ] **A**: Keep single unit per ticket (simpler, faster)
- [ ] **B**: Support multiple units per ticket (requires junction table + UI refactor)

### Q2: Date Editing Scope?
- [ ] Just tickets?
- [ ] All forms (customers, locations, equipment, employees)?

### Q3: Execution Order?
**Recommended**: Database → PDF → Forms → Email → Global date editing

---

## TESTING CHECKLIST (After Each Phase):

### Phase 1 Testing:
- [ ] Verify Units table has refrigerant_type and voltage columns
- [ ] Check data integrity after schema changes

### Phase 2 Testing:
- [ ] Print PDF from dashboard - verify layout
- [ ] Check alignment (LEFT at margin 0, RIGHT at edge)
- [ ] Verify units grid displays refrigerant + voltage
- [ ] Test phone number formatting

### Phase 3 Testing:
- [ ] Create new ticket - form matches PDF layout
- [ ] Edit existing ticket - can change created date
- [ ] Multi-unit selection works (if Option B)

### Phase 4 Testing:
- [ ] Create ticket - NO auto-email sent
- [ ] Click Email button - PDF attached correctly
- [ ] Recipient picker works (admin/customer/custom)
- [ ] Email delivery confirmed

### Phase 5 Testing:
- [ ] Date editing works in all forms
- [ ] Backdating validated
- [ ] No data corruption

---

## NOTES:
- **No auto-push** - Test locally first, ask before pushing to production
- **Commit frequently** - After each phase completion
- **Document** - Update this checklist as we progress
- **Verify** - Syntax check + manual test before moving to next phase

---

## PROGRESS TRACKING:

### Completed:
- [x] Email module base integration (already pushed - needs modification)
- [x] Email button added to dashboard & tickets
- [x] Disabled seed_unit_readings.py
- [x] **Phase 1: Database foundation**
  - [x] Verified Units table has refrigerant_type & voltage columns
  - [x] Created TicketUnits junction table (Option B - multi-unit support)
  - [x] Verified date columns in all tables
- [x] **Phase 2: PDF template redesign**
  - [x] Created centralized core/ticket_document.py module (400+ lines)
  - [x] Updated dashboard.py to use new module
  - [x] Updated tickets.py print handler to use new module
  - [x] Updated email to attach PDF (not text body)
  - [x] New layout: Company LEFT, Ticket# RIGHT, units grid with refrigerant+voltage
  - [x] Multi-unit support (queries TicketUnits, falls back to single unit)
  - [x] All syntax tests passed
  - [x] PDF generation tested (ticket 28: 2059 bytes)
  - [x] Email delivery tested (sent to work-orders@gcchvacr.com)

### In Progress:
- [ ] Phase 3: Form layout updates
- [ ] Phase 4: Email integration (auto-email removal, recipient picker)
- [ ] Phase 5: Global date editing

### Decisions Made:
- [x] Q1: Multi-Unit Approach → **Option B** (junction table for 1-4 units)
- [ ] Q2: Date Editing Scope → Pending (just tickets vs all forms)
