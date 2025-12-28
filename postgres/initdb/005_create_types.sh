#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "imdbowner" --dbname "imdbdb" <<-EOSQL
  CREATE TYPE imdb.titleType AS ENUM('movie', 'short', 'tvEpisode', 'tvMiniSeries', 'tvMovie', 'tvPilot', 'tvSeries', 'tvShort', 'tvSpecial', 'video', 'videoGame');
  CREATE TYPE imdb.genre AS ENUM('Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Talk-Show', 'Thriller', 'War', 'Western');
EOSQL
