// Spotify Service - Lấy preview URLs và album covers
const SpotifyService = {
    accessToken: null,
    tokenExpiry: null,

    // Client credentials
    // Note: Trong production, nên lưu ở backend để bảo mật
    CLIENT_ID: '6ed***', // Thay bằng ID thực của bạn
    CLIENT_SECRET: '4af***', // Thay bằng Secret thực của bạn

    // Chuyển đổi Spotify URI sang Embed URL
    uriToEmbed(uri) {
        if (!uri) {
            console.warn('⚠️ uriToEmbed: URI is null or undefined');
            return null;
        }

        console.log('🔄 uriToEmbed input:', uri);

        const parts = uri.split(":");
        if (parts.length !== 3) {
            console.error('❌ Invalid URI format:', uri, '- Expected format: spotify:track:ID');
            return null;
        }

        const id = parts[2];
        const embedUrl = `https://open.spotify.com/embed/track/${id}`;

        console.log('✅ uriToEmbed output:', embedUrl);

        return embedUrl;
    },

    async getAccessToken() {
        if (this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry) {
            return this.accessToken;
        }

        try {
            // Nếu chưa cấu hình credentials thực, fallback về demo mode
            if (!this.CLIENT_ID || this.CLIENT_ID === '1c4b8b0c89e14c3a9a6d0e5f7a8b9c0d' || !this.CLIENT_SECRET || this.CLIENT_SECRET === 'YOUR_CLIENT_SECRET_HERE') {
                console.warn('⚠️ Please configure real Spotify CLIENT_ID and CLIENT_SECRET in spotify.js');
                this.accessToken = 'demo_token';
                this.tokenExpiry = Date.now() + 3600000;
                return this.accessToken;
            }

            const credentials = btoa(`${this.CLIENT_ID}:${this.CLIENT_SECRET}`);
            const response = await fetch('https://accounts.spotify.com/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Basic ${credentials}`
                },
                body: 'grant_type=client_credentials'
            });

            if (!response.ok) {
                console.error('Failed to get Spotify token:', response.statusText);
                return null;
            }

            const data = await response.json();
            this.accessToken = data.access_token;
            this.tokenExpiry = Date.now() + (data.expires_in * 1000) - 60000; // Trừ 1 phút để an toàn

            return this.accessToken;
        } catch (error) {
            console.error('Error getting Spotify token:', error);
            return null;
        }
    },

    async getTrackInfo(trackUri, options = {}) {
        const { fallbackToMock = true } = options;

        if (!trackUri || typeof trackUri !== 'string') {
            console.warn('⚠️ getTrackInfo called with invalid trackUri:', trackUri);
            return fallbackToMock ? this.getMockTrackInfo(trackUri) : null;
        }
    
        // Trích xuất track ID từ URI (spotify:track:TRACK_ID)
        const trackId = trackUri.replace('spotify:track:', '');
    
        try {
            const token = await this.getAccessToken();
        
            // Nếu là demo mode, trực tiếp dùng mock data
            if (!token || token === 'demo_token' || token === 'demo_mode') {
                return fallbackToMock ? this.getMockTrackInfo(trackUri) : null;
            }
            console.log(`🎧 Fetching track info for ID: ${trackId} with token: ${token ? 'VALID' : 'INVALID'}`);
    
            const response = await fetch(`https://api.spotify.com/v1/tracks/${trackId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
    
            if (!response.ok) {
                return fallbackToMock ? this.getMockTrackInfo(trackUri) : null;
            }
    
            const data = await response.json();
    
            return {
                preview_url: data.preview_url,
                album_image: data.album?.images?.[1]?.url || data.album?.images?.[0]?.url,
                album_image_small: data.album?.images?.[2]?.url || data.album?.images?.[0]?.url,
                duration_ms: data.duration_ms
            };
        } catch (error) {
            console.error('Error fetching track info:', error);
            return fallbackToMock ? this.getMockTrackInfo(trackUri) : null;
        }
    },
    getMockTrackInfo(trackUri) {
        const fallbackUri = trackUri || 'spotify:track:default';
        const trackId = fallbackUri.replace('spotify:track:', '');
        const albumInfo = this.getMockAlbumImage(`spotify:album:${trackId}`);

        return {
            preview_url: null,
            album_image: albumInfo.image,
            album_image_small: albumInfo.image_small,
            duration_ms: null,
            is_mock: true
        };
    },

    async getAlbumImage(albumUri) {
        if (!albumUri || typeof albumUri !== 'string') {
            console.warn('⚠️ getAlbumImage called with invalid albumUri:', albumUri);
            return this.getMockAlbumImage(albumUri);
        }

        const albumId = albumUri.replace('spotify:album:', '');
    
        try {
            const token = await this.getAccessToken();
    
            // Nếu là demo mode, trực tiếp dùng mock data
            if (!token || token === 'demo_token' || token === 'demo_mode') {
                return this.getMockAlbumImage(albumUri);
            }
    
            const response = await fetch(`https://api.spotify.com/v1/albums/${albumId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
    
            if (!response.ok) {
                return this.getMockAlbumImage(albumUri);
            }
    
            const data = await response.json();
    
            return {
                image: data.images?.[1]?.url || data.images?.[0]?.url,
                image_small: data.images?.[2]?.url || data.images?.[0]?.url
            };
        } catch (error) {
            console.error('Error fetching album image:', error);
            return this.getMockAlbumImage(albumUri);
        }
    },
    getMockAlbumImage(albumUri) {
        if (!albumUri) {
            return {
                image: 'https://placehold.co/300x300/1DB954/ffffff/png?text=🎵',
                image_small: 'https://placehold.co/64x64/1DB954/ffffff/png?text=🎵'
            };
        }

        // Danh sách màu cho album covers khác nhau
        const albumColors = [
            { bg: '1DB954', text: 'ffffff', emoji: '🎵' },
            { bg: 'FF6B6B', text: 'ffffff', emoji: '🎸' },
            { bg: '4ECDC4', text: 'ffffff', emoji: '🎹' },
            { bg: 'FFD93D', text: '333333', emoji: '🎺' },
            { bg: '95E1D3', text: '333333', emoji: '🎷' },
            { bg: 'F38181', text: 'ffffff', emoji: '🎻' },
            { bg: '6C5CE7', text: 'ffffff', emoji: '🥁' },
            { bg: 'FD79A8', text: 'ffffff', emoji: '🎤' },
            { bg: '00B894', text: 'ffffff', emoji: '🎧' },
            { bg: 'FDCB6E', text: '333333', emoji: '🎼' },
        ];

        // Trích xuất album ID từ URI
        const albumId = albumUri.replace('spotify:album:', '');

        // Tạo hash tốt hơn từ albumId
        let hash = 0;
        for (let i = 0; i < albumId.length; i++) {
            const char = albumId.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        hash = Math.abs(hash);

        const colorIndex = (hash * 13) % albumColors.length; // Nhân với số lẻ khác
        const color = albumColors[colorIndex];

        return {
            image: `https://via.placeholder.com/300x300/${color.bg}/${color.text}?text=${encodeURIComponent(color.emoji)}`,
            image_small: `https://via.placeholder.com/64x64/${color.bg}/${color.text}?text=${encodeURIComponent(color.emoji)}`
        };
    },

    // Cache để tránh gọi API nhiều lần
    trackInfoCache: new Map(),

    async getCachedTrackInfo(trackUri) {
        if (!trackUri) {
            console.warn('⚠️ getCachedTrackInfo called with empty trackUri');
            return this.getMockTrackInfo(trackUri);
        }

        if (this.trackInfoCache.has(trackUri)) {
            console.log(`📦 Cache HIT for: ${trackUri.substring(0, 30)}...`);
            return this.trackInfoCache.get(trackUri);
        }

        console.log(`🔍 Cache MISS for: ${trackUri.substring(0, 30)}... - Fetching new data`);
        const info = await this.getTrackInfo(trackUri);
        const safeInfo = info || this.getMockTrackInfo(trackUri);
        this.trackInfoCache.set(trackUri, safeInfo);
        return safeInfo;
    }
};

// Export cho sử dụng trong các file khác
window.SpotifyService = SpotifyService;
