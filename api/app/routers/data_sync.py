"""
Data synchronization router for fetching chart data from iTunes Charts API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date, timedelta
from app.services.external_api_service import ExternalAPIService
from app.services.chart_service import ChartService
from app.core.dependencies import require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/sync", tags=["Data Synchronization"])


@router.post("/fetch/all", status_code=status.HTTP_201_CREATED)
async def fetch_all_sources(
    country: str = "US",
    current_user: User = Depends(require_role(UserRole.EDITOR, UserRole.ADMIN))
):
    """
    Fetch chart data from iTunes Charts.
    
    Requires Editor or Admin role.
    No API key required - iTunes Charts is free and public.
    
    - **country**: Country code (default: US)
    """
    try:
        entries = ExternalAPIService.fetch_all_sources(country)
        
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No data fetched from iTunes Charts. Check network connectivity."
            )
        
        # Import entries
        chart_service = ChartService()
        result = chart_service.create_batch(entries, validate_duplicates=True)
        
        return {
            "message": "iTunes chart data fetched and imported successfully",
            "fetched": len(entries),
            "imported": result["imported"],
            "skipped": result["skipped"],
            "errors": result.get("errors", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )


@router.post("/fetch/itunes", status_code=status.HTTP_201_CREATED)
async def fetch_itunes(
    country: str = "us",
    limit: int = 200,
    days_back: int = 0,
    current_user: User = Depends(require_role(UserRole.EDITOR, UserRole.ADMIN))
):
    """
    Fetch top songs from iTunes Charts.
    
    Requires Editor or Admin role.
    No API key required - iTunes Charts is free and public.
    
    - **country**: Country code (default: us)
    - **limit**: Number of entries to fetch (default: 200, max: 200)
    - **days_back**: Number of days to create historical data for (0 = today only, 7 = last week, 30 = last month)
                      For demo purposes, creates entries for past days using today's chart data
    """
    try:
        entries = ExternalAPIService.fetch_itunes_top_songs(country, min(limit, 200))
        
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to fetch iTunes data"
            )
        
        chart_service = ChartService()
        
        # If days_back > 0, create historical entries for demo
        if days_back > 0:
            all_results = {
                "fetched": len(entries),
                "imported": 0,
                "skipped": 0
            }
            
            # Create entries for each day going back
            for day_offset in range(days_back + 1):  # +1 to include today
                target_date = date.today() - timedelta(days=day_offset)
                
                # Create entries with the target date
                dated_entries = []
                for entry in entries:
                    # Create a new entry with the target date
                    from app.schemas.chart import ChartEntryCreate
                    dated_entry = ChartEntryCreate(
                        date=target_date,
                        rank=entry.rank,
                        song=entry.song,
                        artist=entry.artist,
                        album=entry.album,
                        source=entry.source,
                        country=entry.country,
                        streams=entry.streams,
                        duration_ms=entry.duration_ms
                    )
                    # Copy platform_data if it exists
                    if hasattr(entry, 'platform_data') and entry.platform_data:
                        object.__setattr__(dated_entry, 'platform_data', entry.platform_data)
                    dated_entries.append(dated_entry)
                
                # Import entries for this date
                result = chart_service.create_batch(dated_entries, validate_duplicates=True)
                all_results["imported"] += result["imported"]
                all_results["skipped"] += result["skipped"]
            
            return {
                "message": f"iTunes data fetched and imported for {days_back + 1} days (today + {days_back} past days)",
                "fetched": all_results["fetched"],
                "imported": all_results["imported"],
                "skipped": all_results["skipped"],
                "days_created": days_back + 1
            }
        else:
            # Normal single-day fetch
            result = chart_service.create_batch(entries, validate_duplicates=True)
            return {
                "message": "iTunes data fetched and imported successfully",
                "fetched": len(entries),
                "imported": result["imported"],
                "skipped": result["skipped"]
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )
