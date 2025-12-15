"""
Service for fetching real music chart data from external APIs.
"""
import requests
from typing import List
from datetime import date
from app.schemas.chart import ChartEntryCreate, ChartSource


class ExternalAPIService:
    """Service for fetching real chart data from iTunes Charts API."""
    
    @staticmethod
    def fetch_itunes_top_songs(country: str = "us", limit: int = 200) -> List[ChartEntryCreate]:
        """
        Fetch top songs from iTunes Store Charts (free, no authentication required).
        
        Country codes: us, gb, de, fr, jp, etc.
        """
        try:
            url = "https://itunes.apple.com/rss/topsongs/limit=200/json"
            if country != "us":
                # iTunes has country-specific feeds
                url = f"https://itunes.apple.com/{country}/rss/topsongs/limit=200/json"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                entries = []
                today = date.today()
                
                feed = data.get("feed", {})
                songs = feed.get("entry", [])
                
                for idx, song in enumerate(songs[:limit], start=1):
                    try:
                        song_name = song.get("im:name", {}).get("label", "")
                        artist_name = song.get("im:artist", {}).get("label", "")
                        album_name = song.get("im:collection", {}).get("im:name", {}).get("label", "")
                        
                        entry = ChartEntryCreate(
                            date=today,
                            rank=idx,
                            song=song_name,
                            artist=artist_name,
                            album=album_name,
                            source=ChartSource.APPLE_MUSIC,
                            country=country.upper(),
                            platform_data={
                                "itunes_id": song.get("id", {}).get("attributes", {}).get("im:id", ""),
                                "itunes_url": song.get("id", {}).get("label", ""),
                                "category": song.get("category", {}).get("attributes", {}).get("label", ""),
                                "release_date": song.get("im:releaseDate", {}).get("label", "")
                            }
                        )
                        entries.append(entry)
                    except Exception as e:
                        print(f"Error processing iTunes song {idx}: {str(e)}")
                        continue
                
                return entries
            else:
                print(f"iTunes API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching iTunes data: {str(e)}")
            return []
    
    @staticmethod
    def fetch_all_sources(country: str = "US") -> List[ChartEntryCreate]:
        """
        Fetch chart data from iTunes Charts.
        
        This method exists for compatibility but only fetches from iTunes.
        """
        print("Fetching iTunes top songs...")
        itunes_entries = ExternalAPIService.fetch_itunes_top_songs(country.lower(), limit=200)
        print(f"Fetched {len(itunes_entries)} entries from iTunes")
        return itunes_entries
