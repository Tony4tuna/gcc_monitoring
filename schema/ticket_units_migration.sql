-- Migration: Add Multi-Unit Support to Tickets
-- Date: 2026-01-27
-- Purpose: Allow 1-4 units per service ticket

-- Junction table to link tickets to multiple units
CREATE TABLE IF NOT EXISTS TicketUnits (
    ticket_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    sequence_order INTEGER DEFAULT 1,  -- 1-4 for display order
    PRIMARY KEY (ticket_id, unit_id),
    FOREIGN KEY (ticket_id) REFERENCES ServiceCalls(ID) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES Units(unit_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ticket_units_ticket ON TicketUnits(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_units_unit ON TicketUnits(unit_id);

-- Note: Existing ServiceCalls.unit_id column will remain for backward compatibility
-- New tickets will use TicketUnits table for multi-unit support
