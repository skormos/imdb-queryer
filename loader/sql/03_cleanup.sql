-- The IMDB files reference titles and people that are not in the other files
-- (including adult titles, which the parser drops). Remove those rows so the
-- foreign keys in 04_constraints.sql can be added.

\echo 'Deleting episodes whose series is missing...'
DELETE FROM imdb_new.episode e
WHERE NOT EXISTS (SELECT 1 FROM imdb_new.title t WHERE t.id = e.series_id);

\echo 'Deleting episodes whose title is missing...'
DELETE FROM imdb_new.episode e
WHERE NOT EXISTS (SELECT 1 FROM imdb_new.title t WHERE t.id = e.id);

\echo 'Deleting principals whose title is missing...'
DELETE FROM imdb_new.principal p
WHERE NOT EXISTS (SELECT 1 FROM imdb_new.title t WHERE t.id = p.titleId);

\echo 'Deleting principals whose person is missing...'
DELETE FROM imdb_new.principal p
WHERE NOT EXISTS (SELECT 1 FROM imdb_new.person n WHERE n.id = p.personId);

\echo 'Deleting ratings whose title is missing...'
DELETE FROM imdb_new.rating r
WHERE NOT EXISTS (SELECT 1 FROM imdb_new.title t WHERE t.id = r.titleId);
