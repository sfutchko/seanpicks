#!/usr/bin/env python3
"""
Professional Betting Edges - Advanced features used by sharp bettors
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ProfessionalEdgeCalculator:
    """
    Advanced betting calculations used by professional bettors
    """
    
    def __init__(self):
        self.clv_history = []  # Track closing line value
        
    def remove_vig(self, odds1: int, odds2: int) -> Tuple[float, float]:
        """
        Remove juice to find true probability (no-vig line)
        This is what sharp bettors use to find true value
        """
        # Convert American odds to implied probability
        def american_to_prob(odds):
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        
        prob1 = american_to_prob(odds1)
        prob2 = american_to_prob(odds2)
        total = prob1 + prob2
        
        # Remove the vig
        true_prob1 = prob1 / total
        true_prob2 = prob2 / total
        
        return true_prob1, true_prob2
    
    def calculate_expected_value(self, win_prob: float, american_odds: int, 
                                bet_amount: float = 100) -> Dict:
        """
        Calculate expected value - THE most important metric
        Positive EV = profitable long term
        """
        # Convert American to decimal
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(american_odds)) + 1
        
        # Calculate EV
        win_amount = bet_amount * (decimal_odds - 1)
        lose_amount = bet_amount
        
        ev = (win_prob * win_amount) - ((1 - win_prob) * lose_amount)
        ev_percentage = (ev / bet_amount) * 100
        
        return {
            'expected_value': round(ev, 2),
            'ev_percentage': round(ev_percentage, 2),
            'break_even_percentage': round(1 / decimal_odds * 100, 2),
            'edge': round((win_prob * 100) - (1 / decimal_odds * 100), 2),
            'is_positive_ev': ev > 0
        }
    
    def kelly_criterion(self, win_prob: float, american_odds: int, 
                       kelly_fraction: float = 0.25) -> float:
        """
        Kelly Criterion for optimal bet sizing
        Most pros use 1/4 Kelly to reduce variance
        """
        # Convert to decimal
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(american_odds)) + 1
        
        b = decimal_odds - 1  # Net odds received on win
        q = 1 - win_prob      # Probability of losing
        
        # Full Kelly formula
        kelly = (b * win_prob - q) / b
        
        # Never bet if negative
        if kelly <= 0:
            return 0
        
        # Use fractional Kelly (safer)
        fractional_kelly = kelly * kelly_fraction
        
        # Cap at 5% of bankroll max
        return min(fractional_kelly, 0.05)
    
    def track_closing_line_value(self, pick_odds: int, closing_odds: int, 
                                 did_bet_win: Optional[bool] = None) -> Dict:
        """
        Track if we beat the closing line - #1 indicator of long-term success
        Sharp bettors MUST beat CLV consistently
        """
        # For favorites (negative odds), lower is better
        # For underdogs (positive odds), higher is better
        beat_closing = False
        
        if pick_odds < 0 and closing_odds < 0:
            # Both favorites
            beat_closing = pick_odds > closing_odds  # Less negative is better
        elif pick_odds > 0 and closing_odds > 0:
            # Both underdogs  
            beat_closing = pick_odds > closing_odds  # More positive is better
        elif pick_odds < 0 and closing_odds > 0:
            # Line flipped - we got favorite, closed underdog
            beat_closing = True  # Great CLV
        elif pick_odds > 0 and closing_odds < 0:
            # Line flipped against us
            beat_closing = False
        
        clv_points = abs(pick_odds - closing_odds)
        
        result = {
            'pick_line': pick_odds,
            'closing_line': closing_odds,
            'beat_closing': beat_closing,
            'clv_points': clv_points,
            'timestamp': datetime.now()
        }
        
        if did_bet_win is not None:
            result['won_bet'] = did_bet_win
            
        self.clv_history.append(result)
        
        # Calculate running CLV percentage
        if len(self.clv_history) > 0:
            clv_wins = sum(1 for h in self.clv_history if h['beat_closing'])
            clv_percentage = (clv_wins / len(self.clv_history)) * 100
            result['career_clv_percentage'] = round(clv_percentage, 2)
            
            # Elite is >55%, Good is >52%, Break-even is 50%
            if clv_percentage >= 55:
                result['clv_grade'] = 'ELITE'
            elif clv_percentage >= 52:
                result['clv_grade'] = 'PROFITABLE'  
            elif clv_percentage >= 50:
                result['clv_grade'] = 'BREAK-EVEN'
            else:
                result['clv_grade'] = 'LOSING'
        
        return result
    
    def identify_arbitrage(self, odds_dict: Dict[str, Dict]) -> List[Dict]:
        """
        Find arbitrage opportunities across books
        Free money but accounts might get limited
        """
        arbs = []
        
        # Example: odds_dict = {
        #   'draftkings': {'team1': -110, 'team2': -110},
        #   'fanduel': {'team1': +100, 'team2': -120}
        # }
        
        books = list(odds_dict.keys())
        if len(books) < 2:
            return arbs
            
        # Check all combinations
        for book1 in books:
            for book2 in books:
                if book1 != book2:
                    # Check if betting both sides profits
                    for team in ['team1', 'team2']:
                        other_team = 'team2' if team == 'team1' else 'team1'
                        
                        if team in odds_dict[book1] and other_team in odds_dict[book2]:
                            odds1 = odds_dict[book1][team]
                            odds2 = odds_dict[book2][other_team]
                            
                            # Calculate if arb exists
                            prob1 = self._american_to_decimal(odds1)
                            prob2 = self._american_to_decimal(odds2)
                            
                            if (1/prob1 + 1/prob2) < 1:
                                profit = (1 - (1/prob1 + 1/prob2)) * 100
                                arbs.append({
                                    'book1': book1,
                                    'book2': book2,
                                    'team1_odds': odds1,
                                    'team2_odds': odds2,
                                    'profit_percentage': round(profit, 2)
                                })
        
        return arbs
    
    def find_middles(self, spreads_by_book: Dict[str, float]) -> List[Dict]:
        """
        Find middle opportunities (can win both bets)
        Example: Team A -2.5 at Book1, Team B +3.5 at Book2
        If game lands on 3, both bets win
        """
        middles = []
        books = list(spreads_by_book.keys())
        
        for book1 in books:
            for book2 in books:
                if book1 != book2:
                    spread1 = spreads_by_book[book1]
                    spread2 = spreads_by_book[book2]
                    
                    # Check for middle
                    if spread1 < 0 and spread2 > 0:  # Different sides
                        middle_size = spread2 - abs(spread1)
                        if middle_size >= 0.5:  # At least half point middle
                            middles.append({
                                'book1': book1,
                                'book2': book2, 
                                'spread1': spread1,
                                'spread2': spread2,
                                'middle_size': middle_size,
                                'win_numbers': f"{abs(spread1)} to {spread2}"
                            })
        
        return middles
    
    def calculate_correlated_parlay_value(self, legs: List[Dict]) -> Dict:
        """
        Identify correlated parlays with hidden value
        Books often misprice these
        """
        correlations = []
        
        # Check for correlations
        for i, leg1 in enumerate(legs):
            for leg2 in legs[i+1:]:
                correlation = self._check_correlation(leg1, leg2)
                if correlation['is_correlated']:
                    correlations.append(correlation)
        
        # Calculate true odds vs offered odds
        if correlations:
            return {
                'has_correlation': True,
                'correlations': correlations,
                'recommendation': 'Positive correlation increases parlay value'
            }
        
        return {'has_correlation': False}
    
    def _check_correlation(self, leg1: Dict, leg2: Dict) -> Dict:
        """
        Check if two bet legs are correlated
        """
        correlation_pairs = [
            # Same game correlations
            ('team_total_over', 'team_moneyline'),  # Team scores more -> likely wins
            ('game_over', 'both_team_overs'),        # High scoring game
            ('player_points_over', 'team_total_over'),  # Star scorer -> team scores
            ('first_half_over', 'game_over'),        # Pace correlation
            
            # Cross-game correlations  
            ('division_rival_wins', 'playoff_implications'),
            ('weather_unders', 'multiple_games'),     # System weather
        ]
        
        # Simple correlation check (would be more complex in production)
        if leg1.get('game_id') == leg2.get('game_id'):
            if 'over' in str(leg1.get('bet_type', '')).lower() and \
               'over' in str(leg2.get('bet_type', '')).lower():
                return {
                    'is_correlated': True,
                    'type': 'same_game_totals',
                    'strength': 'strong'
                }
        
        return {'is_correlated': False}
    
    def _american_to_decimal(self, odds: int) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1
    
    def situational_angles(self, game_data: Dict) -> List[str]:
        """
        Identify profitable situational angles
        These are the patterns sharp bettors exploit
        """
        angles = []
        
        # Revenge game
        if game_data.get('last_meeting_margin') and game_data['last_meeting_margin'] >= 20:
            angles.append("📍 REVENGE SPOT: Lost by 20+ last meeting")
        
        # Sandwich game  
        if game_data.get('next_opponent_rank') and game_data['next_opponent_rank'] <= 5:
            angles.append("📍 LOOK-AHEAD: Elite opponent next week")
            
        # Travel fatigue
        if game_data.get('travel_miles') and game_data['travel_miles'] > 2000:
            if game_data.get('days_rest') <= 3:
                angles.append("📍 TRAVEL FATIGUE: 2000+ miles on short rest")
        
        # Division games late season
        if game_data.get('division_game') and game_data.get('week') >= 14:
            angles.append("📍 DIVISION GAME: Late season implications")
            
        # Primetime letdown
        if game_data.get('last_game_primetime') and not game_data.get('current_primetime'):
            angles.append("📍 LETDOWN: After primetime game")
        
        # Weather angle
        if game_data.get('temperature') and game_data['temperature'] < 32:
            if game_data.get('dome_team_outside'):
                angles.append("📍 WEATHER: Dome team in freezing conditions")
        
        # Coach against former team
        if game_data.get('coach_revenge'):
            angles.append("📍 MOTIVATION: Coach vs former team")
            
        # Undefeated upset angle
        if game_data.get('undefeated') and game_data.get('underdog'):
            angles.append("📍 UPSET ALERT: Undefeated team as underdog")
        
        return angles


def calculate_true_probability(home_ml: int, away_ml: int) -> Dict:
    """
    Quick function to get no-vig probability
    This is what the "true" odds should be
    """
    calc = ProfessionalEdgeCalculator()
    home_prob, away_prob = calc.remove_vig(home_ml, away_ml)
    
    return {
        'home_true_prob': round(home_prob * 100, 2),
        'away_true_prob': round(away_prob * 100, 2),
        'home_no_vig_line': probability_to_american(home_prob),
        'away_no_vig_line': probability_to_american(away_prob)
    }


def probability_to_american(prob: float) -> int:
    """Convert probability to American odds"""
    if prob >= 0.5:
        # Favorite
        return -int(prob / (1 - prob) * 100)
    else:
        # Underdog
        return int((1 - prob) / prob * 100)