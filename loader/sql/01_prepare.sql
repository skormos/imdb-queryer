-- Start from a clean staging schema (a previous failed load may have left one behind).
DROP SCHEMA IF EXISTS imdb_new CASCADE;
CREATE SCHEMA imdb_new AUTHORIZATION imdbowner;

-- Default privileges are tied to the schema itself, so set them on the new schema.
-- They move with it when it is renamed to imdb, and cover tables you create later.
ALTER DEFAULT PRIVILEGES IN SCHEMA imdb_new GRANT INSERT, SELECT, UPDATE, DELETE ON TABLES TO imdbreadwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA imdb_new GRANT USAGE ON SEQUENCES TO imdbreadwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA imdb_new GRANT SELECT ON TABLES TO imdbreadonly;
