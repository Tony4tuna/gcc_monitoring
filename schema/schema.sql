PRAGMA foreign_keys = ON;

-- =========================
-- Core: Customers & Locations (from your PDFs)
-- =========================

CREATE TABLE IF NOT EXISTS Customers (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name      TEXT,
  last_name       TEXT,
  company         TEXT,
  email           TEXT,
  phone1          TEXT,
  phone2          TEXT,
  mobile          TEXT,
  fax             TEXT,
  extension1      TEXT,
  extension2      TEXT,
  address1        TEXT,
  address2        TEXT,
  city            TEXT,
  state           TEXT,
  zip             TEXT,
  website         TEXT,
  notes           TEXT,
  extended_notes  TEXT,
  idstring        TEXT,
  csr             TEXT,
  referral        TEXT,
  credit_status   TEXT,
  flag_and_lock   INTEGER DEFAULT 0,
  created         TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS PropertyLocations (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id     INTEGER NOT NULL,
  address1        TEXT,
  address2        TEXT,
  city            TEXT,
  state           TEXT,
  zip             TEXT,
  contact         TEXT,
  job_phone       TEXT,
  job_phone2      TEXT,
  notes           TEXT,
  extended_notes  TEXT,
  residential     INTEGER DEFAULT 0,
  commercial      INTEGER DEFAULT 0,
  custid          TEXT,
  date_created    TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(customer_id) REFERENCES Customers(ID) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_locations_customer_id ON PropertyLocations(customer_id);

-- =========================
-- Auth: External login table (separate from Customers)
-- =========================
-- One customer can have multiple login accounts (owner, manager, tech, etc).
-- Optionally tie a login to a specific location.
CREATE TABLE IF NOT EXISTS Logins (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  login_id        TEXT NOT NULL UNIQUE,             -- username or email
  password_hash   TEXT NOT NULL,                    -- PBKDF2 hash
  password_salt   TEXT NOT NULL,                    -- per-user salt
  hierarchy       TEXT NOT NULL,                    -- GOD, ADMIN, CSR, CLIENT, TECH, VIEWER, etc
  customer_id     INTEGER,                          -- nullable for GOD/global users
  location_id     INTEGER,                          -- nullable
  is_active       INTEGER DEFAULT 1,
  created         TEXT DEFAULT (datetime('now')),
  last_login      TEXT,
  FOREIGN KEY(customer_id) REFERENCES Customers(ID) ON DELETE SET NULL,
  FOREIGN KEY(location_id) REFERENCES PropertyLocations(ID) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_logins_customer_id ON Logins(customer_id);
CREATE INDEX IF NOT EXISTS idx_logins_location_id ON Logins(location_id);

-- =========================
-- Equipment master table (Unit ID fields.pdf)
-- =========================
CREATE TABLE IF NOT EXISTS Units (
  unit_id         INTEGER PRIMARY KEY,              -- your 5-digit Unit_ID
  location_id     INTEGER NOT NULL,                 -- link to PropertyLocations.ID
  make            TEXT,
  model           TEXT,
  serial          TEXT,
  note_id         INTEGER,                          -- optional link to Notes
  inst_date       TEXT,                             -- store as text, ex: YYYYMMDD or YYYY-MM-DD
  created         TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(location_id) REFERENCES PropertyLocations(ID) ON DELETE CASCADE,
  FOREIGN KEY(note_id) REFERENCES Notes(ID) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_units_location_id ON Units(location_id);

-- Optional: Notes table (because your Unit table references a "note index")
CREATE TABLE IF NOT EXISTS Notes (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  title           TEXT,
  body            TEXT,
  created         TEXT DEFAULT (datetime('now'))
);

-- =========================
-- Telemetry / parameters table (equipment parameters to retrieved.pdf)
-- Comprehensive HVAC/R monitoring parameters
-- Treat as TEXT; cast to REAL/INT in queries when needed.
-- =========================
CREATE TABLE IF NOT EXISTS UnitReadings (
  reading_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  unit_id         INTEGER NOT NULL,
  ts              TEXT DEFAULT (datetime('now')),   -- server timestamp

  -- ===== TEMPERATURE PARAMETERS (°F or °C) =====
  i_temp          TEXT,                              -- Indoor/Return air temperature
  o_temp          TEXT,                              -- Outdoor air temperature
  supply_temp     TEXT,                              -- Supply air temperature
  return_temp     TEXT,                              -- Return air temperature (same as i_temp?)
  delta_t         TEXT,                              -- Delta T (temperature differential)
  
  -- ===== ELECTRICAL PARAMETERS =====
  v_1             TEXT,                              -- Voltage phase 1 (VAC)
  v_2             TEXT,                              -- Voltage phase 2 (VAC) [added]
  v_3             TEXT,                              -- Voltage phase 3 (VAC) [added]
  a_1             TEXT,                              -- Amperage phase 1 (AMP)
  a_2             TEXT,                              -- Amperage phase 2 (AMP) [added]
  a_3             TEXT,                              -- Amperage phase 3 (AMP) [added]
  id_l1           TEXT,                              -- Input data line 1
  id_l2           TEXT,                              -- Input data line 2
  
  -- ===== HUMIDITY & ENVIRONMENTAL =====
  h_1             TEXT,                              -- Humidity sensor 1 (%)
  h_2             TEXT,                              -- Humidity sensor 2 (%)
  rh              TEXT,                              -- Relative humidity (%)
  
  -- ===== PRESSURE PARAMETERS =====
  l_v             TEXT,                              -- Line voltage / Suction pressure
  discharge_psi   TEXT,                              -- Discharge pressure (PSI) [added]
  suction_psi     TEXT,                              -- Suction pressure (PSI) [added]
  
  -- ===== CAPACITOR & ELECTRICAL COMPONENTS =====
  c_1             TEXT,                              -- Capacitor 1 (µF or status)
  c_2             TEXT,                              -- Capacitor 2 (µF or status)
  c_3             TEXT,                              -- Capacitor 3 (µF or status)
  
  -- ===== TIME & OPERATIONAL METRICS =====
  time_1          TEXT,                              -- Time parameter 1 (runtime hours)
  time_2          TEXT,                              -- Time parameter 2
  date_1          TEXT,                              -- Date parameter 1
  runtime_hours   TEXT,                              -- Total runtime hours (cumulative) [added]
  compressor_runtime_hours TEXT,                     -- Compressor specific runtime [added]
  
  -- ===== SETPOINTS & CONTROL =====
  sp_1            TEXT,                              -- Setpoint 1 (cooling setpoint, °F)
  sp_2            TEXT,                              -- Setpoint 2 (heating setpoint, °F)
  sp_deadband     TEXT,                              -- Setpoint deadband [added]
  
  -- ===== FAN & MOTOR PARAMETERS =====
  rpm_1           TEXT,                              -- Fan/motor 1 speed (RPM or %)
  rpm_2           TEXT,                              -- Fan/motor 2 speed (RPM or %)
  fan_speed_percent TEXT,                            -- Fan speed (0-100%) [added]
  
  -- ===== EXPANSION VALVE & REFRIGERANT =====
  ev_1            TEXT,                              -- Expansion valve 1 (%)
  ev_2            TEXT,                              -- Expansion valve 2 (%)
  superheat       TEXT,                              -- Superheat (°F) [added]
  subcooling      TEXT,                              -- Subcooling (°F) [added]
  
  -- ===== COMPRESSOR & COMPONENT STATUS =====
  cn_1            TEXT,                              -- Compressor number 1 / status
  cn_2            TEXT,                              -- Compressor number 2 / status
  compressor_amps TEXT,                              -- Compressor amperage [added]
  
  -- ===== OPERATIONAL MODE & STATUS =====
  mode            TEXT,                              -- Operating mode (Off/Idle/Cooling/Heating/Economizer/Fault)
  unit_status     TEXT,                              -- Unit status (Online/Offline/Error) [added]
  fault_code      TEXT,                              -- Fault/error code if any [added]
  
  -- ===== ACCUMULATOR & SYSTEM HEALTH =====
  accumulator_level TEXT,                            -- Accumulator charge level [added]
  oil_pressure    TEXT,                              -- Oil pressure (PSI) [added]
  
  -- ===== DEMAND & LOAD =====
  demand_percent  TEXT,                              -- System demand (%) [added]
  load_percent    TEXT,                              -- Current load (%) [added]
  
  -- ===== ALARMS & DIAGNOSTICS =====
  alarm_status    TEXT,                              -- Alarm status (None/Active/Cleared) [added]
  alert_message   TEXT,                              -- Alert message or description [added]

  FOREIGN KEY(unit_id) REFERENCES Units(unit_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_readings_unit_ts ON UnitReadings(unit_id, ts);
CREATE INDEX IF NOT EXISTS idx_readings_unit_mode ON UnitReadings(unit_id, mode);
CREATE INDEX IF NOT EXISTS idx_readings_fault ON UnitReadings(fault_code) WHERE fault_code IS NOT NULL;

-- =========================
-- Service calls & reports (so the app can do real things)
-- =========================
CREATE TABLE IF NOT EXISTS ServiceCalls (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id     INTEGER NOT NULL,
  location_id     INTEGER,
  unit_id         INTEGER,
  title           TEXT,
  description     TEXT,
  materials_services TEXT,
  labor_description TEXT,
  priority        TEXT DEFAULT 'Normal',            -- Low/Normal/High/Emergency
  status          TEXT DEFAULT 'Open',              -- Open/In Progress/Closed
  requested_by_login_id INTEGER,
  created         TEXT DEFAULT (datetime('now')),
  closed          TEXT,
  FOREIGN KEY(customer_id) REFERENCES Customers(ID) ON DELETE CASCADE,
  FOREIGN KEY(location_id) REFERENCES PropertyLocations(ID) ON DELETE SET NULL,
  FOREIGN KEY(unit_id) REFERENCES Units(unit_id) ON DELETE SET NULL,
  FOREIGN KEY(requested_by_login_id) REFERENCES Logins(ID) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_servicecalls_status ON ServiceCalls(status);

CREATE TABLE IF NOT EXISTS Reports (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id     INTEGER NOT NULL,
  location_id     INTEGER,
  unit_id         INTEGER,
  report_type     TEXT,                              -- temperature_history, alarms, maintenance, etc
  params_json     TEXT,                              -- store request parameters as JSON text
  status          TEXT DEFAULT 'Queued',              -- Queued/Running/Done/Failed
  created         TEXT DEFAULT (datetime('now')),
  completed       TEXT,
  output_path     TEXT,
  requested_by_login_id INTEGER,
  FOREIGN KEY(customer_id) REFERENCES Customers(ID) ON DELETE CASCADE,
  FOREIGN KEY(location_id) REFERENCES PropertyLocations(ID) ON DELETE SET NULL,
  FOREIGN KEY(unit_id) REFERENCES Units(unit_id) ON DELETE SET NULL,
  FOREIGN KEY(requested_by_login_id) REFERENCES Logins(ID) ON DELETE SET NULL
);
