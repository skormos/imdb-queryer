ALTER TABLE imdb_new.episode
    ADD CONSTRAINT fk_episode_title_id
        FOREIGN KEY (id) REFERENCES imdb_new.title (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT fk_series_title_id
        FOREIGN KEY (series_id) REFERENCES imdb_new.title (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;

ALTER TABLE imdb_new.principal
    ADD PRIMARY KEY (titleId, ordering),
    ADD CONSTRAINT fk_title FOREIGN KEY (titleId) REFERENCES imdb_new.title (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT fk_person FOREIGN KEY (personId) REFERENCES imdb_new.person (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;

ALTER TABLE imdb_new.rating
    ADD CONSTRAINT fk_title FOREIGN KEY (titleId) REFERENCES imdb_new.title (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;

-- Search indexes
CREATE INDEX idx_title_primary_title ON imdb_new.title (primary_title);
CREATE INDEX idx_title_original_title ON imdb_new.title (original_title);
CREATE INDEX idx_person_name ON imdb_new.person (name);

-- Foreign-key lookups in the other direction ("everything person X was in", "all episodes of series Y")
CREATE INDEX idx_principal_person_id ON imdb_new.principal (personId);
CREATE INDEX idx_episode_series_id ON imdb_new.episode (series_id);
