-- This is the production-safe, flexible version of the schema.
-- It uses JSONB to store any number of measurement variables.

CREATE TABLE IF NOT EXISTS profiles (
    profile_id SERIAL PRIMARY KEY,
    float_id INT NOT NULL,
    profile_time TIMESTAMP NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    UNIQUE(float_id, profile_time, latitude, longitude)
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id SERIAL PRIMARY KEY,
    profile_id INT REFERENCES profiles(profile_id) ON DELETE CASCADE,
    depth REAL,
    -- This single JSONB column will store all measurement data for a given depth.
    -- e.g., {"PSAL": 34.5, "TEMP": 12.3, "PSAL_ERR": 0.116}
    data JSONB
);