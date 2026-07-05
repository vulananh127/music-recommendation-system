-- ============================================================================
-- FULL LOAD DỮ LIỆU TỪ STAGING SANG BẢNG CHÍNH
-- ============================================================================
-- Các bước ETL:
-- 1. Loại bỏ dòng thiếu khóa chính (URI)
-- 2. Chuẩn hóa URI về lower-case
-- 3. Cắt khoảng trắng (trim)
-- ============================================================================
CREATE OR REPLACE PROCEDURE full_load_from_staging()
LANGUAGE plpgsql
AS $$
DECLARE 
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    batch_start_time TIMESTAMP;
    batch_end_time TIMESTAMP;
BEGIN
    batch_start_time := NOW();
    RAISE NOTICE '========================================';
    RAISE NOTICE 'LOADING DỮ LIỆU TỪ STAGING SANG BẢNG CHÍNH';
    RAISE NOTICE '========================================';

    -- ----------------------------------------------------------------------------
    -- XÓA TOÀN BỘ BẢN GHI TRONG BẢNG CHÍNH TRƯỚC KHI LOAD TRÁNH CONFLICTS
    -- ----------------------------------------------------------------------------
    TRUNCATE TABLE 
        fp_rules_tracks, 
        fp_rules_artists, 
        fp_itemsets_tracks,
        fp_itemsets_artists
    RESTART IDENTITY;
    TRUNCATE TABLE 
        playlist_tracks,
        track_frequency,
        tracks,
        playlists,
        albums,    
        artists
    RESTART IDENTITY
    CASCADE;

    -- ----------------------------------------------------------------------------
    -- 1. Loading artists từ staging_tracks
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading artists from staging_tracks...';
    INSERT INTO artists (artist_uri, artist_name)
    SELECT DISTINCT
        TRIM(artist_uri) AS artist_uri,
        TRIM(artist_name) AS artist_name
    FROM staging_tracks
    WHERE artist_uri IS NOT NULL 
    AND TRIM(artist_uri) != ''
    AND artist_name IS NOT NULL;
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);

    -- ----------------------------------------------------------------------------
    -- 2. Loading ALBUMS từ staging_tracks
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading albums from staging_tracks...';
    INSERT INTO albums (album_uri, album_name)
    SELECT DISTINCT
        TRIM(album_uri) AS album_uri,
        TRIM(album_name) AS album_name
    FROM staging_tracks
    WHERE album_uri IS NOT NULL 
    AND TRIM(album_uri) != ''
    AND album_name IS NOT NULL;
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);
    -- ----------------------------------------------------------------------------
    -- 3. Loading TRACKS từ staging_tracks
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading tracks từ staging_tracks';
    INSERT INTO tracks (track_uri, track_name, artist_id, album_id, duration_ms)
    SELECT DISTINCT
        TRIM(st.track_uri) AS track_uri,
        TRIM(st.track_name) AS track_name,
        ar.id AS artist_id,
        al.id AS album_id,
        st.duration_ms
    FROM staging_tracks st
    LEFT JOIN artists ar ON TRIM(st.artist_uri) = ar.artist_uri
    LEFT JOIN albums al ON TRIM(st.album_uri) = al.album_uri
    WHERE st.track_uri IS NOT NULL 
    AND TRIM(st.track_uri) != ''
    AND st.track_name IS NOT NULL;
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);
    -- ----------------------------------------------------------------------------
    -- 4. Loading PLAYLISTS từ staging_playlists
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading playlists từ staging_playlists';
    INSERT INTO playlists (pid, name, num_tracks, num_samples, num_holdouts, actual_track_count)
    SELECT DISTINCT
        TRIM(pid) AS pid,
        TRIM(name) AS name,
        num_tracks,
        num_samples,
        num_holdouts,
        actual_track_count
    FROM staging_playlists
    WHERE pid IS NOT NULL 
    AND TRIM(pid) != '';
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);
    -- ----------------------------------------------------------------------------
    -- 5. Loading PLAYLIST_TRACKS từ staging_tracks
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading playlist_tracks từ staging_tracks';
    INSERT INTO playlist_tracks (playlist_id, track_id, pos)
    SELECT DISTINCT
        pl.id AS playlist_id,
        tr.id AS track_id,
        MIN(st.pos) AS pos
    FROM staging_tracks st
    INNER JOIN playlists pl ON TRIM(st.pid) = pl.pid
    INNER JOIN tracks tr ON TRIM(st.track_uri) = tr.track_uri
    WHERE st.pid IS NOT NULL 
    AND TRIM(st.pid) != ''
    AND st.track_uri IS NOT NULL 
    AND TRIM(st.track_uri) != ''
    GROUP BY
    pl.id,
    tr.id;
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);

    -- ----------------------------------------------------------------------------
    -- 6. Loading FP_RULES_ARTISTS từ staging_artist_rules
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading fp_rules_artist từ staging_artists_rules';
    INSERT INTO fp_rules_artists (
        antecedents, 
        consequents, 
        antecedent_names, 
        consequent_names,
        support, 
        confidence, 
        lift, 
        conviction,
        antecedent_len, 
        consequent_len
    )
    SELECT
        -- Chuyển chuỗi thành mảng và giữ nguyên case của URI
        CASE WHEN antecedents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedents), ', ')
            ELSE string_to_array(TRIM(antecedents), ',')
        END AS antecedents,
        CASE WHEN consequents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequents), ', ')
            ELSE string_to_array(TRIM(consequents), ',')
        END AS consequents,
        CASE WHEN antecedent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedent_names), ', ')
            ELSE string_to_array(TRIM(antecedent_names), ',')
        END AS antecedent_names,
        CASE WHEN consequent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequent_names), ', ')
            ELSE string_to_array(TRIM(consequent_names), ',')
        END AS consequent_names,
        support,
        confidence,
        lift,
        conviction,
        antecedent_len,
        consequent_len
    FROM staging_artist_rules
    WHERE antecedents IS NOT NULL 
    AND TRIM(antecedents) != ''
    AND consequents IS NOT NULL 
    AND TRIM(consequents) != '';
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);

    -- ----------------------------------------------------------------------------
    -- 7. Loading FP_RULES_TRACKS từ staging_track_rules
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'load fp_rules_tracks từ staging_track_rules';
    INSERT INTO fp_rules_tracks (
        antecedents, 
        consequents, 
        antecedent_names, 
        consequent_names,
        support, 
        confidence, 
        lift, 
        conviction,
        antecedent_len, 
        consequent_len
    )
    SELECT
        CASE WHEN antecedents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedents), ', ')
            ELSE string_to_array(TRIM(antecedents), ',')
        END AS antecedents,
        CASE WHEN consequents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequents), ', ')
            ELSE string_to_array(TRIM(consequents), ',')
        END AS consequents,
        CASE WHEN antecedent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedent_names), ', ')
            ELSE string_to_array(TRIM(antecedent_names), ',')
        END AS antecedent_names,
        CASE WHEN consequent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequent_names), ', ')
            ELSE string_to_array(TRIM(consequent_names), ',')
        END AS consequent_names,
        support,
        confidence,
        lift,
        conviction,
        antecedent_len,
        consequent_len
    FROM staging_track_rules
    WHERE antecedents IS NOT NULL 
    AND TRIM(antecedents) != ''
    AND consequents IS NOT NULL 
    AND TRIM(consequents) != '';
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);

    -- ----------------------------------------------------------------------------
    -- 8. Loading TRACK_FREQUENCY từ staging_tracks_frequency
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    RAISE NOTICE 'Loading track_frequency từ staging_tracks';
    INSERT INTO track_frequency (
        track_uri,
        track_name,
        artist_name,
        artist_uri,
        frequency,
        updated_at
    )
    SELECT
        TRIM(st.track_uri) AS track_uri,
        TRIM(st.track_name) AS track_name,
        TRIM(st.artist_name) AS artist_name,
        TRIM(st.artist_uri) AS artist_uri,
        COUNT(DISTINCT TRIM(st.pid)) AS frequency,
        CURRENT_TIMESTAMP
    FROM staging_tracks st
    WHERE st.track_uri IS NOT NULL
    AND TRIM(st.track_uri) != ''
    AND st.track_name IS NOT NULL
    GROUP BY
        TRIM(st.track_uri),
        TRIM(st.track_name),
        TRIM(st.artist_name),
        TRIM(st.artist_uri);
    end_time := NOW(); 
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);
    -- ----------------------------------------------------------------------------
    -- 9. DỌN DẸP STAGING (tùy chọn - chạy sau khi verify)
    -- ----------------------------------------------------------------------------
    start_time := NOW();
    TRUNCATE TABLE staging_tracks;
    TRUNCATE TABLE staging_playlists;
    TRUNCATE TABLE staging_artist_rules;
    TRUNCATE TABLE staging_track_rules;
    TRUNCATE TABLE staging_track_frequency;
    end_time := NOW();
    RAISE NOTICE 'load duration: % seconds', EXTRACT(EPOCH FROM end_time - start_time);
    batch_end_time := NOW();
    RAISE NOTICE '========================================';    
    RAISE NOTICE 'Data load Batch Duration: % seconds', EXTRACT(EPOCH FROM batch_end_time - batch_start_time);
    RAISE NOTICE '========================================';
    EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'LOAD FAILED at %', NOW();
        RAISE;
END;
$$;


