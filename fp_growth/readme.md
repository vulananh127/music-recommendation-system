# Cấu trúc thư mục fp_growth 

Thư mục chứa các file liên quan đến dataset và thuật toán fp-growth 

## 1. /dataset directory 
### /dataset/raw
- thư mục chứa file dataset thô tải từ link : https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge/dataset_files

### /dataset/script 
- thư mục chứa script để tách dữ liệu thô ( json file về playlist_clean.csv, track_clean.csv, track_frequency.csv)

## 2. /transaction directory 
- chứa các file transaction để sẵn sàng đưa vào thuật toán 

## 3. script train
- fpgrowth_recommender.py : script train level track 
- fpgrowth_artist.py : script train level artist 

## 4. /model directory
- chứa các file luật kết hợp cuối cùng và script đánh giá chất lượng luật 

## 5. /docs directory 
- chứa các hình ảnh mô tả biểu đồ phân tích 

