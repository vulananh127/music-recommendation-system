/*
    - DDL Scripts : Tạo bảng staging
    - Mục đích: 
        Tạo các bảng staging trong schema public , xóa nếu đã tồn tại.
        Chạy script để định dạng lại các bảng staging trước khi load dữ liệu.
*/


DROP TABLE IF EXISTS staging_tracks;
DROP TABLE IF EXISTS staging_playlists;
DROP TABLE IF EXISTS staging_artist_rules;
DROP TABLE IF EXISTS staging_track_rules;
DROP TABLE IF EXISTS staging_track_frequency;


CREATE TABLE staging_tracks (
    pid             VARCHAR(255),
    pos             INT,
    track_uri       VARCHAR(255),
    track_name      TEXT,
    artist_name     TEXT,
    artist_uri      VARCHAR(255),
    album_name      TEXT,
    album_uri       VARCHAR(255),
    duration_ms     INT
);


CREATE TABLE staging_playlists (
    pid                 VARCHAR(255),
    name                TEXT,
    num_tracks          INT,
    num_samples         INT,
    num_holdouts        INT,
    actual_track_count  INT
);


CREATE TABLE staging_artist_rules (
    antecedents       TEXT,   -- chuỗi, sẽ chuyển sang ARRAY
    consequents       TEXT,
    antecedent_names  TEXT,
    consequent_names  TEXT,
    support           NUMERIC,
    confidence        NUMERIC,
    lift              NUMERIC,
    conviction        NUMERIC,
    antecedent_len    INT,
    consequent_len    INT
);


CREATE TABLE staging_track_rules (
    antecedents       TEXT,
    consequents       TEXT,
    antecedent_names  TEXT,
    consequent_names  TEXT,
    support           NUMERIC,
    confidence        NUMERIC,
    lift              NUMERIC,
    conviction        NUMERIC,
    antecedent_len    INT,
    consequent_len    INT
);


CREATE TABLE staging_track_frequency (
    track_uri       VARCHAR(255),
    track_name      TEXT,
    artist_name     TEXT,
    artist_uri      VARCHAR(255),
    frequency       INT
);

