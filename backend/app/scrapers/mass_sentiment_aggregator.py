#!/usr/bin/env python3
"""
Mass Sentiment Aggregator
Combines data from multiple sources for comprehensive public sentiment
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

class MassSentimentAggregator:
    def __init__(self):
        self.sources = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def scrape_teamrankings(self, sport='nfl'):
        """Scrape TeamRankings public picks"""
        picks_data = {}
        
        try:
            url = f"https://www.teamrankings.com/{sport}/picks/"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find pick tables
                tables = soup.find_all('table', class_='tr-table')
                
                for table in tables:
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            matchup = cells[0].text.strip()
                            public_pick = cells[2].text.strip()
                            
                            # Extract percentage if available
                            pct_match = re.search(r'(\d+)%', public_pick)
                            if pct_match:
                                picks_data[matchup] = {
                                    'public_percentage': int(pct_match.group(1)),
                                    'source': 'teamrankings'
                                }
                                
        except Exception as e:
            print(f"Error scraping TeamRankings: {e}")
            
        return picks_data
    
    def scrape_action_network_free(self):
        """Scrape free data from Action Network"""
        action_data = {}
        
        try:
            # Action Network public betting page (some free data)
            url = "https://www.actionnetwork.com/nfl/public-betting"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for any free data elements
                games = soup.find_all('div', class_='game-card')
                
                for game in games:
                    # Extract whatever free data is visible
                    team_elements = game.find_all('span', class_='team-name')
                    if len(team_elements) >= 2:
                        away = team_elements[0].text.strip()
                        home = team_elements[1].text.strip()
                        
                        # Check for any percentage displays
                        pct_elements = game.find_all('span', class_='percentage')
                        if pct_elements:
                            action_data[f"{away} @ {home}"] = {
                                'has_sharp_action': 'sharp' in game.text.lower(),
                                'source': 'action_network_free'
                            }
                            
        except Exception as e:
            print(f"Error scraping Action Network: {e}")
            
        return action_data
    
    def scrape_vegas_insider(self):
        """Scrape VegasInsider consensus"""
        vegas_data = {}
        
        try:
            url = "https://www.vegasinsider.com/nfl/matchups/"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find consensus elements
                matchups = soup.find_all('div', class_='matchup-card')
                
                for matchup in matchups:
                    teams = matchup.find_all('span', class_='team')
                    if len(teams) >= 2:
                        # Look for consensus indicators
                        consensus = matchup.find('div', class_='consensus')
                        if consensus:
                            vegas_data[f"{teams[0].text} @ {teams[1].text}"] = {
                                'consensus': consensus.text.strip(),
                                'source': 'vegas_insider'
                            }
                            
        except Exception as e:
            print(f"Error scraping Vegas Insider: {e}")
            
        return vegas_data
    
    def aggregate_all_sources(self, games_list):
        """Aggregate sentiment from all available sources"""
        aggregated = {}
        
        print("Gathering mass sentiment data from multiple sources...")
        
        # ESPN Scraper
        from scrapers.espn_scraper import ESPNScraper
        espn = ESPNScraper()
        espn_data = espn.analyze_all_games()
        
        # Covers Forum
        from scrapers.covers_forum_scraper import CoversForumScraper
        covers = CoversForumScraper()
        covers_consensus = covers.get_consensus()
        covers_forums = covers.scrape_forum_picks()
        
        # TeamRankings
        teamrankings = self.scrape_teamrankings()
        
        # Action Network Free
        action_free = self.scrape_action_network_free()
        
        # Vegas Insider
        vegas = self.scrape_vegas_insider()
        
        # Combine all data
        for game in games_list:
            game_key = f"{game['away_team']} @ {game['home_team']}"
            
            aggregated[game_key] = {
                'sources_count': 0,
                'total_sentiment_points': 0,
                'consensus_percentages': [],
                'sharp_indicators': 0,
                'public_lean': 'neutral'
            }
            
            # Add ESPN data
            if game.get('game_id') in espn_data:
                aggregated[game_key]['espn'] = espn_data[game['game_id']]
                aggregated[game_key]['sources_count'] += 1
                
            # Add Covers consensus
            if game_key in covers_consensus:
                aggregated[game_key]['covers'] = covers_consensus[game_key]
                aggregated[game_key]['consensus_percentages'].append(
                    covers_consensus[game_key]['home_percentage']
                )
                aggregated[game_key]['sources_count'] += 1
                
            # Add TeamRankings
            for matchup, data in teamrankings.items():
                if game['home_team'].lower() in matchup.lower():
                    aggregated[game_key]['teamrankings'] = data
                    aggregated[game_key]['consensus_percentages'].append(
                        data.get('public_percentage', 50)
                    )
                    aggregated[game_key]['sources_count'] += 1
                    
            # Add Action Network indicators
            if game_key in action_free:
                aggregated[game_key]['action_indicators'] = action_free[game_key]
                if action_free[game_key].get('has_sharp_action'):
                    aggregated[game_key]['sharp_indicators'] += 1
                aggregated[game_key]['sources_count'] += 1
                
            # Calculate overall sentiment
            if aggregated[game_key]['consensus_percentages']:
                avg_home_pct = sum(aggregated[game_key]['consensus_percentages']) / len(
                    aggregated[game_key]['consensus_percentages']
                )
                
                if avg_home_pct > 60:
                    aggregated[game_key]['public_lean'] = 'home_heavy'
                elif avg_home_pct < 40:
                    aggregated[game_key]['public_lean'] = 'away_heavy'
                else:
                    aggregated[game_key]['public_lean'] = 'balanced'
                    
                aggregated[game_key]['average_home_percentage'] = round(avg_home_pct, 1)
                
        return aggregated
    
    def calculate_contrarian_value(self, game_data, aggregated_sentiment):
        """Calculate contrarian betting value based on mass sentiment"""
        contrarian_score = 0
        
        if aggregated_sentiment.get('public_lean') == 'home_heavy':
            # Public heavy on home, consider away
            if aggregated_sentiment.get('average_home_percentage', 50) > 70:
                contrarian_score += 3  # Strong contrarian
            elif aggregated_sentiment.get('average_home_percentage', 50) > 60:
                contrarian_score += 2  # Moderate contrarian
                
        elif aggregated_sentiment.get('public_lean') == 'away_heavy':
            # Public heavy on away, consider home
            if aggregated_sentiment.get('average_home_percentage', 50) < 30:
                contrarian_score += 3  # Strong contrarian
            elif aggregated_sentiment.get('average_home_percentage', 50) < 40:
                contrarian_score += 2  # Moderate contrarian
                
        # Add sharp indicators
        if aggregated_sentiment.get('sharp_indicators', 0) > 0:
            contrarian_score += 2
            
        # Factor in number of sources
        if aggregated_sentiment.get('sources_count', 0) >= 3:
            contrarian_score += 1  # More reliable with multiple sources
            
        return contrarian_score