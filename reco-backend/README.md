# Music Recommendation System - Backend

Backend hoàn chỉnh cho hệ thống gợi ý nhạc với các chức năng:

## Tính năng

### 1. Authentication
- Đăng ký tài khoản
- Đăng nhập với JWT token
- Xác thực người dùng

### 2. Playlist Management
- Tạo playlist mới
- Xem danh sách playlist
- Xem chi tiết playlist
- Cập nhật playlist
- Xóa playlist

### 3. Track Management
- Thêm bài hát vào playlist
- Xóa bài hát khỏi playlist

### 4. Search
- Tìm kiếm bài hát theo tên
- Tìm kiếm bài hát theo nghệ sĩ
- Tìm kiếm nghệ sĩ
- Hỗ trợ fuzzy matching

### 5. Recommendation
- Nhận gợi ý bài hát dựa trên FP-Growth rules
- Nhận gợi ý nghệ sĩ dựa trên FP-Growth rules

### 6. Analytics & Logging
- Gửi log tất cả events đến Elasticsearch
- Tracking CTR (Click Through Rate)
- Analytics cho recommendations
- Playlist events tracking
- Search analytics



## API Endpoints

### Authentication
- `POST /api/auth/register` - Đăng ký
- `POST /api/auth/login` - Đăng nhập
- `GET /api/auth/me` - Lấy thông tin user hiện tại

### Playlists
- `POST /api/playlists` - Tạo playlist
- `GET /api/playlists` - Lấy danh sách playlist
- `GET /api/playlists/{id}` - Lấy chi tiết playlist
- `PUT /api/playlists/{id}` - Cập nhật playlist
- `DELETE /api/playlists/{id}` - Xóa playlist

### Playlist Tracks
- `POST /api/playlists/{id}/tracks` - Thêm bài hát
- `DELETE /api/playlists/{id}/tracks/{track_id}` - Xóa bài hát

### Search
- `GET /api/search/tracks?q={query}&artist={artist}` - Tìm kiếm bài hát
- `GET /api/search/artists?q={query}` - Tìm kiếm nghệ sĩ

### Recommendation
- `GET /api/recommend/tracks?antecedents={uris}&limit={limit}` - Gợi ý bài hát
- `GET /api/recommend/artists?antecedents={uris}&limit={limit}` - Gợi ý bài hát dựa trên nghệ sĩ 
- `GET  /api/recommend/all`
Gợi ý bài hát dựa trên cả hai cấp độ 

### Events
- `POST /api/events/click` - Log click event
- `POST /api/events/view` - Log view event

## Cài đặt và Chạy

### 1. Khởi động services

```bash
docker-compose up -d
```

### 3. Khởi tạo Elasticsearch index

```bash
curl http://localhost:9200

bash es-init/bootstrap.sh
```

### 4. Truy cập services

- Backend API: http://localhost:8080
- API Documentation: http://localhost:8080/docs
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200

## Elasticsearch Analytics

### Index: `analytics`

Lưu trữ các events:
- `user_register`, `user_login`
- `playlist_create`, `playlist_view`, `playlist_update`, `playlist_delete`
- `playlist_track_add`, `playlist_track_remove`
- `search_tracks`, `search_artists`
- `recommendation_served`
- `click`, `view`

## Kibana Dashboard

Xem hướng dẫn setup tại `es-init/kibana_setup.md`

### Các metrics được track:
- Top bài hát được gợi ý
- Top nghệ sĩ hay đi cùng nhau
- Rule usage over time
- CTR analysis
- Playlist events
- Search analytics

## Development

### Cài đặt dependencies

```bash
cd backend
pip install -r app/requirements.txt
```

### Chạy development server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Notes

- Tất cả endpoints (trừ `/health`) yêu cầu authentication
- JWT token có thời hạn 30 ngày
- Elasticsearch logging có error handling, không fail request nếu ES không available
- CORS được cấu hình để cho phép tất cả origins (nên giới hạn trong production)




