"""
Chart router for managing music chart entries.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional, List, Dict, Any
from datetime import date
import json
from app.schemas.chart import (
    ChartEntryCreate,
    ChartEntryUpdate,
    ChartEntryResponse,
    BatchResponse,
    ChartQueryParams,
    ChartTopQuery,
    ArtistQuery,
    ChartSource,
    TrendAnalysis,
    TrendQuery
)
from app.services.chart_service import ChartService
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.post("", response_model=ChartEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_chart_entry(
    request: Request,
    current_user: User = Depends(require_role(UserRole.EDITOR, UserRole.ADMIN))
):
    """
    Create a single chart entry.
    
    Requires Editor or Admin role.
    
    - **date**: Chart publication date
    - **rank**: Position in chart (1-200)
    - **song**: Song title
    - **artist**: Artist name
    - **source**: Platform (Apple Music)
    - **platform_data**: Optional platform-specific fields (JSON object)
    """
    body = await request.json()
    platform_data = body.pop("platform_data", None)
    entry = ChartEntryCreate(**body)
    if platform_data:
        object.__setattr__(entry, 'platform_data', platform_data)
    chart_service = ChartService()
    entry_dict = chart_service.create_entry(entry)
    return ChartEntryResponse(**entry_dict)


@router.post("/batch", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_chart_entries_batch(
    request: Request,
    current_user: User = Depends(require_role(UserRole.EDITOR, UserRole.ADMIN))
):
    """
    Import multiple chart entries in batch.
    
    Requires Editor or Admin role.
    Maximum 1000 entries per request.
    
    - **entries**: List of chart entries to import
    - **validate_duplicates**: Whether to check for duplicate entries
    """
    body = await request.json()
    entries_data = body.get("entries", [])
    validate_duplicates = body.get("validate_duplicates", True)
    
    if len(entries_data) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 entries per batch request"
        )
    
    entries = []
    for entry_data in entries_data:
        platform_data = entry_data.pop("platform_data", None)
        entry = ChartEntryCreate(**entry_data)
        if platform_data:
            object.__setattr__(entry, 'platform_data', platform_data)
        entries.append(entry)
    
    chart_service = ChartService()
    result = chart_service.create_batch(entries, validate_duplicates)
    return BatchResponse(**result)


@router.get("", response_model=List[ChartEntryResponse])
async def get_charts(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    filter_date: Optional[date] = Query(None, alias="date", description="Filter by specific date"),
    date_from: Optional[date] = Query(None, description="Filter from date (for date ranges)"),
    date_to: Optional[date] = Query(None, description="Filter to date (for date ranges)"),
    source: Optional[ChartSource] = Query(None, description="Filter by platform"),
    country: Optional[str] = Query(None, description="Filter by country"),
    artist: Optional[str] = Query(None, description="Filter by artist name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve chart entries with pagination and filtering.
    
    Requires authentication.
    
    - **limit**: Maximum number of entries to return (1-1000)
    - **offset**: Number of entries to skip
    - **date**: Filter by specific date (takes precedence over date_from/date_to)
    - **date_from**: Filter from date (for date ranges)
    - **date_to**: Filter to date (for date ranges)
    - **source**: Filter by platform
    - **country**: Filter by country code
    - **artist**: Filter by artist name (case-insensitive)
    """
    chart_service = ChartService()
    source_str = source.value if source else None
    entries = chart_service.get_entries_direct(
        limit=limit,
        offset=offset,
        filter_date=filter_date,
        date_from=date_from,
        date_to=date_to,
        source=source_str,
        country=country,
        artist=artist
    )
    return [ChartEntryResponse(**entry) for entry in entries]


@router.get("/top", response_model=List[ChartEntryResponse])
async def get_top_charts(
    date: date = Query(..., description="Date for top charts"),
    limit: int = Query(default=10, ge=1, le=100),
    source: Optional[ChartSource] = Query(None, description="Filter by platform"),
    country: Optional[str] = Query(None, description="Filter by country"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get top songs for a specific date.
    
    Requires authentication.
    Returns entries sorted by rank.
    
    - **date**: Required date for top charts
    - **limit**: Maximum number of entries (1-100)
    - **source**: Optional platform filter
    - **country**: Optional country filter
    """
    query = ChartTopQuery(date=date, limit=limit, source=source, country=country)
    chart_service = ChartService()
    entries = chart_service.get_top_charts(query)
    return [ChartEntryResponse(**entry) for entry in entries]


@router.get("/artist/{artist_name}", response_model=List[ChartEntryResponse])
async def get_artist_history(
    artist_name: str,
    date_from: Optional[date] = Query(None, description="Start date for history"),
    date_to: Optional[date] = Query(None, description="End date for history"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all chart appearances for an artist.
    
    Requires authentication.
    Returns entries sorted by date (newest first) and rank.
    
    - **artist_name**: Artist name (URL encoded)
    - **date_from**: Optional start date
    - **date_to**: Optional end date
    """
    from datetime import datetime
    chart_service = ChartService()
    date_from_dt = datetime.combine(date_from, datetime.min.time()) if date_from else None
    date_to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None
    entries = chart_service.get_artist_history(artist_name, date_from_dt, date_to_dt)
    return [ChartEntryResponse(**entry) for entry in entries]


@router.get("/{entry_id}", response_model=ChartEntryResponse)
async def get_chart_entry(
    entry_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a single chart entry by ID.
    
    Requires authentication.
    """
    chart_service = ChartService()
    entry = chart_service.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart entry not found"
        )
    return ChartEntryResponse(**entry)


@router.put("/{entry_id}", response_model=ChartEntryResponse)
async def update_chart_entry(
    entry_id: str,
    request: Request,
    current_user: User = Depends(require_role(UserRole.EDITOR, UserRole.ADMIN))
):
    """
    Update an existing chart entry.
    
    Requires Editor or Admin role.
    Only provided fields will be updated (partial update).
    """
    body = await request.json()
    platform_data = body.pop("platform_data", None)
    update_data = ChartEntryUpdate(**body)
    if platform_data:
        object.__setattr__(update_data, 'platform_data', platform_data)
    
    chart_service = ChartService()
    entry = chart_service.update_entry(entry_id, update_data)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart entry not found"
        )
    return ChartEntryResponse(**entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chart_entry(
    entry_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete a chart entry.
    
    Requires Admin role.
    """
    chart_service = ChartService()
    deleted = chart_service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart entry not found"
        )
    return None

