create database test
go

use test
go

-- Tạo bảng RawPlaylist chứa các thông tin của playlist
Create table RawPlaylist (
	pid INT PRIMARY KEY,
	name NVARCHAR(300),
	num_tracks INT,
	num_samples INT, 
	num_holdouts INT,
	actual_track_count INT)
GO

-- Thêm dữ liệu vào RawPlaylist từ file dữ liệu .csv (8000 dòng) 
BULK INSERT RawPlaylist
FROM 'C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\DATA\playlist_clean.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    FIELDQUOTE = '"',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001',
    MAXERRORS = 0
);
go

-- Tạo bảng RawTrack chứa các thông tin về bài hát và id playlist chứa bài hát đó
CREATE TABLE RawTrack (
    pid INT FOREIGN KEY REFERENCES RawPlaylist(pid),
    pos INT,
    track_uri NVARCHAR(300),
    track_name NVARCHAR(MAX),
    artist_name NVARCHAR(300),
    artist_uri NVARCHAR(300),
    album_name NVARCHAR(MAX),
    album_uri NVARCHAR(300),
    duration_ms INT
);
go

-- insert dữ liệu vào RawTrack (280000 dòng)
BULK INSERT RawTrack
FROM 'C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\DATA\track_clean.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    FIELDQUOTE = '"',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001',
    MAXERRORS = 0
);
go

-- Tạo bảng lưu playlist (ver lọc track)
CREATE TABLE Playlist_ver1 (
    pid INT PRIMARY KEY,
    name NVARCHAR(300),
    num_tracks INT,
    num_samples INT,
    num_holdouts INT
);
GO

-- insert dữ liệu vào bảng (8000 dòng)
INSERT INTO Playlist_ver1
SELECT
    pid,
    name,
    num_tracks,
    num_samples,
    num_holdouts
FROM RawPlaylist;
GO

-- Tạo bảng lưu transaction (ver lọc track)
CREATE TABLE Playlist_track_ver1 (
    pid INT FOREIGN KEY REFERENCES Playlist_ver1 (pid),
    pos INT,
    track_uri NVARCHAR(300),
    track_name NVARCHAR(MAX),
    artist_name NVARCHAR(300),
    artist_uri NVARCHAR(300),
    album_name NVARCHAR(MAX),
    album_uri NVARCHAR(300),
    duration_ms INT
);
GO

-- insert dữ liệu vào bảng (280000 dòng)
INSERT INTO Playlist_track_ver1
SELECT
    pid,
    pos,
    track_uri,
    track_name,
    artist_name,
    artist_uri,
    album_name,
    album_uri,
    duration_ms
FROM RawTrack;
GO

-- BẮT ĐẦU LÀM SẠCH DỮ LIỆU
-- Xóa các bài hát chỉ xuất hiện đúng 1 lần [ count(track_uri) = 1 ] (LẦN 1)
-- Xóa trong bảng Playlist_track_ver1 (38450 dòng)
DELETE pt
FROM Playlist_track_ver1 pt
JOIN (
    SELECT track_uri
    FROM Playlist_track_ver1
    GROUP BY track_uri
    HAVING COUNT(*) = 1
) t ON pt.track_uri = t.track_uri;
GO

-- Cập nhật lại số lượng num_samples và num_holdouts sau khi đã xóa các bài hát chỉ xuất hiện 1 lần (LẦN 1) (7948 dòng)
UPDATE p
SET
    num_samples = t.cnt,
    num_holdouts = p.num_tracks - t.cnt
FROM Playlist_ver1 p
JOIN (
    SELECT pid, COUNT(*) AS cnt
    FROM Playlist_track_ver1
    GROUP BY pid
) t ON p.pid = t.pid;
GO

-- Nếu playlist không còn bài hát nào, num_samples sẽ NULL → đặt lại num_samples = 0 (52 dòng)
UPDATE Playlist_ver1
SET num_samples = 0,
    num_holdouts = num_tracks
WHERE pid NOT IN (
    SELECT DISTINCT pid FROM Playlist_track_ver1
);
GO


-- Sau khi cập nhật lại số lượng bài hát trong playlist
-- Xóa các playlist chỉ còn 0/1 bài hát [ num_samples in (0,1) ] (LẦN 1)
-- Xóa Playlist_track_ver1 trước (73 dòng)
DELETE FROM Playlist_track_ver1
WHERE pid IN (
    SELECT pid
    FROM Playlist_ver1
    WHERE num_samples <= 1
);
GO

-- Xóa Playlist sau (125 dòng)
DELETE FROM Playlist_ver1
WHERE num_samples <= 1;
GO

-- Sau khi xóa các playlist chỉ có 0/1 bài hát
-- Xóa các bài hát còn lại trong playlist vừa xóa
-- Xóa các bài hát chỉ xuất hiện 1 lần (LẦN 2) (37 dòng)
DELETE pt
FROM Playlist_track_ver1 pt
JOIN (
    SELECT track_uri
    FROM Playlist_track_ver1
    GROUP BY track_uri
    HAVING COUNT(*) <= 1
) t ON pt.track_uri = t.track_uri;
GO

-- Cập nhật lại số lượng bài hát num_samples và num_holdouts (LẦN 2) (7875 dòng)
UPDATE p
SET num_samples = ISNULL(t.cnt, 0)
FROM Playlist_ver1 p
LEFT JOIN (
    SELECT pid, COUNT(*) AS cnt
    FROM Playlist_track_ver1
    GROUP BY pid
) t ON p.pid = t.pid;
GO

-- Sau khi cập nhật lại số lượng bài hát trong playlist (LẦN 2)
-- Xóa các playlist chỉ còn 0/1 bài hát [ num_samples in (0,1) ]
-- Xóa Playlist_track_ver1 trước (0 dòng) 
DELETE FROM Playlist_track_ver1
WHERE pid IN (
    SELECT pid
    FROM Playlist_ver1
    WHERE num_samples <= 1
);
GO

-- Xóa Playlist sau (1 dòng) --> có 1 playlist không có bài hát nào
DELETE FROM Playlist_ver1
WHERE num_samples <= 1;
GO

-- DỮ LIỆU ĐÃ ĐẠT CHUẨN: 
-- CÁC TRACK XUẤT HIỆN ÍT NHẤT 2 LẦN
-- CÁC PLAYLIST CÓ TỪ 2 TRACK TRỞ LÊN

-- Tổng có 7874 playlist
SELECT COUNT(*) AS total_playlists FROM Playlist_ver1; 
-- Tổng có 241440 transaction (ver lọc track)
SELECT COUNT(*) AS total_playlist_tracks FROM Playlist_track_ver1;
-- Tổng cộng có 27562 track
SELECT COUNT(distinct track_uri) AS total_tracks FROM Playlist_track_ver1;

-- Playlist có num_samples: min = 2, max = 100
SELECT MIN(num_samples) AS min_tracks,
       MAX(num_samples) AS max_tracks
FROM Playlist_ver1;


-- Xuất ra file playlist_track để train luật track
-- Tạo bảng lưu Track_rules
CREATE TABLE Track_rules (
	pid INT FOREIGN KEY REFERENCES Playlist_ver1 (pid),
	list_track_uri NVARCHAR(MAX))
GO

-- Thêm dữ liệu vào bảng (7874 dòng)
INSERT INTO Track_rules (pid, list_track_uri)
SELECT 
    pt.pid,
    STRING_AGG(pt.track_uri, ', ') AS list_track_uri
FROM Playlist_track_ver1 pt
GROUP BY pt.pid;

-- Xuất ra file playlist_track.csv (7874 dòng)
SELECT pid, list_track_uri
FROM Track_rules
order by pid

-- XUẤT FILE track_uri_map (tổng 27562 track)
SELECT distinct track_name, track_uri
FROM Playlist_track_ver1
GO