#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "imdbdb" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
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
