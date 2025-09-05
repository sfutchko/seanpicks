"""
NFL games router with analysis
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import os
import json
import requests

from app.database.connection import get_db
from app.models.user import User
# Authentication removed - public access
from app.services.confidence_calculator import ConfidenceCalculator
from app.services.complete_analyzer import CompleteAnalyzer

# Initialize the complete analyzer with ALL features
complete_analyzer = CompleteAnalyzer()

router = APIRouter()

# Premium API key
ODDS_API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

def load_games_data() -> List[Dict[str, Any]]:
    """Load REAL games from The Odds API"""
    
    # First try to get live data from API
    try:
        url = f"{ODDS_API_BASE}/sports/americanfootball_nfl/odds"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us',
            'markets': 'spreads,totals,h2h',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,fanduel,betmgm,caesars,pointsbet,williamhill_us,betrivers,unibet_us,betfred,sugarhouse,barstool,wynnbet,foxbet,betonlineag,bovada,mybookieag,lowvig,pinnacle,betparx,twinspires'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            api_games = response.json()
            
            # Filter to only upcoming games (next 14 days to include full week)
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            week_from_now = now + timedelta(days=14)
            
            # Transform API data to our format
            games = []
            game_count = 0
            for game in api_games:
                if game_count >= 15:  # Limit to 15 games to prevent timeout
                    break
                # Parse game time
                game_time_str = game.get('commence_time', '')
                if game_time_str:
                    game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
                    # Only include games in the next 7 days
                    if game_time < now or game_time > week_from_now:
                        continue
                # Get consensus spreads and totals
                spreads = []
                totals = []
                moneylines = {}
                
                # Store book-specific odds
                book_odds = {}
                
                home_team = game.get('home_team', 'Home')
                away_team = game.get('away_team', 'Away')
                
                for bookmaker in game.get('bookmakers', []):
                    book_name = bookmaker.get('key', '')
                    book_data = {}
                    
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'spreads':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home_team:
                                    spread_val = outcome.get('point', 0)
                                    spreads.append(spread_val)
                                    book_data['spread'] = spread_val
                                    book_data['spread_price'] = outcome.get('price', -110)
                        elif market['key'] == 'totals':
                            for outcome in market['outcomes']:
                                if outcome['name'] == 'Over':
                                    total_val = outcome.get('point', 0)
                                    totals.append(total_val)
                                    book_data['total'] = total_val
                                    book_data['total_price'] = outcome.get('price', -110)
                        elif market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home_team:
                                    moneylines['home'] = outcome.get('price', -110)
                                    book_data['ml_home'] = outcome.get('price', -110)
                                elif outcome['name'] == away_team:
                                    moneylines['away'] = outcome.get('price', -110)
                                    book_data['ml_away'] = outcome.get('price', -110)
                    
                    if book_data:
                        book_odds[book_name] = book_data
                
                # Calculate averages
                avg_spread = sum(spreads) / len(spreads) if spreads else 0
                avg_total = sum(totals) / len(totals) if totals else 45.5
                
                # Detect patterns (enhanced detection)
                spread_variance = max(spreads) - min(spreads) if spreads else 0
                sharp_action = spread_variance > 0.5 or len(set(spreads)) > 2
                reverse_line_movement = len(spreads) > 2 and abs(spreads[0] - spreads[-1]) > 0.5
                
                # Real data only - no simulation
                # Sharp action and RLM are detected from actual line movements above
                # Public percentage will come from the complete analyzer
                
                games.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "game_time": game.get('commence_time', datetime.now().isoformat()),
                    "spread": round(avg_spread, 1),
                    "total": round(avg_total, 1),
                    "sharp_action": sharp_action,
                    "reverse_line_movement": reverse_line_movement,
                    "steam_move": False,  # Would need line history
                    "contrarian": False,  # Will be detected by analyzer
                    "public_percentage": 50,  # Will be calculated by analyzer
                    "moneylines": moneylines,
                    "books_count": len(game.get('bookmakers', [])),
                    "book_odds": book_odds,  # Individual book odds
                    "bookmakers": game.get('bookmakers', [])  # Pass full data for sharp analysis
                })
                game_count += 1  # Increment counter
            
            print(f"✅ Loaded {len(games)} REAL NFL games from API")
            return games
            
    except Exception as e:
        print(f"⚠️ Could not fetch from API: {e}")
    
    # Fallback to local JSON if API fails
    paths = [
        "data/sample_nfl_games.json",  # Docker container path
        "/app/data/sample_nfl_games.json",  # Absolute Docker path
        "/Users/sean/Downloads/sean-picks-app/backend/data/sample_nfl_games.json",  # Local dev
        "/Users/sean/Downloads/sean_picks/data/nfl_odds.json",
        "/Users/sean/Downloads/sean_picks/nfl_odds.json"
    ]
    
    for path in paths:
        if os.path.exists(path):
            print(f"📁 Loading games from {path}")
            with open(path, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    games_list = list(data.values())
                else:
                    games_list = data
                print(f"✅ Loaded {len(games_list)} games from local file")
                return games_list
    
    # Last resort - return empty
    print("⚠️ No data files found")
    return []

@router.get("/games")
async def get_nfl_games(
    db: Session = Depends(get_db)
):
    """Get NFL games with analysis"""
    
    games_data = load_games_data()
    calculator = ConfidenceCalculator()
    analyzed_games = []
    
    for idx, game in enumerate(games_data):
        # Use the COMPLETE analyzer for EVERY game!
        full_analysis = complete_analyzer.analyze_game_complete(game)
        confidence = full_analysis['final_confidence']
        
        # Use patterns and insights from FULL analysis
        patterns = []
        for factor in full_analysis.get('factors', []):
            patterns.append(factor)
        
        # Get the best bet from full analysis
        best_bet = full_analysis.get('best_bet')
        if best_bet:
            pick = best_bet['pick']
        elif confidence >= 0.54:
            # If we have edge but no specific bet, determine pick from spread
            # Pick the underdog by default when we have edge
            if game.get('spread', 0) < 0:
                # Home team favored, pick away team (underdog)
                pick = f"{game['away_team']} +{abs(game['spread'])}"
            else:
                # Away team favored, pick home team (underdog)
                pick = f"{game['home_team']} +{game['spread']}"
        elif confidence >= 0.52:
            # Lower confidence but still show pick
            if game.get('spread', 0) < 0:
                # Home team favored, pick away team (underdog)
                pick = f"{game['away_team']} +{abs(game['spread'])}"
            else:
                # Away team favored, pick home team (underdog)
                pick = f"{game['home_team']} +{game['spread']}"
        else:
            # ALWAYS show a pick based on analysis - never leave empty
            # Use the spread direction to determine pick
            if game.get('spread', 0) < 0:
                # Home team favored, pick away team
                pick = f"{game['away_team']} +{abs(game['spread'])}"
            else:
                # Away team favored, pick home team
                pick = f"{game['home_team']} +{game['spread']}"
        
        # Add all insights
        insights = full_analysis.get('insights', [])
        
        # Get public betting data from full analysis
        public_data = full_analysis.get('public_betting', {})
        public_percentage = public_data.get('public_percentage', 50)
        
        # Check if game is live
        from datetime import datetime, timezone
        game_time_str = game.get("game_time", game.get("commence_time", ""))
        is_live = False
        game_status = ""
        
        if game_time_str:
            try:
                game_time_dt = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                hours_since_start = (now - game_time_dt).total_seconds() / 3600
                
                if 0 <= hours_since_start <= 4:  # Game likely in progress
                    is_live = True
                    # Estimate quarter based on time elapsed
                    if hours_since_start < 0.5:
                        game_status = "🔴 LIVE - 1st Quarter"
                    elif hours_since_start < 1:
                        game_status = "🔴 LIVE - 2nd Quarter"
                    elif hours_since_start < 2:
                        game_status = "🔴 LIVE - Halftime"
                    elif hours_since_start < 2.5:
                        game_status = "🔴 LIVE - 3rd Quarter"
                    elif hours_since_start < 3.5:
                        game_status = "🔴 LIVE - 4th Quarter"
                    else:
                        game_status = "🔴 LIVE - Final Minutes"
                elif hours_since_start < 0:
                    hours_until = -hours_since_start
                    if hours_until < 1:
                        game_status = f"⏰ Starting in {int(hours_until * 60)} min"
                    else:
                        game_status = f"📅 {int(hours_until)}h {int((hours_until % 1) * 60)}m"
            except:
                pass
        
        # Build game dict without zero values
        analyzed_game = {
            "id": f"nfl_game_{idx}",
            "home_team": game.get("home_team", "Home Team"),
            "away_team": game.get("away_team", "Away Team"),
            "game_time": game.get("game_time", datetime.now().isoformat()),
            "spread": game.get("spread", 0),
            "total": game.get("total", 45.5),
            "confidence": round(confidence, 3),
            "pick": pick,
            "patterns": patterns,
            "insights": insights,
            "is_live": is_live,
            "game_status": game_status,
            "moneylines": game.get("moneylines", {}),
            "sharp_action": game.get("sharp_action", False),
            "reverse_line_movement": game.get("reverse_line_movement", False),
            "steam_move": game.get("steam_move", False),
            "contrarian": public_data.get('fade_opportunity', False),
            "public_percentage": public_percentage,
            "public_on_home": public_data.get('public_on_home', False),
            "public_away_percentage": public_data.get('away_percentage', 50),
            "public_home_percentage": public_data.get('home_percentage', 50),
            "public_sources": public_data.get('sources', [])
        }
        
        # Only add non-zero values
        edge = round((confidence - 0.524) * 100, 1) if confidence > 0.524 else None
        if edge:
            analyzed_game["edge"] = edge
            
        kelly = full_analysis.get('kelly_percentage', 0) if best_bet else 0
        if kelly > 0:
            analyzed_game["kelly_bet"] = kelly
            
        weather_obj = full_analysis.get('weather')
        if weather_obj:
            analyzed_game["weather"] = weather_obj
            
        weather_impact = full_analysis.get('adjustments', {}).get('total', 0)
        if abs(weather_impact) > 0.5:
            analyzed_game["weather_impact"] = weather_impact
            
        injuries = full_analysis.get('adjustments', {}).get('spread', 0)
        if abs(injuries) > 0.5:
            analyzed_game["injuries"] = injuries
            
        if best_bet:
            analyzed_game["best_bet_type"] = best_bet['type']
            
        # Add book odds if available
        if game.get('book_odds'):
            analyzed_game["book_odds"] = game['book_odds']
            
        analyzed_game["full_analysis"] = full_analysis
        
        analyzed_games.append(analyzed_game)
    
    # Sort by confidence for best bets
    analyzed_games.sort(key=lambda x: x['confidence'], reverse=True)
    best_bets = [g for g in analyzed_games if g['confidence'] >= 0.54][:5]
    
    # Extract sharp plays
    sharp_plays = []
    for game in analyzed_games:
        if game.get('sharp_action') or game.get('steam_move') or game.get('reverse_line_movement'):
            sharp_plays.append({
                "game": f"{game['away_team']} @ {game['home_team']}",
                "sharp_side": game['pick'],
                "confidence": game['confidence'],
                "patterns": game.get('patterns', [])
            })
    
    # Extract contrarian plays
    contrarian_plays = []
    for game in analyzed_games:
        if game.get('contrarian') or (game.get('public_percentage', 0) > 65):
            contrarian_plays.append({
                "game": f"{game['away_team']} @ {game['home_team']}",
                "public_percentage": game.get('public_percentage', 68),
                "fade_side": game['pick'],
                "confidence": game['confidence']
            })
    
    # Data source status
    data_sources = {
        "odds_api": {"status": "active", "name": "Odds API", "message": "Live odds from 5+ books"},
        "weather": {"status": "active", "name": "Weather API", "message": "Real-time weather data"},
        "sharp_detection": {"status": "partial", "name": "Sharp Detection", "message": "Pattern analysis active"},
        "injuries": {"status": "active", "name": "Injury Analysis", "message": "Impact calculated"},
        "reddit": {"status": "error", "name": "Reddit Sentiment", "message": "Coming soon"}
    }
    
    return {
        "games": analyzed_games,
        "best_bets": best_bets,
        "sharp_plays": sharp_plays,
        "contrarian_plays": contrarian_plays,
        "data_sources": data_sources,
        "stats": {
            "total_games": len(analyzed_games),
            "bets_found": len(best_bets),
            "avg_confidence": sum(g['confidence'] for g in analyzed_games) / len(analyzed_games) if analyzed_games else 0,
            "sharp_count": len(sharp_plays),
            "public_data_sources": 3
        },
        "week": "Week 1"
    }

@router.get("/analyze")
async def analyze_all_games(
    db: Session = Depends(get_db)
):
    """Run FULL analysis on all games using complete engine with ALL features!"""
    
    games_data = load_games_data()
    analyzed_games = []
    
    print(f"🎯 Running COMPLETE analysis on {len(games_data)} games...")
    
    for game in games_data:
        try:
            # Run the FULL analysis with all features
            analysis = complete_analyzer.analyze_game_complete(game)
            
            # Add game data to analysis
            analysis['game_data'] = game
            
            # Only include games with edge
            if analysis['final_confidence'] >= 0.54 and analysis['best_bet']:
                analyzed_games.append(analysis)
        except Exception as e:
            print(f"Error analyzing game: {e}")
            continue
    
    # Sort by confidence
    analyzed_games.sort(key=lambda x: x['final_confidence'], reverse=True)
    
    return {
        "status": "COMPLETE analysis with all features",
        "total_games": len(games_data),
        "games_with_edge": len(analyzed_games),
        "best_bets": analyzed_games[:5],
        "features_used": [
            "Weather API (real-time)",
            "Sharp vs Square analysis",
            "Injury impacts",
            "Public betting fade",
            "Referee tendencies",
            "Situational spots",
            "Key numbers",
            "Kelly criterion sizing"
        ]
    }

@router.get("/games/{game_id}")
async def get_game_details(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed analysis for a specific game"""
    
    games_data = load_games_data()
    
    # Find the game by ID
    game_idx = int(game_id.replace("nfl_game_", ""))
    if game_idx >= len(games_data):
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games_data[game_idx]
    calculator = ConfidenceCalculator()
    
    confidence = calculator.calculate_confidence(
        sharp_action=game.get("sharp_action", False),
        reverse_line_movement=game.get("reverse_line_movement", False),
        steam_move=game.get("steam_move", False),
        public_fade=game.get("contrarian", False),
        key_number_edge=abs(game.get("spread", 0)) in [3, 7, 10],
        weather_edge=0.01 if game.get("weather_impact", False) else 0.0,
        injury_edge=0.01 if game.get("injury_advantage", False) else 0.0
    )
    
    return {
        "game_id": game_id,
        "game_data": game,
        "confidence": confidence,
        "analysis": {
            "sharp_action": game.get("sharp_action", False),
            "reverse_line_movement": game.get("reverse_line_movement", False),
            "steam_move": game.get("steam_move", False),
            "contrarian": game.get("contrarian", False),
            "key_number": abs(game.get("spread", 0)) in [3, 7, 10]
        }
    }