-- Service Tickets Schema

CREATE TABLE IF NOT EXISTS ServiceTickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    location_id INTEGER,
    unit_id INTEGER,
    
    -- Ticket details
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'on_hold', 'resolved', 'closed', 'cancelled')),
    category TEXT,
    
    -- Assignment
    assigned_to INTEGER,
    assigned_by INTEGER,
    
    -- Scheduling
    scheduled_date TEXT,
    completed_date TEXT,
    
    -- Tracking
    created_by INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    -- Additional info
    notes TEXT,
    resolution TEXT,
    
    FOREIGN KEY (customer_id) REFERENCES Customers(ID) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES PropertyLocations(ID) ON DELETE SET NULL,
    FOREIGN KEY (unit_id) REFERENCES Equipment(unit_id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to) REFERENCES EmployeeProfile(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_by) REFERENCES EmployeeProfile(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES EmployeeProfile(employee_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tickets_customer ON ServiceTickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_location ON ServiceTickets(location_id);
CREATE INDEX IF NOT EXISTS idx_tickets_unit ON ServiceTickets(unit_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON ServiceTickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON ServiceTickets(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tickets_created ON ServiceTickets(created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_number ON ServiceTickets(ticket_number);
