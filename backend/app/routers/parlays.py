"""
Parlay optimization router
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.nfl import load_games_data as load_nfl_games
from app.routers.ncaaf import load_games_data as load_ncaaf_games
from app.services.confidence_calculator import ConfidenceCalculator
from app.services.mlb_data_aggregator import MLBDataAggregator
from app.services.mlb_analyzer import MLBCompleteAnalyzer
import itertools

router = APIRouter()

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
        3: 6.96,   # $100 bet returns $696
        4: 13.28,  # $100 bet returns $1328
        5: 25.63,  # $100 bet returns $2563
        6: 49.64   # $100 bet returns $4964
    }
    return multipliers.get(num_legs, 2.64 ** num_legs)

@router.get("/recommendations")
async def get_parlay_recommendations(
    sport: str = "all",
    current_user: User = Depends(get_current_user)
):
    """Get optimized parlay recommendations"""
    
    calculator = ConfidenceCalculator()
    all_games = []
    
    # Load NFL games
    if sport in ["all", "nfl"]:
        nfl_games = load_nfl_games()
        for idx, game in enumerate(nfl_games):
            confidence = calculator.calculate_confidence(
                sharp_action=game.get("sharp_action", False),
                reverse_line_movement=game.get("reverse_line_movement", False),
                steam_move=game.get("steam_move", False),
                public_fade=game.get("contrarian", False),
                key_number_edge=abs(game.get("spread", 0)) in [3, 7, 10]
            )
            game['confidence'] = confidence
            game['sport'] = 'NFL'
            game['id'] = f'nfl_{idx}'
            all_games.append(game)
    
    # Load NCAAF games
    if sport in ["all", "ncaaf"]:
        ncaaf_games = load_ncaaf_games()
        for idx, game in enumerate(ncaaf_games):
            confidence = calculator.calculate_confidence(
                sharp_action=game.get("sharp_action", False),
                reverse_line_movement=game.get("reverse_line_movement", False),
                steam_move=game.get("steam_move", False),
                public_fade=game.get("contrarian", False),
                key_number_edge=abs(game.get("spread", 0)) in [3, 7, 10, 14]
            )
            game['confidence'] = confidence
            game['sport'] = 'NCAAF'
            game['id'] = f'ncaaf_{idx}'
            all_games.append(game)
    
    # Load MLB games
    if sport in ["all", "mlb"]:
        mlb_aggregator = MLBDataAggregator()
        mlb_analyzer = MLBCompleteAnalyzer()
        mlb_games_raw = mlb_aggregator.get_todays_games()
        
        for idx, game_raw in enumerate(mlb_games_raw):
            # Analyze the game
            analysis = mlb_analyzer.analyze_game(game_raw)
            
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
                'venue': analysis.get('venue', '')
            }
            all_games.append(game)
    
    # Filter high confidence games (lowered threshold for more parlays)
    high_conf_games = [g for g in all_games if g['confidence'] >= 0.53]
    high_conf_games.sort(key=lambda x: x['confidence'], reverse=True)
    
    parlays = []
    
    # Generate 2-team parlays
    for combo in itertools.combinations(high_conf_games[:6], 2):
        avg_confidence = sum(g['confidence'] for g in combo) / 2
        
        parlay = {
            "id": f"parlay_2_{len(parlays)}",
            "type": "2-team",
            "games": [
                {
                    "team": combo[0].get('home_team', 'Home'),
                    "spread": combo[0].get('spread', 0),
                    "sport": combo[0]['sport'],
                    "confidence": round(combo[0]['confidence'], 3)
                },
                {
                    "team": combo[1].get('home_team', 'Home'),
                    "spread": combo[1].get('spread', 0),
                    "sport": combo[1]['sport'],
                    "confidence": round(combo[1]['confidence'], 3)
                }
            ],
            "combined_confidence": round(avg_confidence, 3),
            "multiplier": 2.64,
            "potential_payout": round(2.64 * 20, 2),  # $20 bet
            "expected_value": round((avg_confidence ** 2) * 2.64 * 20 - 20, 2)
        }
        parlays.append(parlay)
    
    # Generate 3-team parlays (higher threshold)
    for combo in itertools.combinations(high_conf_games[:5], 3):
        avg_confidence = sum(g['confidence'] for g in combo) / 3
        
        if avg_confidence >= 0.53:
            parlay = {
                "id": f"parlay_3_{len(parlays)}",
                "type": "3-team",
                "games": [
                    {
                        "team": g.get('home_team', 'Home'),
                        "spread": g.get('spread', 0),
                        "sport": g['sport'],
                        "confidence": round(g['confidence'], 3)
                    }
                    for g in combo
                ],
                "combined_confidence": round(avg_confidence, 3),
                "multiplier": 6.96,
                "potential_payout": round(6.96 * 20, 2),  # $20 bet
                "expected_value": round((avg_confidence ** 3) * 6.96 * 20 - 20, 2)
            }
            parlays.append(parlay)
    
    # Sort by expected value
    parlays.sort(key=lambda x: x['expected_value'], reverse=True)
    
    # Get best parlay
    best_parlay = parlays[0] if parlays else None
    
    return {
        "sport": sport,
        "parlays": parlays[:10],
        "best_parlay": best_parlay,
        "suggested_bet": 20,  # 2% of $1000 bankroll
        "bankroll": current_user.bankroll
    }

@router.post("/calculate")
async def calculate_parlay(
    parlay: ParlayRequest,
    current_user: User = Depends(get_current_user)
):
    """Calculate parlay odds and expected value"""
    
    num_legs = len(parlay.legs)
    
    if num_legs < 2:
        return {
            "error": "Parlay must have at least 2 legs"
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
    
    # Determine recommendation
    if expected_value > 0:
        recommendation = "Positive EV - Good bet"
    elif expected_value > -parlay.bet_amount * 0.1:
        recommendation = "Slightly negative EV - Proceed with caution"
    else:
        recommendation = "Negative EV - Not recommended"
    
    return {
        "num_legs": num_legs,
        "probability": round(combined_prob * 100, 2),
        "payout": round(potential_payout, 2),
        "expected_value": round(expected_value, 2),
        "recommendation": recommendation,
        "break_even_prob": round((1 / multiplier) * 100, 2)
    }