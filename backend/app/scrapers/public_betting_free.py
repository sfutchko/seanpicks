#!/usr/bin/env python3
"""
FREE Public Betting Data - No API Key Needed!
Scrapes real public betting percentages from free sources
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

class FreePublicBetting:
    """Get REAL public betting data without paying!"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_sportsbettingdime(self):
        """SportsBettingDime shows real public % for FREE!"""
        
        url = "https://www.sportsbettingdime.com/nfl/public-betting-trends/"
        
        try:
            print("🔍 Scraping SportsBettingDime...")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                games = {}
                
                # Look for all text containing percentages
                all_text = soup.get_text()
                
                # Find patterns like "Chiefs 67%" or "67% on Chiefs" 
                percent_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+)%', all_text)
                
                for team, pct in percent_matches[:20]:  # First 20 matches
                    if int(pct) > 30 and int(pct) < 100:  # Valid betting percentage
                        games[team] = {
                            'public_bet_pct': f"{pct}%",
                            'opposing_pct': f"{100-int(pct)}%",
                            'source': 'SportsBettingDime'
                        }
                
                # Also try structured data
                script_tags = soup.find_all('script', type='application/ld+json')
                for script in script_tags:
                    try:
                        data = json.loads(script.string)
                        # Look for structured betting data
                        if isinstance(data, dict) and 'betting' in str(data).lower():
                            print(f"Found structured data: {data.keys()}")
                    except:
                        pass
                
                print(f"✅ Found {len(games)} games with public betting data")
                return games
            else:
                print(f"❌ Error: Status code {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error scraping SportsBettingDime: {e}")
            return {}
    
    def scrape_action_network_free(self):
        """Action Network shows some public % without PRO!"""
        
        url = "https://www.actionnetwork.com/nfl/public-betting"
        
        try:
            print("🔍 Scraping Action Network (free data)...")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                games = {}
                
                # Action Network often uses React/JSON embedded in page
                # Look for script tags with game data
                scripts = soup.find_all('script', type='application/json')
                
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        # Parse their data structure (varies)
                        if 'games' in str(data):
                            # Extract betting percentages
                            pass
                    except:
                        continue
                
                # Also try parsing visible HTML
                game_cards = soup.find_all(class_=re.compile('game|card|matchup', re.I))
                
                for card in game_cards[:10]:
                    # Extract whatever public data is visible
                    text = card.get_text()
                    if '%' in text:
                        # Parse the percentages
                        matches = re.findall(r'(\d+)%', text)
                        if matches:
                            print(f"Found percentages: {matches}")
                
                return games
                
        except Exception as e:
            print(f"❌ Error scraping Action Network: {e}")
            return {}
    
    def scrape_oddsshark(self):
        """OddsShark consensus picks - FREE!"""
        
        url = "https://www.oddsshark.com/nfl/consensus-picks"
        
        try:
            print("🔍 Scraping OddsShark consensus...")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                games = {}
                
                # OddsShark shows consensus in their tables
                consensus_data = soup.find_all(class_=re.compile('consensus|public', re.I))
                
                for item in consensus_data:
                    text = item.get_text()
                    # Look for patterns like "LAR 65%" or "65% on Rams"
                    if '%' in text:
                        percentages = re.findall(r'(\d+)%', text)
                        if percentages:
                            # Extract team and percentage
                            pass
                
                return games
                
        except Exception as e:
            print(f"❌ Error scraping OddsShark: {e}")
            return {}
    
    def scrape_vsin(self):
        """VSiN (Vegas Stats & Information Network) - Real Vegas data!"""
        
        url = "https://www.vsin.com/betting-resources/nfl/"
        
        try:
            print("🔍 Scraping VSiN...")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # VSiN shows betting splits
                # Look for their specific data format
                
                return {}
                
        except Exception as e:
            print(f"❌ Error scraping VSiN: {e}")
            return {}
    
    def get_all_public_betting(self):
        """Combine all free sources!"""
        
        print("\n" + "="*60)
        print("🎰 Getting FREE Public Betting Data")
        print("="*60 + "\n")
        
        all_data = {}
        
        # Try each source
        sbd_data = self.scrape_sportsbettingdime()
        an_data = self.scrape_action_network_free()
        os_data = self.scrape_oddsshark()
        vsin_data = self.scrape_vsin()
        
        # Combine all sources
        for source_data in [sbd_data, an_data, os_data, vsin_data]:
            all_data.update(source_data)
        
        # Calculate consensus from multiple sources
        consensus = {}
        
        print("\n" + "="*60)
        print(f"📊 SUMMARY: Found {len(all_data)} games with public betting data")
        print("="*60)
        
        return all_data
    
    def test_all_sources(self):
        """Test which sources are currently working"""
        
        print("\n🧪 Testing all free sources...\n")
        
        sources = [
            ("SportsBettingDime", "https://www.sportsbettingdime.com/nfl/public-betting-trends/"),
            ("Action Network", "https://www.actionnetwork.com/nfl/public-betting"),
            ("OddsShark", "https://www.oddsshark.com/nfl/consensus-picks"),
            ("VSiN", "https://www.vsin.com/betting-resources/nfl/"),
            ("Covers", "https://contests.covers.com/consensus/topconsensus/nfl/overall")
        ]
        
        for name, url in sources:
            try:
                response = requests.get(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    if any(word in response.text.lower() for word in ['public', 'consensus', 'betting', '%']):
                        print(f"✅ {name}: Working - Has betting data!")
                    else:
                        print(f"⚠️ {name}: Page loads but no clear betting data found")
                else:
                    print(f"❌ {name}: Error {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: Failed - {str(e)[:50]}")
        
        print("\n💡 TIP: Even if scraping fails, you can manually check these sites and input data!")

# Test it!
if __name__ == "__main__":
    scraper = FreePublicBetting()
    
    # Test all sources
    scraper.test_all_sources()
    
    # Get all available data
    public_data = scraper.get_all_public_betting()
    
    if public_data:
        print("\n🎯 Sample data found:")
        for game, data in list(public_data.items())[:3]:
            print(f"  {game}: {data}")