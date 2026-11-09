#!/usr/bin/env bash

# Creates the (empty) imdb schema. The tables are created and filled by the
# loader service (loader/load.sh), which can be re-run at any time to refresh.

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "imdbdb" <<-EOSQL
  CREATE SCHEMA imdb AUTHORIZATION imdbowner;
EOSQL

# Set search_path for the database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "imdbdb" <<-EOSQL
  ALTER DATABASE imdbdb SET search_path TO imdb, public;
EOSQL

# Set search_path for specific users (optional but recommended)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "imdbdb" <<-EOSQL
  ALTER ROLE imdbowner SET search_path TO imdb, public;
  ALTER ROLE imdbreadwrite SET search_path TO imdb, public;
  ALTER ROLE imdbreadonly SET search_path TO imdb, public;
EOSQL
