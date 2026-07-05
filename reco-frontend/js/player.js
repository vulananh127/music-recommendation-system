// Music Player Controller
const MusicPlayer = {
    audioElement: null,
    currentTrack: null,
    playlist: [],
    currentIndex: -1,
    isPlaying: false,
    
    init() {
        this.audioElement = document.getElementById('audioPlayer');
        this.setupEventListeners();
        this.setupAudioListeners();
    },
    
    setupEventListeners() {
        // Play/Pause button
        const playBtn = document.getElementById('playerPlayBtn');
        playBtn.addEventListener('click', () => this.togglePlay());
        
        // Previous/Next buttons
        document.getElementById('playerPrevBtn').addEventListener('click', () => this.playPrevious());
        document.getElementById('playerNextBtn').addEventListener('click', () => this.playNext());
        
        // Volume control
        const volumeSlider = document.getElementById('volumeSlider');
        volumeSlider.addEventListener('input', (e) => {
            this.setVolume(e.target.value / 100);
        });
        
        const volumeBtn = document.getElementById('playerVolumeBtn');
        volumeBtn.addEventListener('click', () => this.toggleMute());
        
        // Progress bar
        const progressBar = document.getElementById('playerProgressBar');
        progressBar.addEventListener('click', (e) => this.seek(e));
        
        // Track play buttons (delegated)
        document.addEventListener('click', (e) => {
            const playBtn = e.target.closest('.track-play-btn');
            if (playBtn) {
                e.preventDefault();
                const trackUri = playBtn.dataset.trackUri;
                const trackRow = playBtn.closest('[data-track-data]');
                
                if (trackRow) {
                    try {
                        const trackData = JSON.parse(trackRow.dataset.trackData);
                        this.playTrack(trackData, trackUri);
                    } catch (err) {
                        console.error('Error parsing track data:', err);
                    }
                }
            }
        });
    },
    
    setupAudioListeners() {
        // Update progress bar
        this.audioElement.addEventListener('timeupdate', () => {
            this.updateProgress();
        });
        
        // Track ended
        this.audioElement.addEventListener('ended', () => {
            this.playNext();
        });
        
        // Can play
        this.audioElement.addEventListener('canplay', () => {
            this.updateDuration();
        });
        
        // Error handling
        this.audioElement.addEventListener('error', (e) => {
            console.error('Audio error:', e);
            this.showToast('Unable to play this track. Preview may not be available.', 'error');
            this.updatePlayButton(false);
        });
        
        // Playing
        this.audioElement.addEventListener('playing', () => {
            this.isPlaying = true;
            this.updatePlayButton(true);
        });
        
        // Paused
        this.audioElement.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayButton(false);
        });
    },
    
    async playTrack(trackData, trackUri) {
        console.log(`▶️ Player: Playing track with URI: ${trackUri}`);
        
        // Get Spotify track info (preview URL and album art)
        const spotifyInfo = await window.SpotifyService.getCachedTrackInfo(trackUri);
        
        console.log(`🎧 Player: Received preview URL: ${spotifyInfo.preview_url}`);
        
        // Update current track
        this.currentTrack = {
            ...trackData,
            track_uri: trackUri,
            preview_url: spotifyInfo.preview_url,
            album_image: spotifyInfo.album_image,
            album_image_small: spotifyInfo.album_image_small
        };
        
        // Update UI
        this.updatePlayerUI();
        
        // Update Now Playing sidebar với album image
        if (window.UI && window.UI.renderNowPlaying) {
            window.UI.renderNowPlaying({
                ...trackData,
                albumImage: spotifyInfo.album_image
            });
        }
        
        // If no preview URL available
        if (!spotifyInfo.preview_url) {
            this.showToast('Preview not available for this track', 'warning');
            return;
        }
        
        // Load and play audio
        this.audioElement.src = spotifyInfo.preview_url;
        console.log(`🔊 Player: Audio element src set to: ${this.audioElement.src}`);
        
        try {
            await this.audioElement.play();
            this.isPlaying = true;
            this.updateAllPlayButtons();
        } catch (err) {
            console.error('Error playing audio:', err);
            this.showToast('Failed to play audio', 'error');
        }
    },
    
    togglePlay() {
        if (!this.audioElement.src) {
            this.showToast('No track selected', 'info');
            return;
        }
        
        if (this.isPlaying) {
            this.audioElement.pause();
        } else {
            this.audioElement.play().catch(err => {
                console.error('Error playing:', err);
                this.showToast('Failed to play audio', 'error');
            });
        }
    },
    
    playPrevious() {
        if (this.playlist.length === 0) return;
        
        this.currentIndex--;
        if (this.currentIndex < 0) {
            this.currentIndex = this.playlist.length - 1;
        }
        
        const track = this.playlist[this.currentIndex];
        this.playTrack(track, track.track_uri);
    },
    
    playNext() {
        if (this.playlist.length === 0) {
            // If no playlist, just stop
            this.audioElement.pause();
            return;
        }
        
        this.currentIndex++;
        if (this.currentIndex >= this.playlist.length) {
            this.currentIndex = 0;
        }
        
        const track = this.playlist[this.currentIndex];
        this.playTrack(track, track.track_uri);
    },
    
    setVolume(volume) {
        this.audioElement.volume = volume;
        this.updateVolumeIcon(volume);
    },
    
    toggleMute() {
        this.audioElement.muted = !this.audioElement.muted;
        this.updateVolumeIcon(this.audioElement.muted ? 0 : this.audioElement.volume);
    },
    
    seek(event) {
        const progressBar = event.currentTarget;
        const rect = progressBar.getBoundingClientRect();
        const percent = (event.clientX - rect.left) / rect.width;
        const newTime = percent * this.audioElement.duration;
        
        if (!isNaN(newTime)) {
            this.audioElement.currentTime = newTime;
        }
    },
    
    updateProgress() {
        const percent = (this.audioElement.currentTime / this.audioElement.duration) * 100;
        const progressFill = document.getElementById('playerProgressFill');
        const progressHandle = document.getElementById('playerProgressHandle');
        
        if (!isNaN(percent)) {
            progressFill.style.width = `${percent}%`;
            progressHandle.style.left = `${percent}%`;
        }
        
        // Update time display
        const currentTime = this.formatTime(this.audioElement.currentTime);
        document.getElementById('playerCurrentTime').textContent = currentTime;
    },
    
    updateDuration() {
        const duration = this.formatTime(this.audioElement.duration);
        document.getElementById('playerDuration').textContent = duration;
    },
    
    updatePlayerUI() {
        if (!this.currentTrack) return;
        
        // Update track name
        document.getElementById('playerTrackName').textContent = this.currentTrack.title || 'Unknown Track';
        
        // Update artist
        document.getElementById('playerTrackArtist').textContent = this.currentTrack.artist || 'Unknown Artist';
        
        // Update album art
        const albumArt = document.getElementById('playerAlbumArt');
        if (this.currentTrack.album_image_small) {
            albumArt.innerHTML = `<img src="${this.currentTrack.album_image_small}" alt="Album Art">`;
        } else {
            albumArt.innerHTML = '<i class="fas fa-music"></i>';
        }
        
        // Load album images for all visible tracks
        this.loadVisibleAlbumImages();
    },
    
    updatePlayButton(isPlaying) {
        const playBtn = document.getElementById('playerPlayBtn');
        const icon = playBtn.querySelector('i');
        
        if (isPlaying) {
            icon.classList.remove('fa-play');
            icon.classList.add('fa-pause');
        } else {
            icon.classList.remove('fa-pause');
            icon.classList.add('fa-play');
        }
    },
    
    updateAllPlayButtons() {
        // Remove playing class from all buttons
        document.querySelectorAll('.track-play-btn').forEach(btn => {
            btn.classList.remove('playing');
            const icon = btn.querySelector('i');
            icon.classList.remove('fa-pause');
            icon.classList.add('fa-play');
        });
        
        // Add playing class to current track
        if (this.currentTrack && this.currentTrack.track_uri) {
            const currentBtn = document.querySelector(`[data-track-uri="${this.currentTrack.track_uri}"]`);
            if (currentBtn && this.isPlaying) {
                currentBtn.classList.add('playing');
                const icon = currentBtn.querySelector('i');
                icon.classList.remove('fa-play');
                icon.classList.add('fa-pause');
            }
        }
    },
    
    updateVolumeIcon(volume) {
        const volumeBtn = document.getElementById('playerVolumeBtn');
        const icon = volumeBtn.querySelector('i');
        
        icon.classList.remove('fa-volume-up', 'fa-volume-down', 'fa-volume-mute');
        
        if (volume === 0) {
            icon.classList.add('fa-volume-mute');
        } else if (volume < 0.5) {
            icon.classList.add('fa-volume-down');
        } else {
            icon.classList.add('fa-volume-up');
        }
    },
    
    async loadVisibleAlbumImages() {
        // Load album images for all visible album art elements
        const albumArtElements = document.querySelectorAll('.track-album-art[data-album-uri]');
        
        for (const element of albumArtElements) {
            const albumUri = element.dataset.albumUri;
            if (!albumUri || element.querySelector('img')) continue; // Skip if already loaded
            
            try {
                const albumInfo = await window.SpotifyService.getAlbumImage(albumUri);
                if (albumInfo.image_small) {
                    element.innerHTML = `<img src="${albumInfo.image_small}" alt="Album">`;
                }
            } catch (err) {
                console.error('Error loading album image:', err);
            }
        }
    },
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas ${iconMap[type]}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },
    
    setPlaylist(tracks) {
        this.playlist = tracks;
        this.currentIndex = -1;
    }
};

// Initialize player when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        MusicPlayer.init();
    });
} else {
    MusicPlayer.init();
}

// Export for use in other modules
// window.MusicPlayer = MusicPlayer;
