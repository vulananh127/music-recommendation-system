const API = {
   getAuthToken() {
      return localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
   },

   setAuthToken(token) {
      localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, token);
   },

   removeAuthToken() {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
      localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
   },

   async request(url, options = {}) {
      const token = this.getAuthToken();

      const headers = {
         'Content-Type': 'application/json',
         ...options.headers
      };

      if (token) {
         headers['Authorization'] = `Bearer ${token}`;
      }

      try {
         const response = await fetch(url, {
            ...options,
            headers
         });

         if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Request failed');
         }

         return await response.json();
      } catch (error) {
         console.error('API Request Error:', error);
         throw error;
      }
   },

   async publicRequest(url, options = {}) {
      const headers = {
         'Content-Type': 'application/json',
         ...options.headers
      };

      try {
         const response = await fetch(url, {
            ...options,
            headers
         });

         if (!response.ok) {
            // For public endpoints, return empty array instead of throwing
            console.warn(`Public API request failed: ${response.status} ${response.statusText}`);
            return [];
         }

         return await response.json();
      } catch (error) {
         console.error('Public API Request Error:', error);
         return [];
      }
   },

   async login(email, password) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.LOGIN);
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(url, {
         method: 'POST',
         headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
         },
         body: formData.toString()
      });

      if (!response.ok) {
         const error = await response.json();
         throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();

      if (data.access_token) {
         this.setAuthToken(data.access_token);
         localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify({
            id: data.user_id,
            email: data.email,
            name: data.name
         }));
      }

      return {
         token: data.access_token,
         user: {
            id: data.user_id,
            email: data.email,
            name: data.name
         }
      };
   },

   async register(name, email, password) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.REGISTER);

      const response = await fetch(url, {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({ name, email, password })
      });

      if (!response.ok) {
         const error = await response.json();
         throw new Error(error.detail || 'Registration failed');
      }

      const data = await response.json();

      if (data.access_token) {
         this.setAuthToken(data.access_token);
         localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify({
            id: data.user_id,
            email: data.email,
            name: data.name
         }));
      }

      return {
         token: data.access_token,
         user: {
            id: data.user_id,
            email: data.email,
            name: data.name
         }
      };
   },

   async logout() {
      this.removeAuthToken();
   },

   async getCurrentUser() {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_USER);
      return await this.request(url);
   },

   async getPlaylists() {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_PLAYLISTS);
      const playlists = await this.request(url);
      return playlists.map(playlist => ({
         id: playlist.id,
         name: playlist.name,
         trackCount: playlist.num_tracks || 0,
         created_at: playlist.created_at
      }));
   },

   async getPlaylist(playlistId) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_PLAYLIST, { id: playlistId });
      const playlist = await this.request(url);
      return {
         id: playlist.id,
         name: playlist.name,
         trackCount: playlist.num_tracks || 0,
         tracks: playlist.tracks || [],
         created_at: playlist.created_at
      };
   },

   async createPlaylist(name) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.CREATE_PLAYLIST);
      return await this.request(url, {
         method: 'POST',
         body: JSON.stringify({ name })
      });
   },

   async updatePlaylist(playlistId, data) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.UPDATE_PLAYLIST, { id: playlistId });
      return await this.request(url, {
         method: 'PUT',
         body: JSON.stringify(data)
      });
   },

   async deletePlaylist(playlistId) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.DELETE_PLAYLIST, { id: playlistId });
      return await this.request(url, {
         method: 'DELETE'
      });
   },

   /**
    * Search tracks using PostgreSQL Full-Text Search
    * @param {string} query - Search query string
    * @param {string|null} artistFilter - Optional artist URI filter
    * @param {number} limit - Maximum number of results (default: 20)
    * @param {number} offset - Offset for pagination (default: 0)
    * @returns {Promise<Object>} Search results with tracks, counts, and metadata
    */
   async searchTracks(query, artistFilter = null, limit = 20, offset = 0) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.SEARCH_TRACKS);
      const params = new URLSearchParams();
      params.append('query', query);

      if (artistFilter) {
         params.append('artist_filter', artistFilter);
      }
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await this.request(`${url}?${params.toString()}`);

      return {
         query: response.query,
         artistFilter: response.artist_filter,
         totalCount: response.total_count,
         resultCount: response.result_count,
         tracks: this.mapSearchResultsToTracks(response.tracks),
         limit: response.limit,
         offset: response.offset,
         latencyMs: response.latency_ms,
         fromCache: response.from_cache || false
      };
   },

   /**
    * Search artists using Full-Text Search
    * @param {string} query - Search query string
    * @param {number} limit - Maximum number of results (default: 20)
    * @param {number} offset - Offset for pagination (default: 0)
    * @returns {Promise<Object>} Search results with artists, counts, and metadata
    */
   async searchArtists(query, limit = 20, offset = 0) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.SEARCH_ARTISTS);
      const params = new URLSearchParams();
      params.append('query', query);
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await this.request(`${url}?${params.toString()}`);

      return {
         query: response.query,
         totalCount: response.total_count,
         resultCount: response.result_count,
         artists: response.artists.map(artist => ({
            id: artist.id,
            artistUri: artist.artist_uri,
            artistName: artist.artist_name,
            trackCount: artist.track_count,
            relevanceScore: artist.relevance_score
         })),
         limit: response.limit,
         offset: response.offset,
         latencyMs: response.latency_ms,
         fromCache: response.from_cache || false
      };
   },

   /**
    * Search user's playlists using Full-Text Search
    * @param {string} query - Search query string
    * @param {number} limit - Maximum number of results (default: 20)
    * @param {number} offset - Offset for pagination (default: 0)
    * @returns {Promise<Object>} Search results with playlists
    */
   async searchPlaylists(query, limit = 20, offset = 0) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.SEARCH_PLAYLISTS);
      const params = new URLSearchParams();
      params.append('query', query);
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await this.request(`${url}?${params.toString()}`);

      return {
         query: response.query,
         totalCount: response.total_count,
         resultCount: response.result_count,
         playlists: response.playlists.map(playlist => ({
            id: playlist.id,
            pid: playlist.pid,
            name: playlist.name,
            numTracks: playlist.num_tracks,
            createdAt: playlist.created_at,
            relevanceScore: playlist.relevance_score
         })),
         limit: response.limit,
         offset: response.offset,
         latencyMs: response.latency_ms
      };
   },


   /**
    * Get track recommendations based on antecedent tracks
    * @param {Array<string>} antecedents - Array of track URIs
    * @param {number} limit - Maximum number of recommendations (default: 10)
    * @returns {Promise<Object>} Recommendations with rules and tracks
    */
   async getTrackRecommendations(antecedents, limit = 10) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_TRACK_RECOMMENDATIONS);

      try {
         const response = await this.request(url, {
            method: 'POST',
            body: JSON.stringify({
               antecedents: antecedents,
               limit: limit
            })
         });

         return {
            latencyMs: response.latency_ms,
            count: response.count,
            items: response.items.map(item => ({
               ruleId: item.rule_id,
               antecedents: item.antecedents,
               consequents: item.consequents.map(track => ({
                  id: track.id,
                  trackUri: track.track_uri,
                  trackName: track.track_name,
                  artistName: track.artist_name,
                  artistUri: track.artist_uri,
                  albumName: track.album_name,
                  albumUri: track.album_uri,
                  durationMs: track.duration_ms
               })),
               score: item.score,
               confidence: item.confidence,
               lift: item.lift,
               support: item.support
            })),
            fromCache: response.from_cache || false
         };
      } catch (error) {
         console.error("Error getting track recommendations:", error);
         return { latencyMs: 0, count: 0, items: [], fromCache: false };
      }
   },

   /**
    * Get artist recommendations based on antecedent artists
    * @param {Array<string>} antecedents - Array of artist URIs
    * @param {number} limit - Maximum number of recommendations (default: 10)
    * @returns {Promise<Object>} Artist recommendations with top tracks
    */
   async getArtistRecommendations(antecedents, limit = 10) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_ARTIST_RECOMMENDATIONS);

      try {
         const response = await this.request(url, {
            method: 'POST',
            body: JSON.stringify({
               antecedents: antecedents,
               limit: limit
             })
         });

         return {
            latencyMs: response.latency_ms,
            count: response.count,
            items: response.items.map(item => ({
               ruleId: item.rule_id,
               antecedents: item.antecedents,
               consequents: item.consequents,
               score: item.score,
               confidence: item.confidence,
               lift: item.lift,
               support: item.support,
               topTracks: item.top_tracks.map(track => ({
                  id: track.id,
                  trackUri: track.track_uri,
                  trackName: track.track_name,
                  artistName: track.artist_name,
                  durationMs: track.duration_ms,
                  frequency: track.frequency
               }))
            })),
            fromCache: response.from_cache || false
         };
      } catch (error) {
         console.error("Error getting artist recommendations:", error);
         return { latencyMs: 0, count: 0, items: [], fromCache: false };
      }
   },

   /**
    * Get comprehensive recommendations (both tracks and artists) from a playlist
    * @param {Array<string>} trackAntecedents - Array of track URIs for recommendations
    * @param {Array<string>} artistAntecedents - Array of artist URIs for recommendations
    * @param {number} limit - Number of recommendations per type (default: 10)
    * @returns {Promise<Object>} Combined track and artist recommendations
    */
   async getAllRecommendations(trackAntecedents = [], artistAntecedents = [], limit = 10) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_ALL_RECOMMENDATIONS);

      try {
         const response = await this.request(url, {
            method: 'POST',
            body: JSON.stringify({
               track_antecedents: trackAntecedents,
               artist_antecedents: artistAntecedents,
               limit: limit
            })
         });

         return {
            latencyMs: response.latency_ms,
            tracks: {
               count: response.track_recommendations.count,
               items: response.track_recommendations.items.map(item => ({
                  ruleId: item.rule_id,
                  antecedents: item.antecedents,
                  antecedentsName: item.antecedent_names,
                  consequents: item.consequents.map(track => ({
                     id: track.id,
                     trackUri: track.track_uri,
                     trackName: track.track_name,
                     artistName: track.artist_name,
                     artistUri: track.artist_uri,
                     albumName: track.album_name,
                     albumUri: track.album_uri,
                     durationMs: track.duration_ms
                  })),
                  score: item.score,
               confidence: item.confidence,
               lift: item.lift,
               support: item.support
               }))
            },
            artists: {
               count: response.artist_recommendations.count,
               items: response.artist_recommendations.items.map(item => ({
                  ruleId: item.rule_id,
                  antecedents: item.antecedents,
                  antecedentsName: item.antecedent_names,
                  consequents: item.consequents,
                  score: item.score,
                  confidence: item.confidence,
                  lift: item.lift,
                  support: item.support,
                  topTracks: (item.top_tracks || []).map(track => ({
                     id: track.id,
                     trackUri: track.track_uri,
                     trackName: track.track_name,
                     artistName: track.artist_name,
                     durationMs: track.duration_ms,
                     frequency: track.frequency
                  }))
               }))
            },
            fromCache: response.from_cache || false
         };
      } catch (error) {
         console.error("Error getting all recommendations:", error);
         return {
            latencyMs: 0,
            tracks: { count: 0, items: [] },
            artists: { count: 0, items: [] },
            fromCache: false
         };
      }
   },

   /**
    * Get recommendations for a specific playlist (convenience method)
    * Automatically extracts track and artist URIs from playlist
    * @param {number} playlistId - Playlist ID
    * @param {number} limit - Number of recommendations per type (default: 10)
    * @returns {Promise<Object>} Combined recommendations
    */
   async getPlaylistRecommendations(playlistId, limit = 10) {
      try {
         const tracks = await this.getPlaylistTracks(playlistId);

         if (!tracks || tracks.length === 0) {
            return {
               latencyMs: 0,
               trackRecommendations: { count: 0, items: [] },
               artistRecommendations: { count: 0, items: [] },
               totalRecommendations: 0,
               fromCache: false
            };
         }

         const trackUris = tracks.map(track => track.uri);

         const artistUris = [...new Set(tracks.map(track => track.artistUri).filter(Boolean))];

         return await this.getAllRecommendations(trackUris, artistUris, limit);
      } catch (error) {
         console.error("Error getting playlist recommendations:", error);
         return {
            latencyMs: 0,
            trackRecommendations: { count: 0, items: [] },
            artistRecommendations: { count: 0, items: [] },
            totalRecommendations: 0,
            fromCache: false
         };
      }
   },


   mapSearchResultsToTracks(results) {
      if (!Array.isArray(results)) {
         return [];
      }

      return results.map(track => ({
         id: track.id || this.extractIdFromUri(track.track_uri || track.uri),
         uri: track.track_uri || track.uri,
         title: track.track_name || track.name || track.title,
         artist: track.artist_name || track.artist,
         artistUri: track.artist_uri,
         album: track.album_name || track.album,
         albumUri: track.album_uri,
         duration: track.duration_ms ? Math.floor(track.duration_ms / 1000) : 0,
         durationMs: track.duration_ms,
         relevanceScore: track.relevance_score
      }));
   },

   extractIdFromUri(uri) {
      if (!uri) return null;
      const parts = uri.split(':');
      return parts[parts.length - 1];
   },

   async getPlaylistTracks(playlistId) {
      const playlist = await this.getPlaylist(playlistId);
      return (playlist.tracks || []).map(track => ({
         id: track.id,
         uri: track.track_uri,
         title: track.track_name,
         artist: track.artist_name,
         artistUri: track.artist_uri,
         album: track.album_name,
         albumUri: track.album_uri,
         duration: Math.floor(track.duration_ms / 1000),
         durationMs: track.duration_ms,
         pos: track.pos,
         addedAt: track.added_at
      }));
   },

   async addTrackToPlaylist(playlistId, trackId, position = null) {
      console.log('🔧 API.addTrackToPlaylist called:', {
         playlistId,
         trackId,
         trackIdType: typeof trackId,
         trackIdParsed: parseInt(trackId),
         position
      });

      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.ADD_TRACK_TO_PLAYLIST, { playlistId });
      console.log('📍 Request URL:', url);

      const payload = {
         track_id: parseInt(trackId),
         position: position
      };
      console.log('📦 Payload:', payload);

      try {
         const result = await this.request(url, {
            method: 'POST',
            body: JSON.stringify(payload)
         });
         console.log('✅ API response:', result);
         return result;
      } catch (error) {
         console.error('❌ API request failed:', error);
         throw error;
      }
   },

   async removeTrackFromPlaylist(playlistId, trackId) {
      const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.REMOVE_TRACK_FROM_PLAYLIST, { playlistId, trackId });
      return await this.request(url, {
         method: 'DELETE'
      });
   },


   async getRecommendations(playlistId) {
      return await this.getPlaylistRecommendations(playlistId, 10);
   },


   async logClickEvent(data) {
      try {
         const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.LOG_CLICK_EVENT);
         await this.request(url, {
            method: 'POST',
            body: JSON.stringify({
               item_id: data.track_uri || data.item_id,
               item_type: data.item_type || 'track',
               rule_id: data.rule_id || null,
               rule_type: data.rule_type || null,
               playlist_id: data.playlist_id || null,
               context: data.context || {}
            })
         });
      } catch (error) {
         console.warn('Failed to log click event:', error);
      }
   },

   async logViewEvent(data) {
      try {
         const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.LOG_VIEW_EVENT);
         await this.request(url, {
            method: 'POST',
            body: JSON.stringify({
               item_id: data.track_uri || data.item_id,
               item_type: data.item_type || 'track',
               context: data.context || {}
            })
         });
      } catch (error) {
         console.warn('Failed to log view event:', error);
      }
   },


   async getPopularTracks() {
      try {
         const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_POPULAR_TRACKS);
         const tracks = await this.publicRequest(url);
         if (!Array.isArray(tracks)) return [];
         return tracks.map(track => ({
            id: track.id,
            uri: track.track_uri,
            title: track.track_name,
            artist: track.artist_name,
            artistUri: track.artist_uri,
            album: track.album_name,
            albumUri: track.album_uri,
            duration: track.duration_ms ? Math.floor(track.duration_ms / 1000) : 0,
            durationMs: track.duration_ms,
            frequency: track.frequency
         }));
      } catch (error) {
         console.error('Error fetching popular tracks:', error);
         return [];
      }
   },

   async getPopularArtist() {
      try {
         const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_POPULAR_ARTIST);
         const result = await this.publicRequest(url);
         return result || null;
      } catch (error) {
         console.error('Error fetching popular artist:', error);
         return null;
      }
   },

   async getArtistTracks(artistUri, limit = 10) {
      try {
         const url = CONFIG.buildUrl(CONFIG.ENDPOINTS.GET_ARTIST_TRACKS, { artistUri }) + `?limit=${limit}`;
         const tracks = await this.publicRequest(url);
         if (!Array.isArray(tracks)) return [];
         return tracks.map(track => ({
            id: track.id,
            uri: track.track_uri,
            title: track.track_name,
            artist: track.artist_name,
            artistUri: track.artist_uri,
            album: track.album_name,
            albumUri: track.album_uri,
            duration: track.duration_ms ? Math.floor(track.duration_ms / 1000) : 0,
            durationMs: track.duration_ms
         }));
      } catch (error) {
         console.error('Error fetching artist tracks:', error);
         return [];
      }
   },
};

window.API = API;
