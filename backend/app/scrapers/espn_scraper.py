#!/usr/bin/env python3
"""
ESPN Comments Scraper
Scrapes comments from ESPN game pages for public sentiment
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

class ESPNScraper:
    def __init__(self):
        self.base_url = "https://www.espn.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_nfl_games(self):
        """Get current week NFL games from ESPN"""
        games = []
        try:
            # ESPN NFL scoreboard
            url = f"{self.base_url}/nfl/scoreboard"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find game links
                game_links = soup.find_all('a', href=re.compile(r'/nfl/game/_/gameId/\d+'))
                
                for link in game_links[:10]:  # Limit to 10 games
                    game_id = link['href'].split('/')[-1]
                    games.append({
                        'game_id': game_id,
                        'url': f"{self.base_url}{link['href']}"
                    })
                    
        except Exception as e:
            print(f"Error getting ESPN games: {e}")
            
        return games
    
    def scrape_game_sentiment(self, game_url):
        """Scrape sentiment from game preview/recap"""
        sentiment_data = {
            'comments': [],
            'picks': {'home': 0, 'away': 0},
            'total_engagement': 0
        }
        
        try:
            # Get game preview page
            preview_url = game_url.replace('/game/', '/preview/')
            response = requests.get(preview_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract expert picks if available
                picks_section = soup.find('div', class_='picks-section')
                if picks_section:
                    home_picks = len(picks_section.find_all('span', class_='pick-home'))
                    away_picks = len(picks_section.find_all('span', class_='pick-away'))
                    sentiment_data['picks']['home'] = home_picks
                    sentiment_data['picks']['away'] = away_picks
                
                # Try to find fan poll results
                poll_section = soup.find('div', class_='fan-poll')
                if poll_section:
                    percentages = poll_section.find_all('span', class_='percentage')
                    if len(percentages) >= 2:
                        sentiment_data['fan_poll'] = {
                            'away': float(percentages[0].text.strip('%')),
                            'home': float(percentages[1].text.strip('%'))
                        }
                
            # Also check game conversation API endpoint
            game_id = game_url.split('/')[-1]
            api_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
            
            api_response = requests.get(api_url, headers=self.headers)
            if api_response.status_code == 200:
                data = api_response.json()
                
                # Extract any available metrics
                if 'winprobability' in data:
                    sentiment_data['win_probability'] = data['winprobability']
                    
                if 'predictor' in data:
                    sentiment_data['predictor'] = data['predictor']
                    
        except Exception as e:
            print(f"Error scraping ESPN game: {e}")
            
        return sentiment_data
    
    def analyze_all_games(self):
        """Analyze sentiment for all games"""
        all_sentiment = {}
        games = self.get_nfl_games()
        
        for game in games:
            print(f"Analyzing ESPN game {game['game_id']}...")
            sentiment = self.scrape_game_sentiment(game['url'])
            all_sentiment[game['game_id']] = sentiment
            time.sleep(1)  # Be respectful
            
        return all_sentiment