/**
 * API Service for Sean Picks
 */

import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// No authentication needed - removed token interceptor

// No authentication needed - removed auth error handling

// Auth endpoints
export const auth = {
  register: (data: { email: string; username: string; password: string; bankroll: number }) =>
    api.post('/api/auth/register', data),
  
  login: (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  
  me: () => api.get('/api/auth/me'),
};

// NFL endpoints
export const nfl = {
  getGames: () => api.get('/api/nfl/games'),
  getGame: (id: string) => api.get(`/api/nfl/games/${id}`),
};

// NCAAF endpoints
export const ncaaf = {
  getGames: () => api.get('/api/ncaaf/games'),
  getGame: (id: string) => api.get(`/api/ncaaf/games/${id}`),
};

// MLB endpoints
export const mlb = {
  getGames: () => api.get('/api/mlb/games'),
  getGame: (id: string) => api.get(`/api/mlb/games/${id}`),
};

// Parlay endpoints
export const parlays = {
  getRecommendations: (sport: string) => api.get(`/api/parlays/recommendations?sport=${sport}`),
  calculate: (data: any) => api.post('/api/parlays/calculate', data),
};

// Live betting endpoints
export const live = {
  getGames: (sport: string = 'nfl') => api.get(`/api/live/games?sport=${sport}`),
  getAlerts: () => api.get('/api/live/alerts'),
};

// User endpoints
export const users = {
  getProfile: () => api.get('/api/users/profile'),
  updateBankroll: (bankroll: number) => api.put('/api/users/bankroll', { bankroll }),
  updatePreferences: (preferences: any) => api.put('/api/users/preferences', { preferences }),
};

export default api;