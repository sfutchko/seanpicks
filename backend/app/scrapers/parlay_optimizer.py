"""
SEAN PICKS - Parlay Optimizer
Finds the best correlated parlays with highest expected value
"""

import itertools
from datetime import datetime
import json
import os

class ParlayOptimizer:
    """Find optimal parlay combinations"""
    
    def __init__(self):
        # Correlation patterns between bets
        self.correlations = {
            'same_game': {
                'favorite_covers_and_over': 0.58,  # Favorites covering often means high scoring
                'favorite_covers_and_under': 0.42,  # Less correlated
                'dog_covers_and_under': 0.56,      # Dogs covering often means lower scoring
                'dog_covers_and_over': 0.44,       # Less correlated
                'first_half_winner_wins_game': 0.75,  # Strong correlation
                'high_total_both_teams_score': 0.62,  # In high totals, both teams usually score
            },
            'cross_game': {
                'both_favorites': 0.51,  # Slight positive correlation
                'both_dogs': 0.49,       # Slight negative correlation
                'both_overs': 0.52,      # Weather/scoring environment correlation
                'both_unders': 0.52,     # Weather/scoring environment correlation
                'division_rivals': 0.48,  # More unpredictable
            }
        }
        
        # Parlay payout multipliers (decimal odds)
        self.payout_multipliers = {
            2: 2.6,   # 2-team parlay
            3: 6.0,   # 3-team parlay
            4: 12.0,  # 4-team parlay
            5: 25.0,  # 5-team parlay
            6: 50.0   # 6-team parlay
        }
        
        # Safe parlay strategies
        self.safe_strategies = {
            'money_line_favorites': {
                'description': 'Parlay 2-3 heavy ML favorites',
                'min_confidence': 0.65,
                'max_legs': 3,
                'expected_hit_rate': 0.42
            },
            'teasers': {
                'description': '6-point teaser crossing key numbers',
                'min_confidence': 0.58,
                'max_legs': 2,
                'expected_hit_rate': 0.55
            },
            'correlated_same_game': {
                'description': 'Same game parlay with correlated outcomes',
                'min_confidence': 0.55,
                'max_legs': 3,
                'expected_hit_rate': 0.35
            }
        }
        
        # Aggressive parlay strategies
        self.aggressive_strategies = {
            'dog_parlay': {
                'description': 'Multiple underdog money lines',
                'min_confidence': 0.52,
                'max_legs': 4,
                'expected_hit_rate': 0.15,
                'payout_target': 10.0
            },
            'prop_ladder': {
                'description': 'Player props in same game',
                'min_confidence': 0.54,
                'max_legs': 5,
                'expected_hit_rate': 0.20
            }
        }
    
    def calculate_parlay_probability(self, legs, correlation_factor=1.0):
        """Calculate probability of parlay hitting"""
        base_prob = 1.0
        
        for leg in legs:
            base_prob *= leg['confidence']
        
        # Adjust for correlation
        adjusted_prob = base_prob * correlation_factor
        
        return min(adjusted_prob, 0.99)  # Cap at 99%
    
    def calculate_expected_value(self, legs, bet_amount=100):
        """Calculate expected value of parlay"""
        # Get parlay probability
        prob = self.calculate_parlay_probability(legs)
        
        # Calculate realistic payout multiplier
        # For spreads, most are -110 but can vary
        # More conservative/realistic calculation
        num_legs = len(legs)
        
        # Use ACTUAL DraftKings/FanDuel multipliers (total return including stake)
        # These are what you'll really get
        realistic_multipliers = {
            2: 2.64,   # $100 bet returns $264 (wins $164)
            3: 6.96,   # $100 bet returns $696 (wins $596) - matches your DK experience!
            4: 13.28,  # $100 bet returns $1328
            5: 26.45,  # $100 bet returns $2645
        }
        
        if num_legs in realistic_multipliers:
            multiplier = realistic_multipliers[num_legs]
        else:
            # Each -110 bet has decimal odds of 1.909
            multiplier = 1.909 ** num_legs
        
        # Calculate actual payout
        win_amount = bet_amount * multiplier
        expected_value = (prob * win_amount) - ((1 - prob) * bet_amount)
        
        return {
            'probability': prob,
            'payout': win_amount,
            'expected_value': expected_value,
            'roi': (expected_value / bet_amount) * 100
        }
    
    def find_correlated_bets(self, games):
        """Find bets that are correlated"""
        correlated_parlays = []
        
        for game in games:
            # Same game correlations
            if game.get('confidence', 0) >= 0.55:
                
                # Favorite covers + Over
                if game.get('best_bet', '').endswith('(favorite)') and game.get('total_lean') == 'over':
                    correlated_parlays.append({
                        'type': 'same_game',
                        'game': game['game'],
                        'legs': [
                            {
                                'bet': game['best_bet'],
                                'confidence': game['confidence']
                            },
                            {
                                'bet': f"OVER {game.get('total', 45)}",
                                'confidence': game.get('total_confidence', 0.52)
                            }
                        ],
                        'correlation': self.correlations['same_game']['favorite_covers_and_over'],
                        'description': 'Favorite covers + game goes over'
                    })
                
                # Dog covers + Under
                if '(underdog)' in game.get('best_bet', '') and game.get('total_lean') == 'under':
                    correlated_parlays.append({
                        'type': 'same_game',
                        'game': game['game'],
                        'legs': [
                            {
                                'bet': game['best_bet'],
                                'confidence': game['confidence']
                            },
                            {
                                'bet': f"UNDER {game.get('total', 45)}",
                                'confidence': game.get('total_confidence', 0.52)
                            }
                        ],
                        'correlation': self.correlations['same_game']['dog_covers_and_under'],
                        'description': 'Dog covers + game stays under'
                    })
        
        # Cross-game correlations (both favorites, both overs, etc.)
        if len(games) >= 2:
            for combo in itertools.combinations(games, 2):
                game1, game2 = combo
                
                # Both favorites
                if ('(favorite)' in game1.get('best_bet', '') and 
                    '(favorite)' in game2.get('best_bet', '') and
                    game1.get('confidence', 0) >= 0.58 and 
                    game2.get('confidence', 0) >= 0.58):
                    
                    correlated_parlays.append({
                        'type': 'cross_game',
                        'games': [game1['game'], game2['game']],
                        'legs': [
                            {
                                'bet': game1['best_bet'],
                                'confidence': game1['confidence']
                            },
                            {
                                'bet': game2['best_bet'],
                                'confidence': game2['confidence']
                            }
                        ],
                        'correlation': self.correlations['cross_game']['both_favorites'],
                        'description': 'Both favorites cover'
                    })
        
        return correlated_parlays
    
    def find_best_teasers(self, games):
        """Find best teaser opportunities"""
        teasers = []
        
        # 6-point teasers for games crossing key numbers
        key_numbers = [3, 7, 10]
        
        for game in games:
            spread = abs(game.get('spread', 0))
            
            # Check if 6-point teaser crosses key numbers
            for key in key_numbers:
                if spread >= key - 6 and spread <= key + 6:
                    # Determine if favorite or underdog
                    is_favorite = '(favorite)' in game.get('best_bet', '')
                    is_underdog = '(underdog)' in game.get('best_bet', '')
                    
                    # For teasers:
                    # - Favorites get points added (e.g., -7 becomes -1)
                    # - Underdogs get more points (e.g., +3 becomes +9)
                    if is_favorite:
                        teased_spread = game.get('spread', 0) + 6  # Make favorite spread better
                    elif is_underdog:
                        teased_spread = abs(game.get('spread', 0)) + 6  # Give underdog more points
                    else:
                        teased_spread = spread + 6  # Default
                    
                    # Extract team name from bet more intelligently
                    best_bet = game.get('best_bet', '')
                    if best_bet:
                        # Split by space and find where the number starts
                        parts = best_bet.split()
                        team_parts = []
                        for part in parts:
                            # Stop when we hit a number (spread)
                            if part.startswith('+') or part.startswith('-') or part[0].isdigit():
                                break
                            team_parts.append(part)
                        team_name = ' '.join(team_parts)
                    else:
                        team_name = game['game'].split(' @ ')[0]
                    
                    if not team_name:  # Fallback
                        team_name = game['game'].split(' @ ')[0]
                    
                    teasers.append({
                        'game': game['game'],
                        'team': team_name,
                        'original_spread': game.get('spread', spread),
                        'teased_spread': teased_spread,
                        'crosses_key': key,
                        'is_favorite': is_favorite,
                        'confidence': min(game.get('confidence', 0.5) + 0.05, 0.65)  # Teasers add confidence
                    })
        
        # Find best 2-team teaser combinations
        best_teasers = []
        if len(teasers) >= 2:
            # Group teasers by game to avoid duplicates
            games_dict = {}
            for teaser in teasers:
                game = teaser['game']
                # Keep only the best teaser for each game (one that crosses most important key number)
                if game not in games_dict or teaser['crosses_key'] == 3:  # Prioritize crossing 3
                    games_dict[game] = teaser
            
            # Now create combinations from unique games
            unique_teasers = list(games_dict.values())
            
            if len(unique_teasers) >= 2:
                for combo in itertools.combinations(unique_teasers, 2):
                    teaser1, teaser2 = combo
                    
                    legs = [
                        {
                            'bet': f"{teaser1['team']} {teaser1['teased_spread']:+.1f}",
                            'confidence': teaser1['confidence']
                        },
                        {
                            'bet': f"{teaser2['team']} {teaser2['teased_spread']:+.1f}",
                            'confidence': teaser2['confidence']
                        }
                    ]
                    
                    best_teasers.append({
                        'type': 'teaser',
                        'games': [teaser1['game'], teaser2['game']],
                        'legs': legs,
                        'description': f"6-point teaser crossing {teaser1['crosses_key']} and {teaser2['crosses_key']}",
                        'expected_value': self.calculate_expected_value(legs)
                    })
        
        return best_teasers
    
    def optimize_parlays(self, games, max_parlays=5, bankroll=1000):
        """Find optimal parlay combinations"""
        all_parlays = []
        
        # Find correlated parlays
        correlated = self.find_correlated_bets(games)
        for parlay in correlated:
            ev = self.calculate_expected_value(parlay['legs'])
            parlay['expected_value'] = ev
            all_parlays.append(parlay)
        
        # Find teasers
        teasers = self.find_best_teasers(games)
        all_parlays.extend(teasers)
        
        # Find high confidence straight parlays
        high_conf_games = [g for g in games if g.get('confidence', 0) >= 0.58]
        
        if len(high_conf_games) >= 2:
            # 2-team parlays
            for combo in itertools.combinations(high_conf_games[:6], 2):
                legs = [
                    {'bet': combo[0]['best_bet'], 'confidence': combo[0]['confidence']},
                    {'bet': combo[1]['best_bet'], 'confidence': combo[1]['confidence']}
                ]
                ev = self.calculate_expected_value(legs)
                
                if ev['roi'] > 10:  # Only positive EV parlays
                    all_parlays.append({
                        'type': 'straight',
                        'games': [combo[0]['game'], combo[1]['game']],
                        'legs': legs,
                        'description': '2-team high confidence parlay',
                        'expected_value': ev
                    })
            
            # 3-team parlays for higher payout
            if len(high_conf_games) >= 3:
                for combo in itertools.combinations(high_conf_games[:4], 3):
                    legs = [
                        {'bet': combo[0]['best_bet'], 'confidence': combo[0]['confidence']},
                        {'bet': combo[1]['best_bet'], 'confidence': combo[1]['confidence']},
                        {'bet': combo[2]['best_bet'], 'confidence': combo[2]['confidence']}
                    ]
                    ev = self.calculate_expected_value(legs)
                    
                    if ev['roi'] > 20:  # Higher threshold for 3-teamers
                        all_parlays.append({
                            'type': 'straight',
                            'games': [combo[0]['game'], combo[1]['game'], combo[2]['game']],
                            'legs': legs,
                            'description': '3-team parlay (higher risk/reward)',
                            'expected_value': ev
                        })
        
        # Sort by expected value
        all_parlays.sort(key=lambda x: x['expected_value']['roi'], reverse=True)
        
        # Get top parlays
        top_parlays = all_parlays[:max_parlays]
        
        # Calculate bet sizing using Kelly Criterion
        for parlay in top_parlays:
            prob = parlay['expected_value']['probability']
            odds = parlay['expected_value']['payout'] / 100  # Convert to decimal odds
            
            # Kelly formula: f = (p * b - q) / b
            # where p = probability of winning, q = probability of losing, b = odds - 1
            b = odds - 1
            q = 1 - prob
            kelly_fraction = max(0, (prob * b - q) / b)
            
            # Use fractional Kelly (25% of full Kelly) for parlays
            safe_kelly = kelly_fraction * 0.25
            
            # Cap at 2% of bankroll for any single parlay
            bet_percentage = min(safe_kelly, 0.02)
            bet_amount = int(bankroll * bet_percentage)
            
            parlay['recommended_bet'] = max(10, bet_amount)  # Minimum $10 bet
            parlay['kelly_percentage'] = bet_percentage
            
            # Recalculate payout for actual bet amount
            actual_payout = parlay['expected_value']['payout'] * (parlay['recommended_bet'] / 100)
            parlay['expected_value']['actual_payout'] = actual_payout
        
        return top_parlays
    
    def format_for_dashboard(self, games, bankroll=1000):
        """Format parlay recommendations for dashboard"""
        parlays = self.optimize_parlays(games, max_parlays=5, bankroll=bankroll)
        
        formatted = []
        for i, parlay in enumerate(parlays, 1):
            ev = parlay['expected_value']
            
            # Format legs with clearer descriptions
            legs_text = []
            for leg in parlay['legs']:
                # Clean up the bet text for display
                bet_text = leg['bet']
                # If it's a spread bet, make it clearer
                if '+' in bet_text or '-' in bet_text:
                    parts = bet_text.rsplit(' ', 1)  # Split on last space
                    if len(parts) == 2:
                        team_game = parts[0]
                        spread = parts[1]
                        bet_text = f"{team_game} {spread}"
                
                legs_text.append(f"• {bet_text} ({leg['confidence']:.1%})")
            
            # Calculate actual payout for recommended bet
            actual_payout = ev['payout'] * (parlay['recommended_bet'] / 100)
            
            formatted.append({
                'rank': i,
                'type': parlay['type'].upper(),
                'description': parlay['description'],
                'legs': legs_text,
                'legs_count': len(parlay['legs']),
                'probability': f"{ev['probability']:.1%}",
                'payout': f"${actual_payout:.0f}",
                'roi': f"{ev['roi']:.1f}%",
                'bet_amount': f"${parlay['recommended_bet']}",
                'confidence_level': 'HIGH' if ev['probability'] > 0.30 else 'MEDIUM' if ev['probability'] > 0.20 else 'LOW',
                'games': parlay.get('games', [parlay.get('game')])
            })
        
        # Get best parlay
        best = None
        if formatted:
            best = formatted[0]
            best['action'] = 'BEST PARLAY'
        
        return {
            'parlays': formatted,
            'best_parlay': best,
            'total_recommended': len(formatted)
        }


class ParlayRules:
    """Rules and guidelines for parlay betting"""
    
    @staticmethod
    def get_rules():
        return {
            'max_percentage': 0.05,  # Never bet more than 5% of bankroll on parlays
            'correlation_required': True,  # Prefer correlated outcomes
            'avoid': [
                'More than 4 legs (hit rate drops dramatically)',
                'Negative correlation bets in same parlay',
                'All favorites or all dogs (no balance)',
                'Props from different games (no correlation)'
            ],
            'prefer': [
                '2-3 leg parlays with 60%+ confidence',
                'Same game parlays with correlation',
                'Teasers crossing key numbers (3, 7)',
                'Mix of favorites and totals'
            ],
            'bankroll_management': {
                'daily_limit': 0.02,  # 2% of bankroll daily on parlays
                'per_parlay': 0.01,   # 1% max per parlay
                'stop_loss': -0.05    # Stop if down 5% on parlays
            }
        }


if __name__ == "__main__":
    # Example games data
    sample_games = [
        {
            'game': 'Bills @ Chiefs',
            'best_bet': 'Chiefs -3.5 (favorite)',
            'confidence': 0.62,
            'spread': -3.5,
            'total': 48.5,
            'total_confidence': 0.55,
            'total_lean': 'over'
        },
        {
            'game': 'Cowboys @ Eagles',
            'best_bet': 'Eagles -7 (favorite)',
            'confidence': 0.58,
            'spread': -7,
            'total': 45.5,
            'total_confidence': 0.53,
            'total_lean': 'under'
        },
        {
            'game': 'Dolphins @ Patriots',
            'best_bet': 'Patriots +3.5 (underdog)',
            'confidence': 0.56,
            'spread': 3.5,
            'total': 42,
            'total_confidence': 0.54,
            'total_lean': 'under'
        }
    ]
    
    optimizer = ParlayOptimizer()
    
    print("=" * 60)
    print(" PARLAY OPTIMIZER")
    print("=" * 60)
    
    results = optimizer.format_for_dashboard(sample_games, bankroll=1000)
    
    if results['parlays']:
        print(f"\nFound {results['total_recommended']} recommended parlays:\n")
        
        for parlay in results['parlays']:
            print(f"{parlay['rank']}. {parlay['type']} - {parlay['description']}")
            print(f"   Legs ({parlay['legs_count']}):")
            for leg in parlay['legs']:
                print(f"   {leg}")
            print(f"   Probability: {parlay['probability']}")
            print(f"   Payout: {parlay['payout']} on {parlay['bet_amount']}")
            print(f"   ROI: {parlay['roi']}")
            print(f"   Confidence: {parlay['confidence_level']}")
            print()
    
    # Print rules
    rules = ParlayRules.get_rules()
    print("\nPARLAY BETTING RULES:")
    print("-" * 40)
    print("Avoid:")
    for rule in rules['avoid']:
        print(f"  ❌ {rule}")
    print("\nPrefer:")
    for rule in rules['prefer']:
        print(f"  ✅ {rule}")