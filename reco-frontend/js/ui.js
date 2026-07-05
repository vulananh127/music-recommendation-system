const UI = {
   renderPlaylists(playlists) {
      const playlistsList = document.getElementById('playlistsList');

      if (!playlists || playlists.length === 0) {
         playlistsList.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.9rem;">No playlists yet</p>';
         return;
      }

      playlistsList.innerHTML = playlists.map(playlist => `
            <button class="playlist-item" data-playlist-id="${playlist.id}">
                <span class="playlist-item-name">${this.escapeHtml(playlist.name)}</span>
                <span class="playlist-item-count">${playlist.trackCount || 0} songs</span>
            </button>
        `).join('');
   },

   renderHomeView(popularTracks, popularArtist, artistTracks, playlists = []) {
      document.getElementById('emptyState').classList.add('hidden');
      document.getElementById('playlistView').classList.add('hidden');
      document.getElementById('searchResults').classList.add('hidden');

      const homeView = document.getElementById('homeView');
      homeView.classList.remove('hidden');

      const favoriteSongsBody = document.getElementById('favoriteSongsBody');
      if (!popularTracks || popularTracks.length === 0) {
         favoriteSongsBody.innerHTML = '<p style="padding: 2rem; color: var(--text-secondary);">No favorite songs yet! Please login to view popular tracks.</p>';
      } else {
         favoriteSongsBody.innerHTML = popularTracks.map((track, index) => {
            const embedUrl = track.uri ? window.SpotifyService.uriToEmbed(track.uri) : '';
            const trackData = {
               id: track.id,
               uri: track.uri,
               title: track.title,
               artist: track.artist_name || track.artist,
               album: track.album_name || track.album,
               albumUri: track.albumUri || track.album_uri,
               durationMs: this.getTrackDurationMs(track)
            };
            return `
               <div class="search-result-item home-track-row track-row" data-track-id="${track.id}" data-track-data='${JSON.stringify(trackData).replace(/'/g, "&#39;")}' style="grid-template-columns: 50px 3fr 2fr 1fr 100px;">
                  <div class="col-play">
                     ${index + 1}
                  </div>
                  <div>${this.escapeHtml(track.title || 'Unknown Track')}</div>
                  <div style="color: var(--text-secondary)">${this.escapeHtml(track.artist_name || track.artist || 'Unknown Artist')}</div>
                  <div style="color: var(--text-secondary); text-align: center">${this.formatDuration(trackData.durationMs)}</div>
                  <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; position: relative;">
                     ${embedUrl ? `<button class="btn-add btn-play-spotify" data-embed-url="${embedUrl}" title="Play on Spotify"><i class="fas fa-play"></i></button>` : ''}
                     ${playlists && playlists.length > 0 ? `
                        <button class="btn-add btn-playlist-dropdown" data-track-id="${track.id}" title="Add to playlist">
                           <i class="fas fa-plus"></i>
                        </button>
                        <div class="playlist-dropdown-menu">
                           <button class="dropdown-item btn-create-playlist-with-track" data-track='${JSON.stringify(trackData).replace(/'/g, "&#39;")}'>
                              <i class="fas fa-plus-circle"></i>
                              <span>Create New Playlist</span>
                           </button>
                           <div class="dropdown-divider"></div>
                           ${playlists.map(playlist => `
                              <button class="dropdown-item btn-add-from-search" data-playlist-id="${playlist.id}" data-track-id="${track.id}">
                                 <i class="fas fa-list-music"></i>
                                 <span>${this.escapeHtml(playlist.name)}</span>
                              </button>
                           `).join('')}
                        </div>
                     ` : `
                        <button class="btn-add btn-create-playlist-with-track" data-track='${JSON.stringify(trackData).replace(/'/g, "&#39;")}' title="Create playlist with this track">
                           <i class="fas fa-plus"></i>
                        </button>
                     `}
                  </div>
               </div>
            `;
         }).join('');
      }

      const favoriteArtistBody = document.getElementById('favoriteArtistBody');
      const favoriteArtistTitle = document.getElementById('favoriteArtistTitle');

      if (popularArtist && artistTracks && artistTracks.length > 0) {
         favoriteArtistTitle.textContent = `Favorite Artist: ${this.escapeHtml(popularArtist.artist_name)}`;

         favoriteArtistBody.innerHTML = artistTracks.map((track, index) => {
            const embedUrl = track.uri ? window.SpotifyService.uriToEmbed(track.uri) : '';
            const trackData = {
               id: track.id,
               uri: track.uri,
               title: track.title,
               artist: track.artist_name || track.artist,
               album: track.album_name || track.album,
               albumUri: track.albumUri || track.album_uri,
               durationMs: this.getTrackDurationMs(track)
            };
            return `
               <div class="search-result-item home-track-row track-row" data-track-id="${track.id}" data-track-data='${JSON.stringify(trackData).replace(/'/g, "&#39;")}' style="grid-template-columns: 50px 3fr 2fr 1fr 100px;">
                  <div class="col-play">
                     ${index + 1}
                  </div>
                  <div>${this.escapeHtml(track.title || 'Unknown Track')}</div>
                  <div style="color: var(--text-secondary)">${this.escapeHtml(track.artist_name || track.artist || 'Unknown Artist')}</div>
                  <div style="color: var(--text-secondary); text-align: center">${this.formatDuration(trackData.durationMs)}</div>
                  <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; position: relative;">
                     ${embedUrl ? `<button class="btn-add btn-play-spotify" data-embed-url="${embedUrl}" title="Play on Spotify"><i class="fas fa-play"></i></button>` : ''}
                     ${playlists && playlists.length > 0 ? `
                        <button class="btn-add btn-playlist-dropdown" data-track-id="${track.id}" title="Add to playlist">
                           <i class="fas fa-plus"></i>
                        </button>
                        <div class="playlist-dropdown-menu">
                           <button class="dropdown-item btn-create-playlist-with-track" data-track='${JSON.stringify(trackData).replace(/'/g, "&#39;")}'>
                              <i class="fas fa-plus-circle"></i>
                              <span>Create New Playlist</span>
                           </button>
                           <div class="dropdown-divider"></div>
                           ${playlists.map(playlist => `
                              <button class="dropdown-item btn-add-from-search" data-playlist-id="${playlist.id}" data-track-id="${track.id}">
                                 <i class="fas fa-list-music"></i>
                                 <span>${this.escapeHtml(playlist.name)}</span>
                              </button>
                           `).join('')}
                        </div>
                     ` : `
                        <button class="btn-add btn-create-playlist-with-track" data-track='${JSON.stringify(trackData).replace(/'/g, "&#39;")}' title="Create playlist with this track">
                           <i class="fas fa-plus"></i>
                        </button>
                     `}
                  </div>
               </div>
            `;
         }).join('');
      } else {
         favoriteArtistTitle.textContent = 'Favorite Artist';
         favoriteArtistBody.innerHTML = '<p style="padding: 2rem; color: var(--text-secondary);">No favorite artist yet! Please login to view.</p>';
      }
   },

   renderPlaylistView(playlist, tracks) {
      document.getElementById('emptyState').classList.add('hidden');
      document.getElementById('searchResults').classList.add('hidden');
      document.getElementById('homeView').classList.add('hidden');
      const playlistView = document.getElementById('playlistView');
      playlistView.classList.remove('hidden');

      document.getElementById('playlistTitle').textContent = playlist.name;
      document.getElementById('playlistSongCount').textContent = `${tracks.length} songs`;

      this.renderTracks(tracks, playlist.id);
   },

   renderTracks(tracks, playlistId) {
      const songsTableBody = document.getElementById('songsTableBody');

      if (!tracks || tracks.length === 0) {
         songsTableBody.innerHTML = '<p style="padding: 2rem; color: var(--text-secondary);">No songs in this playlist yet</p>';
         return;
      }

      songsTableBody.innerHTML = tracks.map((track, index) => {
         const trackData = {
            id: track.id,
            uri: track.uri,
            title: track.title || track.track_name,
            artist: track.artist || track.artist_name,
            album: track.album || track.album_name,
            albumUri: track.albumUri || track.album_uri,
            durationMs: this.getTrackDurationMs(track)
         };
         const embedUrl = track.uri ? window.SpotifyService.uriToEmbed(track.uri) : '';
         return `
               <div class="search-result-item song-row track-row" data-track-id="${track.id}" data-track-data='${JSON.stringify(trackData).replace(/'/g, "&#39;")}' style="grid-template-columns: 50px 3fr 2fr 1fr 100px;">
                  <div class="col-play">
                     ${index + 1}
                  </div>
                  <div>${this.escapeHtml(trackData.title || 'Unknown Track')}</div>
                  <div style="color: var(--text-secondary)">${this.escapeHtml(trackData.artist || 'Unknown Artist')}</div>
                  <div style="color: var(--text-secondary); text-align: center">${this.formatDuration(trackData.durationMs)}</div>
               <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; position: relative;">
                  ${embedUrl ? `<button class="btn-add btn-play-spotify" data-embed-url="${embedUrl}" title="Play on Spotify"><i class="fas fa-play"></i></button>` : ''}
                  <button class="btn-remove-track" data-track-id="${track.id}" data-playlist-id="${playlistId}" title="Remove from playlist" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 4px;">
                     <i class="fas fa-trash"></i>
                  </button>
               </div>
            </div>
         `;
      }).join('');
   },

   renderRecommendations(recommendations) {
      const recommendationsTable = document.getElementById('recommendationsTable');

      if (!recommendations) {
         recommendationsTable.innerHTML = '<p style="padding: 2rem; color: var(--text-secondary);">No recommendations available. Click "Get Recommendations" to find similar songs.</p>';
         return;
      }

      const trackRecs = recommendations.tracks?.items || [];
      const artistRecs = recommendations.artists?.items || [];

      const getBasedOnText = (antecedentsName) => {
         if (!Array.isArray(antecedentsName)) return '';
         return antecedentsName
            .map(name => String(name || '').trim())
            .filter(Boolean)
            .join(', ');
      };

      const mergeItemsByTrack = (items) => {
         const mergedMap = new Map();

         items.forEach(item => {
            const trackKey = item.id || item.trackUri || `${item.trackName || ''}|${item.artistName || ''}`;
            const basedOnNames = (item.basedOnText || '')
               .split(',')
               .map(name => name.trim())
               .filter(Boolean);

            if (!mergedMap.has(trackKey)) {
               mergedMap.set(trackKey, {
                  ...item,
                  basedOnSet: new Set(basedOnNames)
               });
               return;
            }

            const existing = mergedMap.get(trackKey);
            basedOnNames.forEach(name => existing.basedOnSet.add(name));
         });

         return Array.from(mergedMap.values()).map(item => ({
            ...item,
            basedOnText: Array.from(item.basedOnSet).join(', ')
         }));
      };

      const trackItems = [];
      trackRecs.forEach(rule => {
         (rule.consequents || []).forEach(track => {
            trackItems.push({
               ...track,
               ruleId: rule.ruleId,
               antecedentsName: rule.antecedentsName || [],
               basedOnText: getBasedOnText(rule.antecedentsName)
            });
         });
      });

      const artistItems = [];
      artistRecs.forEach(rule => {
         (rule.topTracks || []).forEach(track => {
            artistItems.push({
               ...track,
               ruleId: rule.ruleId,
               antecedentsName: rule.antecedentsName || [],
               basedOnText: getBasedOnText(rule.antecedentsName)
            });
         });
      });

      const uniqueTrackItems = mergeItemsByTrack(trackItems);
      const uniqueArtistItems = mergeItemsByTrack(artistItems);

      const totalRecommendations = uniqueTrackItems.length + uniqueArtistItems.length;
      const totalRules = trackRecs.length + artistRecs.length;

      if (totalRecommendations === 0) {
         recommendationsTable.innerHTML = `
            <p style="padding: 2rem; color: var(--text-secondary);">
               No recommendations found for this playlist. 
               ${recommendations.fromCache ? '<span style="color: var(--success);">(cached)</span>' : ''}
            </p>
         `;
         return;
      }

      let html = `
         <div style="padding: 1rem; background: var(--surface); border-radius: 8px; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
               <div style="margin-bottom: 0.2rem;">
                  <strong>${totalRules}</strong> rules found
                  <span style="color: var(--text-secondary); margin-left: 1rem;">
                     (${trackRecs.length} track rules, ${artistRecs.length} artist rules)
                  </span>
               </div>
               <strong>${totalRecommendations}</strong> recommendations found
               <span style="color: var(--text-secondary); margin-left: 1rem;">
                  (${uniqueTrackItems.length} tracks, ${uniqueArtistItems.length} artists)
               </span>
               
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
               ${recommendations.fromCache ?
            '<span style="color: var(--success); font-size: 0.85rem;"><i class="fas fa-check-circle"></i> Cached</span>' :
            '<span style="color: var(--text-secondary); font-size: 0.85rem;">Live</span>'
         }
               <span style="color: var(--text-secondary); font-size: 0.85rem;">${recommendations.latencyMs}ms</span>
            </div>
         </div>
      `;

      if (uniqueTrackItems.length > 0) {
         html += `
            <div class="recommendation-section">
               <h3 style="margin: 1.5rem 0 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                  <i class="fas fa-music"></i>
                  Track Recommendations
                  <span style="font-size: 0.85rem; color: var(--text-secondary); font-weight: normal;">(${uniqueTrackItems.length})</span>
               </h3>
         `;

         uniqueTrackItems.forEach((track, index) => {
            const basedOn = track.basedOnText || '';
            html += `
               <div class="search-result-item recommendation-row track-row" data-track-id="${track.id}" data-track-data='${JSON.stringify({ id: track.id, uri: track.trackUri, title: track.trackName, artist: track.artistName, album: track.albumName, albumUri: track.albumUri, durationMs: this.getTrackDurationMs(track) }).replace(/'/g, "&#39;")}' style="grid-template-columns: 50px 3fr 2fr 1fr 100px;">
                  <div class="col-play">
                        ${index + 1}
                  </div>
                  <div>
                     ${this.escapeHtml(track.trackName)}
                     ${basedOn ? `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem;">Based on: ${this.escapeHtml(basedOn)}</div>` : ''}
                  </div>
                  <div style="color: var(--text-secondary)">${this.escapeHtml(track.artistName)}</div>
                  <div style="color: var(--text-secondary); text-align: center">${this.formatDuration(this.getTrackDurationMs(track))}</div>
                  <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; position: relative;">
                     ${track.trackUri ? `<button class="btn-add btn-play-spotify" data-embed-url="${window.SpotifyService.uriToEmbed(track.trackUri)}" title="Play on Spotify"><i class="fas fa-play"></i></button>` : ''}
                     <button class="btn-add btn-add-recommendation" 
                           data-track-id="${track.id}"
                           data-track-uri="${track.trackUri}"
                           data-rule-id="${track.ruleId}"
                           data-rule-type="track"
                           title="Add to playlist">
                        <i class="fas fa-plus"></i>
                     </button>
                  </div>
               </div>
            `;
         });

         html += `</div>`;
      }

      if (uniqueArtistItems.length > 0) {
         html += `
            <div class="recommendation-section">
               <h3 style="margin: 1.5rem 0 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                  <i class="fas fa-user-music"></i>
                  Artist Recommendations
                  <span style="font-size: 0.85rem; color: var(--text-secondary); font-weight: normal;">(${uniqueArtistItems.length})</span>
               </h3>
         `;

         uniqueArtistItems.forEach((track, index) => {
            const basedOn = track.basedOnText || '';
            html += `
               <div class="search-result-item recommendation-row track-row" data-track-id="${track.id}" data-track-data='${JSON.stringify({ id: track.id, uri: track.trackUri, title: track.trackName, artist: track.artistName, durationMs: this.getTrackDurationMs(track) }).replace(/'/g, "&#39;")}' style="grid-template-columns: 50px 3fr 2fr 1fr 100px;">
                  <div class="col-play">
                     ${index + 1}
                  </div>
                  <div>
                     ${this.escapeHtml(track.trackName)}
                     ${basedOn ? `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem;">Based on: ${this.escapeHtml(basedOn)}</div>` : ''}
                  </div>
                  <div style="color: var(--text-secondary)">${this.escapeHtml(track.artistName)}</div>
                  <div style="color: var(--text-secondary); text-align: center">${this.formatDuration(this.getTrackDurationMs(track))}</div>
                  <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; position: relative;">
                     ${track.trackUri ? `<button class="btn-add btn-play-spotify" data-embed-url="${window.SpotifyService.uriToEmbed(track.trackUri)}" title="Play on Spotify"><i class="fas fa-play"></i></button>` : ''}
                     <button class="btn-add btn-add-recommendation" 
                           data-track-id="${track.id}"
                           data-track-uri="${track.trackUri}"
                           data-rule-id="${track.ruleId}"
                           data-rule-type="artist"
                           title="Add to playlist">
                        <i class="fas fa-plus"></i>
                     </button>
                  </div>
               </div>
            `;
         });

         html += `</div>`;
      }

      recommendationsTable.innerHTML = html;
   },

   renderSearchResults(results, playlists = [], title = 'Search Results') {
      document.getElementById('emptyState').classList.add('hidden');
      document.getElementById('playlistView').classList.add('hidden');
      document.getElementById('homeView').classList.add('hidden');
      const searchResults = document.getElementById('searchResults');
      searchResults.classList.remove('hidden');

      const searchResultsBody = document.getElementById('searchResultsBody');
      const tracks = results.tracks || [];

      if (tracks.length === 0) {
         searchResultsBody.innerHTML = `
            <h2>${title}</h2>
            <p style="padding: 2rem; color: var(--text-secondary);">No results found</p>
         `;
         return;
      }

      let html = `<h2>${title}</h2>`;

      // Render Tracks Section
      html += `
         <div class="search-section">
            <h3 class="search-section-title">
               <i class="fas fa-music"></i>
               Tracks (${tracks.length})
            </h3>
            <div class="track-results-list">
      `;

      tracks.forEach((track, index) => {
         // Normalize field names from API response
         const trackData = {
            id: track.id,
            uri: track.uri || track.track_uri,
            title: track.title || track.track_name,
            artist: track.artist || track.artist_name,
            album: track.album || track.album_name,
            albumUri: track.albumUri || track.album_uri,
            durationMs: this.getTrackDurationMs(track)
         };
         html += `
            <div class="search-result-item track-row" data-track-id="${track.id}" data-track-data='${JSON.stringify(trackData).replace(/'/g, "&#39;")}'>
               <div class="col-play">
                  ${index + 1}
               </div>
               <div>${this.escapeHtml(trackData.title)}</div>
               <div style="color: var(--text-secondary)">${this.escapeHtml(trackData.artist)}</div>
               <div style="color: var(--text-secondary); text-align: center">${this.formatDuration(trackData.durationMs)}</div>
               <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; position: relative;">
                  ${trackData.uri ? `<button class="btn-add btn-play-spotify" data-embed-url="${window.SpotifyService.uriToEmbed(trackData.uri)}" title="Play on Spotify">
                     <i class="fas fa-play"></i>
                  </button>` : ''}
                  ${playlists && playlists.length > 0 ? `
                     <button class="btn-add btn-playlist-dropdown" data-track-id="${track.id}" title="Add to playlist">
                        <i class="fas fa-plus"></i>
                     </button>
                     <div class="playlist-dropdown-menu">
                        <button class="dropdown-item btn-create-playlist-with-track" data-track='${JSON.stringify(trackData).replace(/'/g, "&#39;")}'>
                           <i class="fas fa-plus-circle"></i>
                           <span>Create New Playlist</span>
                        </button>
                        <div class="dropdown-divider"></div>
                        ${playlists.map(playlist => `
                           <button class="dropdown-item btn-add-from-search" data-playlist-id="${playlist.id}" data-track-id="${track.id}">
                              <i class="fas fa-list-music"></i>
                              <span>${this.escapeHtml(playlist.name)}</span>
                           </button>
                        `).join('')}
                     </div>
                  ` : `
                     <button class="btn-add btn-create-playlist-with-track" data-track='${JSON.stringify(trackData).replace(/'/g, "&#39;")}' title="Create playlist with this track">
                        <i class="fas fa-plus"></i>
                     </button>
                  `}
               </div>
            </div>
         `;
      });

      html += `
            </div>
         </div>
      `;

      searchResultsBody.innerHTML = html;
   },

   renderMiniSearchResults(results, selectedTracks = []) {
      const miniSearchResults = document.getElementById('miniSearchResults');
      const tracks = results.tracks || [];
      const artists = results.artists || [];

      if (tracks.length === 0 && artists.length === 0) {
         miniSearchResults.innerHTML = '<div class="mini-search-empty">No results found</div>';
         return;
      }

      const selectedIds = selectedTracks.map(t => t.id);
      let html = '';

      // Render Tracks
      if (tracks.length > 0) {
         if (artists.length > 0) {
            html += '<div class="mini-search-section-title">Tracks</div>';
         }

         tracks.forEach(track => {
            const isSelected = selectedIds.includes(track.id);
            const buttonClass = isSelected ? 'btn-add-to-new-playlist added' : 'btn-add-to-new-playlist';
            const buttonContent = isSelected ? '<i class="fas fa-check"></i>' : '<i class="fas fa-plus"></i>';

            html += `
               <div class="mini-search-item">
                  <div class="mini-search-item-info">
                     <div class="mini-search-item-title">${this.escapeHtml(track.title)}</div>
                     <div class="mini-search-item-artist">${this.escapeHtml(track.artist)}</div>
                  </div>
                  <button class="${buttonClass}" data-track='${JSON.stringify(track).replace(/'/g, "&#39;")}' ${isSelected ? 'disabled' : ''}>
                     ${buttonContent}
                  </button>
               </div>
            `;
         });
      }

      miniSearchResults.innerHTML = html;
   },

   renderSelectedTracks(tracks) {
      const selectedTracksSection = document.getElementById('selectedTracksSection');
      const selectedTracksList = document.getElementById('selectedTracksList');
      const selectedCount = document.getElementById('selectedCount');

      if (!tracks || tracks.length === 0) {
         selectedTracksSection.classList.add('hidden');
         return;
      }

      selectedTracksSection.classList.remove('hidden');
      selectedCount.textContent = tracks.length;

      selectedTracksList.innerHTML = tracks.map(track => `
         <div class="selected-track-item">
            <div class="selected-track-info">
               <div class="selected-track-title">${this.escapeHtml(track.title)}</div>
               <div class="selected-track-artist">${this.escapeHtml(track.artist)}</div>
            </div>
            <button class="btn-remove-selected" data-track-id="${track.id}">
               <i class="fas fa-times"></i>
            </button>
         </div>
      `).join('');
   },

   renderNowPlaying(track) {
      const nowPlayingContent = document.getElementById('nowPlayingContent');

      if (!track) {
         nowPlayingContent.innerHTML = `
                <div class="empty-now-playing">
                    <i class="fas fa-headphones"></i>
                    <p>Select a song to view details</p>
                </div>
            `;
         return;
      }

      nowPlayingContent.innerHTML = `
            <div class="now-playing-cover">
                ${track.albumImage ? `<img src="${track.albumImage}" alt="${this.escapeHtml(track.album || 'Album')}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">` : ''}
                <i class="fas fa-music" style="${track.albumImage ? 'display:none' : ''}"></i>
            </div>
            <div class="now-playing-info">
                <h2 class="now-playing-title">${this.escapeHtml(track.title)}</h2>
                <p class="now-playing-artist">${this.escapeHtml(track.artist)}</p>
                
                ${track.album ? `
                <div class="info-section">
                    <div class="info-label">
                        <i class="fas fa-compact-disc"></i>
                        <span>Album</span>
                    </div>
                    <p class="info-value">${this.escapeHtml(track.album)}</p>
                </div>
                ` : ''}
                
                <div class="info-section">
                    <div class="info-label">
                        <i class="fas fa-user"></i>
                        <span>Artist</span>
                    </div>
                    <p class="info-value">${this.escapeHtml(track.artist)}</p>
                </div>
                
                <div class="info-section">
                    <div class="info-label">
                        <i class="fas fa-clock"></i>
                        <span>Duration</span>
                    </div>
                    <p class="info-value">${this.formatDuration(this.getTrackDurationMs(track))}</p>
                </div>
            </div>
        `;
   },

   updateAuthButton(user) {
      const authButton = document.getElementById('authButton');

      if (user) {
         authButton.innerHTML = `
                <i class="fas fa-user"></i>
                <span>${this.escapeHtml(user.name)}</span>
            `;
         authButton.setAttribute('data-authenticated', 'true');
      } else {
         authButton.innerHTML = `
                <i class="fas fa-user"></i>
                <span>Login / Register</span>
            `;
         authButton.removeAttribute('data-authenticated');
      }
   },

   showModal(modalId) {
      const modal = document.getElementById(modalId);
      modal.classList.remove('hidden');
   },

   hideModal(modalId) {
      const modal = document.getElementById(modalId);
      modal.classList.add('hidden');
   },

   showToast(message, type = 'info') {
      const existingToasts = document.querySelectorAll('.toast-notification');
      existingToasts.forEach(toast => toast.remove());

      const toast = document.createElement('div');
      toast.className = `toast-notification toast-${type}`;

      let icon = 'fa-info-circle';
      if (type === 'success') icon = 'fa-check-circle';
      if (type === 'error') icon = 'fa-exclamation-circle';
      if (type === 'warning') icon = 'fa-exclamation-triangle';

      toast.innerHTML = `
         <i class="fas ${icon}"></i>
         <span>${this.escapeHtml(message)}</span>
      `;

      document.body.appendChild(toast);

      setTimeout(() => toast.classList.add('show'), 10);

      setTimeout(() => {
         toast.classList.remove('show');
         setTimeout(() => toast.remove(), 300);
      }, 3000);
   },

   setActivePlaylist(playlistId) {
      document.querySelectorAll('.playlist-item').forEach(item => {
         if (item.dataset.playlistId == playlistId) {
            item.classList.add('active');
         } else {
            item.classList.remove('active');
         }
      });
   },

   setPlayingTrack(trackId) {
      document.querySelectorAll('.song-row, .home-track-row').forEach(row => {
         if (row.dataset.trackId == trackId) {
            row.classList.add('playing');
         } else {
            row.classList.remove('playing');
         }
      });
   },

   getTrackDurationMs(track) {
      if (!track) return 0;
      const durationMs = track.durationMs ?? track.duration_ms ?? 0;
      return Number(durationMs) || 0;
   },

   formatDuration(durationMs) {
      if (!durationMs || durationMs <= 0) return '0:00';
      const seconds = Math.floor(durationMs / 1000);
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
   },

   escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
   },

   showEmptyState() {
      document.getElementById('emptyState').classList.remove('hidden');
      document.getElementById('playlistView').classList.add('hidden');
      document.getElementById('searchResults').classList.add('hidden');
      document.getElementById('homeView').classList.add('hidden');
   }
};

window.UI = UI;
