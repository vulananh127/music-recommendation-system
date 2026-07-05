-- ============================================================================
-- SCRIPT KIỂM TRA CHẤT LƯỢNG DỮ LIỆU (DATA QUALITY CHECK)
-- ============================================================================
-- Kiểm tra: NULL values, duplicates, orphan records, data integrity,
--           format validation, statistical anomalies
-- ============================================================================

-- ============================================================================
-- PHẦN 1: KIỂM TRA DỮ LIỆU STAGING
-- ============================================================================

-- 1.1 Kiểm tra NULL/Empty trong khóa chính của staging_tracks
SELECT '========== 1.1. NULL/Empty URIs trong staging_tracks ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE track_uri IS NULL OR TRIM(track_uri) = '') AS missing_track_uri,
    COUNT(*) FILTER (WHERE artist_uri IS NULL OR TRIM(artist_uri) = '') AS missing_artist_uri,
    COUNT(*) FILTER (WHERE album_uri IS NULL OR TRIM(album_uri) = '') AS missing_album_uri,
    COUNT(*) FILTER (WHERE pid IS NULL OR TRIM(pid) = '') AS missing_pid,
    COUNT(*) AS total_rows
FROM staging_tracks;

-- 1.2 Kiểm tra NULL trong tên
SELECT '========== 1.2. NULL names trong staging_tracks ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE track_name IS NULL OR TRIM(track_name) = '') AS missing_track_name,
    COUNT(*) FILTER (WHERE artist_name IS NULL OR TRIM(artist_name) = '') AS missing_artist_name,
    COUNT(*) FILTER (WHERE album_name IS NULL OR TRIM(album_name) = '') AS missing_album_name,
    COUNT(*) AS total_rows
FROM staging_tracks;

-- 1.3 Kiểm tra duplicates trong staging_tracks
SELECT '========== 1.3. Duplicate records trong staging_tracks ==========' AS check_name;
SELECT 
    pid, 
    track_uri, 
    pos,
    COUNT(*) AS duplicate_count
FROM staging_tracks
WHERE track_uri IS NOT NULL AND pid IS NOT NULL
GROUP BY pid, track_uri, pos
HAVING COUNT(*) > 1
LIMIT 10;

-- 1.4 Kiểm tra staging_playlists
SELECT '========== 1.4. NULL/Empty PIDs trong staging_playlists ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE pid IS NULL OR TRIM(pid) = '') AS missing_pid,
    COUNT(*) AS total_rows
FROM staging_playlists;

-- 1.5 Kiểm tra mismatch giữa num_tracks và actual_track_count
SELECT '========== 1.5. Playlists có mismatch track count ==========' AS check_name;
SELECT 
    pid,
    name,
    num_tracks,
    actual_track_count,
    ABS(num_tracks - actual_track_count) AS difference
FROM staging_playlists
WHERE num_tracks != actual_track_count
ORDER BY difference DESC
LIMIT 10;

-- 1.6 Kiểm tra staging rules
SELECT '========== 1.6. NULL/Empty trong staging_artist_rules ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE antecedents IS NULL OR TRIM(antecedents) = '') AS missing_antecedents,
    COUNT(*) FILTER (WHERE consequents IS NULL OR TRIM(consequents) = '') AS missing_consequents,
    COUNT(*) AS total_rows
FROM staging_artist_rules;

SELECT '========== 1.7. NULL/Empty trong staging_track_rules ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE antecedents IS NULL OR TRIM(antecedents) = '') AS missing_antecedents,
    COUNT(*) FILTER (WHERE consequents IS NULL OR TRIM(consequents) = '') AS missing_consequents,
    COUNT(*) AS total_rows
FROM staging_track_rules;

-- ============================================================================
-- PHẦN 2: KIỂM TRA BẢNG CHÍNH (MAIN TABLES)
-- ============================================================================

-- 2.1 Tổng quan số lượng records
SELECT '========== 2.1. Tổng quan số lượng records ==========' AS check_name;
SELECT 
    'users' AS table_name, COUNT(*) AS record_count FROM users
UNION ALL
SELECT 'artists', COUNT(*) FROM artists
UNION ALL
SELECT 'albums', COUNT(*) FROM albums
UNION ALL
SELECT 'tracks', COUNT(*) FROM tracks
UNION ALL
SELECT 'playlists', COUNT(*) FROM playlists
UNION ALL
SELECT 'playlist_tracks', COUNT(*) FROM playlist_tracks
UNION ALL
SELECT 'fp_rules_tracks', COUNT(*) FROM fp_rules_tracks
UNION ALL
SELECT 'fp_rules_artists', COUNT(*) FROM fp_rules_artists
ORDER BY table_name;

-- 2.2 Kiểm tra NULL values trong bảng chính
SELECT '========== 2.2. NULL values trong Artists ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE artist_uri IS NULL) AS null_uri,
    COUNT(*) FILTER (WHERE artist_name IS NULL) AS null_name,
    COUNT(*) AS total_rows
FROM artists;

SELECT '========== 2.3. NULL values trong Albums ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE album_uri IS NULL) AS null_uri,
    COUNT(*) FILTER (WHERE album_name IS NULL) AS null_name,
    COUNT(*) AS total_rows
FROM albums;

SELECT '========== 2.4. NULL values trong Tracks ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE track_uri IS NULL) AS null_uri,
    COUNT(*) FILTER (WHERE track_name IS NULL) AS null_name,
    COUNT(*) FILTER (WHERE artist_id IS NULL) AS null_artist_id,
    COUNT(*) FILTER (WHERE album_id IS NULL) AS null_album_id,
    COUNT(*) AS total_rows
FROM tracks;

-- 2.5 Kiểm tra Orphan Records
SELECT '========== 2.5. Orphan tracks (không có artist hoặc album) ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE artist_id IS NULL) AS tracks_without_artist,
    COUNT(*) FILTER (WHERE album_id IS NULL) AS tracks_without_album,
    COUNT(*) FILTER (WHERE artist_id IS NULL AND album_id IS NULL) AS tracks_without_both
FROM tracks;

SELECT '========== 2.6. Orphan playlist_tracks (track không tồn tại) ==========' AS check_name;
SELECT COUNT(*) AS orphan_count
FROM playlist_tracks pt
LEFT JOIN tracks t ON pt.track_id = t.id
WHERE t.id IS NULL;

SELECT '========== 2.7. Orphan playlist_tracks (playlist không tồn tại) ==========' AS check_name;
SELECT COUNT(*) AS orphan_count
FROM playlist_tracks pt
LEFT JOIN playlists p ON pt.playlist_id = p.id
WHERE p.id IS NULL;

-- ============================================================================
-- PHẦN 3: KIỂM TRA DATA INTEGRITY
-- ============================================================================

-- 3.1 Kiểm tra duplicate URIs
SELECT '========== 3.1. Duplicate URIs trong Artists ==========' AS check_name;
SELECT artist_uri, COUNT(*) AS duplicate_count
FROM artists
GROUP BY artist_uri
HAVING COUNT(*) > 1
LIMIT 10;

SELECT '========== 3.2. Duplicate URIs trong Albums ==========' AS check_name;
SELECT album_uri, COUNT(*) AS duplicate_count
FROM albums
GROUP BY album_uri
HAVING COUNT(*) > 1
LIMIT 10;

SELECT '========== 3.3. Duplicate URIs trong Tracks ==========' AS check_name;
SELECT track_uri, COUNT(*) AS duplicate_count
FROM tracks
GROUP BY track_uri
HAVING COUNT(*) > 1
LIMIT 10;

-- 3.4 Kiểm tra case sensitivity issues
SELECT '========== 3.4. Case sensitivity issues trong Artists ==========' AS check_name;
SELECT 
    LOWER(artist_uri) AS uri_lower,
    COUNT(DISTINCT artist_uri) AS different_cases,
    STRING_AGG(DISTINCT artist_uri, ' | ') AS variations
FROM artists
GROUP BY LOWER(artist_uri)
HAVING COUNT(DISTINCT artist_uri) > 1
LIMIT 10;

-- 3.5 Kiểm tra whitespace issues
SELECT '========== 3.5. URIs có khoảng trắng thừa trong Artists ==========' AS check_name;
SELECT COUNT(*) AS whitespace_issues
FROM artists
WHERE artist_uri != TRIM(artist_uri)
   OR artist_uri LIKE '% %';

-- ============================================================================
-- PHẦN 4: KIỂM TRA TÍNH HỢP LỆ CỦA DỮ LIỆU
-- ============================================================================

-- 4.1 Kiểm tra format URI
SELECT '========== 4.1. URIs không đúng format Spotify (artists) ==========' AS check_name;
SELECT COUNT(*) AS invalid_format
FROM artists
WHERE artist_uri NOT LIKE 'spotify:artist:%';

SELECT '========== 4.2. URIs không đúng format Spotify (tracks) ==========' AS check_name;
SELECT COUNT(*) AS invalid_format
FROM tracks
WHERE track_uri NOT LIKE 'spotify:track:%';

-- 4.3 Kiểm tra duration_ms hợp lý
SELECT '========== 4.3. Tracks có duration bất thường ==========' AS check_name;
SELECT 
    COUNT(*) FILTER (WHERE duration_ms IS NULL) AS null_duration,
    COUNT(*) FILTER (WHERE duration_ms <= 0) AS zero_or_negative,
    COUNT(*) FILTER (WHERE duration_ms < 10000) AS too_short_10s,
    COUNT(*) FILTER (WHERE duration_ms > 600000) AS too_long_10min,
    COUNT(*) AS total_tracks
FROM tracks;

-- 4.4 Kiểm tra kiểu dữ liệu và nội dung mảng của bảng fp_rules_artists sau khi chèn
SELECT 
    antecedents,
    pg_typeof(antecedents) as data_type,
    left(antecedents::text, 50) as preview
FROM fp_rules_artists
LIMIT 1;

SELECT antecedents[1] FROM fp_rules_artists LIMIT 1;
SELECT array_length(antecedents, 1) FROM fp_rules_artists LIMIT 1; 
SELECT 'spotify:artist:13ubrt8qoocpljq2fl1kca' = ANY(antecedents) FROM fp_rules_artists; 
-- 4.5 Kiểm tra kiểu dữ liệu và nội dung mảng của fp_rules_tracks sau khi chèn
SELECT 
    antecedents,
    pg_typeof(antecedents) as data_type,
    left(antecedents::text, 50) as preview
FROM fp_rules_tracks 
LIMIT 1;

SELECT antecedents[1] FROM fp_rules_tracks LIMIT 1;
SELECT array_length(antecedents, 1) FROM fp_rules_tracks LIMIT 1; 
SELECT 'spotify:track:7ll3mvfwffsd25pbz72agj' = ANY(antecedents) FROM fp_rules_tracks; 
-- 4.6 Kiểm tra playlist track count
SELECT '========== 4.4. Playlists có số lượng tracks không khớp ==========' AS check_name;
WITH playlist_actual_counts AS (
    SELECT 
        p.id,
        p.pid,
        p.name,
        p.num_tracks,
        COUNT(pt.id) AS actual_count
    FROM playlists p
    LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
    GROUP BY p.id, p.pid, p.name, p.num_tracks
)
SELECT 
    COUNT(*) FILTER (WHERE num_tracks != actual_count) AS mismatch_count,
    COUNT(*) AS total_playlists
FROM playlist_actual_counts;

-- ============================================================================
-- PHẦN 5: KIỂM TRA THỐNG KÊ VÀ ANOMALIES
-- ============================================================================

-- 5.1 Phân bố track duration
SELECT '========== 5.1. Phân bố thời lượng tracks (ms) ==========' AS check_name;
SELECT 
    MIN(duration_ms) AS min_duration,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY duration_ms) AS p25,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) AS median,
    AVG(duration_ms)::INT AS average,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY duration_ms) AS p75,
    MAX(duration_ms) AS max_duration
FROM tracks
WHERE duration_ms IS NOT NULL;

-- 5.2 Phân bố số tracks per playlist
SELECT '========== 5.2. Phân bố số tracks per playlist ==========' AS check_name;
WITH playlist_counts AS (
    SELECT 
        p.id,
        COUNT(pt.id) AS track_count
    FROM playlists p
    LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
    GROUP BY p.id
)
SELECT 
    MIN(track_count) AS min_tracks,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY track_count) AS p25,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY track_count) AS median,
    AVG(track_count)::INT AS average,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY track_count) AS p75,
    MAX(track_count) AS max_tracks
FROM playlist_counts;

-- 5.3 Top tracks xuất hiện nhiều nhất
SELECT '========== 5.3. Top 10 tracks xuất hiện trong nhiều playlists nhất ==========' AS check_name;
SELECT 
    t.track_name,
    t.track_uri,
    COUNT(DISTINCT pt.playlist_id) AS playlist_count
FROM tracks t
JOIN playlist_tracks pt ON t.id = pt.track_id
GROUP BY t.id, t.track_name, t.track_uri
ORDER BY playlist_count DESC
LIMIT 10;

-- 5.4 Artists có nhiều tracks nhất
SELECT '========== 5.4. Top 10 artists có nhiều tracks nhất ==========' AS check_name;
SELECT 
    a.artist_name,
    a.artist_uri,
    COUNT(t.id) AS track_count
FROM artists a
JOIN tracks t ON a.id = t.artist_id
GROUP BY a.id, a.artist_name, a.artist_uri
ORDER BY track_count DESC
LIMIT 10;

-- 5.5 Kiểm tra FP-Growth rules quality
SELECT '========== 5.5. Thống kê FP-Growth Track Rules ==========' AS check_name;
SELECT 
    COUNT(*) AS total_rules,
    AVG(support)::NUMERIC(10,6) AS avg_support,
    AVG(confidence)::NUMERIC(10,6) AS avg_confidence,
    AVG(lift)::NUMERIC(10,6) AS avg_lift,
    MIN(confidence) AS min_confidence,
    MAX(confidence) AS max_confidence,
    COUNT(*) FILTER (WHERE lift < 1) AS rules_with_negative_correlation
FROM fp_rules_tracks;

SELECT '========== 5.6. Thống kê FP-Growth Artist Rules ==========' AS check_name;
SELECT 
    COUNT(*) AS total_rules,
    AVG(support)::NUMERIC(10,6) AS avg_support,
    AVG(confidence)::NUMERIC(10,6) AS avg_confidence,
    AVG(lift)::NUMERIC(10,6) AS avg_lift,
    MIN(confidence) AS min_confidence,
    MAX(confidence) AS max_confidence,
    COUNT(*) FILTER (WHERE lift < 1) AS rules_with_negative_correlation
FROM fp_rules_artists;

-- ============================================================================
-- PHẦN 6: TÓM TẮT KẾT QUẢ
-- ============================================================================

SELECT '========== 6.1. Data Quality Score Summary ==========' AS check_name;
WITH quality_checks AS (
    SELECT
        -- Check 1: No NULL URIs in main tables
        CASE WHEN (SELECT COUNT(*) FROM artists WHERE artist_uri IS NULL) = 0 THEN 1 ELSE 0 END AS check_artist_uri,
        CASE WHEN (SELECT COUNT(*) FROM tracks WHERE track_uri IS NULL) = 0 THEN 1 ELSE 0 END AS check_track_uri,
        
        -- Check 2: No duplicates
        CASE WHEN (SELECT COUNT(*) FROM (SELECT artist_uri FROM artists GROUP BY artist_uri HAVING COUNT(*) > 1) x) = 0 THEN 1 ELSE 0 END AS check_no_dup_artists,
        CASE WHEN (SELECT COUNT(*) FROM (SELECT track_uri FROM tracks GROUP BY track_uri HAVING COUNT(*) > 1) x) = 0 THEN 1 ELSE 0 END AS check_no_dup_tracks,
        
        -- Check 3: No orphan records
        CASE WHEN (SELECT COUNT(*) FROM playlist_tracks pt LEFT JOIN tracks t ON pt.track_id = t.id WHERE t.id IS NULL) = 0 THEN 1 ELSE 0 END AS check_no_orphan_tracks,
        
        -- Check 4: Valid URI format
        CASE WHEN (SELECT COUNT(*) FROM artists WHERE artist_uri NOT LIKE 'spotify:artist:%') = 0 THEN 1 ELSE 0 END AS check_valid_artist_uri,
        CASE WHEN (SELECT COUNT(*) FROM tracks WHERE track_uri NOT LIKE 'spotify:track:%') = 0 THEN 1 ELSE 0 END AS check_valid_track_uri,
        
        -- Check 5: Reasonable duration
        CASE WHEN (SELECT COUNT(*) FROM tracks WHERE duration_ms <= 0 OR duration_ms > 3600000) < (SELECT COUNT(*) * 0.01 FROM tracks) THEN 1 ELSE 0 END AS check_reasonable_duration
)
SELECT 
    (check_artist_uri + check_track_uri + check_no_dup_artists + check_no_dup_tracks + 
     check_no_orphan_tracks + check_valid_artist_uri + check_valid_track_uri + check_reasonable_duration) AS passed_checks,
    8 AS total_checks,
    ROUND((check_artist_uri + check_track_uri + check_no_dup_artists + check_no_dup_tracks + 
           check_no_orphan_tracks + check_valid_artist_uri + check_valid_track_uri + check_reasonable_duration)::NUMERIC / 8 * 100, 2) AS quality_score_pct
FROM quality_checks;

SELECT * FROM fp_rules_tracks
WHERE antecedents @> ARRAY['spotify:track:7lL3MvFWFFSD25pBz72Agj']::text[];
SELECT id, antecedents, pg_typeof(antecedents)
FROM fp_rules_tracks;


-- Kiểm tra dữ liệu thực tế
SELECT antecedents, consequents 
FROM staging_track_rules 
WHERE 'spotify:track:1dgr8epw5eouzzvhzckbx5' = ANY(antecedents)
LIMIT 5;

-- Hoặc
SELECT antecedents, consequents 
FROM staging_track_rules 
WHERE antecedents && ARRAY['spotify:track:1dgr8epw5eouzzvhzckbx5']::text[]
LIMIT 5;

SELECT 
    antecedents, 
    consequents,
    pg_typeof(antecedents) as type,
    length(antecedents) as len
FROM staging_track_rules
LIMIT 3;

-- Test với 1 track
SELECT antecedents, consequents, confidence, lift
FROM fp_rules_tracks 
WHERE antecedents LIKE '%spotify:track:1vrd6uogamckngnshjqlst%'
ORDER BY (confidence * lift) DESC
LIMIT 5;

SELECT COUNT(DISTINCT track_uri) FROM (
    SELECT DISTINCT unnest(antecedents) AS track_uri FROM fp_rules_tracks
    UNION
    SELECT DISTINCT unnest(consequents) FROM fp_rules_tracks
) t;

-- Kiểm tra số lượng valid artists
SELECT COUNT(DISTINCT artist_uri) FROM (
    SELECT DISTINCT unnest(antecedents) AS artist_uri FROM fp_rules_artists
    UNION
    SELECT DISTINCT unnest(consequents) FROM fp_rules_artists
) a;

-- Thay 'spotify:track:xxx' bằng track_uri thực tế
SELECT 
    t.track_uri,
    t.track_name,
    a.artist_uri,
    a.artist_name,
    -- Kiểm tra xem track có trong rules không
    EXISTS(
        SELECT 1 FROM fp_rules_tracks 
        WHERE t.track_uri = ANY(antecedents) OR t.track_uri = ANY(consequents)
    ) as track_in_rules,
    -- Kiểm tra xem artist có trong rules không
    EXISTS(
        SELECT 1 FROM fp_rules_artists 
        WHERE a.artist_uri = ANY(antecedents) OR a.artist_uri = ANY(consequents)
    ) as artist_in_rules
FROM tracks t
JOIN artists a ON t.artist_id = a.id
WHERE t.track_uri = 'spotify:track:49bzzavzzyhx0sd4awuonj';

-- Test với track không có trong rules
SELECT 
    t.id, t.track_uri, t.track_name, t.duration_ms,
    a.artist_name, a.artist_uri
FROM tracks t
INNER JOIN artists a ON t.artist_id = a.id
WHERE (
    EXISTS (
        SELECT 1 FROM fp_rules_tracks 
        WHERE t.track_uri = ANY(antecedents) 
           OR t.track_uri = ANY(consequents)
    )
    OR
    EXISTS (
        SELECT 1 FROM fp_rules_artists 
        WHERE a.artist_uri = ANY(antecedents) 
           OR a.artist_uri = ANY(consequents)
    )
)
AND t.track_uri = 'spotify:track:49bzzavzzyhx0sd4awuonj';

-- Kết quả mong đợi: 0 rows