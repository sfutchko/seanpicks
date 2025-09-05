import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { nfl, ncaaf, mlb, parlays, users, live } from '../services/api';
import './Dashboard.css';
import './BestBets.css';
import HelpModal from './HelpModal';

interface Weather {
  temperature?: number;
  wind_speed?: number;
  description?: string;
}

interface Game {
  id: string;
  home_team: string;
  away_team: string;
  game_time: string;
  spread: number;
  total: number;
  confidence: number;
  edge: number;
  pick: string;
  patterns: string[];
  insights?: string[];
  moneylines: any;
  kelly_bet?: number;
  weather?: Weather;
  weather_impact?: number;
  injuries?: number;
  best_bet_type?: string;
  full_analysis?: any;
  sharp_action?: boolean;
  reverse_line_movement?: boolean;
  steam_move?: boolean;
  contrarian?: boolean;
  public_percentage?: number;
  public_on_home?: boolean;
  public_away_percentage?: number;
  public_home_percentage?: number;
  public_sources?: string[];
  books_count?: number;
  book_odds?: {
    [key: string]: {
      spread?: number;
      spread_price?: number;
      total?: number;
      total_price?: number;
      ml_home?: number;
      ml_away?: number;
    }
  };
}

interface SharpPlay {
  game: string;
  sharp_side: string;
  confidence: number;
  patterns?: string[];
}

interface ContrarianPlay {
  game: string;
  public_percentage: number;
  fade_side: string;
  confidence: number;
}

interface ParlayLeg {
  team: string;
  pick: string;
  spread?: number;
}

interface ParlayRec {
  legs: ParlayLeg[];
  potential_payout: number;
  recommended_bet: number;
  expected_value: number;
  confidence: number;
  type?: string;
  games?: any[];
  multiplier?: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [sport, setSport] = useState<'nfl' | 'ncaaf' | 'mlb'>('nfl');
  const [games, setGames] = useState<Game[]>([]);
  const [bestBets, setBestBets] = useState<Game[]>([]);
  const [parlayRecs, setParlayRecs] = useState<ParlayRec[]>([]);
  const [sharpPlays, setSharpPlays] = useState<SharpPlay[]>([]);
  const [contrarian, setContrarian] = useState<ContrarianPlay[]>([]);
  const [dataStatus, setDataStatus] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [bankroll, setBankroll] = useState(() => {
    const saved = localStorage.getItem('bankroll');
    return saved ? Number(saved) : 1000;
  });
  const [unitSize, setUnitSize] = useState(() => {
    const saved = localStorage.getItem('unitSize');
    return saved ? Number(saved) : 20;
  });
  const [liveGames, setLiveGames] = useState<any[]>([]);
  const [upcomingGames, setUpcomingGames] = useState<any[]>([]);
  const [showHelp, setShowHelp] = useState(false);

  // Helper function to format spread to standard betting line (whole or .5)
  const formatSpread = (spread: number): string => {
    // Round to nearest 0.5
    const rounded = Math.round(spread * 2) / 2;
    return rounded > 0 ? `+${rounded}` : `${rounded}`;
  };

  // Stats calculations
  const totalGames = games.length;
  const edgesFound = bestBets.length;
  const avgConfidence = bestBets.length > 0 
    ? (bestBets.reduce((sum, g) => sum + g.confidence, 0) / bestBets.length * 100).toFixed(1)
    : '0';
  const bestEdge = bestBets.length > 0 && bestBets[0].edge 
    ? bestBets[0].edge.toFixed(1) 
    : '0';

  // Helper function for weather icons
  const getWeatherIcon = (weather: any): string => {
    if (!weather) return '⛅'; // Default weather if no data
    
    const temp = weather.temperature;
    const wind = weather.wind_speed || 0;
    const desc = (weather.description || '').toLowerCase();
    
    // Check if it's a dome (72 degrees with no wind and "Dome" in description)
    if (temp === 72 && wind === 0 && desc.includes('dome')) {
      return '🏟️'; // Dome
    }
    
    // Check description first for more accurate weather
    if (desc.includes('storm') || desc.includes('thunder')) return '⛈️';
    if (desc.includes('rain') || desc.includes('drizzle') || desc.includes('shower')) return '🌧️';
    if (desc.includes('snow') || desc.includes('blizzard')) return '❄️';
    if (desc.includes('fog') || desc.includes('mist')) return '🌫️';
    if (desc.includes('clear') || desc.includes('sun')) return '☀️';
    if (desc.includes('overcast')) return '☁️';
    if (desc.includes('cloud')) return '⛅';
    
    // Check extreme conditions
    if (temp < 32) return '❄️'; // Freezing
    if (temp > 85) return '🔥'; // Hot
    if (wind > 20) return '💨'; // Very windy
    
    // If no specific conditions, return based on temperature
    if (temp > 75) return '☀️'; // Warm and likely clear
    if (temp < 50) return '☁️'; // Cool and likely cloudy
    
    return '⛅'; // Default partly cloudy
  };

  // Helper function to get best line for a game
  const getBestLine = (game: any): {book: string, spread: number, displaySpread: number} | null => {
    if (!game.book_odds || Object.keys(game.book_odds).length === 0) {
      return null;
    }
    
    // Find the best spread (most favorable for the pick)
    let bestBook = '';
    let bestSpread = game.spread || 0;
    
    // Determine if we're betting on home or away team
    // The pick string contains the team name at the beginning
    const pickingHome = game.pick && game.pick.includes(game.home_team);
    const pickingAway = game.pick && game.pick.includes(game.away_team);
    
    Object.entries(game.book_odds).forEach(([book, odds]: [string, any]) => {
      if (odds.spread !== undefined) {
        // If no best book yet, use this one
        if (!bestBook) {
          bestBook = book;
          bestSpread = odds.spread;
        } else {
          // Home team gets the spread as-is, away team wants opposite
          if (pickingHome) {
            // For home team, we want the most positive spread (or least negative)
            if (odds.spread > bestSpread) {
              bestSpread = odds.spread;
              bestBook = book;
            }
          } else if (pickingAway) {
            // For away team, we want the most negative home spread (which gives away team more points)
            // Since spreads are for home team, more negative = more points for away
            if (odds.spread < bestSpread) {
              bestSpread = odds.spread;
              bestBook = book;
            }
          }
        }
      }
    });
    
    // Calculate display spread based on which team we're picking
    let displaySpread = bestSpread;
    if (pickingAway) {
      // Flip the sign for away team
      displaySpread = -bestSpread;
    }
    
    return bestBook ? {book: bestBook, spread: bestSpread, displaySpread: displaySpread} : null;
  };

  // Helper function to format book names
  const formatBookName = (book: string): string => {
    const bookMap: {[key: string]: string} = {
      'draftkings': 'DraftKings',
      'fanduel': 'FanDuel',
      'betmgm': 'BetMGM',
      'caesars': 'Caesars',
      'pointsbet': 'PointsBet',
      'betrivers': 'BetRivers',
      'williamhill_us': 'William Hill',
      'unibet_us': 'Unibet',
      'betfred': 'BetFred',
      'sugarhouse': 'SugarHouse',
      'barstool': 'Barstool',
      'wynnbet': 'WynnBET',
      'foxbet': 'FOX Bet',
      'betonlineag': 'BetOnline',
      'bovada': 'Bovada',
      'mybookieag': 'MyBookie',
      'lowvig': 'Lowvig',
      'pinnacle': 'Pinnacle',
      'betparx': 'BetParx',
      'twinspires': 'TwinSpires',
      'betUS': 'BetUS'
    };
    return bookMap[book.toLowerCase()] || book.toUpperCase();
  };

  useEffect(() => {
    const fetchData = async () => {
      await loadGames();
      // User profile not needed
      await loadParlays();
      await loadLiveGames();
    };
    fetchData();
    
    // Refresh live games every 60 seconds
    const interval = setInterval(() => {
      loadLiveGames();
    }, 60000);
    
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sport]);

  // User profile not needed - using default values

  const loadGames = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log(`Loading ${sport} games...`);
      let response;
      if (sport === 'nfl') {
        response = await nfl.getGames();
      } else if (sport === 'ncaaf') {
        response = await ncaaf.getGames();
      } else {
        response = await mlb.getGames();
      }
      
      console.log(`API called: ${sport === 'nfl' ? 'NFL' : 'NCAAF'}`);
      
      console.log('Full response:', response);
      console.log('Response data:', response.data);
      
      if (response.data) {
        const gamesData = response.data.games || [];
        const bestBetsData = response.data.best_bets || [];
        
        console.log(`Setting ${gamesData.length} games`);
        console.log(`Setting ${bestBetsData.length} best bets`);
        
        setGames(gamesData);
        setBestBets(bestBetsData);
        
        // Debug weather data
        console.log('Best Bets Weather Data:');
        bestBetsData.forEach((game: any, idx: number) => {
          console.log(`Game ${idx + 1}: ${game.away_team} @ ${game.home_team}`);
          console.log('Weather:', game.weather);
        });
        
        // Use sharp_plays from API response
        console.log('Sharp plays from API:', response.data.sharp_plays);
        if (response.data.sharp_plays && response.data.sharp_plays.length > 0) {
          console.log(`Setting ${response.data.sharp_plays.length} sharp plays from API`);
          setSharpPlays(response.data.sharp_plays);
        } else {
          // Fallback to extracting from games and transforming to SharpPlay format
          const sharps = gamesData
            .filter((g: Game) => g.sharp_action || g.steam_move || g.reverse_line_movement)
            .map((g: Game) => ({
              game: `${g.away_team} @ ${g.home_team}`,
              sharp_side: g.pick || 'Unknown',
              confidence: g.confidence || 0.5,
              patterns: g.patterns || []
            }));
          console.log(`Setting ${sharps.length} sharp plays from games (fallback)`);
          setSharpPlays(sharps);
        }
        
        // Use contrarian_plays from API response  
        console.log('Contrarian plays from API:', response.data.contrarian_plays);
        if (response.data.contrarian_plays && response.data.contrarian_plays.length > 0) {
          console.log(`Setting ${response.data.contrarian_plays.length} contrarian plays from API`);
          setContrarian(response.data.contrarian_plays);
        } else {
          // Fallback to extracting from games and transforming to ContrarianPlay format
          const contrarians = gamesData
            .filter((g: Game) => g.contrarian || (g.public_percentage && g.public_percentage > 65))
            .map((g: Game) => ({
              game: `${g.away_team} @ ${g.home_team}`,
              public_percentage: g.public_percentage || 68,
              fade_side: g.pick || 'Unknown',
              confidence: g.confidence || 0.5
            }));
          console.log(`Setting ${contrarians.length} contrarian plays from games (fallback)`);
          setContrarian(contrarians);
        }
        
        // Set data status
        setDataStatus(response.data.data_sources || {});
      } else {
        console.error('No data in response');
        setGames([]);
        setBestBets([]);
      }
    } catch (err: any) {
      console.error('Error loading games:', err);
      setError(err.message || err.response?.data?.detail || 'Failed to load games');
      setGames([]);
      setBestBets([]);
    } finally {
      setLoading(false);
    }
  };

  const loadParlays = async () => {
    try {
      console.log(`Loading ${sport} parlays...`);
      const response = await parlays.getRecommendations(sport);
      console.log('Parlays full response:', response);
      console.log('Parlays data:', response.data);
      
      if (response.data && response.data.parlays) {
        console.log(`Received ${response.data.parlays.length} parlays`);
        setParlayRecs(response.data.parlays);
      } else {
        console.log('No parlays in response');
        setParlayRecs([]);
      }
    } catch (err: any) {
      console.error('Error loading parlays:', err);
      console.error('Parlay error details:', err.response);
      setParlayRecs([]);
    }
  };
  
  const loadLiveGames = async () => {
    try {
      const response = await live.getGames(sport);
      console.log('Live games response:', response.data);
      if (response.data) {
        const liveData = response.data.live_games || [];
        const upcomingData = response.data.upcoming_games || [];
        console.log(`Setting ${liveData.length} live games`);
        console.log(`Setting ${upcomingData.length} upcoming games`);
        setLiveGames(liveData);
        setUpcomingGames(upcomingData);
      }
    } catch (err) {
      console.error('Error loading live games:', err);
      setLiveGames([]);
      setUpcomingGames([]);
    }
  };

  // Removed logout functionality - no authentication needed

  const updateBankroll = (newBankroll: number) => {
    setBankroll(newBankroll);
    setUnitSize(newBankroll * 0.02);
    // Store locally since no authentication
    localStorage.setItem('bankroll', newBankroll.toString());
    localStorage.setItem('unitSize', (newBankroll * 0.02).toString());
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.65) return '#22c55e';
    if (confidence >= 0.58) return '#84cc16';
    if (confidence >= 0.54) return '#eab308';
    return '#94a3b8';
  };

  const getWeatherDisplay = (weather?: Weather) => {
    if (!weather) return '';
    
    let icon = '';
    const desc = (weather.description || '').toLowerCase();
    const temp = weather.temperature || 72;
    const wind = weather.wind_speed || 0;
    
    // Weather icon
    if (desc.includes('rain') || desc.includes('shower')) {
      icon = '🌧️';
    } else if (desc.includes('storm') || desc.includes('thunder')) {
      icon = '⛈️';
    } else if (desc.includes('snow')) {
      icon = '🌨️';
    } else if (desc.includes('fog') || desc.includes('mist')) {
      icon = '🌫️';
    } else if (desc.includes('cloud')) {
      icon = '☁️';
    } else if (desc.includes('clear') || desc.includes('sun')) {
      icon = '☀️';
    } else if (desc.includes('overcast')) {
      icon = '🌥️';
    } else {
      icon = '⛅';
    }
    
    // Add wind if significant
    let windText = '';
    if (wind >= 20) {
      windText = ' 💨💨';
    } else if (wind >= 15) {
      windText = ' 💨';
    }
    
    // Add temperature
    let tempText = '';
    if (temp <= 32) {
      tempText = ' 🥶';
    } else if (temp >= 90) {
      tempText = ' 🔥';
    }
    
    return `${icon} ${Math.round(temp)}°F${windText}${tempText}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  // Debug log the state
  console.log('Current state:', {
    sharpPlays: sharpPlays.length,
    parlayRecs: parlayRecs.length,
    contrarian: contrarian.length,
    liveGames: liveGames.length,
    bestBets: bestBets.length,
    games: games.length
  });

  return (
    <div className="dashboard">
      {/* HEADER SECTION */}
      <header className="dashboard-header">
        <div className="header-main">
          <h1 className="main-title">🎯 SEAN PICKS</h1>
          <p className="subtitle">Professional Sports Betting Analysis</p>
        </div>
        
        <div className="header-stats">
          <div className="stat-box">
            <div className="stat-value">{sport.toUpperCase()}</div>
            <div className="stat-label">League</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{totalGames}</div>
            <div className="stat-label">Games</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{edgesFound}</div>
            <div className="stat-label">Edges</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{avgConfidence}%</div>
            <div className="stat-label">Avg Conf</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">${bankroll}</div>
            <div className="stat-label">Bankroll</div>
          </div>
        </div>

        <div className="header-controls">
          <div className="sport-selector">
            <button 
              className={sport === 'nfl' ? 'active' : ''}
              onClick={() => setSport('nfl')}
            >
              NFL
            </button>
            <button 
              className={sport === 'ncaaf' ? 'active' : ''}
              onClick={() => setSport('ncaaf')}
            >
              NCAAF
            </button>
            <button 
              className={sport === 'mlb' ? 'active' : ''}
              onClick={() => setSport('mlb')}
            >
              MLB ⚾
            </button>
          </div>
          
          <div className="user-controls">
            <div className="bankroll-input">
              <label>Bankroll:</label>
              <input 
                type="number"
                value={bankroll}
                onChange={(e) => updateBankroll(Number(e.target.value))}
                step="100"
              />
              <span className="unit-display">Unit: ${unitSize.toFixed(0)}</span>
            </div>
            <button onClick={() => navigate('/tracker')} className="tracker-btn">
              📊 Performance
            </button>
            <button onClick={() => setShowHelp(true)} className="help-btn">
              ❓ Help
            </button>
          </div>
        </div>
      </header>

      {loading && <div className="loading-overlay">Loading {sport.toUpperCase()} games...</div>}
      {error && <div className="error-message">{error}</div>}

      {/* MAIN CONTENT AREA */}
      <div className="main-container">
        
        {/* TOP LAYOUT CONTAINER - Best Bets Left, Info Panels Right */}
        <div className="top-layout-container">
          {/* LEFT COLUMN - BEST BETS */}
          {bestBets.length > 0 && (
            <section className="best-bets-container">
              <div className="section-title">
                <h2>
                  {sport === 'nfl' && '🏈 NFL'} 
                  {sport === 'ncaaf' && '🎓 COLLEGE'} 
                  {sport === 'mlb' && '⚾ MLB'} BEST BETS
                </h2>
                <span className="section-subtitle">Top {bestBets.length} Value Plays Today</span>
              </div>
              
              <div className="best-bets-list">
                {bestBets.slice(0, 5).map((game, index) => (
                  <div key={game.id} className={`best-bet-card rank-${index + 1}`}>
                    <div className="bet-rank-badge">#{index + 1}</div>
                    
                    <div className="bet-content">
                    <div className="bet-header">
                      <div className="bet-matchup">
                        <span className="team-away">{game.away_team}</span>
                        <span className="at-symbol">@</span>
                        <span className="team-home">{game.home_team}</span>
                      </div>
                      <div className="bet-datetime">
                        {formatDate(game.game_time)} • {getWeatherIcon(game.weather)} {game.weather?.temperature ? `${Math.round(game.weather.temperature)}°F` : ''}
                      </div>
                    </div>
                    
                    <div className="bet-main">
                      <div className="bet-pick-info">
                        <div className="pick-label">PICK:</div>
                        <div className="pick-details">
                          <span className="pick-team">{game.pick}</span>
                          {game.best_bet_type && (
                            <span className="pick-type">{game.best_bet_type}</span>
                          )}
                        </div>
                      </div>
                      
                      {/* Best Line Available */}
                      {(() => {
                        const bestLine = getBestLine(game);
                        if (bestLine && game.book_odds && Object.keys(game.book_odds).length > 0) {
                          // Get other good books
                          // Determine if picking home or away
                          const pickingAway = game.pick && game.pick.includes(game.away_team);
                          
                          const otherBooks = Object.entries(game.book_odds)
                            .filter(([book]) => book !== bestLine.book)
                            .filter(([_, odds]: [string, any]) => odds.spread !== undefined)
                            .slice(0, 3)
                            .map(([book, odds]: [string, any]) => ({
                              book: formatBookName(book),
                              spread: pickingAway ? -odds.spread : odds.spread
                            }));
                          
                          return (
                            <div className="best-line-box">
                              <div className="best-line-label">📱 BEST LINE:</div>
                              <div className="best-line-details">
                                <span className="best-book-name">{formatBookName(bestLine.book)}</span>
                                <span className="best-book-spread">{bestLine.displaySpread > 0 ? '+' : ''}{bestLine.displaySpread}</span>
                              </div>
                              {otherBooks.length > 0 && (
                                <div className="other-books-line">
                                  <span className="also-at">Also: </span>
                                  {otherBooks.map((book, idx) => (
                                    <span key={idx} className="other-book">
                                      {book.book} {book.spread > 0 ? '+' : ''}{book.spread}
                                      {idx < otherBooks.length - 1 && ' • '}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        } else {
                          // Always show a fallback when no book odds are available
                          return (
                            <div className="best-line-box">
                              <div className="best-line-label">📱 BEST LINE:</div>
                              <div className="best-line-details">
                                <span className="best-book-name">Check Multiple Books</span>
                                <span className="best-book-spread">{game.pick && game.pick.includes(game.away_team) ? 
                                  ((-game.spread) > 0 ? '+' : '') + (-game.spread) : 
                                  (game.spread > 0 ? '+' : '') + game.spread}</span>
                              </div>
                              <div className="other-books-line">
                                <span className="also-at">Line: {game.pick && game.pick.includes(game.away_team) ? 
                                  ((-game.spread) > 0 ? '+' : '') + (-game.spread) : 
                                  (game.spread > 0 ? '+' : '') + game.spread} at most books</span>
                              </div>
                            </div>
                          );
                        }
                      })()}
                      
                      <div className="bet-odds-info">
                        <div className="odds-row">
                          <span className="odds-label">Spread:</span>
                          <span className="odds-value">{formatSpread(game.spread)}</span>
                        </div>
                        <div className="odds-row">
                          <span className="odds-label">ML:</span>
                          <span className="odds-value">
                            {game.moneylines?.home || game.moneylines?.away ? 
                              (game.spread < 0 ? 
                                (game.moneylines?.home || '-150') : 
                                (game.moneylines?.away || '+130')) 
                              : 'N/A'}
                          </span>
                        </div>
                        <div className="odds-row">
                          <span className="odds-label">O/U:</span>
                          <span className="odds-value">{game.total}</span>
                        </div>
                      </div>
                      
                      <div className="bet-confidence-section">
                        <div className="confidence-label">Confidence</div>
                        <div className="confidence-bar-container">
                          <div 
                            className="confidence-bar-fill"
                            style={{ 
                              width: `${game.confidence * 100}%`,
                              backgroundColor: getConfidenceColor(game.confidence)
                            }}
                          />
                        </div>
                        <div className="confidence-stats">
                          <span className="conf-value">{(game.confidence * 100).toFixed(1)}%</span>
                          {game.edge && <span className="edge-value">+{game.edge.toFixed(1)}% edge</span>}
                        </div>
                      </div>
                      
                      {/* Weather & Public Info */}
                      <div className="bet-extra-info">
                        {game.weather && (
                          <div className="weather-row">
                            <span className="weather-icon">{getWeatherIcon(game.weather)}</span>
                            <span className="weather-temp">{Math.round(game.weather.temperature || 70)}°F</span>
                            {game.weather.wind_speed && game.weather.wind_speed > 15 && (
                              <span className="wind-alert">💨 {Math.round(game.weather.wind_speed)}mph</span>
                            )}
                          </div>
                        )}
                        
                        {game.public_percentage && (
                          <div className="public-row">
                            <div className="public-bar-container">
                              <div className="public-label">
                                {game.public_on_home ? 'HOME' : 'AWAY'}
                              </div>
                              <div className="public-bar">
                                <div 
                                  className="public-fill"
                                  style={{ 
                                    width: `${game.public_percentage}%`,
                                    backgroundColor: game.public_percentage > 65 ? '#ff4444' : game.public_percentage > 55 ? '#ffaa00' : '#00ff88'
                                  }}
                                />
                                <span className="public-percent">{game.public_percentage}%</span>
                              </div>
                            </div>
                            {game.public_percentage > 65 && (
                              <span className="fade-indicator">FADE</span>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <div className="bet-sizing">
                        <div className="sizing-title">Recommended Bet:</div>
                        <div className="sizing-amount">
                          ${game.kelly_bet ? (bankroll * game.kelly_bet).toFixed(0) : unitSize * (index === 0 ? 2 : 1)}
                        </div>
                        <div className="sizing-info">
                          {game.kelly_bet ? `${(game.kelly_bet * 100).toFixed(1)}% Kelly` : `${index === 0 ? 2 : 1} unit`}
                        </div>
                      </div>
                    </div>
                    
                    {game.patterns && game.patterns.length > 0 && (
                      <div className="bet-patterns">
                        {game.patterns.map((pattern, i) => (
                          <span key={i} className="pattern-tag">{pattern}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

          {/* RIGHT COLUMN - INFO PANELS */}
          <div className="right-sidebar-panels">
            {/* Sharp Money Panel */}
            <div className="info-panel sharp-money-panel">
              <div className="info-panel-header">
                <h3>💰 Sharp Money</h3>
                <span className="panel-badge">PRO</span>
              </div>
              <div className="info-panel-content">
                {sharpPlays.slice(0, 4).map((play, index) => {
                  const edge = ((play.confidence - 0.524) * 100).toFixed(1);
                  return (
                    <div key={index} className="info-item sharp-item">
                      <div className="info-item-game">{play.game}</div>
                      <div className="info-item-details">
                        <span className="sharp-side">{play.sharp_side}</span>
                        <span className="sharp-edge">+{edge}% EDGE</span>
                      </div>
                      {play.patterns && play.patterns.length > 0 && (
                        <div className="sharp-patterns">
                          {play.patterns.slice(0, 2).map((p, i) => (
                            <span key={i} className="mini-pattern">📊 {p}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
                {sharpPlays.length === 0 && (
                  <div className="no-data-message">No sharp plays detected</div>
                )}
              </div>
            </div>

            {/* Live Betting Panel */}
            <div className="info-panel live-betting-panel">
              <div className="info-panel-header">
                <h3>🔴 Live Betting</h3>
                <span className="panel-badge live-badge">LIVE</span>
              </div>
              <div className="info-panel-content">
                {liveGames.length > 0 ? (
                  liveGames.slice(0, 3).map((game) => (
                    <div key={game.id} className="info-item">
                      <div className="info-item-game">
                        {game.away_team} @ {game.home_team}
                      </div>
                      <div className="info-item-details">
                        <span className="live-score">{game.score || '0-0'}</span>
                        <span className="live-quarter">{game.quarter || 'Q1'}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-data-message">No live games</div>
                )}
              </div>
            </div>

            {/* Best Parlays Panel */}
            <div className="info-panel parlays-panel">
              <div className="info-panel-header">
                <h3>🎲 Best Parlays</h3>
                <span className="panel-badge">HOT</span>
              </div>
              <div className="info-panel-content">
                {parlayRecs.slice(0, 3).map((parlay, index) => (
                  <div key={index} className="info-item parlay-item">
                    <div className="parlay-header">
                      <span className="parlay-type">{parlay.type || '3-team'}</span>
                      <span className="parlay-confidence">{((parlay.confidence || 0.55) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="parlay-legs">
                      <span className="parlay-legs-count">{parlay.legs?.length || 3} legs</span>
                    </div>
                    {parlay.games && (
                      <div className="parlay-games">
                        {parlay.games.slice(0, 3).map((game: any, i: number) => (
                          <div key={i} className="parlay-game">
                            <span className="parlay-team">{game.team}</span>
                            <span className="parlay-spread">{game.spread > 0 ? '+' : ''}{game.spread}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {parlayRecs.length === 0 && (
                  <div className="no-data-message">Loading parlays...</div>
                )}
              </div>
            </div>

            {/* Fade Public Panel */}
            <div className="info-panel fade-public-panel">
              <div className="info-panel-header">
                <h3>🔄 Fade Public</h3>
                <span className="panel-badge fade-badge">FADE</span>
              </div>
              <div className="info-panel-content">
                {contrarian.slice(0, 3).map((play, index) => (
                  <div key={index} className="info-item">
                    <div className="info-item-game">{play.game}</div>
                    <div className="info-item-details">
                      <span className="public-heavy">{play.public_percentage}% Public</span>
                      <span className="fade-pick">{play.fade_side}</span>
                    </div>
                    <div className="fade-bar">
                      <div 
                        className="fade-bar-fill"
                        style={{ 
                          width: `${play.public_percentage}%`,
                          backgroundColor: '#ef4444'
                        }}
                      />
                    </div>
                  </div>
                ))}
                {contrarian.length === 0 && (
                  <div className="no-data-message">No fade opportunities</div>
                )}
              </div>
            </div>
          </div>
        </div>
        {/* END TOP LAYOUT CONTAINER */}

        {/* MAIN GAMES SECTION */}
        <main className="games-section">
            <div className="section-title">
              <h2>ALL {sport.toUpperCase()} GAMES</h2>
              <span className="section-subtitle">{games.length} games analyzed</span>
            </div>
            
            <div className="games-grid">
              {games.map((game) => (
                <div key={game.id} className="game-card">
                  <div className="game-card-header">
                    <div className="game-matchup">
                      <span className="away">{game.away_team}</span>
                      <span className="at">@</span>
                      <span className="home">{game.home_team}</span>
                    </div>
                    <div className="game-time-weather">
                      <div className="game-datetime">
                        {formatDate(game.game_time)} • {getWeatherIcon(game.weather)} {game.weather?.temperature ? `${Math.round(game.weather.temperature)}°F` : ''}
                        {game.weather?.wind_speed && game.weather.wind_speed > 15 && (
                          <span> 💨{Math.round(game.weather.wind_speed)}mph</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Main Odds Display */}
                  <div className="game-main-odds">
                    <div className="odds-row">
                      <div className="odds-item">
                        <div className="odds-label">Spread</div>
                        <div className="odds-value">{game.spread > 0 ? '+' : ''}{game.spread}</div>
                      </div>
                      <div className="odds-item">
                        <div className="odds-label">Total</div>
                        <div className="odds-value">{game.total}</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Public Betting */}
                  {game.public_percentage && (
                    <div className="public-section">
                      <div className="public-header">Public Betting (100)</div>
                      <div className="public-split">
                        <div className="public-team">
                          <div className="public-bar-container">
                            <div 
                              className="public-bar-fill home" 
                              style={{ width: `${game.public_home_percentage}%` }}
                            />
                            <span className="public-percent">{game.public_home_percentage}%</span>
                          </div>
                          <span className="team-name">{game.home_team}</span>
                        </div>
                        <div className="public-team">
                          <div className="public-bar-container">
                            <div 
                              className="public-bar-fill away" 
                              style={{ width: `${game.public_away_percentage}%` }}
                            />
                            <span className="public-percent">{game.public_away_percentage}%</span>
                          </div>
                          <span className="team-name">{game.away_team}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Moneylines by Book - Sorted by Best Line */}
                  {game.book_odds && (
                    <div className="moneylines-section">
                      <div className="ml-header">Sportsbook Lines (Best to Worst)</div>
                      <div className="ml-columns">
                        <div className="ml-column">
                          <div className="ml-team-name">{game.away_team}</div>
                          {(() => {
                            // Determine if we're picking the away team
                            const pickingAway = game.pick && game.pick.includes(game.away_team);
                            
                            // Sort all books by best spread for away team
                            const sortedBooks = Object.entries(game.book_odds || {})
                              .filter(([_, odds]: [string, any]) => odds.spread !== undefined)
                              .sort((a: [string, any], b: [string, any]) => {
                                // For away team, they want the most positive spread (opposite of home spread)
                                const spreadA = -a[1].spread; // Flip sign for away team
                                const spreadB = -b[1].spread;
                                // Higher spread is better for away team
                                return spreadB - spreadA;
                              });
                            
                            return sortedBooks.map(([book, odds]: [string, any], index) => {
                              const awaySpread = -odds.spread;
                              const isBest = index === 0;
                              return (
                                <div key={book} className={`ml-row ${isBest && pickingAway ? 'best-line' : ''}`}>
                                  <span className="book-name">{formatBookName(book)}</span>
                                  <span className={`ml-spread ${isBest && pickingAway ? 'best-spread' : ''}`}>
                                    {awaySpread > 0 ? '+' : ''}{awaySpread}
                                  </span>
                                  <span className="ml-odds">{odds.ml_away || '-'}</span>
                                </div>
                              );
                            });
                          })()}
                        </div>
                        <div className="ml-column">
                          <div className="ml-team-name">{game.home_team}</div>
                          {(() => {
                            // Determine if we're picking the home team
                            const pickingHome = game.pick && game.pick.includes(game.home_team);
                            
                            // Sort all books by best spread for home team
                            const sortedBooks = Object.entries(game.book_odds || {})
                              .filter(([_, odds]: [string, any]) => odds.spread !== undefined)
                              .sort((a: [string, any], b: [string, any]) => {
                                // For home team, higher spread is better (less negative or more positive)
                                const spreadA = a[1].spread;
                                const spreadB = b[1].spread;
                                return spreadB - spreadA;
                              });
                            
                            return sortedBooks.map(([book, odds]: [string, any], index) => {
                              const isBest = index === 0;
                              return (
                                <div key={book} className={`ml-row ${isBest && pickingHome ? 'best-line' : ''}`}>
                                  <span className="book-name">{formatBookName(book)}</span>
                                  <span className={`ml-spread ${isBest && pickingHome ? 'best-spread' : ''}`}>
                                    {odds.spread > 0 ? '+' : ''}{odds.spread}
                                  </span>
                                  <span className="ml-odds">{odds.ml_home || '-'}</span>
                                </div>
                              );
                            });
                          })()}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Pick & Analysis Section */}
                  {game.pick && (
                    <div className="pick-analysis">
                      <div className="pick-header">
                        <span className="pick-text">{game.pick}</span>
                        <span className="pick-confidence">({(game.confidence * 100).toFixed(0)}% confidence)</span>
                      </div>
                      
                      {game.kelly_bet && game.kelly_bet > 0.5 && (
                        <div className="bet-recommendation">
                          <div className="bet-amount">
                            <span className="bet-label">💵</span>
                            <span className="bet-value">${Math.max(20, Math.round(unitSize * game.kelly_bet))}</span>
                            <span className="bet-unit">({Math.round(game.kelly_bet)}%)</span>
                          </div>
                          {game.edge && (
                            <div className="bet-payout">
                              Win ${Math.max(20, Math.round(unitSize * game.kelly_bet * 0.9))} → ${Math.max(40, Math.round(unitSize * game.kelly_bet * 1.9))}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Key Insights */}
                      {game.insights && game.insights.length > 0 && (
                        <div className="key-insights">
                          {game.insights[0] && (
                            <div className="key-insight">🎯 {game.insights[0]}</div>
                          )}
                        </div>
                      )}
                      
                      <div className="books-available">
                        {game.books_count || 10} Books Available
                      </div>
                    </div>
                  )}
                  
                  
                  
                  <div className="game-card-indicators">
                    {game.sharp_action && <span className="ind sharp">SHARP</span>}
                    {game.reverse_line_movement && <span className="ind rlm">RLM</span>}
                    {game.steam_move && <span className="ind steam">STEAM</span>}
                    {game.contrarian && <span className="ind fade">FADE</span>}
                  </div>
                </div>
              ))}
            </div>
          </main>
        </div>
        
        {/* Help Modal */}
        <HelpModal isOpen={showHelp} onClose={() => setShowHelp(false)} />
      </div>
  );
};

export default Dashboard;