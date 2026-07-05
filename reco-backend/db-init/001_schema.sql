    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255),
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_users_email ON users(email);

    CREATE TABLE artists (
        id SERIAL PRIMARY KEY,
        artist_uri VARCHAR(255) UNIQUE NOT NULL,
        artist_name VARCHAR(255) NOT NULL
    );

    CREATE TABLE albums (
        id SERIAL PRIMARY KEY,
        album_uri VARCHAR(255) UNIQUE NOT NULL,
        album_name VARCHAR(255) NOT NULL
    );

    CREATE TABLE tracks (
        id SERIAL PRIMARY KEY,
        track_uri VARCHAR(255) UNIQUE NOT NULL,
        track_name VARCHAR(255) NOT NULL,
        artist_id INT REFERENCES artists(id) ON DELETE SET NULL,
        album_id INT REFERENCES albums(id) ON DELETE SET NULL,
        duration_ms INT
    );

    CREATE TABLE track_frequency (
        id SERIAL PRIMARY KEY,
        track_uri VARCHAR(255) UNIQUE NOT NULL,   -- định danh bài hát
        track_name VARCHAR(255) NOT NULL,         -- tên bài hát
        artist_name VARCHAR(255) NOT NULL,        -- tên nghệ sĩ
        artist_uri VARCHAR(255) NOT NULL,         -- định danh nghệ sĩ
        frequency INT NOT NULL DEFAULT 0,         -- số lần xuất hiện trong playlists
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    CREATE TABLE playlists (
        id SERIAL PRIMARY KEY,
        pid VARCHAR(255) UNIQUE NOT NULL,
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        name VARCHAR(255),
        num_tracks INT,
        num_samples INT,
        num_holdouts INT,
        actual_track_count INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE playlist_tracks (
        id SERIAL PRIMARY KEY,
        playlist_id INT REFERENCES playlists(id) ON DELETE CASCADE,
        track_id INT REFERENCES tracks(id) ON DELETE CASCADE,
        pos INT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- FP-Growth itemsets (nếu cần)
    CREATE TABLE fp_itemsets_tracks (
        id SERIAL PRIMARY KEY,
        itemsets TEXT[],   -- list track_uri
        support NUMERIC,
        size INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE fp_itemsets_artists (
        id SERIAL PRIMARY KEY,
        itemsets TEXT[],   -- list artist_uri
        support NUMERIC,
        size INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- FP-Growth rules (track-level)
    CREATE TABLE fp_rules_tracks (
        id SERIAL PRIMARY KEY,
        antecedents TEXT[],          -- track_uri
        consequents TEXT[],          -- track_uri
        antecedent_names TEXT[],
        consequent_names TEXT[],
        support NUMERIC,
        confidence NUMERIC,
        lift NUMERIC,
        conviction NUMERIC,
        antecedent_len INT,
        consequent_len INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- FP-Growth rules (artist-level)
    CREATE TABLE fp_rules_artists (
        id SERIAL PRIMARY KEY,
        antecedents TEXT[],          -- artist_uri
        consequents TEXT[],          -- artist_uri
        antecedent_names TEXT[],
        consequent_names TEXT[],
        support NUMERIC,
        confidence NUMERIC,
        lift NUMERIC,
        conviction NUMERIC,
        antecedent_len INT,
        consequent_len INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );