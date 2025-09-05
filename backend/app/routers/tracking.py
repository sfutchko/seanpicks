#!/usr/bin/env python3
"""
API endpoints for bet tracking and performance
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.database.connection import get_db
from app.services.bet_tracker import BetTracker, ResultFetcher
from app.models.bet_tracking import TrackedBet
# Authentication removed - public access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.post("/track-bet")
async def track_bet(
    game: Dict,
    analysis: Dict,
    db: Session = Depends(get_db),
):
    """
    Track a best bet
    """
    tracker = BetTracker(db)
    bet = tracker.track_best_bet(game, analysis)
    return {"message": "Bet tracked successfully", "bet_id": bet.id}


@router.post("/snapshot")
async def create_snapshot(
    best_bets: List[Dict],
    sport: str = "NFL",
    db: Session = Depends(get_db),
):
    """
    Create a snapshot of current best bets
    """
    tracker = BetTracker(db)
    snapshot = tracker.create_snapshot(best_bets, sport)
    return {
        "message": "Snapshot created",
        "snapshot_id": snapshot.id,
        "total_bets": snapshot.total_bets
    }


@router.get("/performance")
async def get_performance(
    days: int = 7,
    sport: str = "NFL",
    demo: bool = False,
    db: Session = Depends(get_db),
):
    """
    Get performance statistics for a specific sport
    """
    # Return demo data if requested or if no real data exists
    tracker = BetTracker(db)
    stats = tracker.get_performance_stats(days, sport)
    
    # If no real data, return zeros (no fake stats)
    if stats.get("total_bets", 0) == 0:
        return {
            "record": "0-0",
            "win_rate": 0,
            "units": 0,
            "roi": 0,
            "total_bets": 0,
            "by_confidence": {
                "high": {"record": "0-0", "count": 0},
                "medium": {"record": "0-0", "count": 0},
                "low": {"record": "0-0", "count": 0}
            }
        }
    
    return stats


@router.get("/pending")
async def get_pending_bets(
    sport: str = "NFL",
    db: Session = Depends(get_db),
):
    """
    Get all pending tracked bets for a specific sport
    """
    tracker = BetTracker(db)
    pending = tracker.get_pending_bets(sport)
    
    return [
        {
            "game_id": bet.game_id,
            "game": f"{bet.away_team} @ {bet.home_team}",
            "pick": bet.pick,
            "spread": bet.spread,
            "confidence": bet.confidence,
            "game_time": bet.game_time.isoformat(),
            "first_seen": bet.first_seen.isoformat(),
            "times_appeared": bet.times_appeared,
            "sport": bet.sport.lower() if bet.sport else 'nfl'
        }
        for bet in pending
    ]


@router.get("/results")
async def get_recent_results(
    limit: int = 20,
    sport: str = "NFL",
    demo: bool = False,
    db: Session = Depends(get_db),
):
    """
    Get recent bet results for a specific sport
    """
    tracker = BetTracker(db)
    results = tracker.get_recent_results(limit, sport)
    
    # Return empty array if no real data (no fake scores)
    if len(results) == 0:
        return []
    
    return results


@router.post("/update-scores")
async def update_scores(
    sport: str = "americanfootball_nfl",
    db: Session = Depends(get_db),
):
    """
    Fetch and update game scores for tracked bets
    Uses improved date matching to get the right games
    """
    from app.services.score_updater import ScoreUpdater
    
    # Note: NFL scores from Odds API appear unreliable
    # MLB scores are more accurate when matched by date
    updater = ScoreUpdater("d4fa91883b15fd5a5594c64e58b884ef", db)
    result = await updater.update_scores(sport)
    
    if result.get('errors'):
        logger.warning(f"Score update errors: {result['errors']}")
    
    return result


from pydantic import BaseModel

class TrackBetsRequest(BaseModel):
    games: List[Dict]
    sport: str = "NFL"

@router.post("/track-current-best-bets")
async def track_current_best_bets(
    request: TrackBetsRequest,
    db: Session = Depends(get_db),
):
    """
    Track all current best bets from the dashboard
    Only tracks games with confidence >= 55% (best bets)
    No time restrictions - tracks all best bets regardless of game time
    """
    tracker = BetTracker(db)
    tracked_count = 0
    tracked_games = []
    games = request.games
    
    for game in games:
        # Only track best bets (55% confidence or higher)
        if game.get('confidence', 0) >= 0.55:
            try:
                bet = tracker.track_best_bet(game, game, sport=request.sport)
                tracked_count += 1
                tracked_games.append(game)
                logger.info(f"Tracked bet: {game.get('away_team')} @ {game.get('home_team')} - Confidence: {game.get('confidence', 0) * 100:.1f}%")
            except Exception as e:
                logger.error(f"Failed to track bet for {game.get('id')}: {e}")
    
    # Create a snapshot only of tracked best bets
    if tracked_games:
        snapshot = tracker.create_snapshot(tracked_games, request.sport)
        return {
            "message": f"Tracked {tracked_count} best bets",
            "snapshot_id": snapshot.id,
            "tracked_bets": [
                {
                    "game": f"{g.get('away_team')} @ {g.get('home_team')}",
                    "confidence": f"{g.get('confidence', 0) * 100:.1f}%",
                    "pick": g.get('pick')
                }
                for g in tracked_games
            ]
        }
    
    return {
        "message": "No best bets to track (all games below 55% confidence)",
        "tracked_count": 0
    }


@router.get("/history/{game_id}")
async def get_bet_history(
    game_id: str,
    db: Session = Depends(get_db),
):
    """
    Get tracking history for a specific game
    """
    bet = db.query(TrackedBet).filter_by(game_id=game_id).first()
    
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    return {
        "game": f"{bet.away_team} @ {bet.home_team}",
        "pick": bet.pick,
        "spread": bet.spread,
        "confidence": bet.confidence,
        "first_seen": bet.first_seen.isoformat(),
        "last_seen": bet.last_seen.isoformat(),
        "times_appeared": bet.times_appeared,
        "result": bet.result,
        "score": f"{bet.away_score}-{bet.home_score}" if bet.home_score else None,
        "actual_spread": bet.actual_spread
    }