#!/usr/bin/env python3
"""
Improved score updater that matches games by date AND teams
"""

import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.bet_tracking import TrackedBet

logger = logging.getLogger(__name__)


class ScoreUpdater:
    """
    Update game scores from Odds API with proper date matching
    """
    
    def __init__(self, api_key: str, db: Session):
        self.api_key = api_key
        self.db = db
        self.base_url = "https://api.the-odds-api.com/v4"
    
    async def update_scores(self, sport: str = "americanfootball_nfl") -> Dict:
        """
        Fetch and update scores with proper date matching
        """
        url = f"{self.base_url}/sports/{sport}/scores"
        params = {
            'apiKey': self.api_key,
            'daysFrom': 3  # Get scores from last 3 days
        }
        
        games_checked = 0
        bets_updated = 0
        errors = []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return {
                        "message": f"Failed to fetch scores: {response.status}",
                        "error": True
                    }
                
                scores_data = await response.json()
                games_checked = len(scores_data)
                
                # Process each completed game
                for game in scores_data:
                    if not game.get('completed'):
                        continue
                    
                    try:
                        result = await self._update_single_game(game)
                        if result:
                            bets_updated += 1
                    except Exception as e:
                        errors.append(f"{game.get('away_team')} @ {game.get('home_team')}: {str(e)}")
        
        return {
            "message": "Score update completed",
            "games_checked": games_checked,
            "bets_updated": bets_updated,
            "errors": errors if errors else None
        }
    
    async def _update_single_game(self, game_data: Dict) -> bool:
        """
        Update a single game's score with date matching
        """
        home_team = game_data['home_team']
        away_team = game_data['away_team']
        game_time = datetime.fromisoformat(game_data['commence_time'].replace('Z', '+00:00'))
        
        # Extract scores
        home_score = None
        away_score = None
        
        for score_data in game_data.get('scores', []):
            if score_data['name'] == home_team:
                home_score = int(score_data['score']) if score_data['score'] is not None else None
            elif score_data['name'] == away_team:
                away_score = int(score_data['score']) if score_data['score'] is not None else None
        
        if home_score is None or away_score is None:
            return False
        
        # Find matching tracked bet by teams AND date (within 24 hours)
        time_window_start = game_time - timedelta(hours=12)
        time_window_end = game_time + timedelta(hours=12)
        
        bet = self.db.query(TrackedBet).filter(
            TrackedBet.home_team == home_team,
            TrackedBet.away_team == away_team,
            TrackedBet.game_time >= time_window_start,
            TrackedBet.game_time <= time_window_end,
            TrackedBet.result == 'PENDING'
        ).first()
        
        if not bet:
            # Try with game_id
            bet = self.db.query(TrackedBet).filter(
                TrackedBet.game_id == game_data.get('id'),
                TrackedBet.result == 'PENDING'
            ).first()
        
        if not bet:
            return False
        
        # Update the bet
        bet.home_score = home_score
        bet.away_score = away_score
        bet.actual_spread = home_score - away_score
        
        # Determine result based on pick
        bet.result = self._calculate_result(bet, home_score, away_score)
        
        self.db.commit()
        
        logger.info(f"Updated {away_team} @ {home_team} ({game_time.date()}): {away_score}-{home_score}")
        return True
    
    def _calculate_result(self, bet: TrackedBet, home_score: int, away_score: int) -> str:
        """
        Calculate if the bet won, lost, or pushed
        """
        if not bet.pick:
            return 'PENDING'
        
        actual_spread = home_score - away_score
        
        # Handle moneyline bets
        if ' ML' in bet.pick or 'ML' in bet.pick:
            pick_team = bet.pick.replace(' ML', '').replace('ML', '').strip()
            if pick_team == bet.home_team:
                return 'WIN' if home_score > away_score else 'LOSS'
            elif pick_team == bet.away_team:
                return 'WIN' if away_score > home_score else 'LOSS'
        
        # Handle spread bets
        if ' +' in bet.pick or ' -' in bet.pick:
            parts = bet.pick.rsplit(' ', 1)
            if len(parts) == 2:
                pick_team = parts[0]
                try:
                    pick_spread = float(parts[1])
                except:
                    pick_spread = bet.spread
            else:
                pick_team = bet.pick.split()[0]
                pick_spread = bet.spread
            
            # Calculate if covered
            if pick_team == bet.home_team or bet.home_team.startswith(pick_team):
                covered = actual_spread + pick_spread > 0
            elif pick_team == bet.away_team or bet.away_team.startswith(pick_team):
                covered = -actual_spread + pick_spread > 0
            else:
                # Try partial match
                if any(word in bet.home_team for word in pick_team.split()):
                    covered = actual_spread + pick_spread > 0
                elif any(word in bet.away_team for word in pick_team.split()):
                    covered = -actual_spread + pick_spread > 0
                else:
                    return 'PENDING'
            
            # Check for push
            if abs(actual_spread + pick_spread) < 0.01:
                return 'PUSH'
            
            return 'WIN' if covered else 'LOSS'
        
        return 'PENDING'