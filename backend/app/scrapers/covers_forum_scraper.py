#!/usr/bin/env python3
"""
Covers.com Forum Scraper
Scrapes consensus and forum discussions from covers.com
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

class CoversForumScraper:
    def __init__(self):
        self.base_url = "https://www.covers.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_consensus(self, sport='nfl'):
        """Get public consensus from covers.com"""
        consensus_data = {}
        
        try:
            # Covers consensus page
            url = f"{self.base_url}/sports/{sport}/consensus-picks"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find consensus tables
                games = soup.find_all('div', class_='covers-CoversConsensusDetailsTable')
                
                for game in games:
                    # Extract team names
                    teams = game.find_all('div', class_='covers-CoversConsensusDetailsTable__team-name')
                    if len(teams) >= 2:
                        away_team = teams[0].text.strip()
                        home_team = teams[1].text.strip()
                        
                        # Extract consensus percentages
                        consensus_bars = game.find_all('div', class_='covers-CoversConsensusDetailsTable__bar')
                        
                        if consensus_bars:
                            # Parse percentages from style width
                            away_pct = 50
                            home_pct = 50
                            
                            for bar in consensus_bars:
                                style = bar.get('style', '')
                                if 'width' in style:
                                    width_match = re.search(r'width:\s*(\d+)%', style)
                                    if width_match:
                                        pct = int(width_match.group(1))
                                        if 'away' in bar.get('class', []):
                                            away_pct = pct
                                        else:
                                            home_pct = 100 - pct
                            
                            consensus_data[f"{away_team} @ {home_team}"] = {
                                'away_percentage': away_pct,
                                'home_percentage': home_pct,
                                'source': 'covers_consensus'
                            }
                            
        except Exception as e:
            print(f"Error getting Covers consensus: {e}")
            
        return consensus_data
    
    def scrape_forum_picks(self, sport='nfl'):
        """Scrape popular picks from forums"""
        forum_sentiment = {}
        
        try:
            # Popular forum threads
            forum_url = f"{self.base_url}/forum/{sport}-betting"
            response = requests.get(forum_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find hot threads
                threads = soup.find_all('div', class_='covers-ForumThreadCard')[:20]
                
                for thread in threads:
                    title = thread.find('a', class_='covers-ForumThreadCard__title')
                    if title:
                        thread_text = title.text.lower()
                        
                        # Look for team mentions and betting language
                        if any(word in thread_text for word in ['pick', 'bet', 'taking', 'fade', 'love', 'hammer']):
                            # Extract reply count as engagement metric
                            replies = thread.find('span', class_='covers-ForumThreadCard__replies')
                            reply_count = 0
                            if replies:
                                reply_count = int(re.sub(r'\D', '', replies.text))
                            
                            # Store high-engagement threads
                            if reply_count > 10:
                                forum_sentiment[title.text] = {
                                    'engagement': reply_count,
                                    'url': f"{self.base_url}{title['href']}"
                                }
                                
        except Exception as e:
            print(f"Error scraping Covers forum: {e}")
            
        return forum_sentiment
    
    def get_matchup_discussions(self, away_team, home_team):
        """Get discussion sentiment for specific matchup"""
        sentiment = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        try:
            # Search for matchup discussions
            search_query = f"{away_team} {home_team}"
            search_url = f"{self.base_url}/search?q={search_query}"
            
            response = requests.get(search_url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Analyze search results
                results = soup.find_all('div', class_='search-result')[:10]
                
                for result in results:
                    text = result.text.lower()
                    
                    # Simple sentiment analysis
                    positive_words = ['love', 'like', 'great', 'best', 'winner', 'lock', 'confident']
                    negative_words = ['hate', 'fade', 'avoid', 'bad', 'terrible', 'trap', 'stay away']
                    
                    pos_count = sum(1 for word in positive_words if word in text)
                    neg_count = sum(1 for word in negative_words if word in text)
                    
                    if pos_count > neg_count:
                        sentiment['positive'] += 1
                    elif neg_count > pos_count:
                        sentiment['negative'] += 1
                    else:
                        sentiment['neutral'] += 1
                        
        except Exception as e:
            print(f"Error getting matchup discussions: {e}")
            
        return sentiment