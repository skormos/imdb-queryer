-- Tables are created without constraints so COPY is fast; 04_constraints.sql adds them.

CREATE TABLE imdb_new.title
(
    id              TEXT                PRIMARY KEY,
    title_type      imdb_new.titleType  NOT NULL,
    primary_title   TEXT                NOT NULL,
    original_title  TEXT                NOT NULL,
    start_year      INT,
    end_year        INT,
    runtime_minutes INT,
    genres          imdb_new.genre[]    NOT NULL
);

CREATE TABLE imdb_new.episode
(
    id        TEXT PRIMARY KEY,
    series_id TEXT NOT NULL,
    season    INT,
    episode   INT
);

CREATE TABLE imdb_new.person
(
    id                 TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    birthYear          INT,
    deathYear          INT,
    primaryProfessions TEXT
);

CREATE TABLE imdb_new.principal
(
    titleId   TEXT NOT NULL,
    ordering  INT  NOT NULL,
    personId  TEXT NOT NULL,
    category  TEXT NOT NULL,
    job       TEXT,
    character TEXT
);

CREATE TABLE imdb_new.rating
(
    titleId       TEXT PRIMARY KEY,
    averageRating FLOAT,
    numVotes      INT
);
