const App = {
   currentUser: null,
   currentPlaylist: null,
   searchTimeout: null,
   miniSearchTimeout: null,
   selectedTracksForNewPlaylist: [],
   isCreatingPlaylist: false,
   lastMiniSearchResults: { tracks: [], artists: [] },
   currentView: 'home',
   currentRecommendations: null,

   playSpotifyEmbed(embedUrl, triggerButton) {
      const container = document.getElementById('spotifySidebarEmbed');
      const autoPlayUrl = embedUrl.includes('?') ? `${embedUrl}&autoplay=1` : `${embedUrl}?autoplay=1`;

      if (container && autoPlayUrl) {
         // reset all other play buttons to play icon
         document.querySelectorAll('.btn-play-spotify').forEach(btn => {
            btn.innerHTML = '<i class="fas fa-play"></i>';
            btn.classList.remove('playing');
         });

         if (triggerButton) {
            triggerButton.innerHTML = '<i class="fas fa-pause"></i>';
            triggerButton.classList.add('playing');
         }

         container.style.display = 'block';
         container.innerHTML = `
            <iframe 
               src="${autoPlayUrl}" 
               width="100%" 
               height="152" 
               frameborder="0" 
               allowtransparency="true" 
               allow="autoplay; encrypted-media">
            </iframe>
         `;
      }
   },

   async init() {
      this.loadUser();

      await this.loadHome();

      this.attachEventListeners();
   },

   normalizeTrackForUi(track) {
      if (!track) return track;

      let durationMs = track.durationMs ?? track.duration_ms;
      if ((durationMs === undefined || durationMs === null) && track.duration !== undefined && track.duration !== null) {
         durationMs = Number(track.duration) * 1000;
      }

      return {
         ...track,
         durationMs: Number(durationMs) || 0
      };
   },

   getTrackIdentity(track) {
      if (!track) return null;

      const rawUri = track.trackUri || track.uri || track.track_uri;
      if (rawUri) {
         return `uri:${String(rawUri).trim().toLowerCase()}`;
      }

      const rawId = track.id;
      if (rawId !== undefined && rawId !== null && rawId !== '') {
         return `id:${String(rawId).trim()}`;
      }

      return null;
   },

   buildTrackIdentitySet(tracks = []) {
      const identitySet = new Set();

      (tracks || []).forEach(track => {
         const identity = this.getTrackIdentity(track);
         if (identity) {
            identitySet.add(identity);
         }
      });

      return identitySet;
   },

   filterRecommendationsByPlaylistTracks(recommendations, playlistTracks = []) {
      if (!recommendations) return recommendations;

      const existingTrackSet = this.buildTrackIdentitySet(playlistTracks);

      const filterRuleItems = (items = [], trackKey) => {
         return (items || [])
            .map(item => {
               const tracks = Array.isArray(item?.[trackKey]) ? item[trackKey] : [];
               const filteredTracks = tracks.filter(track => {
                  const identity = this.getTrackIdentity(track);
                  return identity ? !existingTrackSet.has(identity) : true;
               });

               return {
                  ...item,
                  [trackKey]: filteredTracks
               };
            })
            .filter(item => (item?.[trackKey] || []).length > 0);
      };

      const filteredTrackItems = filterRuleItems(recommendations.tracks?.items || [], 'consequents');
      const filteredArtistItems = filterRuleItems(recommendations.artists?.items || [], 'topTracks');

      return {
         ...recommendations,
         tracks: {
            ...(recommendations.tracks || {}),
            count: filteredTrackItems.length,
            items: filteredTrackItems
         },
         artists: {
            ...(recommendations.artists || {}),
            count: filteredArtistItems.length,
            items: filteredArtistItems
         }
      };
   },

   sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
   },


   loadUser() {
      const userData = window.localStorage.getItem(CONFIG.STORAGE_KEYS.USER_DATA);
      if (userData) {
         this.currentUser = JSON.parse(userData);
         UI.updateAuthButton(this.currentUser);
      }
   },

   async loadHome() {
      try {
         this.currentView = 'home';
         this.currentPlaylist = null;
         await this.loadPlaylists();

         const [popularTracks, popularArtist, playlists] = await Promise.all([
            API.getPopularTracks(),
            API.getPopularArtist(),
            this.currentUser ? API.getPlaylists() : Promise.resolve([])
         ]);

         console.log('📊 Popular Tracks from API:', popularTracks);
         console.log('🎤 Popular Artist from API:', popularArtist);

         // Log track URIs to check validity
         if (popularTracks && popularTracks.length > 0) {
            console.log('🎵 Track URIs:');
            popularTracks.forEach((track, index) => {
               console.log(`  ${index + 1}. ${track.title} - URI: ${track.uri || 'MISSING'}`);
               if (track.uri) {
                  const embedUrl = window.SpotifyService.uriToEmbed(track.uri);
                  console.log(`     Embed URL: ${embedUrl}`);
               }
            });
         }

         let artistTracks = [];
         if (popularArtist && popularArtist.artist_uri) {
            artistTracks = await API.getArtistTracks(popularArtist.artist_uri, 10);
            console.log('🎸 Artist Tracks from API:', artistTracks);
         }

         UI.renderHomeView(popularTracks, popularArtist, artistTracks, playlists);
      } catch (error) {
         console.error('Error loading home:', error);
         UI.showEmptyState();
      }
   },

   attachEventListeners() {
      document.querySelector('.sidebar-header').addEventListener('click', () => {
            this.loadHome();
      });

      document.getElementById('authButton').addEventListener('click', () => {
         if (this.currentUser) {
            this.handleLogout();
         } else {
            UI.showModal('authModal');
         }
      });


      document.getElementById('createPlaylistBtn').addEventListener('click', () => {
         if (!this.currentUser) {
            UI.showToast('Please login to create playlists', 'warning');
            return;
         }
         this.selectedTracksForNewPlaylist = [];
         UI.showModal('playlistModal');
      });

      document.getElementById('searchInput').addEventListener('input', (e) => {
         const query = e.target.value;
         const clearBtn = document.getElementById('clearSearchBtn');
         if (clearBtn) {
            clearBtn.style.display = query.length > 0 ? 'block' : 'none';
         }
         this.handleSearch(query);
      });

      const clearSearchBtn = document.getElementById('clearSearchBtn');
      if (clearSearchBtn) {
         clearSearchBtn.addEventListener('click', () => {
            const searchInput = document.getElementById('searchInput');
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            this.handleSearch('');
            searchInput.focus();
         });
      }

      document.getElementById('searchInput').addEventListener('keypress', (e) => {
         if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (query) {
               clearTimeout(this.searchTimeout);
               this.performSearch(query);
            }
         }
      });

      document.getElementById('closeModal').addEventListener('click', () => {
         this.closePlaylistModal();
      });

      document.getElementById('cancelModal').addEventListener('click', () => {
         this.closePlaylistModal();
      });

      document.getElementById('savePlaylist').addEventListener('click', () => {
         this.handleCreatePlaylist();
      });

      document.getElementById('closeAuthModal').addEventListener('click', () => {
         UI.hideModal('authModal');
      });

      document.querySelectorAll('.auth-tab').forEach(tab => {
         tab.addEventListener('click', (e) => {
            this.switchAuthTab(e.target.dataset.tab);
         });
      });

      document.getElementById('authSubmit').addEventListener('click', () => {
         this.handleAuth();
      });

      document.getElementById('getRecommendationsBtn').addEventListener('click', () => {
         this.handleGetRecommendations();
      });

      document.getElementById('playlistsList').addEventListener('click', (e) => {
         const playlistItem = e.target.closest('.playlist-item');
         if (playlistItem) {
            this.handlePlaylistClick(playlistItem.dataset.playlistId);
         }
      });

      document.getElementById('songsTableBody').addEventListener('click', (e) => {
         const songRow = e.target.closest('.song-row');
         const removeBtn = e.target.closest('.btn-remove-track');
         const removeEmbedBtn = e.target.closest('.btn-remove-track-embed');
         const playSpotifyBtn = e.target.closest('.btn-play-spotify');

         if (removeBtn || removeEmbedBtn) {
            e.stopPropagation();
            const btn = removeBtn || removeEmbedBtn;
            this.handleRemoveTrack(btn.dataset.playlistId, btn.dataset.trackId);
         } else if (playSpotifyBtn) {
            e.stopPropagation();
            if (playSpotifyBtn.classList.contains('playing')) {
               // If already playing, stop/pause it (hide embed & reset icon)
               document.getElementById('spotifySidebarEmbed').style.display = 'none';
               document.getElementById('spotifySidebarEmbed').innerHTML = '';
               playSpotifyBtn.innerHTML = '<i class="fas fa-play"></i>';
               playSpotifyBtn.classList.remove('playing');
            } else {
               this.playSpotifyEmbed(playSpotifyBtn.dataset.embedUrl, playSpotifyBtn);
               if (songRow) {
                  this.handleTrackClick(songRow.dataset.trackId, songRow.dataset.trackData);
               }
            }
         } else if (songRow) {
            this.handleTrackClick(songRow.dataset.trackId, songRow.dataset.trackData);
         }
      });

      document.getElementById('recommendationsTable').addEventListener('click', (e) => {
         const addBtn = e.target.closest('.btn-add-recommendation');
         const trackRow = e.target.closest('.track-row');
         const playSpotifyBtn = e.target.closest('.btn-play-spotify');

         if (addBtn) {
            e.stopPropagation();
            this.handleAddRecommendation(addBtn.dataset.trackId, addBtn);
         } else if (playSpotifyBtn) {
            e.stopPropagation();
            if (playSpotifyBtn.classList.contains('playing')) {
               document.getElementById('spotifySidebarEmbed').style.display = 'none';
               document.getElementById('spotifySidebarEmbed').innerHTML = '';
               playSpotifyBtn.innerHTML = '<i class="fas fa-play"></i>';
               playSpotifyBtn.classList.remove('playing');
            } else {
               this.playSpotifyEmbed(playSpotifyBtn.dataset.embedUrl, playSpotifyBtn);
               if (trackRow) {
                  this.handleTrackClick(trackRow.dataset.trackId, trackRow.dataset.trackData);
               }
            }
         } else if (trackRow) {
            this.handleTrackClick(trackRow.dataset.trackId, trackRow.dataset.trackData);
         }
      });

      document.getElementById('searchResultsBody').addEventListener('click', (e) => {
         const songRow = e.target.closest('.search-result-item');
         const artistRow = e.target.closest('.artist-result-item');
         const addBtn = e.target.closest('.btn-add-from-search');
         const dropdownBtn = e.target.closest('.btn-playlist-dropdown');
         const newPlaylistBtn = e.target.closest('.btn-create-playlist-with-track');
         const viewArtistBtn = e.target.closest('.btn-view-artist');
         const playSpotifyBtn = e.target.closest('.btn-play-spotify');

         if (dropdownBtn) {
            e.stopPropagation();
            this.toggleSearchDropdown(dropdownBtn);
         } else if (playSpotifyBtn) {
            e.stopPropagation();
            if (playSpotifyBtn.classList.contains('playing')) {
               document.getElementById('spotifySidebarEmbed').style.display = 'none';
               document.getElementById('spotifySidebarEmbed').innerHTML = '';
               playSpotifyBtn.innerHTML = '<i class="fas fa-play"></i>';
               playSpotifyBtn.classList.remove('playing');
            } else {
               this.playSpotifyEmbed(playSpotifyBtn.dataset.embedUrl, playSpotifyBtn);
               if (songRow) {
                  this.handleTrackClick(songRow.dataset.trackId, songRow.dataset.trackData);
               } else if (artistRow) { // In case it's in an artist row
                  this.handleTrackClick(artistRow.dataset.trackId, artistRow.dataset.trackData);
               }
            }
         } else if (newPlaylistBtn) {
            e.stopPropagation();
            const trackData = JSON.parse(newPlaylistBtn.dataset.track);
            this.createPlaylist(trackData);
         } else if (addBtn) {
            e.stopPropagation();
            const playlistId = addBtn.dataset.playlistId;
            const trackId = addBtn.dataset.trackId;
            if (playlistId) {
               this.handleAddToSpecificPlaylist(playlistId, trackId);
            }
         } else if (viewArtistBtn) {
            const artistUri = viewArtistBtn.dataset.artistUri;
            this.handleViewArtistTracks(artistUri);
         } else if (songRow) {
            this.handleTrackClick(songRow.dataset.trackId, songRow.dataset.trackData);
         } else if (artistRow) {
            // Handle artist row click - maybe show artist details
            const artistUri = artistRow.dataset.artistUri;
            this.handleViewArtistTracks(artistUri);
         }
      });

      document.getElementById('contentArea').addEventListener('click', (e) => {
         const homeTrackRow = e.target.closest('.home-track-row');
         const playSpotifyBtn = e.target.closest('.btn-play-spotify');
         const dropdownBtn = e.target.closest('.btn-playlist-dropdown');
         const newPlaylistBtn = e.target.closest('.btn-create-playlist-with-track');
         const addBtn = e.target.closest('.btn-add-from-search');

         if (dropdownBtn) {
            e.stopPropagation();
            this.toggleSearchDropdown(dropdownBtn);
         } else if (newPlaylistBtn) {
            e.stopPropagation();
            const trackData = JSON.parse(newPlaylistBtn.dataset.track);
            this.createPlaylist(trackData);
         } else if (addBtn) {
            e.stopPropagation();
            const playlistId = addBtn.dataset.playlistId;
            const trackId = addBtn.dataset.trackId;
            if (playlistId) {
               this.handleAddToSpecificPlaylist(playlistId, trackId);
            }
         } else if (playSpotifyBtn) {
            e.stopPropagation();
            if (playSpotifyBtn.classList.contains('playing')) {
               document.getElementById('spotifySidebarEmbed').style.display = 'none';
               document.getElementById('spotifySidebarEmbed').innerHTML = '';
               playSpotifyBtn.innerHTML = '<i class="fas fa-play"></i>';
               playSpotifyBtn.classList.remove('playing');
            } else {
               this.playSpotifyEmbed(playSpotifyBtn.dataset.embedUrl, playSpotifyBtn);
               if (homeTrackRow) {
                  this.handleTrackClick(homeTrackRow.dataset.trackId, homeTrackRow.dataset.trackData);
               }
            }
         } else if (homeTrackRow && this.currentView === 'home') {
            this.handleTrackClick(homeTrackRow.dataset.trackId, homeTrackRow.dataset.trackData);
         }
      });

      document.getElementById('playlistMenuBtn').addEventListener('click', (e) => {
         e.stopPropagation();
         this.togglePlaylistDropdown();
      });

      document.getElementById('deletePlaylistBtn').addEventListener('click', () => {
         this.handleDeletePlaylist();
      });

      document.getElementById('renamePlaylistBtn').addEventListener('click', () => {
         this.handleRenamePlaylist();
      });

      document.addEventListener('click', (e) => {
         const dropdown = document.getElementById('playlistDropdown');
         if (dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
         }

         document.querySelectorAll('.playlist-dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
         });
      });

      document.getElementById('miniSearchInput').addEventListener('input', (e) => {
         this.handleMiniSearch(e.target.value);
      });

      document.getElementById('miniSearchResults').addEventListener('click', (e) => {
         const addBtn = e.target.closest('.btn-add-to-new-playlist');
         const viewArtistBtn = e.target.closest('.btn-view-artist-mini');

         if (addBtn) {
            const trackData = JSON.parse(addBtn.dataset.track);
            this.addTrackToNewPlaylist(trackData);
         } else if (viewArtistBtn) {
            const artistUri = viewArtistBtn.dataset.artistUri;
            UI.hideModal('playlistModal');
            this.handleViewArtistTracks(artistUri);
         }
      });

      document.getElementById('selectedTracksList').addEventListener('click', (e) => {
         const removeBtn = e.target.closest('.btn-remove-selected');
         if (removeBtn) {
            const trackId = removeBtn.dataset.trackId;
            this.removeTrackFromNewPlaylist(trackId);
         }
      });
   },

   async handleViewArtistTracks(artistUri) {
      try {
         this.currentView = 'search';
         const results = await API.searchTracks('', artistUri, 50);
         const playlists = this.currentUser ? await API.getPlaylists() : [];
         UI.renderSearchResults({ tracks: results.tracks, artists: [] }, playlists, `Artist: ${results.tracks[0]?.artist || 'Unknown'}`);
      } catch (error) {
         console.error('Error loading artist tracks:', error);
         UI.showToast('Error loading artist tracks', 'error');
      }
   },

   async createPlaylist(track) {
      if (!this.currentUser) {
         UI.showToast('Please login to create playlists', 'warning');
         return;
      }
      this.selectedTracksForNewPlaylist = [];
      
      if (track && track.id) {
         const normalizedTrack = this.normalizeTrackForUi(track);
         this.selectedTracksForNewPlaylist.push(normalizedTrack);
         this.lastMiniSearchResults = { tracks: [normalizedTrack], artists: [] };
      } else {
         this.lastMiniSearchResults = { tracks: [], artists: [] };
      }
      
      const searchInput = document.getElementById('miniSearchInput');
      if (searchInput) searchInput.value = '';
      
      UI.renderSelectedTracks(this.selectedTracksForNewPlaylist);
      UI.renderMiniSearchResults(this.lastMiniSearchResults, this.selectedTracksForNewPlaylist);
      
      UI.showModal('playlistModal');
   },

   toggleSearchDropdown(dropdownBtn) {
      const currentDropdown = dropdownBtn?.parentElement?.querySelector('.playlist-dropdown-menu');
      if (!currentDropdown) return;

      const shouldShow = !currentDropdown.classList.contains('show');

      document.querySelectorAll('.playlist-dropdown-menu.show').forEach(menu => {
         menu.classList.remove('show');
      });

      if (shouldShow) {
         currentDropdown.classList.add('show');
      }
   },

   async handleAddToSpecificPlaylist(playlistId, trackId) {
      console.log('🎵 Adding track to playlist:', { playlistId, trackId, type: typeof trackId });

      if (!this.currentUser) {
         UI.showToast('Please login first', 'warning');
         console.warn('⚠️ User not logged in');
         return;
      }

      try {
         console.log('📤 Calling API.addTrackToPlaylist...');
         await API.addTrackToPlaylist(playlistId, trackId);
         console.log('✅ Track added successfully');
         UI.showToast('Track added to playlist!', 'success');
         await this.loadPlaylists();
         await API.logClickEvent({
            item_id: trackId,
            item_type: 'track',
            playlist_id: playlistId,
            context: {
               source: 'search',
               timestamp: new Date().toISOString()
            }
         });
      } catch (error) {
         console.error('❌ Error adding track:', error);
         console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            playlistId,
            trackId
         });
         UI.showToast('Error adding track. track is already in playlist or an error occurred.', 'error');
      }
   },

   togglePlaylistDropdown() {
      const dropdown = document.getElementById('playlistDropdown');
      dropdown.classList.toggle('show');
   },

   async handleDeletePlaylist() {
      if (!this.currentPlaylist) {
         UI.showToast('No playlist selected', 'warning');
         return;
      }

      if (!confirm('Are you sure you want to delete this playlist? This action cannot be undone.')) {
         return;
      }

      try {
         await API.deletePlaylist(this.currentPlaylist);
         this.currentPlaylist = null;
         await this.loadPlaylists();
         await this.loadHome();
         UI.showToast('Playlist deleted successfully', 'success');
      } catch (error) {
         console.error('Error deleting playlist:', error);
         UI.showToast('Error deleting playlist. Please try again.', 'error');
      }
   },

   async handleRenamePlaylist() {
      if (!this.currentPlaylist) {
         UI.showToast('No playlist selected', 'warning');
         return;
      }

      const newName = prompt('Enter new playlist name:');
      if (!newName || !newName.trim()) {
         UI.showToast("The name of playlist hasn't been changed", 'warning');
         return;
      }

      try {
         await API.updatePlaylist(this.currentPlaylist, { name: newName.trim() });
         await this.loadPlaylists();
         await this.handlePlaylistClick(this.currentPlaylist);
         UI.showToast('Playlist renamed successfully', 'success');
      } catch (error) {
         console.error('Error renaming playlist:', error);
         UI.showToast('Error renaming playlist. Please try again.', 'error');
      }
   },

   closePlaylistModal() {
      UI.hideModal('playlistModal');
      document.getElementById('playlistNameInput').value = '';
      document.getElementById('miniSearchInput').value = '';
      document.getElementById('miniSearchResults').innerHTML = '';
      this.selectedTracksForNewPlaylist = [];
      this.lastMiniSearchResults = { tracks: [], artists: [] };
      UI.renderSelectedTracks([]);
   },

   handleMiniSearch(query) {
      clearTimeout(this.miniSearchTimeout);

      if (!query.trim()) {
         document.getElementById('miniSearchResults').innerHTML = '';
         this.lastMiniSearchResults = { tracks: [], artists: [] };
         return;
      }

      this.miniSearchTimeout = setTimeout(async () => {
         try {
            const [tracksResult, artistsResult] = await Promise.all([
               API.searchTracks(query, null, 10),
               API.searchArtists(query, 5)
            ]);

            // Get tracks by matching artists
            const artistTracks = [];
            if (artistsResult.artists && artistsResult.artists.length > 0) {
               const artistTracksPromises = artistsResult.artists.map(artist =>
                  API.getArtistTracks(artist.artistUri, 10)
               );
               const artistTracksResults = await Promise.all(artistTracksPromises);
               artistTracksResults.forEach(tracks => {
                  if (tracks && tracks.length > 0) {
                     artistTracks.push(...tracks);
                  }
               });
            }

            // Combine tracks - remove duplicates based on track ID
            const allTracks = [...(tracksResult.tracks || [])];
            const trackIds = new Set(allTracks.map(t => t.id));

            artistTracks.forEach(track => {
               if (!trackIds.has(track.id)) {
                  allTracks.push(track);
                  trackIds.add(track.id);
               }
            });

            this.lastMiniSearchResults = {
               tracks: allTracks,
               artists: artistsResult.artists || []
            };

            UI.renderMiniSearchResults(this.lastMiniSearchResults, this.selectedTracksForNewPlaylist);
         } catch (error) {
            console.error('Error in mini search:', error);
            document.getElementById('miniSearchResults').innerHTML =
               '<div class="mini-search-empty">Error searching. Please try again.</div>';
         }
      }, CONFIG.SETTINGS.SEARCH_DEBOUNCE_MS);
   },

   addTrackToNewPlaylist(track) {
      const normalizedTrack = this.normalizeTrackForUi(track);
      const exists = this.selectedTracksForNewPlaylist.some(t => t.id === normalizedTrack.id);
      if (exists) {
         return;
      }

      this.selectedTracksForNewPlaylist.push(normalizedTrack);
      UI.renderSelectedTracks(this.selectedTracksForNewPlaylist);
      UI.renderMiniSearchResults(this.lastMiniSearchResults, this.selectedTracksForNewPlaylist);
   },

   removeTrackFromNewPlaylist(trackId) {
      this.selectedTracksForNewPlaylist = this.selectedTracksForNewPlaylist.filter(t => t.id != trackId);
      UI.renderSelectedTracks(this.selectedTracksForNewPlaylist);
      UI.renderMiniSearchResults(this.lastMiniSearchResults, this.selectedTracksForNewPlaylist);
   },

   async loadPlaylists() {
      try {
         if (this.currentUser) {
            const playlists = await API.getPlaylists();
            UI.renderPlaylists(playlists);
         } else {
            UI.renderPlaylists([]);
         }
      } catch (error) {
         console.error('Error loading playlists:', error);
      }
   },

   async handlePlaylistClick(playlistId) {
      try {
         this.currentView = 'playlist';
         this.currentPlaylist = playlistId;
         this.currentRecommendations = null;
         window.localStorage.setItem(CONFIG.STORAGE_KEYS.CURRENT_PLAYLIST, playlistId);

         const [playlist, tracks] = await Promise.all([
            API.getPlaylist(playlistId),
            API.getPlaylistTracks(playlistId)
         ]);

         UI.setActivePlaylist(playlistId);
         UI.renderPlaylistView(playlist, tracks);
         UI.renderRecommendations(null);
      } catch (error) {
         console.error('Error loading playlist:', error);
      }
   },

   async handleTrackClick(trackId, trackDataStr) {
      try {
         let track;

         if (trackDataStr) {
            track = JSON.parse(trackDataStr);
         } else {
            const tracks = await API.getPlaylistTracks(this.currentPlaylist);
            track = tracks.find(t => t.id == trackId || t.uri === trackId);
         }

         if (track) {
            // Cập nhật UI cơ bản ngay lập tức
            track = this.normalizeTrackForUi(track);
            UI.renderNowPlaying(track);
            UI.setPlayingTrack(trackId);
            window.localStorage.setItem(CONFIG.STORAGE_KEYS.NOW_PLAYING, JSON.stringify(track));

            // Bất đồng bộ gọi Spotify API lấy ảnh album nếu có track URI
            if (track.uri && window.SpotifyService) {
               window.SpotifyService.getTrackInfo(track.uri).then(spotifyInfo => {
                  if (spotifyInfo && spotifyInfo.album_image) {
                     track.albumImage = spotifyInfo.album_image;
                     // Cập nhật lại UI với ảnh thật từ Spotify
                     UI.renderNowPlaying(track);
                     window.localStorage.setItem(CONFIG.STORAGE_KEYS.NOW_PLAYING, JSON.stringify(track));
                  }
               }).catch(e => console.error('Error fetching Spotify cover:', e));
            }

            await API.logViewEvent({
               item_id: track.uri || track.id,
               item_type: 'track',
               context: {
                  playlist_id: this.currentPlaylist,
                  timestamp: new Date().toISOString()
               }
            });
         }
      } catch (error) {
         console.error('Error loading track:', error);
      }
   },

   async handleCreatePlaylist() {
      if (this.isCreatingPlaylist) {
         return;
      }

      const name = document.getElementById('playlistNameInput').value.trim();

      if (!name) {
         UI.showToast('Please enter a playlist name', 'warning');
         return;
      }

      this.isCreatingPlaylist = true;

      try {
         const playlist = await API.createPlaylist(name);

         if (this.selectedTracksForNewPlaylist.length > 0) {
            for (const track of this.selectedTracksForNewPlaylist) {
               try {
                  await API.addTrackToPlaylist(playlist.id, track.id);
               } catch (error) {
                  console.error(`Error adding track ${track.id}:`, error);
               }
            }
         }

         const addedCount = this.selectedTracksForNewPlaylist.length;
         this.closePlaylistModal();
         await this.loadPlaylists();
         UI.showToast(`Playlist created with ${addedCount} songs!`, 'success');

         await this.handlePlaylistClick(playlist.id);
      } catch (error) {
         console.error('Error creating playlist:', error);
         UI.showToast('Error creating playlist. Please try again.', 'error');
      } finally {
         this.isCreatingPlaylist = false;
      }
   },

   handleSearch(query) {
      clearTimeout(this.searchTimeout);

      if (!query.trim()) {
         if (this.currentView === 'home') {
            this.loadHome();
         } else if (this.currentPlaylist) {
            this.handlePlaylistClick(this.currentPlaylist);
         } else {
            this.loadHome();
         }
         return;
      }

      this.searchTimeout = setTimeout(() => {
         this.performSearch(query);
      }, CONFIG.SETTINGS.SEARCH_DEBOUNCE_MS);
   },

   async performSearch(query) {
      try {
         this.currentView = 'search';

         const [tracksResult, artistsResult] = await Promise.all([
            API.searchTracks(query, null, 50),
            API.searchArtists(query, 10)
         ]);

         const playlists = this.currentUser ? await API.getPlaylists() : [];

         // Get tracks by matching artists
         const artistTracks = [];
         if (artistsResult.artists && artistsResult.artists.length > 0) {
            const artistTracksPromises = artistsResult.artists.map(artist =>
               API.getArtistTracks(artist.artistUri, 20)
            );
            const artistTracksResults = await Promise.all(artistTracksPromises);
            artistTracksResults.forEach(tracks => {
               if (tracks && tracks.length > 0) {
                  artistTracks.push(...tracks);
               }
            });
         }

         // Combine tracks - remove duplicates based on track ID
         const allTracks = [...(tracksResult.tracks || [])];
         const trackIds = new Set(allTracks.map(t => t.id));

         artistTracks.forEach(track => {
            if (!trackIds.has(track.id)) {
               allTracks.push(track);
               trackIds.add(track.id);
            }
         });

         UI.renderSearchResults(
            {
               tracks: allTracks,
               artists: artistsResult.artists || []
            },
            playlists,
            `Results for "${query}"`
         );
      } catch (error) {
         console.error('Error searching:', error);
         UI.showToast('Error performing search', 'error');
      }
   },

   async handleRemoveTrack(playlistId, trackId) {
      if (!confirm('Remove this track from the playlist?')) {
         return;
      }

      try {
         await API.removeTrackFromPlaylist(playlistId, trackId);
         await this.loadPlaylists();
         await this.handlePlaylistClick(playlistId);
         UI.showToast('Track removed from playlist', 'success');
      } catch (error) {
         console.error('Error removing track:', error);
         UI.showToast('Error removing track. Please try again.', 'error');
      }
   },

   async handleGetRecommendations() {
      if (!this.currentPlaylist) {
         UI.showToast('Please select a playlist first', 'warning');
         return;
      }

      try {
         const recommendationsTable = document.getElementById('recommendationsTable');
         recommendationsTable.innerHTML = '<p style="padding: 2rem; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Loading recommendations...</p>';

         const tracks = await API.getPlaylistTracks(this.currentPlaylist);

         if (!tracks || tracks.length === 0) {
            UI.showToast('Playlist is empty. Add some tracks first!', 'warning');
            UI.renderRecommendations(null);
            return;
         }

         const trackUris = tracks.map(t => t.uri);
         const artistUris = [...new Set(tracks.map(t => t.artistUri).filter(Boolean))];

         const recommendations = await API.getAllRecommendations(trackUris, artistUris, 10);
         const filteredRecommendations = this.filterRecommendationsByPlaylistTracks(recommendations, tracks);
         console.log('📊 Recommendations from API:', recommendations);
         console.log('🧹 Filtered recommendations:', filteredRecommendations);
         this.currentRecommendations = filteredRecommendations;

         UI.renderRecommendations(filteredRecommendations);

         const allTracks = [
            ...filteredRecommendations.tracks.items.flatMap(item => item.consequents),
            ...filteredRecommendations.artists.items.flatMap(item => item.topTracks)
         ];

         for (const track of allTracks) {
            // 🔧 FIX: Sử dụng trackUri thay vì uri
            const itemId = track.trackUri || track.uri || track.id;

            if (!itemId) {
               console.warn('Skipping track without ID:', track);
               continue;
            }

            try {
               await API.logViewEvent({
                  item_id: itemId,
                  item_type: 'track',
                  context: {
                     source: 'recommendation',
                     playlist_id: this.currentPlaylist,
                     timestamp: new Date().toISOString()
                  }
               });
            } catch (error) {
               console.warn('Failed to log view event for track:', itemId, error);
               // Continue với tracks khác
            }
         }

         const totalRecs = filteredRecommendations.tracks.count + filteredRecommendations.artists.count;

         if (totalRecs > 0) {
            UI.showToast(`Found ${totalRecs} rules! (${filteredRecommendations.tracks.count} tracks, ${filteredRecommendations.artists.count} artists)`, 'success');
         } else {
            UI.showToast('No rules found for this playlist', 'info');
         }

      } catch (error) {
         console.error('Error getting recommendations:', error);
         UI.showToast('Error loading recommendations. Please try again.', 'error');
         UI.renderRecommendations(null);
      }
   },

   async handleAddRecommendation(trackId, button) {
      if (!this.currentPlaylist) {
         UI.showToast('Please select a playlist first', 'warning');
         return;
      }

      const trackUri = button ? button.dataset.trackUri : null;
      const ruleId = button ? button.dataset.ruleId : null;
      const ruleType = button ? button.dataset.ruleType : null;

      try {
         await API.addTrackToPlaylist(this.currentPlaylist, trackId);
         await this.loadPlaylists();

         const tracks = await API.getPlaylistTracks(this.currentPlaylist);
         const playlist = await API.getPlaylist(this.currentPlaylist);
         UI.renderPlaylistView(playlist, tracks);

         UI.showToast('Track added to playlist!', 'success');

         await API.logClickEvent({
            item_id: trackUri || trackId,
            item_type: 'track',
            rule_id: ruleId ? parseInt(ruleId) : null,
            rule_type: ruleType || 'track',
            playlist_id: this.currentPlaylist,
            context: {
               source: 'recommendation',
               timestamp: new Date().toISOString()
            }
         });
      } catch (error) {
         console.error('Error adding track:', error);
         UI.showToast('Error adding track. track is already in playlist or an error occurred.', 'error');
      }
   },

   switchAuthTab(tab) {
      document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
      document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

      if (tab === 'login') {
         document.getElementById('loginForm').classList.remove('hidden');
         document.getElementById('registerForm').classList.add('hidden');
         document.getElementById('authSubmit').textContent = 'Login';
         document.getElementById('authModalTitle').textContent = 'Login';
      } else {
         document.getElementById('loginForm').classList.add('hidden');
         document.getElementById('registerForm').classList.remove('hidden');
         document.getElementById('authSubmit').textContent = 'Register';
         document.getElementById('authModalTitle').textContent = 'Register';
      }
   },

   async handleAuth() {
      const isLogin = document.querySelector('.auth-tab.active').dataset.tab === 'login';

      try {
         if (isLogin) {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const data = await API.login(email, password);
            this.currentUser = data.user;
         } else {
            const name = document.getElementById('registerName').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const data = await API.register(name, email, password);
            this.currentUser = data.user;
         }

         UI.updateAuthButton(this.currentUser);
         UI.hideModal('authModal');
         await this.loadHome();
         UI.showToast('Welcome!', 'success');
      } catch (error) {
         console.error('Auth error:', error);
         UI.showToast('Authentication failed. Please try again.', 'error');
      }
   },

   async handleLogout() {
      if (!confirm('Are you sure you want to logout?')) {
         return;
      }

      try {
         await API.logout();
         this.currentUser = null;
         this.currentPlaylist = null;
         this.currentView = 'home';
         this.currentRecommendations = null;
         UI.updateAuthButton(null);
         UI.renderPlaylists([]);
         UI.showEmptyState();
         UI.renderNowPlaying(null);
         UI.showToast('Logged out successfully', 'success');
         UI.showModal('authModal');
      } catch (error) {
         console.error('Logout error:', error);
      }
   },

   async getPlaylistTracks(playlistId) {
      try {
         return await API.getPlaylistTracks(playlistId);
      } catch (error) {
         console.error('Error getting playlist tracks:', error);
         return [];
      }
   },
};

document.addEventListener('DOMContentLoaded', () => {
   App.init();
});
