-- ============================================
-- INDEXES OPTIMIZED FOR PERFORMANCE
-- ============================================

-- Unique indexes & Primary lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_uri ON tracks(track_uri);
CREATE UNIQUE INDEX IF NOT EXISTS idx_artists_uri ON artists(artist_uri);
CREATE UNIQUE INDEX IF NOT EXISTS idx_albums_uri ON albums(album_uri);
CREATE UNIQUE INDEX IF NOT EXISTS idx_playlists_pid ON playlists(pid);
CREATE UNIQUE INDEX IF NOT EXISTS idx_track_frequency_uri ON track_frequency(track_uri);

-- Foreign Key indexes (for JOINs)
CREATE INDEX IF NOT EXISTS idx_tracks_artist_id ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_album_id ON tracks(album_id);
CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id);

-- Playlist relations
CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks_track ON playlist_tracks(track_id);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks_pos ON playlist_tracks(playlist_id, pos);

-- Track frequency indexes
CREATE INDEX IF NOT EXISTS idx_track_frequency_artist_uri ON track_frequency(artist_uri);
CREATE INDEX IF NOT EXISTS idx_track_frequency_freq_desc ON track_frequency(frequency DESC);

-- Composite index for artist top tracks query
CREATE INDEX IF NOT EXISTS idx_track_frequency_artist_freq ON track_frequency(artist_uri, frequency DESC);

-- Rules fast retrieval by score
CREATE INDEX IF NOT EXISTS idx_fp_rules_tracks_score ON fp_rules_tracks((confidence * lift) DESC);
CREATE INDEX IF NOT EXISTS idx_fp_rules_artists_score ON fp_rules_artists((confidence * lift) DESC);

-- ============================================
-- GIN INDEXES FOR ARRAY OPERATIONS
-- ============================================

-- GIN indexes for array containment (&&, @>, <@, = operations)
CREATE INDEX IF NOT EXISTS gin_fp_rules_tracks_ante ON fp_rules_tracks USING GIN (antecedents);
CREATE INDEX IF NOT EXISTS gin_fp_rules_tracks_cons ON fp_rules_tracks USING GIN (consequents);
CREATE INDEX IF NOT EXISTS gin_fp_rules_artists_ante ON fp_rules_artists USING GIN (antecedents);
CREATE INDEX IF NOT EXISTS gin_fp_rules_artists_cons ON fp_rules_artists USING GIN (consequents);

-- GIN indexes for FP itemsets (if used)
CREATE INDEX IF NOT EXISTS gin_fp_itemsets_tracks ON fp_itemsets_tracks USING GIN (itemsets);
CREATE INDEX IF NOT EXISTS gin_fp_itemsets_artists ON fp_itemsets_artists USING GIN (itemsets);

-- ============================================
-- FULL-TEXT SEARCH INDEXES (Bước 6)
-- ============================================

-- Add tsvector columns for full-text search
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS search_vector tsvector;
ALTER TABLE artists ADD COLUMN IF NOT EXISTS search_vector tsvector;
ALTER TABLE playlists ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create GIN indexes for full-text search
CREATE INDEX IF NOT EXISTS idx_tracks_search ON tracks USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_artists_search ON artists USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_playlists_search ON playlists USING GIN (search_vector);

-- Update search vectors
UPDATE tracks SET search_vector = to_tsvector('english', COALESCE(track_name, ''));
UPDATE artists SET search_vector = to_tsvector('english', COALESCE(artist_name, ''));
UPDATE playlists SET search_vector = to_tsvector('english', COALESCE(name, ''));

-- Create triggers to auto-update search vectors
CREATE OR REPLACE FUNCTION tracks_search_trigger() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector('english', COALESCE(NEW.track_name, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION artists_search_trigger() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector('english', COALESCE(NEW.artist_name, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION playlists_search_trigger() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector('english', COALESCE(NEW.name, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tracks_search_update ON tracks;
CREATE TRIGGER tracks_search_update BEFORE INSERT OR UPDATE ON tracks
  FOR EACH ROW EXECUTE FUNCTION tracks_search_trigger();

DROP TRIGGER IF EXISTS artists_search_update ON artists;
CREATE TRIGGER artists_search_update BEFORE INSERT OR UPDATE ON artists
  FOR EACH ROW EXECUTE FUNCTION artists_search_trigger();

DROP TRIGGER IF EXISTS playlists_search_update ON playlists;
CREATE TRIGGER playlists_search_update BEFORE INSERT OR UPDATE ON playlists
  FOR EACH ROW EXECUTE FUNCTION playlists_search_trigger();

-- ============================================
-- ANALYZE TABLES FOR QUERY PLANNER
-- ============================================
ANALYZE tracks;
ANALYZE artists;
ANALYZE albums;
ANALYZE playlists;
ANALYZE playlist_tracks;
ANALYZE track_frequency;
ANALYZE fp_rules_tracks;
ANALYZE fp_rules_artists;