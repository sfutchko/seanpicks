#!/usr/bin/env python3
"""
Reddit Safe Scraper - Respects rate limits and avoids blocking
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import hashlib
from datetime import datetime, timedelta

class RedditSafeScraper:
    def __init__(self):
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_delay = 2  # Minimum 2 seconds between requests
        self.cache = {}  # Simple in-memory cache
        self.cache_duration = 300  # Cache for 5 minutes
        
    def get_headers(self):
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def rate_limit_delay(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(0.5, 1.5)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def make_request(self, url, retries=3):
        """Make request with retry logic"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return cached_data
        
        for attempt in range(retries):
            try:
                self.rate_limit_delay()
                
                response = self.session.get(url, headers=self.get_headers(), timeout=10)
                
                if response.status_code == 200:
                    # Cache successful response
                    self.cache[cache_key] = (response, time.time())
                    return response
                    
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('x-ratelimit-reset', 60))
                    print(f"      ⏳ Rate limited. Waiting {retry_after}s...")
                    
                    if attempt < retries - 1:
                        time.sleep(min(retry_after + 5, 120))  # Cap at 2 minutes
                    else:
                        return None
                        
                elif response.status_code in [503, 504]:
                    # Server issues - wait and retry
                    if attempt < retries - 1:
                        time.sleep(10 * (attempt + 1))
                    
            except Exception as e:
                print(f"      ⚠️ Request error: {str(e)[:50]}")
                if attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))
                    
        return None
    
    def get_game_sentiment(self, away_team, home_team, sport='nfl'):
        """Get sentiment with safe scraping"""
        # Use simpler search to reduce load
        away_short = away_team.split()[-1]
        home_short = home_team.split()[-1]
        
        sentiment_data = {
            'home_percentage': 50,
            'away_percentage': 50,
            'posts_analyzed': 0,
            'confidence': 'LOW',
            'source': 'Reddit'
        }
        
        try:
            # Try getting from daily thread first (less requests)
            if sport == 'nfl':
                url = f"https://old.reddit.com/r/nfl/search.json?q=game+thread+{away_short}+{home_short}&restrict_sr=on&limit=10&sort=new&t=week"
            else:
                url = f"https://old.reddit.com/r/CFB/search.json?q={away_short}+{home_short}&restrict_sr=on&limit=10&sort=new&t=week"
            
            response = self.make_request(url)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    if posts:
                        away_mentions = 0
                        home_mentions = 0
                        total_comments = 0
                        
                        for post in posts[:5]:  # Limit to 5 posts
                            post_data = post.get('data', {})
                            title = post_data.get('title', '').lower()
                            text = post_data.get('selftext', '').lower()
                            comments = post_data.get('num_comments', 0)
                            
                            total_comments += comments
                            
                            # Simple sentiment based on title/text
                            if away_short.lower() in title + text:
                                away_mentions += 1 + (comments // 10)  # Weight by engagement
                            if home_short.lower() in title + text:
                                home_mentions += 1 + (comments // 10)
                        
                        # Calculate percentages
                        total_mentions = away_mentions + home_mentions
                        if total_mentions > 0:
                            away_pct = round((away_mentions / total_mentions) * 100)
                            home_pct = 100 - away_pct
                            
                            sentiment_data['away_percentage'] = away_pct
                            sentiment_data['home_percentage'] = home_pct
                            sentiment_data['posts_analyzed'] = len(posts)
                            sentiment_data['confidence'] = 'MEDIUM' if total_comments > 100 else 'LOW'
                            
                            print(f"      ✅ Safe Reddit: {home_pct}% home from {len(posts)} posts")
                            return sentiment_data
                            
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"      ⚠️ Reddit scrape failed: {str(e)[:50]}")
        
        # Return default if scraping fails
        return sentiment_data
    
    def get_daily_thread_sentiment(self, sport='nfl'):
        """Get sentiment from daily betting threads (single request)"""
        try:
            if sport == 'nfl':
                url = "https://old.reddit.com/r/sportsbook/search.json?q=NFL+daily&restrict_sr=on&limit=1&sort=new"
            else:
                url = "https://old.reddit.com/r/sportsbook/search.json?q=NCAAF+daily&restrict_sr=on&limit=1&sort=new"
            
            response = self.make_request(url)
            
            if response and response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                if posts:
                    post_id = posts[0].get('data', {}).get('id')
                    
                    # Get comments from the daily thread
                    comments_url = f"https://old.reddit.com/r/sportsbook/comments/{post_id}.json?limit=50"
                    comments_response = self.make_request(comments_url)
                    
                    if comments_response and comments_response.status_code == 200:
                        return comments_response.json()
                        
        except Exception as e:
            print(f"      ⚠️ Daily thread error: {str(e)[:50]}")
            
        return None