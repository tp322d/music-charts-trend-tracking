#!/usr/bin/env python3
"""
Script to generate test chart data.
"""
import requests
import random
import sys
from datetime import date, timedelta
from typing import List, Dict


def generate_test_entries(count: int = 100, start_date: date = None) -> List[Dict]:
    """Generate test chart entries."""
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    
    artists = ["Artist A", "Artist B", "Artist C", "Artist D", "Artist E",
               "Taylor Swift", "Ed Sheeran", "Ariana Grande", "The Weeknd", "Billie Eilish"]
    songs = ["Song One", "Song Two", "Song Three", "Song Four", "Song Five",
             "Shake It Off", "Shape of You", "Thank U, Next", "Blinding Lights", "Bad Guy"]
    sources = ["Spotify", "Apple Music", "YouTube Music"]
    
    entries = []
    current_date = start_date
    
    for i in range(count):
        entry = {
            "date": current_date.isoformat(),
            "rank": (i % 200) + 1,
            "song": random.choice(songs),
            "artist": random.choice(artists),
            "album": f"Album {random.randint(1, 5)}",
            "streams": random.randint(100000, 10000000),
            "duration_ms": random.randint(180000, 240000),
            "source": random.choice(sources),
            "country": "Global"
        }
        
        if entry["source"] == "Spotify":
            entry["platform_data"] = {"popularity_score": random.randint(0, 100)}
        elif entry["source"] == "YouTube Music":
            entry["platform_data"] = {"view_count": random.randint(1000000, 100000000)}
        
        entries.append(entry)
        
        if (i + 1) % 10 == 0:
            current_date += timedelta(days=1)
    
    return entries


def import_test_data(api_url: str, token: str, entries: List[Dict]):
    """Import test data to API."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Importing {len(entries)} test entries...")
    
    response = requests.post(
        f"{api_url}/api/v1/charts/batch",
        json={"entries": entries, "validate_duplicates": False},
        headers=headers
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"Successfully imported {result.get('imported', 0)} entries")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def register_test_user(api_url: str) -> tuple:
    """Register a test user."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "editor"
    }
    
    response = requests.post(f"{api_url}/api/v1/auth/register", json=user_data)
    if response.status_code == 201:
        return (user_data["username"], user_data["password"])
    else:
        return (user_data["username"], user_data["password"])


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


def main():
    """Main function."""
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    try:
        print("Setting up test user...")
        username, password = register_test_user(api_url)
        token = login(api_url, username, password)
        print("Authentication successful!")
        
        print(f"Generating {count} test entries...")
        entries = generate_test_entries(count)
        
        import_test_data(api_url, token, entries)
        
        print("Test data generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

