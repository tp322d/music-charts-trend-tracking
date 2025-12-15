#!/usr/bin/env python3
"""
Script to fetch real music chart data from public APIs and import to the system.
"""
import requests
import sys
import os
from datetime import date

# Add parent directory to path to import from api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.app.services.external_api_service import ExternalAPIService


def login(api_url: str, username: str, password: str) -> str:
    """Login and get access token."""
    response = requests.post(
        f"{api_url}/api/v1/auth/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")


def register_user(api_url: str, username: str, password: str, email: str, role: str = "editor"):
    """Register a new user."""
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }
    
    response = requests.post(f"{api_url}/api/v1/auth/register", json=user_data)
    if response.status_code == 201:
        return True
    elif response.status_code == 400:
        # User might already exist
        return False
    else:
        raise Exception(f"Registration failed: {response.text}")


def import_entries(api_url: str, token: str, entries):
    """Import chart entries to API."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Convert ChartEntryCreate objects to dicts
    entries_dict = [entry.model_dump() for entry in entries]
    
    print(f"Importing {len(entries_dict)} entries...")
    
    # Import in batches of 100
    batch_size = 100
    total_imported = 0
    
    for i in range(0, len(entries_dict), batch_size):
        batch = entries_dict[i:i + batch_size]
        
        response = requests.post(
            f"{api_url}/api/v1/charts/batch",
            json={"entries": batch, "validate_duplicates": True},
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            imported = result.get("imported", 0)
            skipped = result.get("skipped", 0)
            total_imported += imported
            print(f"Batch {i//batch_size + 1}: Imported {imported}, Skipped {skipped}")
        else:
            print(f"Error in batch {i//batch_size + 1}: {response.status_code} - {response.text}")
    
    print(f"\nTotal imported: {total_imported} entries")
    return total_imported


def main():
    """Main function."""
    if len(sys.argv) < 4:
        print("Usage: python fetch_real_data.py <api_url> <username> <password> [source] [country]")
        print("\nSources:")
        print("  all - Fetch from all available sources (default)")
        print("  itunes - Fetch from iTunes Charts (no API key required)")
        print("  lastfm - Fetch from Last.fm (requires LASTFM_API_KEY)")
        print("  youtube - Fetch from YouTube Music (requires YOUTUBE_API_KEY)")
        print("\nExamples:")
        print("  python fetch_real_data.py http://localhost:8000 admin admin123")
        print("  python fetch_real_data.py http://localhost:8000 admin admin123 itunes US")
        sys.exit(1)
    
    api_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    source = sys.argv[4] if len(sys.argv) > 4 else "all"
    country = sys.argv[5] if len(sys.argv) > 5 else "US"
    
    try:
        # Try to register user (might already exist)
        print(f"Registering/login user: {username}")
        register_user(api_url, username, password, f"{username}@example.com", "editor")
        
        # Login
        print("Logging in...")
        token = login(api_url, username, password)
        print("Authentication successful!\n")
        
        # Fetch data based on source
        entries = []
        
        if source == "all":
            print("Fetching data from all available sources...")
            entries = ExternalAPIService.fetch_all_sources(country)
        elif source == "itunes":
            print(f"Fetching iTunes top songs for country: {country}...")
            entries = ExternalAPIService.fetch_itunes_top_songs(country.lower(), limit=200)
        elif source == "lastfm":
            print("Fetching Last.fm top tracks...")
            entries = ExternalAPIService.fetch_lastfm_top_tracks(limit=50)
        elif source == "youtube":
            print(f"Fetching YouTube Music trending for region: {country}...")
            entries = ExternalAPIService.fetch_youtube_music_trending(region=country, limit=50)
        else:
            print(f"Unknown source: {source}")
            sys.exit(1)
        
        if not entries:
            print("\nNo data fetched. Please check:")
            print("1. API keys are set (for Last.fm and YouTube)")
            print("2. Internet connection is available")
            print("3. API endpoints are accessible")
            sys.exit(1)
        
        print(f"\nFetched {len(entries)} chart entries")
        
        # Import to API
        imported = import_entries(api_url, token, entries)
        
        print(f"\n✅ Successfully imported {imported} real chart entries!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

