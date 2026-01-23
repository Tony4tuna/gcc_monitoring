-- Settings/Configuration Schema
-- Extends the existing schema with additional configuration tables

-- =========================
-- Company Profile Table
-- =========================
CREATE TABLE IF NOT EXISTS CompanyProfile (
  id                INTEGER PRIMARY KEY CHECK (id = 1),
  company_name      TEXT,
  logo_path         TEXT,
  address1          TEXT,
  address2          TEXT,
  city              TEXT,
  state             TEXT,
  zip               TEXT,
  country           TEXT,
  phone             TEXT,
  fax               TEXT,
  email             TEXT,
  website           TEXT,
  tax_id            TEXT,
  business_license  TEXT,
  industry          TEXT,
  employee_count    TEXT,
  established_year  TEXT,
  description       TEXT,
  updated           TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Employee Profile Table
-- =========================
CREATE TABLE IF NOT EXISTS EmployeeProfile (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id       TEXT UNIQUE NOT NULL,
  first_name        TEXT NOT NULL,
  last_name         TEXT NOT NULL,
  photo_path        TEXT,
  department        TEXT,
  position          TEXT,
  email             TEXT,
  phone             TEXT,
  mobile            TEXT,
  address1          TEXT,
  address2          TEXT,
  city              TEXT,
  state             TEXT,
  zip               TEXT,
  start_date        TEXT,
  end_date          TEXT,
  status            TEXT DEFAULT 'Active',  -- Active/Inactive/Leave/Terminated
  emergency_contact TEXT,
  emergency_phone   TEXT,
  notes             TEXT,
  created           TEXT DEFAULT (datetime('now')),
  updated           TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_employee_status ON EmployeeProfile(status);
CREATE INDEX IF NOT EXISTS idx_employee_email ON EmployeeProfile(email);

-- =========================
-- Email Template Table
-- =========================
CREATE TABLE IF NOT EXISTS EmailTemplate (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  template_name     TEXT UNIQUE NOT NULL,
  template_type     TEXT NOT NULL,  -- alert, reminder, report, notification, etc
  subject           TEXT,
  body              TEXT,
  cc_list           TEXT,
  bcc_list          TEXT,
  is_active         INTEGER DEFAULT 1,
  created           TEXT DEFAULT (datetime('now')),
  updated           TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Service Call Settings Table
-- =========================
CREATE TABLE IF NOT EXISTS ServiceCallSettings (
  id                INTEGER PRIMARY KEY CHECK (id = 1),
  default_priority  TEXT DEFAULT 'Normal',  -- Low/Normal/High/Emergency
  auto_assign        INTEGER DEFAULT 0,
  assignment_method TEXT,                   -- round_robin, by_location, manual, etc
  priority_colors   TEXT,                   -- JSON: {"Low":"#green","Normal":"#blue",...}
  status_workflow   TEXT,                   -- JSON: list of valid status transitions
  notification_on_create INTEGER DEFAULT 1,
  notification_on_close INTEGER DEFAULT 1,
  sla_hours_low     INTEGER DEFAULT 72,
  sla_hours_normal  INTEGER DEFAULT 48,
  sla_hours_high    INTEGER DEFAULT 24,
  sla_hours_emergency INTEGER DEFAULT 4,
  updated           TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Ticket Sequence Table
-- =========================
CREATE TABLE IF NOT EXISTS TicketSequenceSettings (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  sequence_type     TEXT UNIQUE NOT NULL,     -- service, report, work_order, etc
  prefix            TEXT,                      -- e.g., "SVR", "RPT"
  starting_number   INTEGER DEFAULT 1000,
  current_number    INTEGER DEFAULT 1000,
  increment_by      INTEGER DEFAULT 1,
  format_pattern    TEXT,                      -- e.g., "{prefix}-{year}{month}-{seq:05d}"
  reset_period      TEXT,                      -- none, daily, monthly, yearly
  last_reset        TEXT,
  is_active         INTEGER DEFAULT 1,
  created           TEXT DEFAULT (datetime('now')),
  updated           TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ticket_sequence_type ON TicketSequenceSettings(sequence_type);

-- =========================
-- System Settings Table
-- =========================
CREATE TABLE IF NOT EXISTS SystemSettings (
  id                INTEGER PRIMARY KEY CHECK (id = 1),
  app_name          TEXT DEFAULT 'GCC Monitoring',
  app_version       TEXT,
  theme             TEXT DEFAULT 'dark',       -- light, dark, auto
  language          TEXT DEFAULT 'en',
  timezone          TEXT DEFAULT 'UTC',
  date_format       TEXT DEFAULT 'YYYY-MM-DD',
  time_format       TEXT DEFAULT '24h',        -- 24h, 12h
  log_retention_days INTEGER DEFAULT 90,
  max_login_attempts INTEGER DEFAULT 5,
  session_timeout_minutes INTEGER DEFAULT 60,
  enable_two_factor INTEGER DEFAULT 0,
  enable_audit_log  INTEGER DEFAULT 1,
  maintenance_mode  INTEGER DEFAULT 0,
  updated           TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Notification Settings Table
-- =========================
CREATE TABLE IF NOT EXISTS NotificationSettings (
  id                INTEGER PRIMARY KEY CHECK (id = 1),
  email_enabled     INTEGER DEFAULT 1,
  sms_enabled       INTEGER DEFAULT 0,
  push_enabled      INTEGER DEFAULT 0,
  daily_digest      INTEGER DEFAULT 1,
  alert_on_critical INTEGER DEFAULT 1,
  alert_on_warning  INTEGER DEFAULT 1,
  alert_on_info     INTEGER DEFAULT 0,
  default_recipient TEXT,                     -- email or phone
  updated           TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Alert Threshold Settings Table
-- =========================
CREATE TABLE IF NOT EXISTS AlertThresholds (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  threshold_name    TEXT UNIQUE NOT NULL,
  parameter         TEXT NOT NULL,             -- temp, pressure, voltage, etc
  min_value         REAL,
  max_value         REAL,
  warning_level     REAL,
  critical_level    REAL,
  unit              TEXT,                      -- F, PSI, VAC, etc
  enabled           INTEGER DEFAULT 1,
  send_alert        INTEGER DEFAULT 1,
  created           TEXT DEFAULT (datetime('now')),
  updated           TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Maintenance Schedule Table
-- =========================
CREATE TABLE IF NOT EXISTS MaintenanceSchedule (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  task_name         TEXT NOT NULL,
  task_type         TEXT,                      -- preventive, corrective, predictive
  frequency_days    INTEGER,
  description       TEXT,
  assigned_to       INTEGER,                   -- Employee ID
  priority          TEXT DEFAULT 'Normal',
  estimated_hours   REAL,
  is_active         INTEGER DEFAULT 1,
  created           TEXT DEFAULT (datetime('now')),
  updated           TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(assigned_to) REFERENCES EmployeeProfile(id)
);
