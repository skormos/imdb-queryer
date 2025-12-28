#!/usr/bin/env bash

set -e

echo "Deleting orphan episodes by series..."

psql -v ON_ERROR_STOP=1 --username "imdbreadwrite" --dbname "imdbdb" <<-EOSQL
  DELETE FROM imdb.episode e
  WHERE NOT EXISTS (
      SELECT 1
      FROM imdb.title t
      WHERE t.id = e.series_id
  );
EOSQL

echo "Deleting remaining orphan episodes by title..."

psql -v ON_ERROR_STOP=1 --username "imdbreadwrite" --dbname "imdbdb" <<-EOSQL
  DELETE FROM imdb.episode e
  WHERE NOT EXISTS (
      SELECT 1
      FROM imdb.title t
      WHERE t.id = e.id
  );
EOSQL

echo "Deleting orphan principals by title..."

psql -v ON_ERROR_STOP=1 --username "imdbreadwrite" --dbname "imdbdb" <<-EOSQL
  DELETE FROM imdb.principal c
  WHERE NOT EXISTS (
      SELECT 1
      FROM imdb.title t
      WHERE t.id = c.titleid
  );
EOSQL

echo "Deleting orphan principals by person..."

psql -v ON_ERROR_STOP=1 --username "imdbreadwrite" --dbname "imdbdb" <<-EOSQL
  DELETE FROM imdb.principal c
  WHERE NOT EXISTS (
      SELECT 1
      FROM imdb.person p
      WHERE p.id = c.personid
  );
EOSQL

echo "Deleting orphan ratings by title..."

psql -v ON_ERROR_STOP=1 --username "imdbreadwrite" --dbname "imdbdb" <<-EOSQL
  DELETE FROM imdb.rating r
  WHERE NOT EXISTS (
      SELECT 1
      FROM imdb.title t
      WHERE t.id = r.titleid
  );
EOSQL


psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  ALTER TABLE imdb.episode
  ADD CONSTRAINT fk_episode_title_id
      FOREIGN KEY (id) REFERENCES imdb.title(id)
      ON DELETE CASCADE
      ON UPDATE CASCADE,
  ADD CONSTRAINT fk_series_title_id
      FOREIGN KEY (series_id) REFERENCES imdb.title(id)
      ON DELETE RESTRICT
      ON UPDATE CASCADE;

  ALTER TABLE imdb.principal
    ADD PRIMARY KEY (titleId, ordering),
    ADD CONSTRAINT fk_title FOREIGN KEY (titleId) REFERENCES imdb.title (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT fk_person FOREIGN KEY (personId) REFERENCES imdb.person (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;

  ALTER TABLE imdb.rating
    ADD CONSTRAINT fk_title FOREIGN KEY (titleId) REFERENCES imdb.title (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;

    -- Create indexes for search performance
  CREATE INDEX idx_title_primary_title ON imdb.title(primary_title);
  CREATE INDEX idx_title_original_title ON imdb.title(original_title);
  CREATE INDEX idx_person_name ON imdb.person(name);
EOSQL

