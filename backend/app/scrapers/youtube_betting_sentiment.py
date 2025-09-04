#!/usr/bin/env python3
"""
YOUTUBE BETTING SENTIMENT ANALYZER
Pulls public betting sentiment from YouTube comments and videos
Uses YouTube Data API v3
"""

import requests
import json
import re
from datetime import datetime, timedelta

class YouTubeBettingSentiment:
    """Analyze YouTube for betting sentiment"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Popular NFL betting channels
        self.betting_channels = [
            'UCJ5v_MCY6GNUBTO8-D3XoAg',  # ESPN
            'UCiC955FLcQ6NG9klFNAXeOg',  # The Action Network
            # Add more channel IDs as needed
        ]
    
    def search_betting_videos(self, query, max_results=10):
        """Search for betting-related videos"""
        
        url = f"{self.base_url}/search"
        
        # Search for videos from past week
        published_after = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
        
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'order': 'viewCount',
            'publishedAfter': published_after,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get('items', []):
                    videos.append({
                        'video_id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'channel': item['snippet']['channelTitle'],
                        'published': item['snippet']['publishedAt']
                    })
                
                return videos
            else:
                print(f"YouTube API error: {response.status_code}")
                print(response.json())
                return []
                
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []
    
    def get_video_comments(self, video_id, max_results=100):
        """Get comments from a video"""
        
        url = f"{self.base_url}/commentThreads"
        
        params = {
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': max_results,
            'order': 'relevance',
            'textFormat': 'plainText',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                comments = []
                
                for item in data.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'likes': comment['likeCount'],
                        'published': comment['publishedAt']
                    })
                
                return comments
            else:
                # Comments might be disabled
                return []
                
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []
    
    def analyze_game_sentiment(self, away_team, home_team):
        """Analyze sentiment for a specific game"""
        
        print(f"\n📺 Analyzing YouTube sentiment for {away_team} @ {home_team}")
        
        # Search for videos about this game
        queries = [
            f"{away_team} {home_team} NFL picks",
            f"{away_team} vs {home_team} betting",
            f"{away_team} {home_team} prediction"
        ]
        
        all_mentions = {
            away_team: 0,
            home_team: 0,
            'total_comments': 0,
            'total_videos': 0
        }
        
        for query in queries:
            videos = self.search_betting_videos(query, max_results=3)
            all_mentions['total_videos'] += len(videos)
            
            for video in videos:
                # Analyze video title and description
                title_desc = (video['title'] + ' ' + video['description']).lower()
                
                # Look for team mentions with betting context
                away_variations = [away_team.lower(), away_team.split()[-1].lower()]
                home_variations = [home_team.lower(), home_team.split()[-1].lower()]
                
                # Check title/description sentiment
                for away_var in away_variations:
                    if away_var in title_desc:
                        # Look for positive betting keywords near team name
                        positive_patterns = [
                            f"take {away_var}", f"bet {away_var}", f"love {away_var}",
                            f"{away_var} covers", f"{away_var} wins", f"hammer {away_var}",
                            f"{away_var} +", f"pick {away_var}"
                        ]
                        for pattern in positive_patterns:
                            if pattern in title_desc:
                                all_mentions[away_team] += 3  # Weight title mentions more
                
                for home_var in home_variations:
                    if home_var in title_desc:
                        positive_patterns = [
                            f"take {home_var}", f"bet {home_var}", f"love {home_var}",
                            f"{home_var} covers", f"{home_var} wins", f"hammer {home_var}",
                            f"{home_var} -", f"pick {home_var}"
                        ]
                        for pattern in positive_patterns:
                            if pattern in title_desc:
                                all_mentions[home_team] += 3
                
                # Get video comments
                comments = self.get_video_comments(video['video_id'], max_results=50)
                all_mentions['total_comments'] += len(comments)
                
                for comment in comments:
                    comment_text = comment['text'].lower()
                    
                    # Count team mentions in comments
                    for away_var in away_variations:
                        if away_var in comment_text:
                            # Weight by likes
                            weight = 1 + (comment['likes'] * 0.1)  # Each like adds 0.1
                            all_mentions[away_team] += weight
                    
                    for home_var in home_variations:
                        if home_var in comment_text:
                            weight = 1 + (comment['likes'] * 0.1)
                            all_mentions[home_team] += weight
        
        # Calculate percentages
        total_mentions = all_mentions[away_team] + all_mentions[home_team]
        
        if total_mentions > 0:
            away_pct = (all_mentions[away_team] / total_mentions) * 100
            home_pct = (all_mentions[home_team] / total_mentions) * 100
            
            # Calculate weighted mentions for display
            weighted_mentions = int(all_mentions[away_team] + all_mentions[home_team])
            
            return {
                'away_team': away_team,
                'home_team': home_team,
                'away_percentage': round(away_pct),
                'home_percentage': round(home_pct),
                'total_videos': all_mentions['total_videos'],
                'total_comments': all_mentions['total_comments'],
                'weighted_mentions': weighted_mentions,  # Total weighted team mentions
                'confidence': 'HIGH' if all_mentions['total_comments'] > 100 else 'MEDIUM' if all_mentions['total_comments'] > 30 else 'LOW',
                'source': 'YouTube',
                'data_volume': f"{all_mentions['total_videos']} videos, {all_mentions['total_comments']} comments"
            }
        
        return None
    
    def get_trending_picks(self):
        """Get overall trending picks from YouTube"""
        
        print("\n🔥 Getting trending NFL picks from YouTube...")
        
        # Search for general NFL betting content
        videos = self.search_betting_videos("NFL picks week betting", max_results=10)
        
        trending = {}
        
        for video in videos:
            print(f"  📹 {video['title'][:60]}...")
            
            # Extract team names and sentiment from titles
            title = video['title']
            
            # Common patterns in betting video titles
            patterns = [
                r'(\w+)\s+[\+\-]\d+',  # Team +3.5
                r'bet\s+(\w+)',         # bet Chiefs
                r'take\s+(\w+)',        # take Cowboys
                r'(\w+)\s+cover',       # Eagles cover
                r'hammer\s+(\w+)',      # hammer Bills
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, title, re.IGNORECASE)
                for team in matches:
                    if len(team) > 3:  # Filter out short words
                        trending[team] = trending.get(team, 0) + 1
        
        # Sort by mentions
        sorted_trending = sorted(trending.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_trending[:10]  # Top 10 trending teams
    
    def test_api(self):
        """Test if API key is working"""
        
        print("🧪 Testing YouTube API key...")
        
        url = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'q': 'NFL',
            'type': 'video',
            'maxResults': 1,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                print("✅ YouTube API key is working!")
                data = response.json()
                quota_used = 100  # Search costs 100 units
                print(f"  Quota used: {quota_used} units (10,000 daily limit)")
                return True
            else:
                print(f"❌ API error: {response.status_code}")
                print(response.json())
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def test_youtube_integration():
    """Test the YouTube integration"""
    
    API_KEY = "AIzaSyAJGS_FhSvEwzU3P55EkEzPKNeIpTsp7_Q"
    
    print("="*60)
    print("🎥 YOUTUBE BETTING SENTIMENT ANALYZER")
    print("="*60)
    
    youtube = YouTubeBettingSentiment(API_KEY)
    
    # Test API key
    if not youtube.test_api():
        return
    
    # Test with a real game
    print("\nTesting with Cowboys @ Eagles:")
    sentiment = youtube.analyze_game_sentiment("Dallas Cowboys", "Philadelphia Eagles")
    
    if sentiment:
        print(f"\n📊 YouTube Sentiment Results:")
        print(f"  {sentiment['away_team']}: {sentiment['away_percentage']}%")
        print(f"  {sentiment['home_team']}: {sentiment['home_percentage']}%")
        print(f"  Based on: {sentiment['total_videos']} videos, {sentiment['total_comments']} comments")
        print(f"  Confidence: {sentiment['confidence']}")
    
    # Get trending picks
    print("\n🔥 Trending Teams on YouTube:")
    trending = youtube.get_trending_picks()
    for team, mentions in trending[:5]:
        print(f"  • {team}: {mentions} mentions")
    
    return sentiment


if __name__ == "__main__":
    test_youtube_integration()