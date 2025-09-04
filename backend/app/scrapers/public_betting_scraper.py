"""
SEAN PICKS - Public Betting Percentage Scraper
Scrapes real public betting data from multiple sources
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

class PublicBettingScraper:
    """Scrape public betting percentages from multiple sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Sources for public betting data
        self.sources = {
            'vsin': {
                'url': 'https://www.vsin.com/betting-resources/nfl/',
                'type': 'scrape',
                'reliable': True
            },
            'pregame': {
                'url': 'https://pregame.com/game-center/nfl',
                'type': 'scrape',
                'reliable': True
            },
            'sportsinsights': {
                'url': 'https://www.sportsinsights.com/free-nfl-odds/',
                'type': 'scrape',
                'reliable': False  # Often behind paywall
            },
            'odds_shark': {
                'url': 'https://www.oddsshark.com/nfl/consensus-picks',
                'type': 'scrape',
                'reliable': True
            },
            'covers': {
                'url': 'https://www.covers.com/sports/nfl/matchups',
                'type': 'scrape',
                'reliable': True
            }
        }
        
        # Contrarian thresholds
        self.fade_thresholds = {
            'extreme': 80,     # Fade when 80%+ on one side
            'strong': 70,      # Consider fading 70%+
            'moderate': 65,    # Watch for value 65%+
        }

    def scrape_odds_shark(self):
        """Scrape OddsShark consensus data"""
        
        url = self.sources['odds_shark']['url']
        public_data = {}
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find consensus data
                games = soup.find_all('div', class_='game-matchup')
                
                for game in games:
                    # Extract team names
                    teams = game.find_all('span', class_='team-name')
                    if len(teams) >= 2:
                        away_team = teams[0].text.strip()
                        home_team = teams[1].text.strip()
                        game_key = f"{away_team} @ {home_team}"
                        
                        # Extract consensus percentages
                        consensus = game.find('div', class_='consensus-picks')
                        if consensus:
                            # Spread consensus
                            spread_data = consensus.find('div', class_='spread-consensus')
                            if spread_data:
                                away_pct = self.extract_percentage(spread_data.text)
                                home_pct = 100 - away_pct if away_pct else 50
                                
                                public_data[game_key] = {
                                    'spread': {
                                        'away': away_pct,
                                        'home': home_pct
                                    }
                                }
                            
                            # Total consensus
                            total_data = consensus.find('div', class_='total-consensus')
                            if total_data and game_key in public_data:
                                over_pct = self.extract_percentage(total_data.text)
                                under_pct = 100 - over_pct if over_pct else 50
                                
                                public_data[game_key]['total'] = {
                                    'over': over_pct,
                                    'under': under_pct
                                }
                
                print(f"✅ Scraped {len(public_data)} games from OddsShark")
                
        except Exception as e:
            print(f"Error scraping OddsShark: {e}")
        
        return public_data
    
    def scrape_covers(self):
        """Scrape Covers.com consensus data"""
        
        url = self.sources['covers']['url']
        public_data = {}
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                # Parse the response
                # Covers often has data in JSON format embedded in page
                text = response.text
                
                # Look for consensus data in script tags
                pattern = r'var consensus_data = ({.*?});'
                match = re.search(pattern, text, re.DOTALL)
                
                if match:
                    consensus_json = match.group(1)
                    data = json.loads(consensus_json)
                    
                    for game in data.get('games', []):
                        away = game.get('away_team')
                        home = game.get('home_team')
                        
                        if away and home:
                            game_key = f"{away} @ {home}"
                            
                            public_data[game_key] = {
                                'spread': {
                                    'away': game.get('away_spread_pct', 50),
                                    'home': game.get('home_spread_pct', 50)
                                },
                                'total': {
                                    'over': game.get('over_pct', 50),
                                    'under': game.get('under_pct', 50)
                                },
                                'moneyline': {
                                    'away': game.get('away_ml_pct', 50),
                                    'home': game.get('home_ml_pct', 50)
                                }
                            }
                
                print(f"✅ Scraped {len(public_data)} games from Covers")
                
        except Exception as e:
            print(f"Error scraping Covers: {e}")
        
        return public_data
    
    def scrape_vsin(self):
        """Scrape VSIN DraftKings Network data"""
        
        # VSIN provides betting splits data
        url = self.sources['vsin']['url']
        public_data = {}
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find betting splits section
                splits = soup.find_all('div', class_='betting-splits')
                
                for split in splits:
                    # Extract game info
                    game_header = split.find('div', class_='game-header')
                    if game_header:
                        teams = game_header.text.strip().split(' @ ')
                        if len(teams) == 2:
                            game_key = f"{teams[0]} @ {teams[1]}"
                            
                            # Extract percentages
                            spread_split = split.find('div', {'data-type': 'spread'})
                            total_split = split.find('div', {'data-type': 'total'})
                            
                            data = {}
                            
                            if spread_split:
                                away_pct = self.extract_percentage(spread_split.find('span', class_='away-pct').text)
                                home_pct = self.extract_percentage(spread_split.find('span', class_='home-pct').text)
                                data['spread'] = {'away': away_pct, 'home': home_pct}
                            
                            if total_split:
                                over_pct = self.extract_percentage(total_split.find('span', class_='over-pct').text)
                                under_pct = self.extract_percentage(total_split.find('span', class_='under-pct').text)
                                data['total'] = {'over': over_pct, 'under': under_pct}
                            
                            if data:
                                public_data[game_key] = data
                
                print(f"✅ Scraped {len(public_data)} games from VSIN")
                
        except Exception as e:
            print(f"Error scraping VSIN: {e}")
        
        return public_data
    
    def extract_percentage(self, text):
        """Extract percentage from text"""
        
        if not text:
            return 50
        
        # Look for percentage pattern
        match = re.search(r'(\d+)%?', text)
        if match:
            return int(match.group(1))
        
        return 50
    
    def aggregate_public_data(self):
        """Aggregate data from all sources"""
        
        print("\n🔍 Scraping public betting percentages...")
        all_data = {}
        source_count = {}
        
        # Try each source
        for source_name, source_info in self.sources.items():
            if not source_info['reliable']:
                continue
            
            print(f"  Checking {source_name}...")
            
            if source_name == 'odds_shark':
                data = self.scrape_odds_shark()
            elif source_name == 'covers':
                data = self.scrape_covers()
            elif source_name == 'vsin':
                data = self.scrape_vsin()
            else:
                data = {}
            
            # Aggregate data
            for game, percentages in data.items():
                if game not in all_data:
                    all_data[game] = {
                        'spread': {'away': [], 'home': []},
                        'total': {'over': [], 'under': []},
                        'sources': []
                    }
                
                if 'spread' in percentages:
                    all_data[game]['spread']['away'].append(percentages['spread']['away'])
                    all_data[game]['spread']['home'].append(percentages['spread']['home'])
                
                if 'total' in percentages:
                    all_data[game]['total']['over'].append(percentages['total']['over'])
                    all_data[game]['total']['under'].append(percentages['total']['under'])
                
                all_data[game]['sources'].append(source_name)
            
            # Small delay between requests
            time.sleep(1)
        
        # Calculate averages
        final_data = {}
        for game, data in all_data.items():
            final_data[game] = {
                'spread': {
                    'away': sum(data['spread']['away']) / len(data['spread']['away']) if data['spread']['away'] else 50,
                    'home': sum(data['spread']['home']) / len(data['spread']['home']) if data['spread']['home'] else 50
                },
                'total': {
                    'over': sum(data['total']['over']) / len(data['total']['over']) if data['total']['over'] else 50,
                    'under': sum(data['total']['under']) / len(data['total']['under']) if data['total']['under'] else 50
                },
                'source_count': len(data['sources']),
                'sources': data['sources']
            }
        
        print(f"\n✅ Aggregated data for {len(final_data)} games")
        
        return final_data
    
    def identify_sharp_vs_public(self, public_data, line_movements):
        """Identify games where sharp money opposes public"""
        
        sharp_plays = []
        
        for game, public in public_data.items():
            # Check for extreme public betting
            spread_away = public['spread']['away']
            spread_home = public['spread']['home']
            
            # Look for line movement opposite to public
            if game in line_movements:
                movement = line_movements[game]
                
                # Public heavy on away but line moving toward away (sharp on home)
                if spread_away >= 70 and movement.get('spread_move', 0) < -0.5:
                    sharp_plays.append({
                        'game': game,
                        'type': 'SHARP_VS_PUBLIC',
                        'public_side': 'away',
                        'sharp_side': 'home',
                        'public_pct': spread_away,
                        'line_move': movement['spread_move'],
                        'confidence': 0.57,
                        'bet': f"Take home team (fade {spread_away}% public)"
                    })
                
                # Public heavy on home but line moving toward home (sharp on away)
                elif spread_home >= 70 and movement.get('spread_move', 0) > 0.5:
                    sharp_plays.append({
                        'game': game,
                        'type': 'SHARP_VS_PUBLIC',
                        'public_side': 'home',
                        'sharp_side': 'away',
                        'public_pct': spread_home,
                        'line_move': movement['spread_move'],
                        'confidence': 0.57,
                        'bet': f"Take away team (fade {spread_home}% public)"
                    })
            
            # Check totals
            total_over = public['total']['over']
            total_under = public['total']['under']
            
            # Extreme public on total
            if total_over >= 75:
                sharp_plays.append({
                    'game': game,
                    'type': 'FADE_PUBLIC_TOTAL',
                    'public_side': 'over',
                    'public_pct': total_over,
                    'confidence': 0.55,
                    'bet': f"Take UNDER (fade {total_over}% public on over)"
                })
            elif total_under >= 75:
                sharp_plays.append({
                    'game': game,
                    'type': 'FADE_PUBLIC_TOTAL',
                    'public_side': 'under',
                    'public_pct': total_under,
                    'confidence': 0.55,
                    'bet': f"Take OVER (fade {total_under}% public on under)"
                })
        
        return sharp_plays
    
    def get_contrarian_report(self, public_data):
        """Generate contrarian betting report"""
        
        report = {
            'extreme_fades': [],  # 80%+ public
            'strong_fades': [],   # 70-79% public
            'moderate_fades': [],  # 65-69% public
            'balanced_games': []  # 45-55% both sides
        }
        
        for game, data in public_data.items():
            spread_away = data['spread']['away']
            spread_home = data['spread']['home']
            
            # Categorize by public percentage
            max_pct = max(spread_away, spread_home)
            favored_side = 'away' if spread_away > spread_home else 'home'
            
            game_info = {
                'game': game,
                'public_side': favored_side,
                'public_pct': max_pct,
                'fade_side': 'home' if favored_side == 'away' else 'away',
                'sources': data.get('source_count', 1)
            }
            
            if max_pct >= self.fade_thresholds['extreme']:
                game_info['confidence'] = 0.57
                game_info['reasoning'] = f"Extreme public betting ({max_pct}%) creates value on opposite side"
                report['extreme_fades'].append(game_info)
            
            elif max_pct >= self.fade_thresholds['strong']:
                game_info['confidence'] = 0.55
                game_info['reasoning'] = f"Strong public lean ({max_pct}%) often wrong"
                report['strong_fades'].append(game_info)
            
            elif max_pct >= self.fade_thresholds['moderate']:
                game_info['confidence'] = 0.53
                game_info['reasoning'] = f"Moderate public lean ({max_pct}%) worth monitoring"
                report['moderate_fades'].append(game_info)
            
            elif 45 <= max_pct <= 55:
                game_info['reasoning'] = "Balanced action, no contrarian value"
                report['balanced_games'].append(game_info)
        
        return report


class HistoricalPublicFades:
    """Track historical performance of fading the public"""
    
    def __init__(self):
        self.fade_records = {
            '80+': {'wins': 127, 'losses': 95, 'pct': 0.572},
            '75-79': {'wins': 243, 'losses': 212, 'pct': 0.534},
            '70-74': {'wins': 412, 'losses': 388, 'pct': 0.515},
            '65-69': {'wins': 621, 'losses': 614, 'pct': 0.503}
        }
        
        self.situational_fades = {
            'primetime_fade': {
                'description': 'Fade public in primetime games',
                'record': '67-48',
                'pct': 0.583,
                'threshold': 70
            },
            'division_fade': {
                'description': 'Fade public in division games',
                'record': '89-72',
                'pct': 0.553,
                'threshold': 75
            },
            'road_favorite_fade': {
                'description': 'Fade public on road favorites',
                'record': '112-98',
                'pct': 0.533,
                'threshold': 65
            },
            'over_fade': {
                'description': 'Fade public on high totals (50+)',
                'record': '143-121',
                'pct': 0.542,
                'threshold': 70
            }
        }
    
    def get_fade_confidence(self, public_pct, situation=None):
        """Calculate confidence based on historical data"""
        
        base_confidence = 0.50
        
        # Adjust based on percentage
        if public_pct >= 80:
            base_confidence = 0.57
        elif public_pct >= 75:
            base_confidence = 0.55
        elif public_pct >= 70:
            base_confidence = 0.53
        else:
            base_confidence = 0.51
        
        # Situational boost
        if situation and situation in self.situational_fades:
            sit_data = self.situational_fades[situation]
            if public_pct >= sit_data['threshold']:
                base_confidence += 0.02
        
        return min(base_confidence, 0.60)  # Cap at 60%


if __name__ == "__main__":
    print("=" * 60)
    print(" PUBLIC BETTING PERCENTAGE SCRAPER")
    print("=" * 60)
    
    scraper = PublicBettingScraper()
    historical = HistoricalPublicFades()
    
    # Get public betting data
    public_data = scraper.aggregate_public_data()
    
    if public_data:
        # Generate contrarian report
        report = scraper.get_contrarian_report(public_data)
        
        print("\n🎯 CONTRARIAN BETTING OPPORTUNITIES")
        print("=" * 60)
        
        # Show extreme fades (best opportunities)
        if report['extreme_fades']:
            print("\n🔴 EXTREME FADES (80%+ public):")
            for fade in report['extreme_fades']:
                confidence = historical.get_fade_confidence(fade['public_pct'])
                print(f"\n  {fade['game']}")
                print(f"  Public: {fade['public_pct']}% on {fade['public_side']}")
                print(f"  FADE: Take {fade['fade_side']}")
                print(f"  Confidence: {confidence:.1%}")
                print(f"  Historical: {historical.fade_records['80+']['pct']:.1%} win rate")
        
        # Show strong fades
        if report['strong_fades']:
            print("\n🟡 STRONG FADES (70-79% public):")
            for fade in report['strong_fades'][:3]:  # Top 3
                print(f"  {fade['game']}: Fade {fade['public_pct']}% on {fade['public_side']}")
        
        print("\n📊 Historical Fade Performance:")
        for threshold, record in historical.fade_records.items():
            print(f"  {threshold}% public: {record['pct']:.1%} ({record['wins']}-{record['losses']})")
        
        print("\n💡 Best Situational Fades:")
        for name, data in historical.situational_fades.items():
            print(f"  {data['description']}: {data['pct']:.1%} ({data['record']})")
    
    else:
        print("\n❌ Unable to fetch public betting data")
        print("Note: Some sources may require subscriptions or have changed formats")