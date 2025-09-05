import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './BetTracker.css';

interface PerformanceStats {
  record: string;
  win_rate: number;
  units: number;
  roi: number;
  total_bets: number;
  by_confidence: {
    high: { record: string; count: number };
    medium: { record: string; count: number };
    low: { record: string; count: number };
  };
}

interface TrackedBet {
  game: string;
  pick: string;
  spread: number;
  confidence: number;
  result: string;
  score?: string;
  actual_spread?: number;
  game_time: string;
  sport?: string;
}

const BetTracker: React.FC = () => {
  const navigate = useNavigate();
  const [performance, setPerformance] = useState<PerformanceStats | null>(null);
  const [recentResults, setRecentResults] = useState<TrackedBet[]>([]);
  const [pendingBets, setPendingBets] = useState<TrackedBet[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState(7); // Days to show
  const [activeTab, setActiveTab] = useState<'performance' | 'results' | 'pending'>('performance');
  const [selectedSport, setSelectedSport] = useState<'NFL' | 'NCAAF' | 'MLB'>('NFL');
  const [performanceFilter, setPerformanceFilter] = useState<'all' | 'nfl' | 'ncaaf' | 'mlb'>('all');

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchData();
  }, [timeframe]);

  const fetchData = async () => {
    setLoading(true);
    
    try {
      // Fetch performance stats
      const perfResponse = await axios.get(
        `${API_URL}/api/tracking/performance?days=${timeframe}`
      );
      setPerformance(perfResponse.data);

      // Fetch recent results
      const resultsResponse = await axios.get(
        `${API_URL}/api/tracking/results`
      );
      setRecentResults(resultsResponse.data);

      // Fetch pending bets
      const pendingResponse = await axios.get(
        `${API_URL}/api/tracking/pending`
      );
      setPendingBets(pendingResponse.data);
    } catch (error) {
      console.error('Error fetching tracking data:', error);
    } finally {
      setLoading(false);
    }
  };

  const trackCurrentBets = async () => {
    try {
      // Get current best bets based on selected sport
      let endpoint = '/api/nfl/games';
      if (selectedSport === 'NCAAF') endpoint = '/api/ncaaf/games';
      else if (selectedSport === 'MLB') endpoint = '/api/mlb/games';
      const gamesResponse = await axios.get(
        `${API_URL}${endpoint}`
      );
      
      console.log(`${selectedSport} games response:`, gamesResponse.data);
      
      // Both endpoints return an object with games property
      let games = gamesResponse.data.games || [];
      
      console.log(`${selectedSport} games array:`, games);
      
      // Only track games with confidence >= 55% (best bets)
      // No time restriction - track all best bets regardless of game time
      const bestBets = games.filter((g: any) => g.confidence >= 0.55);
      
      console.log('Best bets found:', bestBets.length, bestBets);
      
      if (bestBets.length === 0) {
        alert('No best bets found (confidence >= 55%)');
        return;
      }
      
      // Track them
      const trackResponse = await axios.post(
        `${API_URL}/api/tracking/track-current-best-bets`,
        { games: bestBets }
      );
      
      console.log('Track response:', trackResponse.data);
      
      alert(`${bestBets.length} ${selectedSport} best bets tracked successfully!`);
      fetchData(); // Refresh data
    } catch (error: any) {
      console.error('Error tracking bets:', error);
      console.error('Error response:', error.response?.data);
      alert(`Failed to track bets: ${error.response?.data?.detail || error.message}`);
    }
  };

  const updateScores = async () => {
    try {
      // Update scores for the selected sport
      let sportParam = 'americanfootball_nfl';
      if (selectedSport === 'NCAAF') sportParam = 'americanfootball_ncaaf';
      else if (selectedSport === 'MLB') sportParam = 'baseball_mlb';
      const response = await axios.post(
        `${API_URL}/api/tracking/update-scores?sport=${sportParam}`,
        {}
      );
      
      const data = response.data;
      alert(`Score update completed! Checked ${data.games_checked} games, updated ${data.bets_updated} bets.`);
      setTimeout(fetchData, 1000); // Refresh after 1 second
    } catch (error: any) {
      console.error('Error updating scores:', error);
      alert(`Error updating scores: ${error.response?.data?.message || error.message}`);
    }
  };

  const getResultColor = (result: string) => {
    switch(result) {
      case 'WIN': return '#00ff88';
      case 'LOSS': return '#ff4444';
      case 'PUSH': return '#ffaa00';
      default: return '#666';
    }
  };

  if (loading) {
    return <div className="loading">Loading bet tracking data...</div>;
  }

  return (
    <div className="bet-tracker-container">
      <div className="tracker-header">
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back to Dashboard
        </button>
        <div className="tracker-header-top">
          <h1>📊 Best Bet Performance Tracker</h1>
          <div className="tracker-controls">
          <select 
            value={selectedSport} 
            onChange={(e) => setSelectedSport(e.target.value as 'NFL' | 'NCAAF' | 'MLB')}
            className="sport-selector"
          >
            <option value="NFL">NFL</option>
            <option value="NCAAF">College Football</option>
            <option value="MLB">MLB</option>
          </select>
          <select value={timeframe} onChange={(e) => setTimeframe(Number(e.target.value))}>
            <option value={1}>Last 24 Hours</option>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={365}>Season</option>
          </select>
          <button onClick={trackCurrentBets} className="track-btn">
            Track Current {selectedSport} Best Bets
          </button>
          <button onClick={updateScores} className="update-btn">
            Update Scores
          </button>
          </div>
        </div>
      </div>

      <div className="tracker-tabs">
        <button 
          className={activeTab === 'performance' ? 'active' : ''}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button 
          className={activeTab === 'results' ? 'active' : ''}
          onClick={() => setActiveTab('results')}
        >
          Recent Results
        </button>
        <button 
          className={activeTab === 'pending' ? 'active' : ''}
          onClick={() => setActiveTab('pending')}
        >
          Pending Bets
        </button>
      </div>

      {activeTab === 'performance' && performance && (
        <div className="performance-section">
          <div className="sport-filter-buttons" style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
            <button 
              className={`sport-filter-btn ${performanceFilter === 'all' ? 'active' : ''}`}
              onClick={() => setPerformanceFilter('all')}
              style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #333' }}
            >
              All Sports
            </button>
            <button 
              className={`sport-filter-btn ${performanceFilter === 'nfl' ? 'active' : ''}`}
              onClick={() => setPerformanceFilter('nfl')}
              style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #333' }}
            >
              🏈 NFL
            </button>
            <button 
              className={`sport-filter-btn ${performanceFilter === 'ncaaf' ? 'active' : ''}`}
              onClick={() => setPerformanceFilter('ncaaf')}
              style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #333' }}
            >
              🎓 NCAAF
            </button>
            <button 
              className={`sport-filter-btn ${performanceFilter === 'mlb' ? 'active' : ''}`}
              onClick={() => setPerformanceFilter('mlb')}
              style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #333' }}
            >
              ⚾ MLB
            </button>
          </div>
          <div className="performance-cards">
            <div className="perf-card main-record">
              <h3>
                {performanceFilter === 'all' ? 'Overall' : 
                 performanceFilter === 'nfl' ? '🏈 NFL' :
                 performanceFilter === 'ncaaf' ? '🎓 NCAAF' :
                 performanceFilter === 'mlb' ? '⚾ MLB' : ''} Record
              </h3>
              <div className="record-display">{performance.record}</div>
              <div className="win-rate">{performance.win_rate.toFixed(1)}% Win Rate</div>
            </div>
            
            <div className="perf-card units">
              <h3>Units Won/Lost</h3>
              <div className={`units-display ${performance.units >= 0 ? 'positive' : 'negative'}`}>
                {performance.units >= 0 ? '+' : ''}{performance.units}
              </div>
              <div className="roi-display">ROI: {performance.roi}%</div>
            </div>
            
            <div className="perf-card total-bets">
              <h3>Total Bets Tracked</h3>
              <div className="bets-display">{performance.total_bets}</div>
            </div>
          </div>

          {performance.by_confidence && (
            <div className="confidence-breakdown">
              <h3>Performance by Confidence Level</h3>
              <div className="confidence-cards">
                <div className="conf-card high">
                  <div className="conf-label">High (60%+)</div>
                  <div className="conf-record">{performance.by_confidence.high?.record || '0-0'}</div>
                  <div className="conf-count">{performance.by_confidence.high?.count || 0} bets</div>
                </div>
                <div className="conf-card medium">
                  <div className="conf-label">Medium (55-60%)</div>
                  <div className="conf-record">{performance.by_confidence.medium?.record || '0-0'}</div>
                  <div className="conf-count">{performance.by_confidence.medium?.count || 0} bets</div>
                </div>
                <div className="conf-card low">
                  <div className="conf-label">Low (&lt;55%)</div>
                  <div className="conf-record">{performance.by_confidence.low?.record || '0-0'}</div>
                  <div className="conf-count">{performance.by_confidence.low?.count || 0} bets</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'results' && (
        <div className="results-section">
          <table className="results-table">
            <thead>
              <tr>
                <th>Game</th>
                <th>Pick</th>
                <th>Spread</th>
                <th>Confidence</th>
                <th>Result</th>
                <th>Score</th>
                <th>Cover</th>
              </tr>
            </thead>
            <tbody>
              {recentResults.map((bet, index) => (
                <tr key={index} className={`result-${bet.result.toLowerCase()}`}>
                  <td>
                    <span style={{ marginRight: '8px' }}>
                      {bet.sport === 'nfl' && '🏈'}
                      {bet.sport === 'ncaaf' && '🎓'}
                      {bet.sport === 'mlb' && '⚾'}
                    </span>
                    {bet.game}
                  </td>
                  <td>{bet.pick}</td>
                  <td>{bet.spread > 0 ? '+' : ''}{bet.spread}</td>
                  <td>{bet.confidence}%</td>
                  <td>
                    <span style={{ color: getResultColor(bet.result), fontWeight: 'bold' }}>
                      {bet.result}
                    </span>
                  </td>
                  <td>{bet.score}</td>
                  <td>{bet.actual_spread ? `${bet.actual_spread > 0 ? '+' : ''}${bet.actual_spread}` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'pending' && (
        <div className="pending-section">
          <table className="pending-table">
            <thead>
              <tr>
                <th>Game</th>
                <th>Pick</th>
                <th>Spread</th>
                <th>Confidence</th>
                <th>Game Time</th>
                <th>Times Tracked</th>
              </tr>
            </thead>
            <tbody>
              {pendingBets.map((bet: any, index) => (
                <tr key={index}>
                  <td>
                    <span style={{ marginRight: '8px' }}>
                      {bet.sport === 'nfl' && '🏈'}
                      {bet.sport === 'ncaaf' && '🎓'}
                      {bet.sport === 'mlb' && '⚾'}
                    </span>
                    {bet.game}
                  </td>
                  <td>{bet.pick}</td>
                  <td>{bet.spread > 0 ? '+' : ''}{bet.spread}</td>
                  <td>{(bet.confidence * 100).toFixed(1)}%</td>
                  <td>{new Date(bet.game_time).toLocaleString()}</td>
                  <td>{bet.times_appeared}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default BetTracker;