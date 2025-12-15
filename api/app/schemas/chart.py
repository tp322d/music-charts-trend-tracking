"""
Pydantic schemas for chart-related requests and responses.
"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import date, datetime
from enum import Enum
# Removed from __future__ import annotations to avoid recursion issues


class ChartSource(str, Enum):
    """Chart source/platform enumeration."""
    APPLE_MUSIC = "Apple Music"


class ChartEntryBase(BaseModel):
    """Base chart entry schema."""
    date: date
    rank: int
    song: str
    artist: str
    album: Optional[str] = None
    streams: Optional[int] = None
    duration_ms: Optional[int] = None
    source: ChartSource
    country: str = "Global"


class ChartEntryCreate(ChartEntryBase):
    """Schema for creating a chart entry."""
    # Note: platform_data is handled separately in the router to avoid Pydantic recursion issues
    pass


class ChartEntryUpdate(BaseModel):
    """Schema for updating a chart entry."""
    rank: Optional[int] = None
    song: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    streams: Optional[int] = None
    duration_ms: Optional[int] = None
    source: Optional[ChartSource] = None
    country: Optional[str] = None
    # platform_data handled separately in router


class ChartEntryResponse(BaseModel):
    """Schema for chart entry response."""
    id: str  # MongoDB ObjectId as string
    date: date
    rank: int
    song: str
    artist: str
    album: Optional[str] = None
    streams: Optional[int] = None
    duration_ms: Optional[int] = None
    source: ChartSource
    country: str
    created_at: datetime
    updated_at: datetime
    # platform_data included in response as dict from MongoDB


# ChartEntryBatch schema removed - batch creation now handled directly in router


class BatchResponse(BaseModel):
    """Schema for batch operation response."""
    imported: int
    skipped: int
    errors: List[str] = []


class ChartQueryParams(BaseModel):
    """Schema for chart query parameters."""
    limit: int = 100
    offset: int = 0
    date: Union[date, None] = None
    source: Optional[ChartSource] = None
    country: Optional[str] = None
    artist: Optional[str] = None


class ChartTopQuery(BaseModel):
    """Schema for top charts query."""
    date: date
    limit: int = 10
    source: Optional[ChartSource] = None
    country: Optional[str] = None


class ArtistQuery(BaseModel):
    """Schema for artist history query."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class TrendAnalysis(BaseModel):
    """Schema for trend analysis response."""
    artist: str
    period_days: int
    total_appearances: int
    average_rank: float
    best_rank: int
    worst_rank: int
    total_streams: Optional[int] = None
    trending_score: float


class TrendQuery(BaseModel):
    """Schema for trend analysis query."""
    days: int = 30
    source: Optional[ChartSource] = None
    min_appearances: int = 1

