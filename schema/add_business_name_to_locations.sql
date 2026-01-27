-- Add business_name field for commercial properties (LLC names)
-- For properties where commercial=1, this stores the business/LLC name

ALTER TABLE PropertyLocations ADD COLUMN business_name TEXT DEFAULT '';

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_locations_business_name ON PropertyLocations(business_name);
