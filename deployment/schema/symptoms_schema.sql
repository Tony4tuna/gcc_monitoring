-- Symptoms Table (Client-Facing Issue Descriptions)
-- Used only by clients to describe what they experience

CREATE TABLE IF NOT EXISTS Symptoms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    description     TEXT,
    category        TEXT,           -- e.g., "Cooling", "Heating", "Noise", "Power"
    is_active       INTEGER DEFAULT 1,
    display_order   INTEGER DEFAULT 0,
    created         TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_symptoms_active ON Symptoms(is_active);
CREATE INDEX IF NOT EXISTS idx_symptoms_category ON Symptoms(category);

-- Add symptom_id to ServiceCalls (nullable for admin/tech tickets)
-- This links client tickets to the symptom they selected
ALTER TABLE ServiceCalls ADD COLUMN symptom_id INTEGER REFERENCES Symptoms(id);
CREATE INDEX IF NOT EXISTS idx_servicecalls_symptom ON ServiceCalls(symptom_id);

-- Insert default symptoms
INSERT OR IGNORE INTO Symptoms (code, title, description, category, display_order) VALUES
    ('NOT_COOLING', 'Not cooling properly', 'The unit is running but the space is not getting cool enough', 'Cooling', 1),
    ('NOT_HEATING', 'Not heating properly', 'The unit is running but the space is not getting warm enough', 'Heating', 2),
    ('NO_POWER', 'Unit not turning on', 'The unit does not start or respond when turned on', 'Power', 3),
    ('NOISE', 'Making unusual noise', 'The unit is making loud, strange, or grinding noises', 'Noise', 4),
    ('LEAK', 'Water leaking', 'Water is dripping or pooling around the unit', 'Leak', 5),
    ('ICE', 'Ice forming on unit', 'Ice or frost is visible on the unit or lines', 'Cooling', 6),
    ('SMELL', 'Bad smell or odor', 'The unit is producing an unusual or unpleasant odor', 'Air Quality', 7),
    ('TOO_COLD', 'Space too cold', 'The temperature is lower than desired even at higher settings', 'Cooling', 8),
    ('TOO_HOT', 'Space too hot', 'The temperature is higher than desired even at lower settings', 'Heating', 9),
    ('SHORT_CYCLE', 'Turns on and off frequently', 'The unit starts and stops repeatedly in short cycles', 'Operation', 10),
    ('NO_AIR', 'No air flow', 'Little or no air is coming from the vents', 'Air Flow', 11),
    ('OTHER', 'Other issue', 'Issue not listed above - will describe in notes', 'Other', 99);
