"""
Trend analysis router for chart analytics.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.schemas.chart import TrendAnalysis, TrendQuery, ChartSource
from app.services.chart_service import ChartService
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("/top-artists")
async def get_top_artists(
    days: int = Query(default=30, ge=1, le=365, description="Analysis period in days"),
    source: Optional[ChartSource] = Query(None, description="Filter by platform"),
    min_appearances: int = Query(default=1, ge=1, description="Minimum chart appearances"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get top artists over a time period.
    """
    chart_service = ChartService()
    source_str = source.value if source else None
    trends = chart_service.get_trend_analysis(days, source_str, min_appearances)
    return trends


@router.get("/rising")
async def get_rising_songs(
    period: int = Query(default=7, ge=1, le=90, description="Comparison period in days"),
    min_climb: int = Query(default=10, ge=1, description="Minimum rank improvement"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get fastest climbing songs (not implemented).
    """
    return []


@router.get("/comparison")
async def get_platform_comparison(
    dimension: str = Query(..., description="Comparison dimension: 'source' or 'country'"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare platforms or countries (not implemented).
    """
    return {"message": "Feature not yet implemented"}

