CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

SELECT name, default_version FROM pg_available_extensions
WHERE name IN ('postgis', 'postgis_topology');
