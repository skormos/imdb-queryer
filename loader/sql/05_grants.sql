GRANT USAGE ON SCHEMA imdb_new TO imdbreadwrite, imdbreadonly;
GRANT INSERT, SELECT, UPDATE, DELETE ON ALL TABLES IN SCHEMA imdb_new TO imdbreadwrite;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA imdb_new TO imdbreadwrite;
GRANT SELECT ON ALL TABLES IN SCHEMA imdb_new TO imdbreadonly;
