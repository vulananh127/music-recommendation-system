const CONFIG = {
   API_BASE_URL: 'http://localhost:8080/api',

   // API Endpoints
   ENDPOINTS: {
      LOGIN: '/auth/login',
      REGISTER: '/auth/register',
      GET_USER: '/auth/me',

      GET_PLAYLISTS: '/playlists',
      GET_PLAYLIST: '/playlists/:id',
      CREATE_PLAYLIST: '/playlists',
      UPDATE_PLAYLIST: '/playlists/:id',
      DELETE_PLAYLIST: '/playlists/:id',

      ADD_TRACK_TO_PLAYLIST: '/playlists/:playlistId/tracks',
      REMOVE_TRACK_FROM_PLAYLIST: '/playlists/:playlistId/tracks/:trackId',

      SEARCH_TRACKS: '/search/tracks',
      SEARCH_ARTISTS: '/search/artists',
      SEARCH_PLAYLISTS: '/search/playlists',

      GET_TRACK_RECOMMENDATIONS: '/recommend/tracks',
      GET_ARTIST_RECOMMENDATIONS: '/recommend/artists',
      GET_ALL_RECOMMENDATIONS: '/recommend/all',

      LOG_CLICK_EVENT: '/events/click',
      LOG_VIEW_EVENT: '/events/view',

      GET_POPULAR_TRACKS: '/tracks/popular',
      GET_POPULAR_ARTIST: '/artists/popular',
      GET_ARTIST_TRACKS: '/artists/:artistUri/tracks'
   },

   STORAGE_KEYS: {
      AUTH_TOKEN: 'music_app_auth_token',
      USER_DATA: 'music_app_user_data',
      CURRENT_PLAYLIST: 'music_app_current_playlist',
      NOW_PLAYING: 'music_app_now_playing'
   },

   SETTINGS: {
      ITEMS_PER_PAGE: 20,
      SEARCH_DEBOUNCE_MS: 150,
      RECOMMENDATION_LIMIT: 10,
      SEARCH_DEFAULT_LIMIT: 20,
      SEARCH_DEFAULT_OFFSET: 0
   }
};

CONFIG.buildUrl = function (endpoint, params = {}) {
   let url = this.API_BASE_URL + endpoint;

   for (const [key, value] of Object.entries(params)) {
      url = url.replace(`:${key}`, value);
   }

   return url;
};

window.CONFIG = CONFIG;
