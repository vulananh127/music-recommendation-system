-- Script để load CSV data vào staging tables

-- Load track data
\copy staging_tracks(pid, pos, track_uri, track_name, artist_name, artist_uri, album_name, album_uri, duration_ms) FROM '/backend/app/data/track.csv' DELIMITER ',' CSV HEADER;

-- Load playlist data  
\copy staging_playlists(pid, name, num_tracks, num_samples, num_holdouts) FROM '/backend/app/data/playlist.csv' DELIMITER ',' CSV HEADER;

-- Load artist rules
\copy staging_artist_rules(antecedents, consequents, support, confidence, lift, conviction, antecedent_len, consequent_len) FROM '/backend/app/data/rules_artist.csv' DELIMITER ',' CSV HEADER;

-- Load track rules
\copy staging_track_rules(antecedents, consequents, support, confidence, lift, conviction, antecedent_len, consequent_len) FROM '/backend/app/data/rules_track.csv' DELIMITER ',' CSV HEADER;

-- Load track frequency
\copy staging_track_frequency(track_uri, frequency, track_name, artist_name, artist_uri) FROM '/backend/app/data/track_frequency.csv' DELIMITER ',' CSV HEADER;
