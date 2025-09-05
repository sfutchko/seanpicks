"""
Intelligent Parlay Builder
Based on research:
- 2-3 leg parlays are optimal (27.5% breakeven at -110)
- Correlation between games is key for value
- Use only HIGH confidence picks (55%+)
- Never contradict best bets
"""

from typing import List, Dict, Any, Optional, Tuple
import itertools
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IntelligentParlayBuilder:
    """
    Build smart, consistent parlays based on:
    1. High confidence picks only
    2. Proper correlation analysis
    3. Expected value calculations
    4. Never contradicting our best bets
    """
    
    # Parlay odds multipliers for -110 standard odds
    MULTIPLIERS = {
        2: 2.64,   # Two team parlay
        3: 5.96,   # Three team parlay  
        4: 12.28,  # Four team parlay (rarely recommended)
        5: 24.36,  # Five team (not recommended)
    }
    
    # Breakeven win percentages
    BREAKEVEN_RATES = {
        2: 0.275,  # 27.5% for 2-team
        3: 0.168,  # 16.8% for 3-team
        4: 0.082,  # 8.2% for 4-team
    }
    
    def __init__(self):
        self.min_confidence = 0.55  # Only use best bets
        self.max_legs = 3  # Keep parlays small
        self.correlation_boost = 0.05  # Boost for correlated bets
    
    def build_parlays(self, games: List[Dict]) -> Dict:
        """
        Build intelligent parlay recommendations
        
        Args:
            games: List of analyzed games with picks and confidence
            
        Returns:
            Dictionary with parlay recommendations
        """
        # Filter only high confidence games
        best_bets = [g for g in games if g.get('confidence', 0) >= self.min_confidence]
        
        if len(best_bets) < 2:
            return {
                "parlays": [],
                "best_parlay": None,
                "message": "Not enough high confidence games for parlays"
            }
        
        # Sort by confidence
        best_bets.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Generate parlays
        two_team_parlays = self._generate_two_team_parlays(best_bets[:8])  # Top 8 games
        three_team_parlays = self._generate_three_team_parlays(best_bets[:6])  # Top 6 games
        
        # Combine and sort by expected value
        all_parlays = two_team_parlays + three_team_parlays
        all_parlays.sort(key=lambda x: x['expected_value'], reverse=True)
        
        # Get best parlay
        best_parlay = all_parlays[0] if all_parlays else None
        
        return {
            "parlays": all_parlays[:10],  # Top 10 parlays
            "best_parlay": best_parlay,
            "suggested_bet": 20,  # Conservative 2% of $1000 bankroll
            "analysis": self._generate_analysis(best_parlay) if best_parlay else None
        }
    
    def _generate_two_team_parlays(self, games: List[Dict]) -> List[Dict]:
        """Generate 2-team parlays with proper pick display"""
        parlays = []
        
        for combo in itertools.combinations(games, 2):
            # Check for correlation
            correlation = self._check_correlation(combo[0], combo[1])
            
            # Calculate combined probability
            prob1 = combo[0].get('confidence', 0.55)
            prob2 = combo[1].get('confidence', 0.55)
            
            # Add correlation boost if applicable
            if correlation['correlated']:
                prob_boost = self.correlation_boost
                combined_prob = (prob1 + prob_boost) * (prob2 + prob_boost)
            else:
                combined_prob = prob1 * prob2
            
            # Calculate expected value
            multiplier = self.MULTIPLIERS[2]
            bet_amount = 20
            potential_payout = bet_amount * multiplier
            expected_value = (combined_prob * potential_payout) - bet_amount
            
            # Extract actual picks
            pick1 = self._extract_pick(combo[0])
            pick2 = self._extract_pick(combo[1])
            
            parlay = {
                "id": f"parlay_2_{len(parlays)}",
                "type": "2-TEAM",
                "legs": 2,
                "games": [
                    {
                        "team": pick1['team'],
                        "pick_type": pick1['type'],
                        "spread": pick1['spread'],
                        "sport": combo[0].get('sport', 'NFL'),
                        "confidence": round(prob1 * 100, 1),
                        "game": f"{combo[0].get('away_team')} @ {combo[0].get('home_team')}"
                    },
                    {
                        "team": pick2['team'],
                        "pick_type": pick2['type'],
                        "spread": pick2['spread'],
                        "sport": combo[1].get('sport', 'NFL'),
                        "confidence": round(prob2 * 100, 1),
                        "game": f"{combo[1].get('away_team')} @ {combo[1].get('home_team')}"
                    }
                ],
                "confidence": round((prob1 + prob2) / 2 * 100, 1),  # Average confidence for display
                "combined_confidence": round(combined_prob * 100, 1),  # Actual combined probability
                "multiplier": multiplier,
                "potential_payout": round(potential_payout, 2),
                "expected_value": round(expected_value, 2),
                "correlation": correlation,
                "recommendation": self._get_recommendation(expected_value, combined_prob)
            }
            
            parlays.append(parlay)
        
        return parlays
    
    def _generate_three_team_parlays(self, games: List[Dict]) -> List[Dict]:
        """Generate 3-team parlays (more selective)"""
        parlays = []
        
        for combo in itertools.combinations(games, 3):
            # Only create 3-team if all are high confidence
            if all(g.get('confidence', 0) >= 0.57 for g in combo):
                # Calculate combined probability
                probs = [g.get('confidence', 0.55) for g in combo]
                combined_prob = probs[0] * probs[1] * probs[2]
                
                # Check for any correlation pairs
                has_correlation = False
                for pair in itertools.combinations(combo, 2):
                    if self._check_correlation(pair[0], pair[1])['correlated']:
                        has_correlation = True
                        combined_prob *= 1.03  # Small boost for correlation
                        break
                
                # Calculate expected value
                multiplier = self.MULTIPLIERS[3]
                bet_amount = 20
                potential_payout = bet_amount * multiplier
                expected_value = (combined_prob * potential_payout) - bet_amount
                
                # Only include if positive EV or close
                if expected_value > -5:
                    picks = [self._extract_pick(g) for g in combo]
                    
                    parlay = {
                        "id": f"parlay_3_{len(parlays)}",
                        "type": "3-TEAM",
                        "legs": 3,
                        "games": [
                            {
                                "team": pick['team'],
                                "pick_type": pick['type'],
                                "spread": pick['spread'],
                                "sport": game.get('sport', 'NFL'),
                                "confidence": round(game.get('confidence', 0.55) * 100, 1),
                                "game": f"{game.get('away_team')} @ {game.get('home_team')}"
                            }
                            for pick, game in zip(picks, combo)
                        ],
                        "confidence": round(sum(probs) / len(probs) * 100, 1),  # Average confidence for display
                        "combined_confidence": round(combined_prob * 100, 1),  # Actual combined probability
                        "multiplier": multiplier,
                        "potential_payout": round(potential_payout, 2),
                        "expected_value": round(expected_value, 2),
                        "has_correlation": has_correlation,
                        "recommendation": self._get_recommendation(expected_value, combined_prob)
                    }
                    
                    parlays.append(parlay)
        
        return parlays
    
    def _extract_pick(self, game: Dict) -> Dict:
        """Extract the actual pick from game data"""
        pick_str = game.get('pick', '')
        
        # Handle different pick formats
        if ' ML' in pick_str:
            # Moneyline pick
            team = pick_str.replace(' ML', '').strip()
            return {
                'team': team,
                'type': 'ML',
                'spread': 'ML'
            }
        elif 'OVER' in pick_str or 'UNDER' in pick_str:
            # Total pick - extract the actual matchup
            home = game.get('home_team', '')
            away = game.get('away_team', '')
            matchup = f"{away} @ {home}" if home and away else pick_str
            return {
                'team': matchup,
                'type': 'TOTAL',
                'spread': pick_str
            }
        else:
            # Spread pick - extract team and spread
            # Format is usually "Team Name +/-X.X"
            parts = pick_str.rsplit(' ', 1)
            if len(parts) == 2:
                team = parts[0]
                try:
                    spread = float(parts[1])
                    return {
                        'team': team,
                        'type': 'SPREAD',
                        'spread': f"{'+' if spread > 0 else ''}{spread}"
                    }
                except:
                    pass
            
            # Fallback - use the pick as is
            return {
                'team': pick_str,
                'type': 'SPREAD', 
                'spread': game.get('spread', 0)
            }
    
    def _check_correlation(self, game1: Dict, game2: Dict) -> Dict:
        """Check if two games are correlated"""
        correlation = {
            'correlated': False,
            'type': None,
            'description': None
        }
        
        # Same game different bets (not applicable for our data structure)
        
        # Division rivals playing at same time
        if game1.get('sport') == game2.get('sport'):
            # Check if teams are in same division (simplified)
            nfc_east = ['Dallas Cowboys', 'Philadelphia Eagles', 'New York Giants', 'Washington Commanders']
            afc_west = ['Kansas City Chiefs', 'Los Angeles Chargers', 'Denver Broncos', 'Las Vegas Raiders']
            
            teams1 = [game1.get('home_team'), game1.get('away_team')]
            teams2 = [game2.get('home_team'), game2.get('away_team')]
            
            # Check division correlation
            for division in [nfc_east, afc_west]:
                if any(t in division for t in teams1) and any(t in division for t in teams2):
                    correlation['correlated'] = True
                    correlation['type'] = 'division'
                    correlation['description'] = 'Division games tend to correlate'
                    break
        
        # Weather correlation (outdoor games in same region)
        if game1.get('weather') and game2.get('weather'):
            w1 = game1['weather']
            w2 = game2['weather']
            
            # Both games affected by weather
            if (w1.get('wind_speed', 0) > 15 and w2.get('wind_speed', 0) > 15):
                correlation['correlated'] = True
                correlation['type'] = 'weather'
                correlation['description'] = 'Both games have high winds affecting scoring'
            elif (w1.get('temperature', 70) < 32 and w2.get('temperature', 70) < 32):
                correlation['correlated'] = True
                correlation['type'] = 'weather'
                correlation['description'] = 'Both games in cold weather'
        
        # Totals correlation - both unders or both overs
        pick1 = game1.get('pick', '')
        pick2 = game2.get('pick', '')
        if ('UNDER' in pick1 and 'UNDER' in pick2) or ('OVER' in pick1 and 'OVER' in pick2):
            correlation['correlated'] = True
            correlation['type'] = 'totals'
            correlation['description'] = 'Similar game script expected'
        
        return correlation
    
    def _get_recommendation(self, expected_value: float, probability: float) -> str:
        """Get recommendation based on EV and probability"""
        if expected_value > 5:
            return "STRONG BET - Positive EV"
        elif expected_value > 0:
            return "GOOD VALUE - Small edge"
        elif expected_value > -3:
            return "NEUTRAL - Near breakeven"
        else:
            return "AVOID - Negative EV"
    
    def _generate_analysis(self, parlay: Dict) -> str:
        """Generate analysis text for best parlay"""
        if not parlay:
            return "No parlays available"
        
        legs = parlay['legs']
        confidence = parlay['confidence']
        ev = parlay['expected_value']
        
        analysis = f"This {legs}-team parlay combines our top picks with {confidence}% combined win probability. "
        
        if ev > 0:
            analysis += f"With +${ev:.2f} expected value, this offers genuine profit potential. "
        else:
            analysis += f"While slightly negative EV (${ev:.2f}), the high confidence makes this playable. "
        
        if parlay.get('correlation', {}).get('correlated'):
            analysis += f"These picks are correlated ({parlay['correlation']['description']}), increasing win probability. "
        
        analysis += f"Recommended bet: $20 to win ${parlay['potential_payout']:.2f}."
        
        return analysis