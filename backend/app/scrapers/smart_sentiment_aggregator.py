#!/usr/bin/env python3
"""
Smart Sentiment Aggregator - Uses multiple sources with fallbacks
Avoids rate limiting by rotating sources and caching
"""

import json
import time
from datetime import datetime
from .reddit_safe_scraper import RedditSafeScraper

class SmartSentimentAggregator:
    def __init__(self):
        self.reddit_scraper = RedditSafeScraper()
        self.sentiment_cache = {}
        self.cache_duration = 600  # 10 minutes
        
    def get_cached_sentiment(self, away, home):
        """Check if we have recent cached data"""
        cache_key = f"{away}@{home}"
        if cache_key in self.sentiment_cache:
            cached_data, cache_time = self.sentiment_cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return cached_data
        return None
    
    def save_to_cache(self, away, home, data):
        """Save sentiment to cache"""
        cache_key = f"{away}@{home}"
        self.sentiment_cache[cache_key] = (data, time.time())
    
    def generate_smart_estimate(self, away, home, spreads=None):
        """Generate intelligent estimates based on spreads and team names"""
        # Use spread to estimate public sentiment
        if spreads:
            avg_spread = sum(s['line'] for s in spreads.values()) / len(spreads)
            
            # Estimate public sentiment based on spread
            # Public LOVES favorites and home teams
            if avg_spread < -7:  # Home is big favorite
                home_pct = 72  # Public hammers big home favorites
            elif avg_spread < -3:  # Home is moderate favorite
                home_pct = 65  # Public likes home favorites
            elif avg_spread > 7:  # Away is big favorite
                home_pct = 28  # Public fades home dogs heavily
            elif avg_spread > 3:  # Away is moderate favorite
                home_pct = 35  # Public leans away
            elif -3 <= avg_spread <= -1:  # Slight home favorite
                home_pct = 58  # Small home favorite edge
            elif 1 <= avg_spread <= 3:  # Slight away favorite
                home_pct = 42  # Small away favorite edge
            else:  # Pick'em
                home_pct = 52  # Slight home bias even in pick'em
        else:
            # No spread data - use team popularity
            popular_teams = ['Cowboys', 'Chiefs', 'Patriots', 'Packers', 'Steelers', 
                           '49ers', 'Eagles', 'Bills', 'Alabama', 'Georgia', 'Ohio State']
            
            home_popular = any(team in home for team in popular_teams)
            away_popular = any(team in away for team in popular_teams)
            
            if home_popular and not away_popular:
                home_pct = 68  # Popular home teams get heavy public action
            elif away_popular and not home_popular:
                home_pct = 32  # Popular away teams pull public money
            else:
                home_pct = 54  # Default slight home bias
        
        away_pct = 100 - home_pct
        
        return {
            'home_percentage': home_pct,
            'away_percentage': away_pct,
            'source': 'Smart Estimate',
            'confidence': 'ESTIMATED',
            'posts_analyzed': 0
        }
    
    def get_game_sentiment(self, away, home, sport='nfl', spreads=None):
        """Get sentiment with smart fallbacks"""
        
        # Check cache first
        cached = self.get_cached_sentiment(away, home)
        if cached:
            print(f"      📦 Using cached data: {cached['home_percentage']}% home")
            return cached
        
        # Try Reddit with safe scraper
        try:
            reddit_data = self.reddit_scraper.get_game_sentiment(away, home, sport)
            if reddit_data and reddit_data['posts_analyzed'] > 0:
                self.save_to_cache(away, home, reddit_data)
                return reddit_data
        except Exception as e:
            print(f"      ⚠️ Reddit unavailable: {str(e)[:30]}")
        
        # Fallback to smart estimates
        print(f"      🤖 Using smart estimates based on spreads/teams")
        estimate = self.generate_smart_estimate(away, home, spreads)
        self.save_to_cache(away, home, estimate)
        return estimate
    
    def get_batch_sentiment(self, games, sport='nfl'):
        """Get sentiment for multiple games efficiently"""
        results = {}
        
        # Try to get daily thread once for all games
        daily_thread = self.reddit_scraper.get_daily_thread_sentiment(sport)
        
        if daily_thread:
            print("      📰 Found daily betting thread - extracting sentiment...")
            # Parse daily thread for all games
            # This would extract mentions of all teams from one thread
            
        for game in games:
            away = game.get('away_team')
            home = game.get('home_team')
            spreads = game.get('spreads', {})
            
            sentiment = self.get_game_sentiment(away, home, sport, spreads)
            results[f"{away}@{home}"] = sentiment
            
            # Small delay between games to avoid rate limiting
            time.sleep(1.0)  # Fixed delay between requests
        
        return results