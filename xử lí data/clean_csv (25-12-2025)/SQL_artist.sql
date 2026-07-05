use test
go

-- Tạo bảng lưu Playlist (ver lọc artist)
CREATE TABLE Playlist_ver2 (
    pid INT PRIMARY KEY,
    name NVARCHAR(300),
    num_artists INT  -- số artist khác nhau trong playlist
);
GO

-- insert dữ liệu vào bảng (8000 dòng)
-- Lúc này chưa lọc, num_artists sẽ được cập nhật sau
INSERT INTO Playlist_ver2 (pid, name, num_artists)
SELECT
    pid,
    name,
    0
FROM RawPlaylist;
GO


-- Tạo bảng transaction (ver lọc artist)
CREATE TABLE Playlist_artist_ver2 (
    pid INT FOREIGN KEY REFERENCES Playlist_ver2(pid),
    artist_uri NVARCHAR(300),
    artist_name NVARCHAR(300)
);
GO

-- insert dữ liệu vào bảng (169777 dòng)
-- Mỗi dòng thể hiện 1 artist trong 1 playlist (nếu playlist có 3 bài của cùng artist → vẫn là 1 dòng)
INSERT INTO Playlist_artist_ver2 (pid, artist_uri, artist_name)
SELECT DISTINCT
    pid,
    artist_uri,
    artist_name
FROM RawTrack;
GO

-- BẮT ĐẦU LỌC DỮ LIỆU
-- Xóa các artist chỉ xuất hiện 1 lần (LẦN 1)
-- Xóa trong bảng Playlist_artist_ver2
DELETE pa
FROM Playlist_artist_ver2 pa
JOIN (
    SELECT artist_uri
    FROM Playlist_artist_ver2
    GROUP BY artist_uri
    HAVING COUNT(*) = 1
) t ON pa.artist_uri = t.artist_uri;
GO

-- Cập nhật lại num_artists trong bảng Playlist, sau khi xóa artist chỉ xuất hiện 1 lần (LẦN 1) (7986 dòng)
UPDATE p
SET num_artists = t.cnt
FROM Playlist_ver2 p
JOIN (
    SELECT pid, COUNT(*) AS cnt
    FROM Playlist_artist_ver2
    GROUP BY pid
) t ON p.pid = t.pid;
GO

-- Nếu playlist không còn artist nào, num_artists sẽ NULL → đặt lại num_artists = 0 (14 dòng)
UPDATE Playlist_ver2
SET num_artists = 0
WHERE pid NOT IN (
    SELECT DISTINCT pid FROM Playlist_artist_ver2
);
GO

-- Sau khi cập nhật số lượng artist
-- Xóa các playlist chỉ có 0/1 artist 
-- Xóa Playlist_artist_ver2 trước (309 dòng)
DELETE FROM Playlist_artist_ver2
WHERE pid IN (
    SELECT pid
    FROM Playlist_ver2
    WHERE num_artists <= 1
);
GO

-- Xóa Playlist sau (323 dòng)
DELETE FROM Playlist_ver2
WHERE num_artists <= 1;
GO

-- Sau khi xóa các playlist chỉ có 0/1 artist
-- Xóa các artist còn lại trong playlist vừa xóa
-- Xóa các artist chỉ xuất hiện 0/1 lần (LẦN 2)
-- Xóa trong bảng Playlist_artist_ver2 (16 dòng)
DELETE pa
FROM Playlist_artist_ver2 pa
JOIN (
    SELECT artist_uri
    FROM Playlist_artist_ver2
    GROUP BY artist_uri
    HAVING COUNT(*) <= 1
) t ON pa.artist_uri = t.artist_uri;
GO

-- Cập nhật lại num_artists trong bảng Playlist, sau khi xóa artist chỉ xuất hiện 1 lần (LẦN 2) (7677 dòng)
UPDATE p
SET num_artists = t.cnt
FROM Playlist_ver2 p
JOIN (
    SELECT pid, COUNT(*) AS cnt
    FROM Playlist_artist_ver2
    GROUP BY pid
) t ON p.pid = t.pid;
GO

-- Sau khi cập nhật số lượng artist 
-- Xóa các playlist chỉ có 0/1 artist (LẦN 2)
-- Xóa Playlist_artist_ver2 trước (0 dòng)
DELETE FROM Playlist_artist_ver2
WHERE pid IN (
    SELECT pid
    FROM Playlist_ver2
    WHERE num_artists <= 1
);
GO

-- Xóa Playlist sau (0 dòng)
DELETE FROM Playlist_ver2
WHERE num_artists <= 1;
GO

-- DỮ LIỆU ĐÃ ĐẠT CHUẨN: 
-- CÁC ARTIST XUẤT HIỆN ÍT NHẤT 2 LẦN Ở 2 PLAYLIST KHÁC NHAU
-- CÁC PLAYLIST CÓ TỪ 2 ARTIST TRỞ LÊN

-- Tổng có 7677 playlist
SELECT COUNT(*) AS total_playlists FROM Playlist_ver2; 
-- Tổng có 162888 transaction (ver lọc artist)
SELECT COUNT(*) AS total_playlist_artists FROM Playlist_artist_ver2;
-- Tổng cộng có 7451 artist
SELECT COUNT(distinct artist_uri) AS total_artists FROM Playlist_artist_ver2;

-- Playlist có num_artist: min = 2, max = 95
SELECT
    MIN(num_artists) AS min_artists,
    MAX(num_artists) AS max_artists
FROM Playlist_ver2;

-- Xuất ra file playlist_artist để train luật artist
-- Tạo bảng lưu Artist_rules
CREATE TABLE Artist_rules (
	pid INT FOREIGN KEY REFERENCES Playlist_ver2 (pid),
	list_artist_uri NVARCHAR(MAX))
GO

-- Thêm dữ liệu vào bảng (7677 dòng)
INSERT INTO Artist_rules (pid, list_artist_uri)
SELECT 
    pa.pid,
    STRING_AGG(pa.artist_uri, ', ') AS list_artist_uri
FROM Playlist_artist_ver2 pa
GROUP BY pa.pid;

-- Xuất ra playlist_artist.csv (tổng 7677 dòng)
SELECT pid, list_artist_uri
FROM Artist_rules
order by pid

-- XUẤT FILE artist_uri_map (tổng 7451 artist) 
SELECT distinct artist_name, artist_uri
FROM Playlist_artist_ver2
GO