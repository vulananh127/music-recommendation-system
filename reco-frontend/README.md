# Frontend Music Player - Hướng Dẫn Cài Đặt

## Tổng Quan

Frontend đã được nâng cấp với các tính năng mới:
- ✅ **Phát nhạc trực tiếp** từ Spotify (preview 30 giây)
- ✅ **Hiển thị ảnh bìa album** cho mỗi bài hát
- ✅ **Nút phát nhạc** ở mỗi hàng bài hát
- ✅ **Thanh điều khiển player** cố định ở cuối màn hình
- ✅ **Progress bar** với khả năng seek
- ✅ **Volume control** và mute
- ✅ **Play/Pause, Previous, Next** controls

## Cấu Hình Spotify API (Tùy Chọn)

Để sử dụng đầy đủ tính năng phát nhạc và hiển thị ảnh album, bạn cần đăng ký Spotify Developer Account:

### Bước 1: Đăng Ký Spotify Developer

1. Truy cập https://developer.spotify.com/dashboard
2. Đăng nhập bằng tài khoản Spotify của bạn (hoặc tạo tài khoản mới)
3. Nhấp "Create an App"
4. Điền thông tin:
   - **App Name**: Music Recommendation System
   - **App Description**: Music recommendation and playback system
   - **Redirect URI**: http://localhost:8000 (hoặc domain của bạn)
5. Nhấp "Create"

### Bước 2: Lấy Credentials

1. Trong Dashboard, chọn app vừa tạo
2. Nhấp "Settings"
3. Copy **Client ID** và **Client Secret**

### Bước 3: Cấu Hình Frontend

Mở file `js/spotify.js` và cập nhật:

```javascript
// Line 7-8
CLIENT_ID: 'YOUR_CLIENT_ID_HERE',
```

**Lưu ý**: Trong production thực tế, `CLIENT_SECRET` không nên để trong frontend. Nên tạo một backend endpoint để lấy access token.

## Cấu Hình Backend Endpoint (Khuyến Nghị)

Để bảo mật hơn, bạn nên tạo endpoint backend để lấy Spotify token:

### Tạo file `reco-backend/backend/app/routers/spotify.py`:

```python
from fastapi import APIRouter
import httpx
import os
from datetime import datetime, timedelta

router = APIRouter()

spotify_token_cache = {
    "access_token": None,
    "expires_at": None
}

@router.get("/spotify/token")
async def get_spotify_token():
    # Check cache
    if (spotify_token_cache["access_token"] and 
        spotify_token_cache["expires_at"] and 
        datetime.now() < spotify_token_cache["expires_at"]):
        return {"access_token": spotify_token_cache["access_token"]}
    
    # Get new token
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return {"error": "Spotify credentials not configured"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret)
        )
        
        if response.status_code == 200:
            data = response.json()
            spotify_token_cache["access_token"] = data["access_token"]
            spotify_token_cache["expires_at"] = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
            return {"access_token": data["access_token"]}
        
        return {"error": "Failed to get token"}
```

### Cập nhật `js/spotify.js`:

```javascript
async getAccessToken() {
    if (this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry) {
        return this.accessToken;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/spotify/token`);
        const data = await response.json();
        
        if (data.access_token) {
            this.accessToken = data.access_token;
            this.tokenExpiry = Date.now() + 3500000; // ~58 phút
            return this.accessToken;
        }
        
        return null;
    } catch (error) {
        console.error('Error getting Spotify token:', error);
        return null;
    }
}
```

### Thêm vào `.env`:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Chạy Ứng Dụng

### Cách 1: Mở Trực Tiếp File HTML

1. Mở file `index.html` trong trình duyệt
2. **Lưu ý**: Một số tính năng có thể bị giới hạn do CORS

### Cách 2: Dùng Local Server (Khuyến Nghị)

#### Với Python:
```bash
cd reco-frontend
python -m http.server 8000
```

#### Với Node.js (http-server):
```bash
npm install -g http-server
cd reco-frontend
http-server -p 8000
```

#### Với VS Code Live Server:
1. Cài extension "Live Server"
2. Right-click vào `index.html`
3. Chọn "Open with Live Server"

Sau đó truy cập: http://localhost:8000

## Cấu Trúc Files

```
reco-frontend/
├── index.html              # HTML chính với music player
├── css/
│   └── styles.css         # CSS với styles cho player
├── js/
│   ├── config.js          # Cấu hình API
│   ├── spotify.js         # ⭐ Service tích hợp Spotify API
│   ├── player.js          # ⭐ Controller cho music player
│   ├── api.js             # API calls
│   ├── ui.js              # UI rendering (đã cập nhật)
│   └── app.js             # Main app logic
└── README.md              # File này
```

## Tính Năng Music Player

### 1. Phát Nhạc
- Click vào nút play (▶) ở mỗi hàng bài hát
- Bài hát sẽ phát preview 30 giây từ Spotify
- Nếu không có preview, sẽ hiển thị thông báo

### 2. Điều Khiển Player
- **Play/Pause**: Nút chính ở giữa
- **Previous/Next**: Nút ◀ và ▶ hai bên
- **Seek**: Click vào progress bar để tua
- **Volume**: Slider điều chỉnh âm lượng
- **Mute**: Click vào icon loa

### 3. Hiển Thị Thông Tin
- Tên bài hát và nghệ sĩ đang phát
- Ảnh bìa album (nếu có)
- Thời gian hiện tại / tổng thời gian
- Progress bar

### 4. Album Art
- Hiển thị ở player (bên trái)
- Hiển thị ở cột Album trong bảng danh sách
- Tự động load khi scroll

## Giới Hạn & Lưu Ý

### Spotify API Limits
- **Preview**: Chỉ 30 giây mỗi bài
- **Availability**: Không phải bài nào cũng có preview
- **Rate Limits**: API có giới hạn số request/phút

### Fallback
- Khi không có Spotify token: Sử dụng mock data (ảnh placeholder)
- Khi không có preview: Hiển thị thông báo, không phát nhạc
- Khi lỗi API: Tự động fallback sang placeholder images

## Troubleshooting

### Không phát được nhạc?
1. Kiểm tra console log để xem có lỗi API không
2. Đảm bảo Spotify token đã được cấu hình
3. Thử bài hát khác (có thể bài này không có preview)

### Không hiển thị ảnh album?
1. Kiểm tra Spotify API credentials
2. Kiểm tra console để xem lỗi CORS
3. Đảm bảo đang chạy qua web server (không phải file://)

### CORS Errors?
1. Chạy qua local server (không mở trực tiếp file HTML)
2. Backend endpoint phải enable CORS cho Spotify API

## Demo Mode

Nếu không cấu hình Spotify API, ứng dụng vẫn hoạt động với:
- ✅ Ảnh placeholder cho album covers
- ✅ UI đầy đủ với tất cả controls
- ❌ Không phát nhạc thực tế (do không có preview URL)

## Next Steps

Để nâng cấp thêm:
1. ✨ Tích hợp Spotify Web Playback SDK (phát full bài hát)
2. 📱 Responsive design cho mobile
3. 🎵 Queue management
4. 💾 Lưu trạng thái player (localStorage)
5. 🔀 Shuffle và Repeat modes

## Support

Nếu có vấn đề, kiểm tra:
1. Browser Console (F12) để xem lỗi
2. Network tab để xem API calls
3. Backend logs cho Spotify token endpoint
