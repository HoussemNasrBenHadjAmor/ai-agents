#!/bin/sh
set -e

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" <<EOSQL

CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    last_checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO services (
    name,
    status,
    response_time_ms
)
VALUES
    ('api', 'healthy', 42),
    ('dashboard', 'healthy', 71),
    ('worker', 'degraded', 1400),
    ('redis', 'healthy', 4)
ON CONFLICT (name) DO NOTHING;

INSERT INTO incidents (
    service_name,
    severity,
    description
)
VALUES
    (
        'worker',
        'high',
        'Background worker is processing jobs slowly'
    );

DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'agent_reader'
    ) THEN
        CREATE ROLE agent_reader
        LOGIN PASSWORD '${AGENT_DB_READONLY_PASSWORD}';
    END IF;
END
\$\$;

GRANT CONNECT ON DATABASE agent_lab TO agent_reader;

GRANT USAGE ON SCHEMA public TO agent_reader;

GRANT SELECT ON ALL TABLES IN SCHEMA public
TO agent_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO agent_reader;

EOSQL
