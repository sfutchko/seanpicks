"""
SEAN PICKS - Integrated Live Betting System
Combines live scores with betting patterns for real opportunities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.live_scores_fetcher import LiveScoresFetcher
from scrapers.live_betting_tracker import LiveBettingTracker, LiveAlerts
from datetime import datetime
import json

class IntegratedLiveBetting:
    """Fully integrated live betting system with real data"""
    
    def __init__(self):
        self.scores_fetcher = LiveScoresFetcher()
        self.betting_tracker = LiveBettingTracker()
        self.alerts = LiveAlerts()
        
    def analyze_live_opportunities(self):
        """Get live games and analyze for betting opportunities"""
        
        # Fetch real live scores
        live_games = self.scores_fetcher.get_all_live_games()
        
        if not live_games:
            return {
                'status': 'no_games',
                'message': 'No live games currently',
                'opportunities': []
            }
        
        # Format games for betting tracker
        formatted_games = self.scores_fetcher.format_for_betting_tracker(live_games)
        
        all_opportunities = []
        
        for game in formatted_games:
            # Find betting edges using patterns
            edges = self.betting_tracker.find_live_edges(game)
            
            # Analyze game flow
            flow = self.betting_tracker.analyze_game_flow(game)
            
            # Check for second half opportunities
            if game['halftime']:
                second_half_strats = self.betting_tracker.second_half_strategies({
                    'total_points': game['current_total'],
                    'pregame_total': game['pregame_total'],
                    'home_points': game['home_score'],
                    'away_points': game['away_score'],
                    'home_2h_total': 14,  # Would get from live odds
                    '2h_spread': 3  # Would get from live odds
                })
                
                for strat in second_half_strats:
                    edges.append({
                        'type': 'second_half',
                        'description': strat['reasoning'],
                        'confidence': strat['confidence'],
                        'bet': strat['bet']
                    })
            
            # Check for prop opportunities
            if game['quarter'] >= 3 and game['team_trailing']:
                # Trailing QB will throw more
                edges.append({
                    'type': 'player_prop',
                    'description': f"{game['team_trailing']} QB passing yards OVER",
                    'confidence': 0.55,
                    'bet': f"{game['team_trailing']} QB passing yards OVER"
                })
            
            if game['fourth_quarter'] and game['team_leading']:
                # Leading team will run more
                edges.append({
                    'type': 'player_prop',
                    'description': f"{game['team_leading']} RB rushing yards OVER",
                    'confidence': 0.56,
                    'bet': f"{game['team_leading']} RB rushing yards OVER"
                })
            
            # Package opportunities for this game
            if edges:
                for edge in edges:
                    opportunity = {
                        'game': f"{game['away_team']} @ {game['home_team']}",
                        'league': game['league'],
                        'score': f"{game['away_score']}-{game['home_score']}",
                        'quarter': game['quarter'],
                        'clock': game['clock'],
                        'type': edge['type'],
                        'description': edge['description'],
                        'bet': edge['bet'],
                        'confidence': edge['confidence'],
                        'game_flow': flow,
                        'current_total': game['current_total'],
                        'pregame_total': game['pregame_total'],
                        'pace': flow['pace'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    all_opportunities.append(opportunity)
        
        # Sort by confidence
        all_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Get high priority alerts
        high_priority = []
        for opp in all_opportunities:
            if self.alerts.should_alert(opp):
                alert = self.alerts.format_alert(opp)
                high_priority.append(alert)
        
        return {
            'status': 'success',
            'live_games_count': len(live_games),
            'opportunities_count': len(all_opportunities),
            'opportunities': all_opportunities[:10],  # Top 10 opportunities
            'high_priority_alerts': high_priority[:3]  # Top 3 alerts
        }
    
    def get_formatted_for_dashboard(self):
        """Get live betting data formatted for dashboard display"""
        data = self.analyze_live_opportunities()
        
        if data['status'] == 'no_games':
            return {
                'live_betting': {
                    'active': False,
                    'games_count': 0,
                    'opportunities': [],
                    'best_bet': None
                }
            }
        
        # Format for dashboard
        formatted_opps = []
        for opp in data['opportunities']:
            formatted_opps.append({
                'game': opp['game'],
                'score': opp['score'],
                'quarter': f"Q{opp['quarter']} {opp['clock']}",
                'bet': opp['bet'],
                'confidence': f"{opp['confidence']:.1%}",
                'confidence_value': opp['confidence'],
                'description': opp['description'],
                'pace': opp['pace'].upper()
            })
        
        # Get best bet
        best_bet = None
        if formatted_opps:
            best = formatted_opps[0]
            best_bet = {
                'game': best['game'],
                'bet': best['bet'],
                'confidence': best['confidence'],
                'action': 'BET NOW - Live'
            }
        
        return {
            'live_betting': {
                'active': True,
                'games_count': data['live_games_count'],
                'opportunities': formatted_opps,
                'best_bet': best_bet,
                'alerts': data.get('high_priority_alerts', [])
            }
        }
    
    def save_to_json(self, filename='live_betting_data.json'):
        """Save live betting data to JSON file"""
        data = self.get_formatted_for_dashboard()
        
        output_dir = '/Users/sean/Downloads/sean_picks/data'
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Live betting data saved to {filepath}")
        return filepath


if __name__ == "__main__":
    system = IntegratedLiveBetting()
    
    print("=" * 60)
    print(" INTEGRATED LIVE BETTING SYSTEM")
    print("=" * 60)
    
    # Analyze current opportunities
    results = system.analyze_live_opportunities()
    
    if results['status'] == 'success':
        print(f"\n📊 Found {results['live_games_count']} live games")
        print(f"💰 Identified {results['opportunities_count']} betting opportunities\n")
        
        if results['opportunities']:
            print("TOP LIVE BETTING OPPORTUNITIES:")
            print("-" * 40)
            
            for i, opp in enumerate(results['opportunities'][:5], 1):
                print(f"\n{i}. {opp['game']}")
                print(f"   Score: {opp['score']} | Q{opp['quarter']} {opp['clock']}")
                print(f"   Bet: {opp['bet']}")
                print(f"   Confidence: {opp['confidence']:.1%}")
                print(f"   Reason: {opp['description']}")
                print(f"   Pace: {opp['pace']}")
        
        if results['high_priority_alerts']:
            print("\n" + "=" * 40)
            print("🚨 HIGH PRIORITY ALERTS:")
            print("-" * 40)
            
            for alert in results['high_priority_alerts']:
                print(f"\n{alert['priority']}: {alert['message']}")
                print(f"BET: {alert['bet']}")
                print(f"Confidence: {alert['confidence']}")
    else:
        print(f"\n{results['message']}")
    
    # Save to JSON for dashboard
    filepath = system.save_to_json()
    print(f"\n✅ Data ready for dashboard: {filepath}")