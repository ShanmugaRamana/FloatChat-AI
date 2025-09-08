-- This schema is designed for automated, dynamic data ingestion.
CREATE TABLE IF NOT EXISTS float_profiles (
    id SERIAL PRIMARY KEY,
    -- Made nullable to support both gridded data (no ID) and float data (has ID).
    float_wmo_id TEXT,
    "timestamp" TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    measurements JSONB,
    -- This constraint helps prevent inserting the exact same profile twice.
    UNIQUE(float_wmo_id, "timestamp")
);

-- This table tracks the state of processed files. No changes needed here.
CREATE TABLE IF NOT EXISTS pipeline_tracker (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    file_hash TEXT,
    status TEXT NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);