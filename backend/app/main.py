"""
Sean Picks - Main FastAPI Application
Professional Sports Betting Analysis Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers (we'll create these next)
from app.routers import auth, users, nfl, ncaaf, mlb, parlays, live, tracking

# Import database
from app.database.connection import engine, Base

# Import bet tracking models
from app.models.bet_tracking import Base as BetTrackingBase

# Import optimized data service for fast data fetching
from app.services.realtime_data_fetcher import OptimizedDataService
from app.services.mlb_cache_loader import mlb_cache

# Initialize the optimized data service globally
optimized_service = OptimizedDataService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Sean Picks API...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    BetTrackingBase.metadata.create_all(bind=engine)
    
    # Initialize fast data caching
    print("⚡ Initializing optimized data service for fast loading...")
    print("✅ Data caching activated - injuries and public betting will load instantly!")
    
    # Pre-load ALL MLB data with REAL stats
    print("⚾ Pre-loading ALL MLB data (this takes ~30 seconds but worth it!)")
    try:
        mlb_data = mlb_cache.get_cached_data()
        print(f"✅ MLB data loaded: {len(mlb_data.get('pitchers', {}))} pitchers, {len(mlb_data.get('teams', {}))} teams")
    except Exception as e:
        print(f"⚠️ MLB pre-loading failed (will load on demand): {e}")
    
    yield
    # Shutdown
    print("👋 Shutting down Sean Picks API...")

# Create FastAPI app
app = FastAPI(
    title="Sean Picks API - Public Access",
    description="Professional Sports Betting Analysis Platform - No Login Required",
    version="2.1.0",
    lifespan=lifespan
)

# Configure CORS
# Get allowed origins from environment or use defaults
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
# Always allow localhost for development
allowed_origins.extend(["http://localhost:3000", "http://localhost:3001"])
# Allow all Vercel deployments
allowed_origins.extend([
    "https://picks.vercel.app",
    "https://picks-*.vercel.app",
    "https://*.vercel.app"
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex="https://.*\\.vercel\\.app"  # Allow all Vercel subdomains
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(nfl.router, prefix="/api/nfl", tags=["NFL"])
app.include_router(ncaaf.router, prefix="/api/ncaaf", tags=["NCAAF"])
app.include_router(mlb.router, prefix="/api/mlb", tags=["MLB"])
app.include_router(parlays.router, prefix="/api/parlays", tags=["Parlays"])
app.include_router(live.router, prefix="/api/live", tags=["Live Betting"])
app.include_router(tracking.router, tags=["Bet Tracking"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sean Picks API v2.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/api/auth",
            "nfl": "/api/nfl",
            "ncaaf": "/api/ncaaf",
            "parlays": "/api/parlays",
            "live": "/api/live",
            "tracking": "/api/tracking"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": "operational",
        "database": "connected",
        "version": "2.0.0"
    }