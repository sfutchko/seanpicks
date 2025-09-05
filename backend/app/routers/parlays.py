"""
Parlay optimization router with intelligent parlay building
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.user import User
# Authentication removed - public access
# Import the actual load_games_data functions directly
from app.services.confidence_calculator import ConfidenceCalculator
from app.services.mlb_data_aggregator import MLBDataAggregator
from app.services.mlb_analyzer import MLBCompleteAnalyzer
from app.services.intelligent_parlay_builder import IntelligentParlayBuilder
import itertools
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ParlayLeg(BaseModel):
    game_id: str
    bet_type: str  # spread, total, moneyline
    pick: str
    confidence: float

class ParlayRequest(BaseModel):
    legs: List[ParlayLeg]
    bet_amount: float

def calculate_parlay_multiplier(num_legs: int) -> float:
    """Calculate realistic parlay multipliers for -110 odds"""
    multipliers = {
        2: 2.64,   # $100 bet returns $264
        3: 5.96,   # $100 bet returns $596 (corrected from 6.96)
        4: 12.28,  # $100 bet returns $1228 (corrected from 13.28)
        5: 24.36,  # $100 bet returns $2436 (corrected from 25.63)
        6: 47.41   # $100 bet returns $4741 (corrected from 49.64)
    }
    return multipliers.get(num_legs, 2.64 ** (num_legs * 0.91))  # Adjusted formula

@router.get("/recommendations")
async def get_parlay_recommendations(
    sport: str = "all",
):
    """Get optimized parlay recommendations using intelligent builder"""
    
    parlay_builder = IntelligentParlayBuilder()
    all_games = []
    
    # Load NFL games DIRECTLY from data source
    if sport in ["all", "nfl"]:
        try:
            from app.routers.nfl import load_games_data
            from app.services.complete_analyzer import CompleteAnalyzer
            
            # Load raw games and analyze them
            analyzer = CompleteAnalyzer()
            raw_games = load_games_data()
            
            # Process ALL games and sort by confidence
            analyzed_games = []
            for idx, game in enumerate(raw_games):
                analysis = analyzer.analyze_game_complete(game)
                confidence = analysis['final_confidence']
                best_bet = analysis.get('best_bet')
                
                if best_bet and confidence >= 0.55:
                    game_obj = {
                        'id': f'nfl_{idx}',
                        'sport': 'NFL',
                        'home_team': game.get('home_team'),
                        'away_team': game.get('away_team'),
                        'game_time': game.get('game_time'),
                        'spread': game.get('spread', 0),
                        'total': game.get('total', 45),
                        'pick': best_bet['pick'],  # USE THE ACTUAL PICK
                        'confidence': confidence,  # USE THE ACTUAL CONFIDENCE
                        'sharp_action': game.get('sharp_action', False),
                        'reverse_line_movement': game.get('reverse_line_movement', False),
                        'steam_move': game.get('steam_move', False),
                        'contrarian': game.get('contrarian', False)
                    }
                    analyzed_games.append(game_obj)
            
            # Sort by confidence and take only the BEST games
            analyzed_games.sort(key=lambda x: x['confidence'], reverse=True)
            all_games.extend(analyzed_games[:6])  # Take top 6 for parlays
        except Exception as e:
            logger.error(f"Failed to load NFL games: {e}")
    
    # Load NCAAF games DIRECTLY from data source
    if sport in ["all", "ncaaf"]:
        try:
            from app.routers.ncaaf import load_games_data
            from app.services.ncaaf_analyzer import NCAAFAnalyzer
            
            # Load raw games and analyze them
            analyzer = NCAAFAnalyzer()
            raw_games = load_games_data()
            
            # Process ALL games and sort by confidence
            analyzed_games = []
            for idx, game in enumerate(raw_games):
                analysis = analyzer.analyze_game(game)
                
                if analysis.get('pick') and analysis.get('confidence', 0) >= 0.55:
                    game_obj = {
                        'id': f'ncaaf_{idx}',
                        'sport': 'NCAAF',
                        'home_team': game.get('home_team'),
                        'away_team': game.get('away_team'),
                        'game_time': game.get('game_time'),
                        'spread': game.get('spread', 0),
                        'total': game.get('total', 45),
                        'pick': analysis['pick'],
                        'confidence': analysis['confidence'],
                        'sharp_action': game.get('sharp_action', False),
                        'reverse_line_movement': game.get('reverse_line_movement', False),
                        'steam_move': game.get('steam_move', False),
                        'contrarian': game.get('contrarian', False)
                    }
                    analyzed_games.append(game_obj)
            
            # Sort by confidence and take only the BEST games
            analyzed_games.sort(key=lambda x: x['confidence'], reverse=True)
            all_games.extend(analyzed_games[:6])  # Take top 6 for parlays
        except Exception as e:
            logger.error(f"Failed to load NCAAF games: {e}")
    
    # Load MLB games and sort by confidence
    if sport in ["all", "mlb"]:
        try:
            mlb_aggregator = MLBDataAggregator()
            mlb_analyzer = MLBCompleteAnalyzer()
            mlb_games_raw = mlb_aggregator.get_todays_games()
            
            analyzed_games = []
            for idx, game_raw in enumerate(mlb_games_raw):
                # Analyze the game
                analysis = mlb_analyzer.analyze_game(game_raw)
                
                if 'pick' in analysis and analysis['pick'] and analysis.get('confidence', 0) >= 0.52:
                    # Convert to parlay format
                    game = {
                        'home_team': analysis['home_team'],
                        'away_team': analysis['away_team'],
                        'game_time': analysis['game_time'],
                        'spread': analysis.get('spread', 1.5),
                        'total': analysis.get('total', 8.5),
                        'pick': analysis['pick'],
                        'confidence': analysis['confidence'],
                        'sport': 'MLB',
                        'id': f'mlb_{idx}',
                        'sharp_action': analysis['confidence'] >= 0.52,
                        'venue': analysis.get('venue', ''),
                        'weather': analysis.get('weather')
                    }
                    analyzed_games.append(game)
            
            # Sort by confidence and take only the BEST games
            analyzed_games.sort(key=lambda x: x['confidence'], reverse=True)
            all_games.extend(analyzed_games[:6])  # Take top 6 for parlays
        except Exception as e:
            logger.error(f"Failed to load MLB games: {e}")
    
    # Build intelligent parlays
    parlay_results = parlay_builder.build_parlays(all_games)
    
    # Format for frontend compatibility
    formatted_parlays = []
    for parlay in parlay_results.get('parlays', []):
        formatted = {
            "id": parlay['id'],
            "type": parlay['type'],
            "legs": parlay.get('legs', len(parlay.get('games', []))),
            "games": parlay.get('games', []),
            "confidence": parlay.get('confidence', 0),  # Keep as percentage
            "combined_confidence": parlay.get('combined_confidence', 0),
            "multiplier": parlay['multiplier'],
            "potential_payout": parlay['potential_payout'],
            "expected_value": parlay['expected_value'],
            "recommendation": parlay.get('recommendation', '')
        }
        formatted_parlays.append(formatted)
    
    return {
        "sport": sport,
        "parlays": formatted_parlays,
        "best_parlay": parlay_results.get('best_parlay'),
        "analysis": parlay_results.get('analysis'),
        "suggested_bet": 20,  # 2% of $1000 bankroll
        "bankroll": 1000  # Default bankroll
    }

@router.post("/calculate")
async def calculate_parlay(
    parlay: ParlayRequest,
):
    """Calculate parlay odds and expected value"""
    
    num_legs = len(parlay.legs)
    
    if num_legs < 2:
        return {
            "error": "Parlay must have at least 2 legs"
        }
    
    if num_legs > 4:
        return {
            "error": "Parlays with more than 4 legs are not recommended",
            "reason": "Win probability becomes extremely low"
        }
    
    # Calculate combined probability
    combined_prob = 1.0
    for leg in parlay.legs:
        combined_prob *= leg.confidence
    
    # Get multiplier
    multiplier = calculate_parlay_multiplier(num_legs)
    
    # Calculate expected value
    potential_payout = parlay.bet_amount * multiplier
    expected_value = (combined_prob * potential_payout) - parlay.bet_amount
    
    # Break-even probability
    breakeven_prob = 1 / multiplier
    
    # Determine recommendation
    if expected_value > parlay.bet_amount * 0.1:
        recommendation = "STRONG BET - Significant positive EV"
    elif expected_value > 0:
        recommendation = "GOOD BET - Positive expected value"
    elif expected_value > -parlay.bet_amount * 0.05:
        recommendation = "NEUTRAL - Near breakeven"
    elif expected_value > -parlay.bet_amount * 0.15:
        recommendation = "RISKY - Slightly negative EV"
    else:
        recommendation = "AVOID - Strong negative EV"
    
    # Add advice based on number of legs
    if num_legs > 3:
        recommendation += " | Consider reducing to 2-3 legs for better odds"
    
    return {
        "num_legs": num_legs,
        "probability": round(combined_prob * 100, 2),
        "payout": round(potential_payout, 2),
        "profit": round(potential_payout - parlay.bet_amount, 2),
        "expected_value": round(expected_value, 2),
        "recommendation": recommendation,
        "break_even_prob": round(breakeven_prob * 100, 2),
        "your_prob": round(combined_prob * 100, 2),
        "edge": round((combined_prob - breakeven_prob) * 100, 2),
        "optimal_bet": min(parlay.bet_amount, round(max(0, expected_value * 2), 2))
    }