#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  CREATE TABLE imdb.title
  (
      id              TEXT            PRIMARY KEY,
      title_type      imdb.titleType  NOT NULL,
      primary_title   TEXT            NOT NULL,
      original_title  TEXT            NOT NULL,
      start_year      INT,
      end_year        INT,
      runtime_minutes INT,
      genres          imdb.genre[]    NOT NULL
  );

  CREATE TABLE imdb.episode
  (
      id        TEXT PRIMARY KEY,
      series_id TEXT NOT NULL,
      season    INT,
      episode   INT
  );

  CREATE TABLE imdb.person
  (
      id   TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      birthYear INT,
      deathYear INT,
      primaryProfessions TEXT
  );

  CREATE TABLE imdb.principal
  (
      titleId   TEXT NOT NULL,
      ordering  INT  NOT NULL,
      personId  TEXT NOT NULL,
      category  TEXT NOT NULL,
      job       TEXT,
      character TEXT
  );

  CREATE TABLE imdb.rating
  (
    titleId TEXT PRIMARY KEY,
    averageRating FLOAT,
    numVotes INT
  );
EOSQL
