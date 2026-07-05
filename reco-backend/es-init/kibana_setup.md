# Hướng dẫn Setup Kibana Dashboard

## 1. Tạo Index Pattern

1. Mở Kibana tại `http://localhost:5601`
2. Vào **Management** > **Stack Management** > **Index Patterns**
3. Click **Create index pattern**
4. Nhập tên index: `analytics`
5. Chọn time field: `timestamp`
6. Click **Create index pattern**

## 2. Tạo Visualizations

### Top Bài Hát Được Gợi Ý

1. Vào **Visualize** > **Create visualization**
2. Chọn **Vertical Bar**
3. Chọn index pattern: `analytics`
4. Cấu hình:
   - **Y-axis**: Count
   - **X-axis**: Terms aggregation trên field `consequents.keyword`
   - Size: 10
   - Order: Descending by count

### Top Nghệ Sĩ Hay Đi Cùng Nhau

1. Tạo visualization mới, chọn **Pie Chart**
2. Cấu hình:
   - **Slice size**: Count
   - **Slice by**: Terms trên `antecedents.keyword` (khi rule_type = "artist")
   - Size: 10

### Rule Usage Over Time

1. Tạo visualization mới, chọn **Line Chart**
2. Cấu hình:
   - **Y-axis**: Count
   - **X-axis**: Date Histogram trên `timestamp`
   - **Split series**: Terms trên `rule_type.keyword`

### CTR Analysis

1. Tạo visualization mới, chọn **Metric**
2. Cấu hình:
   - Metric: Count
   - Filter: `event_type: click` hoặc `event_type: view`

### Playlist Events

1. Tạo visualization mới, chọn **Data Table**
2. Cấu hình:
   - Rows: Terms trên `event_type.keyword`
   - Filter: `event_type: playlist_*`

### Search Analytics

1. Tạo visualization mới, chọn **Tag Cloud**
2. Cấu hình:
   - Size: Terms trên `query.keyword`
   - Filter: `event_type: search_*`

## 3. Tạo Dashboard

1. Vào **Dashboard** > **Create dashboard**
2. Thêm các visualizations đã tạo
3. Cấu hình time range: Last 7 days
4. Auto-refresh: 30 seconds
5. Lưu dashboard với tên: "Music Recommendation Analytics"

## 4. Saved Searches (Truy vấn log)

### Tìm kiếm bài hát nâng cao

1. Vào **Discover**
2. Chọn index pattern: `analytics`
3. Tạo query:
   ```
   event_type:search_tracks AND query:*your_search_term*
   ```
4. Sử dụng full-text search với fuzzy matching

### Phân tích CTR

1. Query:
   ```
   event_type:click OR event_type:view
   ```
2. Group by `item_id` để tính CTR

### Phân tích Rule Performance

1. Query:
   ```
   event_type:recommendation_served
   ```
2. Aggregation: Average trên `latency_ms`
3. Group by `rule_type`





