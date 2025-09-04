// API Configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export const API_BASE_URL = `${API_URL}/api`;

export const API_ENDPOINTS = {
  // Auth
  login: `${API_BASE_URL}/auth/login`,
  register: `${API_BASE_URL}/auth/register`,
  
  // Sports Data
  nfl: `${API_BASE_URL}/nfl/games`,
  ncaaf: `${API_BASE_URL}/ncaaf/games`,
  mlb: `${API_BASE_URL}/mlb/games`,
  
  // Live Games
  liveGames: (sport) => `${API_BASE_URL}/live/games?sport=${sport}`,
  
  // Tracking
  tracking: `${API_BASE_URL}/tracking`,
  trackBets: `${API_BASE_URL}/tracking/track-current-best-bets`,
  performance: `${API_BASE_URL}/tracking/performance`,
  updateScores: `${API_BASE_URL}/tracking/update-scores`,
  
  // Parlays
  parlays: (sport) => `${API_BASE_URL}/parlays/recommendations?sport=${sport}`,
};

export default API_ENDPOINTS;