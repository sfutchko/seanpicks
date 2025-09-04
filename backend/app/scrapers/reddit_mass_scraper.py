#!/usr/bin/env python3
"""
Reddit Mass Scraper - Gets large amounts of betting sentiment data
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re

class RedditMassScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.nfl_subreddits = [
            'sportsbook',
            'nfl',
            'fantasyfootball',
            'DynastyFF',
            'sportsbetting'
        ]
        self.cfb_subreddits = [
            'CFB',
            'sportsbook',
            'CFBVegas',
            'sportsbetting',
            'CollegeBasketball'  # Sometimes has football discussion
        ]
        
    def scrape_subreddit(self, subreddit, sport='nfl'):
        """Scrape a subreddit for betting sentiment"""
        sentiment_data = {}
        
        try:
            # Try multiple sorting methods to get more data
            sort_methods = ['hot', 'new', 'top']
            
            for sort in sort_methods:
                url = f"https://old.reddit.com/r/{subreddit}/{sort}/.json?limit=100"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '').lower()
                        text = post_data.get('selftext', '').lower()
                        comments = post_data.get('num_comments', 0)
                        score = post_data.get('score', 0)
                        
                        # Look for team mentions and betting language
                        if sport.lower() in title or sport.lower() in text or 'bet' in title or 'pick' in title:
                            # Extract team names (simplified)
                            teams = self.extract_teams(title + ' ' + text, sport)
                            
                            for team in teams:
                                if team not in sentiment_data:
                                    sentiment_data[team] = {
                                        'mentions': 0,
                                        'positive': 0,
                                        'negative': 0,
                                        'total_engagement': 0
                                    }
                                
                                sentiment_data[team]['mentions'] += 1
                                sentiment_data[team]['total_engagement'] += comments + score
                                
                                # Simple sentiment analysis
                                if any(word in title + text for word in ['love', 'hammer', 'lock', 'best bet', 'confident']):
                                    sentiment_data[team]['positive'] += 1
                                elif any(word in title + text for word in ['fade', 'avoid', 'trap', 'stay away', 'bad']):
                                    sentiment_data[team]['negative'] += 1
                
                time.sleep(1)  # Be respectful to Reddit
                
        except Exception as e:
            print(f"Error scraping r/{subreddit}: {e}")
            
        return sentiment_data
    
    def extract_teams(self, text, sport):
        """Extract team names from text"""
        teams = []
        
        if sport == 'nfl':
            nfl_teams = [
                'chiefs', 'bills', 'eagles', 'cowboys', '49ers', 'bengals',
                'ravens', 'chargers', 'jaguars', 'dolphins', 'vikings', 'giants',
                'jets', 'commanders', 'titans', 'colts', 'packers', 'bears',
                'lions', 'buccaneers', 'falcons', 'saints', 'panthers', 'seahawks',
                'cardinals', 'rams', 'broncos', 'raiders', 'patriots', 'steelers',
                'browns', 'texans'
            ]
            
            for team in nfl_teams:
                if team in text:
                    teams.append(team)
                    
        return teams
    
    def get_game_sentiment(self, away_team, home_team, sport='nfl'):
        """Get sentiment for a specific game from all subreddits"""
        print(f"    🔍 Scraping Reddit for {away_team} @ {home_team}...")
        
        away_mentions = 0
        away_positive = 0
        home_mentions = 0
        home_positive = 0
        total_posts = 0
        
        # Choose subreddits based on sport
        if 'college' in sport.lower() or 'ncaa' in sport.lower() or 'cfb' in sport.lower():
            subreddits = self.cfb_subreddits
        else:
            subreddits = self.nfl_subreddits
            
        for subreddit in subreddits[:3]:  # Limit to avoid too many requests
            try:
                url = f"https://old.reddit.com/r/{subreddit}/search.json?q={away_team.split()[-1]}+{home_team.split()[-1]}&restrict_sr=on&limit=25&sort=new"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '').lower()
                        text = post_data.get('selftext', '').lower()
                        
                        total_posts += 1
                        
                        # Check mentions
                        if away_team.lower() in title + text:
                            away_mentions += 1
                            if any(word in title + text for word in ['take', 'love', 'hammer', 'bet']):
                                away_positive += 1
                                
                        if home_team.lower() in title + text:
                            home_mentions += 1
                            if any(word in title + text for word in ['take', 'love', 'hammer', 'bet']):
                                home_positive += 1
                
                time.sleep(0.5)  # Rate limit
                
            except Exception as e:
                print(f"      ⚠️ Error searching r/{subreddit}: {str(e)[:50]}")
        
        # Calculate percentages
        if away_mentions + home_mentions > 0:
            away_pct = round((away_mentions / (away_mentions + home_mentions)) * 100)
            home_pct = 100 - away_pct
            
            # Adjust based on positive sentiment
            if away_positive > home_positive and away_positive > 0:
                away_pct = min(away_pct + 5, 75)  # Boost but cap at 75%
                home_pct = 100 - away_pct
            elif home_positive > away_positive and home_positive > 0:
                home_pct = min(home_pct + 5, 75)
                away_pct = 100 - home_pct
            
            print(f"      ✅ Reddit: {total_posts} posts analyzed, {home_pct}% on {home_team}")
            
            return {
                'home_percentage': home_pct,
                'away_percentage': away_pct,
                'posts_analyzed': total_posts,
                'confidence': 'MEDIUM' if total_posts >= 5 else 'LOW'
            }
        
        return None
    
    def get_weekly_sentiment(self):
        """Get overall weekly sentiment trends"""
        weekly_data = {}
        
        print("    🔍 Getting weekly Reddit sentiment...")
        
        try:
            # Get the weekly NFL thread
            url = "https://old.reddit.com/r/sportsbook/search.json?q=NFL+daily&restrict_sr=on&limit=10&sort=new"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                for post in posts[:3]:  # Check recent daily threads
                    post_data = post.get('data', {})
                    
                    # Get comments from the daily thread
                    post_id = post_data.get('id')
                    comments_url = f"https://old.reddit.com/r/sportsbook/comments/{post_id}.json?limit=100"
                    
                    comments_response = requests.get(comments_url, headers=self.headers)
                    if comments_response.status_code == 200:
                        comments_data = comments_response.json()
                        
                        # Parse comments for team mentions
                        if len(comments_data) > 1:
                            comments = comments_data[1].get('data', {}).get('children', [])
                            
                            for comment in comments:
                                comment_text = comment.get('data', {}).get('body', '').lower()
                                
                                # Extract betting picks
                                if 'pick:' in comment_text or 'bet:' in comment_text:
                                    teams = self.extract_teams(comment_text, 'nfl')
                                    for team in teams:
                                        if team not in weekly_data:
                                            weekly_data[team] = 0
                                        weekly_data[team] += 1
                    
                    time.sleep(1)
                
                print(f"      ✅ Found sentiment for {len(weekly_data)} teams")
                
        except Exception as e:
            print(f"      ⚠️ Error getting weekly sentiment: {str(e)[:50]}")
        
        return weekly_data