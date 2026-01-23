# Client Home Role-Based Access Control - Test Guide

## Changes Summary

### Modified Files
- `pages/client_home.py` - Complete rebuild with role-based access control

### Role Hierarchy
```python
1: Master (GOD)         - Full access (view/add/edit/delete)
2: Administrator        - Full access except delete clients
3: Tech (tech_gcc)      - Read-only access (view only)
4: Client               - Own data only, profile editing
```

---

## Implementation Details

### Role Checks (in `page()` function)
```python
hierarchy = user.get("hierarchy", 5)
is_master = hierarchy == 1
is_administrator = hierarchy == 2
is_tech = hierarchy == 3
is_client = hierarchy == 4

# Access levels
can_edit = is_master or is_administrator    # Master and Admin can edit
can_delete = is_master                       # Only Master can delete
read_only = is_tech                          # Tech is read-only
own_data_only = is_client                    # Client sees only their data
```

### UI Blocking Strategy

1. **Client Selector**
   - Hidden for Client (4)
   - Visible for Tech (3), Admin (2), Master (1)

2. **Profile Section**
   - Client (4): Editable profile fields (company, email, phone)
   - Others: Read-only customer info display

3. **Location Edit Button**
   - Hidden for Tech (3) and Client (4)
   - Visible for Admin (2) and Master (1)

4. **Equipment Actions**
   - Client (4): View button only
   - Tech (3): View button only (read-only)
   - Admin (2) & Master (1): Edit button

5. **Data Scope**
   - Client (4): `own_data_only=True`, filters to `customer_id` from session
   - Tech (3): Can select client, but read-only
   - Admin (2) & Master (1): Can select any client, full edit

---

## Location-First UI

Equipment is now grouped by location in expandable cards:

```
Location Card
├── Location Name/Address (header)
├── Edit Location button (Master/Admin only)
└── Equipment Grid (3 columns)
    ├── RTU-1 (Make/Model/SN + View/Edit button)
    ├── RTU-2
    └── RTU-3
```

**Before:** Flat location grid → click → modal with equipment  
**After:** Location cards with equipment inline (no modal)

---

## Manual Test Checklist

### Test Setup
Create test logins for each role:
```sql
-- Master (hierarchy=1)
INSERT INTO Logins (login_id, password_hash, hierarchy, customer_id, is_active)
VALUES ('master@test.com', 'test123', 1, 1, 1);

-- Administrator (hierarchy=2)
INSERT INTO Logins (login_id, password_hash, hierarchy, customer_id, is_active)
VALUES ('admin@test.com', 'test123', 2, 1, 1);

-- Tech (hierarchy=3)
INSERT INTO Logins (login_id, password_hash, hierarchy, customer_id, is_active)
VALUES ('tech@test.com', 'test123', 3, NULL, 1);

-- Client (hierarchy=4)
INSERT INTO Logins (login_id, password_hash, hierarchy, customer_id, is_active)
VALUES ('client@test.com', 'test123', 4, 1, 1);
```

---

### Role 1: Master (GOD)

**Expected Behavior:**
- ✅ Redirected to main dashboard (/)
- ✅ Does NOT see client_home.py

**Test Steps:**
1. Login as `master@test.com`
2. Verify redirect to admin dashboard
3. Should see main HVAC Dashboard with all features

**Pass Criteria:**
- ❌ Should never see "My Dashboard" (client home)
- ✅ Should see admin dashboard with full controls

---

### Role 2: Administrator

**Expected Behavior:**
- ✅ Redirected to main dashboard (/)
- ✅ Does NOT see client_home.py
- ✅ Can edit clients (via /clients page)
- ⚠️ Cannot delete clients (blocked in /clients page)

**Test Steps:**
1. Login as `admin@test.com`
2. Verify redirect to admin dashboard
3. Navigate to /clients
4. Verify edit buttons visible
5. Verify delete buttons hidden/disabled

**Pass Criteria:**
- ❌ Should never see "My Dashboard"
- ✅ Should see admin dashboard
- ✅ Full navigation access
- ⚠️ Delete client button hidden (enforce in clients.py)

---

### Role 3: Tech (tech_gcc)

**Expected Behavior:**
- ✅ Shows client_home.py
- ✅ Client selector dropdown visible
- ✅ All data read-only (no edit/delete buttons)
- ✅ Equipment shows "View" buttons only
- ✅ Location edit buttons hidden
- ✅ Can switch between clients

**Test Steps:**
1. Login as `tech@test.com`
2. Verify "My Dashboard" page loads
3. Check client selector dropdown exists
4. Select a client from dropdown
5. Verify locations display with equipment
6. Click "View" button on equipment
7. Verify read-only modal opens
8. Look for edit/delete buttons (should NOT exist)

**Pass Criteria:**
- ✅ Client selector visible and functional
- ✅ Locations display with equipment inline
- ✅ Only "View" buttons on equipment
- ❌ No edit/delete buttons anywhere
- ❌ No location edit buttons
- ✅ Modal shows unit details read-only
- ✅ Can view all clients

---

### Role 4: Client

**Expected Behavior:**
- ✅ Shows client_home.py
- ❌ Client selector hidden
- ✅ Shows only their own data
- ✅ Profile section editable (company, email, phone)
- ✅ Locations show with equipment
- ✅ Equipment shows "View" buttons only
- ❌ Cannot access other clients
- ❌ Cannot access /admin, /clients, /locations pages

**Test Steps:**
1. Login as `client@test.com` (linked to customer_id=1)
2. Verify "My Dashboard" page loads
3. Check NO client selector dropdown
4. Verify "My Profile" section exists
5. Edit profile fields (company, email, phone)
6. Click "Save Profile"
7. Verify success notification
8. Check locations display (only customer_id=1)
9. Click "View" on equipment
10. Try navigating to /clients (should redirect)
11. Try navigating to /admin (should redirect)

**Pass Criteria:**
- ❌ No client selector
- ✅ "My Profile" section visible and editable
- ✅ Only own customer's locations/equipment
- ✅ Profile saves successfully
- ✅ Equipment view-only
- ❌ Cannot access admin pages
- ✅ Logout button visible

---

## Expected UI Elements by Role

| Element | Master (1) | Admin (2) | Tech (3) | Client (4) |
|---------|-----------|-----------|----------|------------|
| Client Selector | N/A (admin dashboard) | N/A (admin dashboard) | ✅ | ❌ |
| Profile Edit | N/A | N/A | ❌ | ✅ |
| Location Edit Btn | N/A | N/A | ❌ | ❌ |
| Equipment Edit Btn | N/A | N/A | ❌ | ❌ |
| Equipment View Btn | N/A | N/A | ✅ | ✅ |
| All Clients Data | N/A | N/A | ✅ | ❌ |

---

## Known Issues / Future Enhancements

### Current Limitations
1. **Location/Unit Edit Integration**
   - Currently shows notify placeholder
   - TODO: Integrate with /locations and /equipment edit flows
   - Could open edit modal or navigate with query params

2. **Administrator Delete Restriction**
   - Currently only enforced in client_home.py
   - Need to add check in `pages/clients.py` to hide delete button for Admin (2)

3. **Work Order Restrictions (Administrator)**
   - Requirement: Admin cannot edit/delete work orders created by Client
   - Not yet implemented (awaiting work orders feature)
   - Will need work_order_repo with creator tracking

### Recommended Next Steps
1. Add delete button hiding in `pages/clients.py` for Admin (2)
2. Implement location/equipment edit modal integration
3. Add work orders module with creator field
4. Add audit logging for profile changes

---

## Troubleshooting

**Client sees other clients' data:**
- Check `customer_id` in session: `current_user().get("customer_id")`
- Verify `own_data_only` is `True` for Client (4)
- Check `list_locations(customer_id=...)` parameter

**Tech can edit:**
- Verify `hierarchy == 3` in session
- Check `read_only` flag is `True`
- Ensure edit buttons have `if not read_only:` guard

**Admin redirected to client home:**
- Check `is_admin()` function returns `True` for hierarchy 1,2
- Verify early return: `if is_admin(): ui.navigate.to("/")`

**Profile not saving (Client):**
- Check `update_customer()` function in `customers_repo.py`
- Verify `customer_id` matches user's customer
- Check database permissions

---

## Code Quality Notes

✅ **Strengths:**
- Clear role hierarchy checks at top of function
- Conditional UI rendering based on role flags
- Data scoping enforced at query level
- Location-first UI improves usability
- Consistent with existing styling

⚠️ **Areas for Improvement:**
- Edit integration stubs (location/unit) need implementation
- Could extract role checking into helper functions
- Profile update could validate fields
- Consider caching customer/location data

---

## Security Validation

### Data Access Tests
```python
# Run these checks in Python console with test logins

# Client (4) should only see own customer_id
user = current_user()  # logged in as client
assert user["hierarchy"] == 4
locations = list_locations(customer_id=user["customer_id"])
# Manually verify all locations belong to that customer

# Tech (3) should see all but edit nothing
# (UI check - no backend restriction needed for read)

# Admin (2) should not delete
# (Check clients.py for delete button hiding)
```

---

## Deployment Notes

**Before deploying:**
1. ✅ Test all 4 roles with real logins
2. ✅ Verify client data isolation
3. ✅ Check responsive layout on mobile
4. ⚠️ Update clients.py to hide delete for Admin
5. ⚠️ Add work order restrictions when feature exists

**Database migrations:**
- None required (uses existing hierarchy column)

**Environment:**
- No new dependencies
- No configuration changes
