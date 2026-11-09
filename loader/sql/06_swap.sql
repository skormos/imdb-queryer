-- Swap the freshly loaded schema in. Everything refers to `imdb` by name
-- (search_path, your queries), so after the rename they see the new data.
BEGIN;
DROP SCHEMA IF EXISTS imdb_old CASCADE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'imdb') THEN
        ALTER SCHEMA imdb RENAME TO imdb_old;
    END IF;
END
$$;
ALTER SCHEMA imdb_new RENAME TO imdb;
COMMIT;

-- Outside the swap transaction: this waits for any open query on the old tables to finish.
DROP SCHEMA imdb_old CASCADE;
