-- HIERARCHY VERIFICATION QUERIES
-- Run these in your SQLite database to verify hierarchy column integrity

-- ============================================================================
-- Query 1: Complete Hierarchy Audit
-- ============================================================================
-- Shows all logins with their hierarchy values and types
SELECT 
    ID,
    login_id,
    hierarchy,
    typeof(hierarchy) AS hierarchy_type,
    is_active,
    customer_id,
    CASE 
        WHEN hierarchy = 1 THEN 'GOD'
        WHEN hierarchy = 2 THEN 'Administrator'
        WHEN hierarchy = 3 THEN 'Tech_GCC'
        WHEN hierarchy = 4 THEN 'Client'
        WHEN hierarchy = 5 THEN 'Client_Mngs'
        ELSE 'UNKNOWN: ' || hierarchy
    END AS hierarchy_label,
    COALESCE(C.company, C.first_name || ' ' || C.last_name, '(unassigned)') AS belongs_to
FROM Logins L
LEFT JOIN Customers C ON C.ID = L.customer_id
ORDER BY hierarchy ASC, ID ASC;

-- ============================================================================
-- Query 2: Quick Type Check
-- ============================================================================
-- Count logins by hierarchy value and data type
SELECT 
    hierarchy,
    typeof(hierarchy) AS type,
    COUNT(*) AS count
FROM Logins
GROUP BY hierarchy, typeof(hierarchy)
ORDER BY hierarchy;

-- ============================================================================
-- Query 3: Find Bad Data
-- ============================================================================
-- Find any non-integer hierarchy values (should return 0 rows if all is good)
SELECT 
    ID,
    login_id,
    hierarchy,
    typeof(hierarchy) AS type
FROM Logins
WHERE typeof(hierarchy) != 'integer'
   OR hierarchy NOT IN (1, 2, 3, 4, 5);

-- ============================================================================
-- Query 4: Verify Client Users
-- ============================================================================
-- Show all hierarchy=4 (Client) users and their assigned customers
SELECT 
    L.ID,
    L.login_id,
    L.hierarchy,
    L.customer_id,
    C.company AS customer_company,
    C.first_name || ' ' || C.last_name AS customer_name,
    L.is_active
FROM Logins L
LEFT JOIN Customers C ON C.ID = L.customer_id
WHERE L.hierarchy = 4
ORDER BY L.ID;

-- ============================================================================
-- DATA FIXING QUERIES (run only if Query 3 found bad data)
-- ============================================================================

-- Fix string hierarchy values (uncomment if needed)
/*
UPDATE Logins SET hierarchy = 1 WHERE hierarchy = 'GOD';
UPDATE Logins SET hierarchy = 2 WHERE hierarchy IN ('admin', 'administrator');
UPDATE Logins SET hierarchy = 3 WHERE hierarchy IN ('Tech_GCC', 'tech_gcc');
UPDATE Logins SET hierarchy = 4 WHERE hierarchy = 'client';
UPDATE Logins SET hierarchy = 5 WHERE hierarchy = 'client_mngs';

-- Verify fix
SELECT DISTINCT typeof(hierarchy) AS type, COUNT(*) FROM Logins GROUP BY type;
*/

-- ============================================================================
-- CREATE TEST USERS (for testing hierarchy levels)
-- ============================================================================

-- Create test Tech user (hierarchy=3)
/*
INSERT INTO Logins (login_id, password_hash, password_salt, hierarchy, is_active, customer_id)
VALUES ('tech@test.com', 'test123', '', 3, 1, NULL);
*/

-- Create test Client user (hierarchy=4) - MUST assign customer_id
/*
-- First, find a customer ID:
SELECT ID, company FROM Customers LIMIT 5;

-- Then insert with that customer_id:
INSERT INTO Logins (login_id, password_hash, password_salt, hierarchy, is_active, customer_id)
VALUES ('client@test.com', 'test123', '', 4, 1, 1);  -- Replace 1 with actual customer ID
*/

-- ============================================================================
-- TESTING QUERIES
-- ============================================================================

-- Test: Get current_user() data structure
SELECT 
    L.ID AS id,
    L.login_id AS email,
    L.hierarchy,
    CASE 
        WHEN L.hierarchy = 1 THEN 'GOD'
        WHEN L.hierarchy = 2 THEN 'administrator'
        WHEN L.hierarchy = 3 THEN 'tech_gcc'
        WHEN L.hierarchy = 4 THEN 'client'
        WHEN L.hierarchy = 5 THEN 'client_mngs'
    END AS role,
    L.customer_id,
    C.company
FROM Logins L
LEFT JOIN Customers C ON C.ID = L.customer_id
WHERE L.login_id = 'client@test.com';  -- Replace with test user email

-- ============================================================================
-- CLEANUP (remove test users)
-- ============================================================================
/*
DELETE FROM Logins WHERE login_id IN ('tech@test.com', 'client@test.com');
*/
