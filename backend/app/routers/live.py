"""
Live betting and game monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import requests

from app.database.connection import get_db
from app.models.user import User
# Authentication removed - public access

router = APIRouter()

ODDS_API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

@router.get("/games")
async def get_live_games(
    sport: str = "nfl",
    db: Session = Depends(get_db)
):
    """Get live/in-play games with current odds"""
    
    # Map sports to API keys
    sport_mapping = {
        "nfl": "americanfootball_nfl",
        "ncaaf": "americanfootball_ncaaf",
        "mlb": "baseball_mlb"
    }
    sport_key = sport_mapping.get(sport, sport)
    
    try:
        # Get live and upcoming games
        url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us',
            'markets': 'spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,fanduel'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Also fetch scores for live games
        scores_url = f"{ODDS_API_BASE}/sports/{sport_key}/scores"
        scores_params = {
            'apiKey': ODDS_API_KEY,
            'daysFrom': '1'  # Get scores from last 24 hours
        }
        scores_response = requests.get(scores_url, params=scores_params, timeout=10)
        
        # Build scores lookup dictionary
        scores_data = {}
        if scores_response.status_code == 200:
            for game_score in scores_response.json():
                game_id = game_score.get('id')
                scores = game_score.get('scores', [])
                if scores and len(scores) >= 2:
                    scores_data[game_id] = {
                        'home_score': scores[0].get('score', '0'),
                        'away_score': scores[1].get('score', '0'),
                        'completed': game_score.get('completed', False)
                    }
        
        if response.status_code == 200:
            all_games = response.json()
            
            # Filter for games happening soon or in progress
            now = datetime.now(timezone.utc)
            three_hours_from_now = now + timedelta(hours=3)
            
            live_games = []
            upcoming_games = []
            
            for game in all_games:
                game_id = game.get('id')
                game_time_str = game.get('commence_time', '')
                
                # Add scores if available
                if game_id in scores_data:
                    game['home_score'] = scores_data[game_id]['home_score']
                    game['away_score'] = scores_data[game_id]['away_score']
                else:
                    game['home_score'] = '0'
                    game['away_score'] = '0'
                
                if game_time_str:
                    game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
                    
                    # Check if game is live (started within last 4 hours)
                    time_since_start = (now - game_time).total_seconds() / 3600  # hours since start
                    if 0 <= time_since_start <= 4:  # Game started 0-4 hours ago
                        # Game is likely in progress
                        game['status'] = 'live'
                        game['quarter'] = get_estimated_quarter(game_time, now, sport)
                        live_games.append(format_live_game(game))
                    
                    # Check if game is starting soon
                    elif now < game_time <= three_hours_from_now:
                        game['status'] = 'upcoming'
                        game['time_until'] = format_time_until(game_time, now)
                        upcoming_games.append(format_live_game(game))
            
            return {
                "live_games": live_games,
                "upcoming_games": upcoming_games,
                "total_live": len(live_games),
                "total_upcoming": len(upcoming_games),
                "last_update": datetime.now().isoformat()
            }
        else:
            print(f"API returned status code: {response.status_code}")
            return {
                "live_games": [],
                "upcoming_games": [],
                "error": f"API returned status {response.status_code}",
                "last_update": datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"Error fetching live games: {e}")
        return {
            "live_games": [],
            "upcoming_games": [],
            "error": str(e)
        }

def get_estimated_quarter(game_time: datetime, now: datetime, sport: str = "nfl") -> str:
    """Estimate game quarter/inning based on start time"""
    elapsed = (now - game_time).total_seconds() / 60  # minutes
    
    if sport == "mlb":
        # MLB games average 3 hours (180 minutes)
        inning = min(9, int(elapsed / 20) + 1)  # ~20 minutes per inning
        
        if elapsed < 20:
            return "Top 1st"
        elif elapsed < 40:
            return "Top 2nd"
        elif elapsed < 60:
            return "Top 3rd"
        elif elapsed < 80:
            return "Top 4th"
        elif elapsed < 100:
            return "Top 5th"
        elif elapsed < 120:
            return "Top 6th"
        elif elapsed < 140:
            return "Top 7th"
        elif elapsed < 160:
            return "Top 8th"
        elif elapsed < 180:
            return "Top 9th"
        else:
            return "Final"
    else:
        # Football games
        if elapsed < 15:
            return "1st Quarter"
        elif elapsed < 30:
            return "End of 1st"
        elif elapsed < 45:
            return "2nd Quarter"
        elif elapsed < 75:  # Halftime
            return "Halftime"
        elif elapsed < 90:
            return "3rd Quarter"
        elif elapsed < 105:
            return "End of 3rd"
        elif elapsed < 120:
            return "4th Quarter"
        elif elapsed < 135:
            return "End of 4th"
        else:
            return "Final"

def format_time_until(game_time: datetime, now: datetime) -> str:
    """Format time until game starts"""
    delta = game_time - now
    hours = delta.total_seconds() / 3600
    
    if hours < 1:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} min"
    else:
        return f"{int(hours)}h {int((hours % 1) * 60)}m"

def format_live_game(game: Dict) -> Dict:
    """Format game data for live display"""
    home_team = game.get('home_team', '')
    away_team = game.get('away_team', '')
    
    # Get current lines from books
    current_lines = {}
    for bookmaker in game.get('bookmakers', []):
        book_name = bookmaker.get('key', '')
        for market in bookmaker.get('markets', []):
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    if outcome['name'] == home_team:
                        current_lines[f'{book_name}_spread'] = outcome.get('point', 0)
            elif market['key'] == 'totals':
                for outcome in market['outcomes']:
                    if outcome['name'] == 'Over':
                        current_lines[f'{book_name}_total'] = outcome.get('point', 0)
    
    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_score": game.get('home_score', '0'),
        "away_score": game.get('away_score', '0'),
        "game_time": game.get('commence_time'),
        "status": game.get('status', 'upcoming'),
        "quarter": game.get('quarter', ''),
        "time_until": game.get('time_until', ''),
        "current_lines": current_lines,
        "movement": detect_line_movement(game)
    }

def detect_line_movement(game: Dict) -> Dict:
    """Detect significant line movements"""
    # TODO: Implement real line movement detection
    # Would need to compare to historical lines from database
    
    # For now, return no movement until we have historical data
    return {"has_movement": False}

@router.get("/alerts")
async def get_betting_alerts(
    db: Session = Depends(get_db)
):
    """Get real-time betting alerts for line movements and opportunities"""
    
    alerts = []
    
    # Check for steam moves (would be real-time in production)
    alerts.append({
        "type": "steam",
        "severity": "high",
        "game": "Example Game",
        "message": "Steam move detected on Under 45.5",
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "alerts": alerts,
        "total": len(alerts)
    }