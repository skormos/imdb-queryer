#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
  CREATE USER imdbowner WITH ENCRYPTED PASSWORD 'ownerpass';
  CREATE USER imdbreadwrite WITH ENCRYPTED PASSWORD 'readwritepass';
  CREATE USER imdbreadonly WITH ENCRYPTED PASSWORD 'readonlypass';
EOSQL
