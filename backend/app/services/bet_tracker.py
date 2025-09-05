#!/usr/bin/env python3
"""
Service for tracking best bets and their performance
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import hashlib
import logging

from app.models.bet_tracking import TrackedBet, BetSnapshot, BetPerformance
from app.database.connection import get_db

logger = logging.getLogger(__name__)


class BetTracker:
    """
    Track best bets and their performance over time
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_best_bet(self, game: Dict, analysis: Dict, sport: str = None) -> TrackedBet:
        """
        Add or update a best bet in the tracking system
        """
        # Create unique ID for this bet
        bet_id = f"{game['id']}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Check if bet already exists
        existing = self.db.query(TrackedBet).filter_by(game_id=game['id']).first()
        
        if existing:
            # Update existing bet
            existing.last_seen = datetime.utcnow()
            existing.times_appeared += 1
            existing.confidence = analysis['confidence']
            existing.kelly_bet = analysis.get('kelly_bet')
            existing.edge = analysis.get('edge')
            bet = existing
        else:
            # Create new tracked bet
            # Handle different datetime formats
            game_time_str = game['game_time']
            if game_time_str.endswith('Z'):
                game_time_str = game_time_str[:-1] + '+00:00'
            
            # Determine sport from game data or use provided sport
            if sport is None:
                # Try to detect sport from game ID or team names
                if 'mlb' in game.get('id', '').lower() or 'baseball' in game.get('id', '').lower():
                    sport = 'MLB'
                elif 'ncaaf' in game.get('id', '').lower() or 'college' in game.get('id', '').lower():
                    sport = 'NCAAF'
                else:
                    sport = 'NFL'  # Default to NFL
            
            bet = TrackedBet(
                id=bet_id,
                game_id=game['id'],
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_time=datetime.fromisoformat(game_time_str),
                pick=analysis['pick'],
                spread=analysis['spread'],
                confidence=analysis['confidence'],
                kelly_bet=analysis.get('kelly_bet'),
                edge=analysis.get('edge'),
                best_book=analysis.get('best_book'),
                best_spread=analysis.get('best_spread'),
                best_odds=analysis.get('best_odds', -110),
                patterns=analysis.get('patterns', []),
                public_percentage=analysis.get('public_percentage'),
                sharp_action=analysis.get('sharp_action'),
                weather=game.get('weather'),
                result='PENDING'
            )
            self.db.add(bet)
        
        self.db.commit()
        return bet
    
    def create_snapshot(self, best_bets: List[Dict], sport: str = "NFL") -> BetSnapshot:
        """
        Create a snapshot of current best bets
        """
        # Calculate snapshot metrics
        total_bets = len(best_bets)
        avg_confidence = sum(b['confidence'] for b in best_bets) / total_bets if total_bets > 0 else 0
        
        # Count pending/completed
        pending = sum(1 for b in best_bets if b.get('result') == 'PENDING')
        wins = sum(1 for b in best_bets if b.get('result') == 'WIN')
        losses = sum(1 for b in best_bets if b.get('result') == 'LOSS')
        pushes = sum(1 for b in best_bets if b.get('result') == 'PUSH')
        
        snapshot = BetSnapshot(
            snapshot_time=datetime.utcnow(),
            sport=sport,
            best_bets=best_bets,
            total_bets=total_bets,
            avg_confidence=avg_confidence,
            pending_count=pending,
            win_count=wins,
            loss_count=losses,
            push_count=pushes
        )
        
        self.db.add(snapshot)
        self.db.commit()
        return snapshot
    
    def update_game_result(self, game_id: str, home_score: int, away_score: int) -> Optional[TrackedBet]:
        """
        Update a tracked bet with the game result
        """
        bet = self.db.query(TrackedBet).filter_by(game_id=game_id).first()
        
        if not bet:
            return None
        
        bet.home_score = home_score
        bet.away_score = away_score
        
        # Calculate actual spread (home perspective)
        actual_spread = home_score - away_score
        bet.actual_spread = actual_spread
        
        # Determine if bet won or lost
        if bet.pick:
            pick_team = bet.pick.split()[0]  # Extract team name
            pick_spread = bet.spread
            
            # Determine if pick was home or away
            if pick_team in bet.home_team:
                # Picked home team
                covered = actual_spread > -pick_spread
            else:
                # Picked away team  
                covered = actual_spread < pick_spread
            
            # Check for push
            if abs(actual_spread + pick_spread) < 0.1:
                bet.result = 'PUSH'
            elif covered:
                bet.result = 'WIN'
            else:
                bet.result = 'LOSS'
        
        self.db.commit()
        return bet
    
    def update_game_result_by_teams(self, home_team: str, away_team: str, home_score: int, away_score: int) -> Optional[TrackedBet]:
        """
        Update a tracked bet with the game result using team names for matching
        """
        # Try to find the bet by matching team names and pending status
        from datetime import datetime, timedelta
        
        # Look for games within the last 3 days that match these teams
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        bet = self.db.query(TrackedBet).filter(
            TrackedBet.home_team == home_team,
            TrackedBet.away_team == away_team,
            TrackedBet.result == 'PENDING',
            TrackedBet.game_time >= three_days_ago
        ).first()
        
        if not bet:
            return None
        
        bet.home_score = home_score
        bet.away_score = away_score
        
        # Calculate actual spread (home perspective)
        actual_spread = home_score - away_score
        bet.actual_spread = actual_spread
        
        # Determine if bet won or lost
        if bet.pick:
            # Handle different pick formats
            if ' ML' in bet.pick:
                # Moneyline bet
                pick_team = bet.pick.replace(' ML', '')
                if pick_team == home_team:
                    bet.result = 'WIN' if home_score > away_score else 'LOSS'
                elif pick_team == away_team:
                    bet.result = 'WIN' if away_score > home_score else 'LOSS'
            elif ' +' in bet.pick or ' -' in bet.pick:
                # Spread bet
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
                
                # Determine if bet won
                if pick_team == home_team:
                    covered = actual_spread + pick_spread > 0
                elif pick_team == away_team:
                    covered = -actual_spread + pick_spread > 0
                else:
                    # Try partial match
                    if home_team.startswith(pick_team) or pick_team in home_team:
                        covered = actual_spread + pick_spread > 0
                    elif away_team.startswith(pick_team) or pick_team in away_team:
                        covered = -actual_spread + pick_spread > 0
                    else:
                        covered = False
                
                # Account for pushes
                if abs(actual_spread + pick_spread) < 0.01:
                    bet.result = 'PUSH'
                elif covered:
                    bet.result = 'WIN'
                else:
                    bet.result = 'LOSS'
        
        self.db.commit()
        return bet
    
    def get_performance_stats(self, days: int = 7, sport: str = "NFL") -> Dict:
        """
        Get performance statistics for tracked bets
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query completed bets
        bets = self.db.query(TrackedBet).filter(
            TrackedBet.first_seen >= cutoff_date,
            TrackedBet.result.in_(['WIN', 'LOSS', 'PUSH'])
        ).all()
        
        if not bets:
            return {
                'record': '0-0',
                'win_rate': 0,
                'units': 0,
                'roi': 0,
                'total_bets': 0
            }
        
        wins = sum(1 for b in bets if b.result == 'WIN')
        losses = sum(1 for b in bets if b.result == 'LOSS')
        pushes = sum(1 for b in bets if b.result == 'PUSH')
        
        # Calculate units (assuming flat betting for now)
        units = wins - losses
        total_bets = wins + losses
        roi = (units / total_bets * 100) if total_bets > 0 else 0
        
        # Win rate by confidence level
        high_conf = [b for b in bets if b.confidence >= 0.60]
        med_conf = [b for b in bets if 0.55 <= b.confidence < 0.60]
        low_conf = [b for b in bets if b.confidence < 0.55]
        
        return {
            'record': f'{wins}-{losses}' + (f'-{pushes}' if pushes > 0 else ''),
            'win_rate': (wins / total_bets * 100) if total_bets > 0 else 0,
            'units': round(units, 2),
            'roi': round(roi, 1),
            'total_bets': len(bets),
            'by_confidence': {
                'high': {
                    'record': f"{sum(1 for b in high_conf if b.result == 'WIN')}-{sum(1 for b in high_conf if b.result == 'LOSS')}",
                    'count': len(high_conf)
                },
                'medium': {
                    'record': f"{sum(1 for b in med_conf if b.result == 'WIN')}-{sum(1 for b in med_conf if b.result == 'LOSS')}",
                    'count': len(med_conf)
                },
                'low': {
                    'record': f"{sum(1 for b in low_conf if b.result == 'WIN')}-{sum(1 for b in low_conf if b.result == 'LOSS')}",
                    'count': len(low_conf)
                }
            }
        }
    
    def get_pending_bets(self, sport: str = "NFL") -> List[TrackedBet]:
        """
        Get all pending tracked bets
        """
        return self.db.query(TrackedBet).filter_by(result='PENDING').all()
    
    def get_recent_results(self, limit: int = 20, sport: str = "NFL") -> List[Dict]:
        """
        Get recent bet results for display
        """
        bets = self.db.query(TrackedBet).filter(
            TrackedBet.result.in_(['WIN', 'LOSS', 'PUSH'])
        ).order_by(TrackedBet.game_time.desc()).limit(limit).all()
        
        results = []
        for bet in bets:
            results.append({
                'game': f"{bet.away_team} @ {bet.home_team}",
                'pick': bet.pick,
                'spread': bet.spread,
                'confidence': round(bet.confidence * 100, 1),
                'result': bet.result,
                'score': f"{bet.away_score}-{bet.home_score}",
                'actual_spread': bet.actual_spread,
                'game_time': bet.game_time.isoformat()
            })
        
        return results


class ResultFetcher:
    """
    Fetch game results from API to update tracked bets
    """
    
    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    async def fetch_scores(self, sport: str = "americanfootball_nfl") -> List[Dict]:
        """
        Fetch completed game scores
        """
        import aiohttp
        
        url = f"{self.base_url}/sports/{sport}/scores"
        params = {
            'apiKey': self.api_key,
            'daysFrom': 1  # Get scores from last day
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch scores: {response.status}")
                    return []
    
    def update_tracked_bets(self, scores: List[Dict], tracker: BetTracker):
        """
        Update tracked bets with final scores
        """
        for game in scores:
            if game.get('completed'):
                game_id = game['id']
                
                # Extract scores
                home_score = None
                away_score = None
                
                for score_data in game.get('scores', []):
                    if score_data['name'] == game['home_team']:
                        home_score = score_data['score']
                    elif score_data['name'] == game['away_team']:
                        away_score = score_data['score']
                
                if home_score is not None and away_score is not None:
                    tracker.update_game_result(game_id, home_score, away_score)
                    logger.info(f"Updated result for {game['away_team']} @ {game['home_team']}: {away_score}-{home_score}")