# TODO: Multi-Unit PDF Attachment

## Issue
When a service ticket has **more than 4 units**, the PDF grid only shows the first 4 units.

## Solution Required
When ticket has >4 units:

### Page 1 (Main Form):
- Show first 4 units in the grid
- In the "Units" section header or notes area, add text:
  - **"See Attachment for Complete Unit List"** or
  - **"Additional units listed on Page 2"**

### Page 2 (Attachment):
- **Title:** "Equipment List - Service Ticket #[ID]"
- List ALL units in table format:
  - Unit ID
  - Make
  - Model  
  - Serial
  - Location (if needed)

## Files to Modify
- `core/ticket_document.py` (PDF generation)
  - Function: `generate_ticket_pdf()`
  - Current grid: Lines ~329-365 (4-row limit)
  - Need to add: Page break + attachment page logic

## Implementation Notes
- Check `len(units) > 4`
- If true:
  - Show first 4 in main grid
  - Add "See Attachment" note
  - Create new page with full unit table
- If ≤4: current behavior (no changes)

## Priority
Medium - Nice to have for large facilities with many units

---
**Created:** 2026-01-27
**Status:** Not Started
