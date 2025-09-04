#!/usr/bin/env python3
"""
REAL DATA SCRAPER - NO MOCK DATA
Scrapes actual injury reports and public betting from multiple sources
"""

import requests
from bs4 import BeautifulSoup
try:
    import lxml
except ImportError:
    lxml = None
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import time

class RealDataScraper:
    """Fetches REAL injury and betting data from multiple sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.timeout = 3  # Reduced to prevent hanging
    
    def get_nfl_injuries(self, team_name: str) -> Dict:
        """Scrape NFL.com injury reports - REAL DATA"""
        
        injuries = {
            'out': [],
            'doubtful': [],
            'questionable': [],
            'impact_score': 0
        }
        
        # Convert team name to NFL.com format
        team_mappings = {
            'Cardinals': 'arizona-cardinals',
            'Falcons': 'atlanta-falcons', 
            'Ravens': 'baltimore-ravens',
            'Bills': 'buffalo-bills',
            'Panthers': 'carolina-panthers',
            'Bears': 'chicago-bears',
            'Bengals': 'cincinnati-bengals',
            'Browns': 'cleveland-browns',
            'Cowboys': 'dallas-cowboys',
            'Broncos': 'denver-broncos',
            'Lions': 'detroit-lions',
            'Packers': 'green-bay-packers',
            'Texans': 'houston-texans',
            'Colts': 'indianapolis-colts',
            'Jaguars': 'jacksonville-jaguars',
            'Chiefs': 'kansas-city-chiefs',
            'Raiders': 'las-vegas-raiders',
            'Chargers': 'los-angeles-chargers',
            'Rams': 'los-angeles-rams',
            'Dolphins': 'miami-dolphins',
            'Vikings': 'minnesota-vikings',
            'Patriots': 'new-england-patriots',
            'Saints': 'new-orleans-saints',
            'Giants': 'new-york-giants',
            'Jets': 'new-york-jets',
            'Eagles': 'philadelphia-eagles',
            'Steelers': 'pittsburgh-steelers',
            '49ers': 'san-francisco-49ers',
            'Seahawks': 'seattle-seahawks',
            'Buccaneers': 'tampa-bay-buccaneers',
            'Titans': 'tennessee-titans',
            'Commanders': 'washington-commanders',
            'Washington': 'washington-commanders'
        }
        
        # Get team slug
        team_slug = None
        for key, value in team_mappings.items():
            if key.lower() in team_name.lower() or team_name.lower() in key.lower():
                team_slug = value
                break
        
        if not team_slug:
            # Try to find partial match
            team_parts = team_name.split()
            for part in team_parts:
                for key, value in team_mappings.items():
                    if part.lower() in key.lower():
                        team_slug = value
                        break
                if team_slug:
                    break
        
        if team_slug:
            try:
                # Try NFL.com injury report page
                url = f"https://www.nfl.com/teams/{team_slug}/injuries"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    # Handle encoding issues
                    try:
                        soup = BeautifulSoup(response.content, 'lxml')
                    except:
                        soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for injury table
                    injury_rows = soup.find_all('tr', class_='nfl-o-roster__player')
                    if not injury_rows:
                        # Alternative selectors
                        injury_rows = soup.find_all('tr', {'data-idx': True})
                    
                    for row in injury_rows[:15]:  # Limit to prevent too many
                        try:
                            # Extract player name
                            name_elem = row.find('a', class_='nfl-o-roster__player-name')
                            if not name_elem:
                                name_elem = row.find('td', class_='player')
                            
                            if name_elem:
                                player_name = name_elem.get_text(strip=True)
                                
                                # Extract status
                                status_elem = row.find('span', class_='nfl-o-roster__player-status')
                                if not status_elem:
                                    status_elem = row.find('td', class_='status')
                                
                                if status_elem:
                                    status = status_elem.get_text(strip=True).lower()
                                    
                                    # Categorize by status
                                    if 'out' in status or 'ir' in status:
                                        injuries['out'].append(player_name)
                                        injuries['impact_score'] += 3
                                    elif 'doubtful' in status:
                                        injuries['doubtful'].append(player_name)
                                        injuries['impact_score'] += 2
                                    elif 'questionable' in status or 'quest' in status:
                                        injuries['questionable'].append(player_name)
                                        injuries['impact_score'] += 1
                        except:
                            continue
                    
                    # If no rows found, try scraping from the main text
                    if not injury_rows:
                        text = soup.get_text()
                        # Look for injury keywords
                        if 'out:' in text.lower():
                            out_section = text.lower().split('out:')[1].split('\n')[0]
                            injuries['out'] = [p.strip() for p in out_section.split(',') if p.strip()][:3]
                            injuries['impact_score'] += len(injuries['out']) * 3
                
            except Exception as e:
                print(f"Error scraping NFL.com for {team_name}: {e}")
        
        # Fallback: Try ESPN as secondary source
        if injuries['impact_score'] == 0:
            injuries = self.scrape_espn_injuries(team_name)
        
        return injuries
    
    def scrape_espn_injuries(self, team_name: str) -> Dict:
        """Scrape ESPN injury page as fallback"""
        
        injuries = {
            'out': [],
            'doubtful': [],
            'questionable': [],
            'impact_score': 0
        }
        
        try:
            # ESPN team ID mapping
            espn_ids = {
                'Cardinals': 'ARI', 'Falcons': 'ATL', 'Ravens': 'BAL',
                'Bills': 'BUF', 'Panthers': 'CAR', 'Bears': 'CHI',
                'Bengals': 'CIN', 'Browns': 'CLE', 'Cowboys': 'DAL',
                'Broncos': 'DEN', 'Lions': 'DET', 'Packers': 'GB',
                'Texans': 'HOU', 'Colts': 'IND', 'Jaguars': 'JAX',
                'Chiefs': 'KC', 'Raiders': 'LV', 'Chargers': 'LAC',
                'Rams': 'LAR', 'Dolphins': 'MIA', 'Vikings': 'MIN',
                'Patriots': 'NE', 'Saints': 'NO', 'Giants': 'NYG',
                'Jets': 'NYJ', 'Eagles': 'PHI', 'Steelers': 'PIT',
                '49ers': 'SF', 'Seahawks': 'SEA', 'Buccaneers': 'TB',
                'Titans': 'TEN', 'Commanders': 'WSH', 'Washington': 'WSH'
            }
            
            team_abbr = None
            for key, value in espn_ids.items():
                if key.lower() in team_name.lower() or team_name.lower() in key.lower():
                    team_abbr = value
                    break
            
            if team_abbr:
                url = f"https://www.espn.com/nfl/team/injuries/_/name/{team_abbr}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    # Handle encoding issues
                    try:
                        soup = BeautifulSoup(response.content, 'lxml')
                    except:
                        soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for injury table rows
                    rows = soup.find_all('tr', class_='Table__TR')
                    
                    for row in rows[:10]:
                        try:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                player = cells[0].get_text(strip=True)
                                status = cells[2].get_text(strip=True).lower()
                                
                                if 'out' in status:
                                    injuries['out'].append(player)
                                    injuries['impact_score'] += 3
                                elif 'doubtful' in status:
                                    injuries['doubtful'].append(player)
                                    injuries['impact_score'] += 2
                                elif 'questionable' in status:
                                    injuries['questionable'].append(player)
                                    injuries['impact_score'] += 1
                        except:
                            continue
        
        except Exception as e:
            print(f"ESPN injury scrape failed for {team_name}: {e}")
        
        return injuries
    
    def get_all_public_betting(self, away_team: str, home_team: str) -> Dict:
        """Get public betting from ALL available sources"""
        
        all_percentages = []
        sources_used = []
        
        # 1. Action Network
        action_data = self.scrape_action_network(away_team, home_team)
        if action_data and action_data.get('percentage'):
            all_percentages.append(action_data['percentage'])
            sources_used.append('Action Network')
        
        # 2. Covers.com with better scraping
        covers_data = self.scrape_covers_better(away_team, home_team)
        if covers_data and covers_data.get('percentage'):
            all_percentages.append(covers_data['percentage'])
            sources_used.append('Covers.com')
        
        # 3. OddsShark
        odds_shark = self.scrape_odds_shark(away_team, home_team)
        if odds_shark and odds_shark.get('percentage'):
            all_percentages.append(odds_shark['percentage'])
            sources_used.append('OddsShark')
        
        # 4. SportsInsights (if available)
        sports_insights = self.scrape_sports_insights(away_team, home_team)
        if sports_insights and sports_insights.get('percentage'):
            all_percentages.append(sports_insights['percentage'])
            sources_used.append('SportsInsights')
        
        # 5. VSiN consensus
        vsin_data = self.scrape_vsin(away_team, home_team)
        if vsin_data and vsin_data.get('percentage'):
            all_percentages.append(vsin_data['percentage'])
            sources_used.append('VSiN')
        
        # Calculate consensus
        if all_percentages:
            avg_percentage = sum(all_percentages) / len(all_percentages)
            home_pct = round(avg_percentage) if avg_percentage > 50 else round(100 - avg_percentage)
            away_pct = 100 - home_pct
            
            return {
                'home_percentage': home_pct,
                'away_percentage': away_pct,
                'public_on_home': home_pct > away_pct,
                'public_percentage': max(home_pct, away_pct),
                'sources_count': len(sources_used),
                'sources': sources_used,
                'confidence': 'HIGH' if len(sources_used) >= 3 else 'MEDIUM' if len(sources_used) >= 2 else 'LOW'
            }
        
        # If no data, use spread-based estimate (but mark as estimated)
        return self.estimate_from_spread(away_team, home_team)
    
    def scrape_action_network(self, away_team: str, home_team: str) -> Optional[Dict]:
        """Scrape Action Network public betting"""
        try:
            # Search for the game
            search_term = f"{away_team} {home_team}"
            url = f"https://www.actionnetwork.com/nfl/public-betting"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                # Handle encoding issues
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for betting percentage elements
                percentages = soup.find_all('span', class_='public-betting-percentage')
                teams = soup.find_all('span', class_='team-name')
                
                for i, team_elem in enumerate(teams):
                    team_text = team_elem.get_text(strip=True)
                    if away_team.lower() in team_text.lower() or home_team.lower() in team_text.lower():
                        if i < len(percentages):
                            pct_text = percentages[i].get_text(strip=True)
                            pct = int(re.findall(r'\d+', pct_text)[0])
                            return {'percentage': pct, 'source': 'Action Network'}
        except Exception as e:
            print(f"Action Network scrape failed: {e}")
        
        return None
    
    def scrape_covers_better(self, away_team: str, home_team: str) -> Optional[Dict]:
        """Improved Covers.com scraping"""
        try:
            # Try multiple URLs
            urls = [
                "https://www.covers.com/sports/nfl/matchups",
                "https://contests.covers.com/consensus/topconsensus/nfl/overall",
                f"https://www.covers.com/sport/football/nfl/consensus-picks"
            ]
            
            for url in urls:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                if response.status_code == 200:
                    # Handle encoding issues
                    try:
                        soup = BeautifulSoup(response.content, 'lxml')
                    except:
                        soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for consensus data
                    consensus_elements = soup.find_all('div', class_='covers-CoversConsensusDetailsCard-consensus')
                    if not consensus_elements:
                        consensus_elements = soup.find_all('div', class_='consensus-pick')
                    
                    # Search for team names and percentages
                    text = soup.get_text()
                    
                    # Look for patterns like "Chiefs 67%"
                    for team in [away_team, home_team]:
                        pattern = rf"{team}[^\d]*(\d+)%"
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            return {'percentage': int(match.group(1)), 'source': 'Covers'}
                    
                    # Alternative: Look for any percentage near team name
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if away_team.lower() in line.lower() or home_team.lower() in line.lower():
                            # Check nearby lines for percentages
                            for j in range(max(0, i-2), min(len(lines), i+3)):
                                pct_match = re.search(r'(\d+)%', lines[j])
                                if pct_match:
                                    pct = int(pct_match.group(1))
                                    if 30 <= pct <= 100:
                                        return {'percentage': pct, 'source': 'Covers'}
                
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            print(f"Covers scrape failed: {e}")
        
        return None
    
    def scrape_odds_shark(self, away_team: str, home_team: str) -> Optional[Dict]:
        """Scrape OddsShark consensus"""
        try:
            url = "https://www.oddsshark.com/nfl/consensus-picks"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                # Handle encoding issues
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for consensus percentages
                consensus_cards = soup.find_all('div', class_='consensus-card')
                
                for card in consensus_cards:
                    card_text = card.get_text()
                    if away_team.lower() in card_text.lower() or home_team.lower() in card_text.lower():
                        pct_match = re.search(r'(\d+)%', card_text)
                        if pct_match:
                            return {'percentage': int(pct_match.group(1)), 'source': 'OddsShark'}
                
                # Alternative method
                percentages = soup.find_all('span', class_='percentage')
                teams = soup.find_all('span', class_='team')
                
                for i, team in enumerate(teams):
                    if away_team.lower() in team.get_text().lower() or home_team.lower() in team.get_text().lower():
                        if i < len(percentages):
                            pct_text = percentages[i].get_text(strip=True)
                            pct = int(re.findall(r'\d+', pct_text)[0])
                            return {'percentage': pct, 'source': 'OddsShark'}
                            
        except Exception as e:
            print(f"OddsShark scrape failed: {e}")
        
        return None
    
    def scrape_sports_insights(self, away_team: str, home_team: str) -> Optional[Dict]:
        """Scrape SportsInsights betting percentages"""
        try:
            url = "https://www.sportsinsights.com/betting-trends/nfl/"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                # Handle encoding issues
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for betting trend tables
                tables = soup.find_all('table', class_='betting-trends-table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        row_text = row.get_text()
                        if away_team.lower() in row_text.lower() or home_team.lower() in row_text.lower():
                            # Extract percentage
                            pct_match = re.search(r'(\d+)%', row_text)
                            if pct_match:
                                return {'percentage': int(pct_match.group(1)), 'source': 'SportsInsights'}
                                
        except Exception as e:
            print(f"SportsInsights scrape failed: {e}")
        
        return None
    
    def scrape_vsin(self, away_team: str, home_team: str) -> Optional[Dict]:
        """Scrape VSiN consensus"""
        try:
            url = "https://www.vsin.com/betting-resources/nfl/"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                # Handle encoding issues
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                
                # Look for team and percentage
                for team in [away_team, home_team]:
                    pattern = rf"{team}[^\d]*(\d+)%"
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return {'percentage': int(match.group(1)), 'source': 'VSiN'}
                        
        except Exception as e:
            print(f"VSiN scrape failed: {e}")
        
        return None
    
    def estimate_from_spread(self, away_team: str, home_team: str) -> Dict:
        """NO ESTIMATES - Return 50/50 when no data available"""
        return {
            'home_percentage': 50,
            'away_percentage': 50,
            'public_on_home': False,
            'public_percentage': 50,
            'sources_count': 0,
            'sources': [],
            'confidence': 'NONE'
        }