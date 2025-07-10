-- Schema for tracking deals and monitoring sessions

CREATE TABLE deals (
    hash TEXT PRIMARY KEY,
    source TEXT,
    merchant TEXT,
    face_value NUMERIC,
    price NUMERIC,
    discount_percent NUMERIC,
    url TEXT,
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    appearances INTEGER
);

CREATE TABLE monitoring_sessions (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMPTZ,
    duration_minutes NUMERIC,
    check_interval_minutes NUMERIC
);

CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES monitoring_sessions(session_id),
    "timestamp" TIMESTAMPTZ,
    check_number INTEGER
);

CREATE TABLE snapshot_deals (
    snapshot_id INTEGER REFERENCES snapshots(id),
    deal_hash TEXT REFERENCES deals(hash),
    PRIMARY KEY (snapshot_id, deal_hash)
);
