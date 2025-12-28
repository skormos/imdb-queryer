#!/usr/bin/env bash

set -e

echo "Starting database data initialization..."

echo "Writing title.basics..."

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  \copy imdb.title from '/src/parsed/title.basics.tsv' with (format CSV, delimiter E'\t', header false, QUOTE E'\b', NULL '\N');
EOSQL

echo "Done writing title.basics..."

echo "Writing title.episode..."

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  \copy imdb.episode from '/src/parsed/title.episode.tsv' with (format CSV, delimiter E'\t', header false, QUOTE E'\b', NULL '\N');
EOSQL

echo "Done writing title.episode..."

echo "Writing name.basics..."

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  \copy imdb.person from '/src/parsed/name.basics.tsv' with (format CSV, delimiter E'\t', header false, QUOTE E'\b', NULL '\N');
EOSQL

echo "Done writing name.basics..."

echo "Writing title.principals..."

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  \copy imdb.principal from '/src/parsed/title.principals.tsv' with (format CSV, delimiter E'\t', header false, QUOTE E'\b', NULL '\N');
EOSQL

echo "Done writing title.principals..."

echo "Writing title.ratings..."

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  \copy imdb.rating from '/src/parsed/title.ratings.tsv' with (format CSV, delimiter E'\t', header false, QUOTE E'\b', NULL '\N');
EOSQL

echo "Done writing title.ratings..."

echo "Cleaning up data for constraints..."

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL

EOSQL
