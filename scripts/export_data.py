#!/usr/bin/env python3
"""
Script to export chart data from API to CSV file.
"""
import csv
import requests
import sys
from datetime import date, timedelta
from typing import List, Dict


def export_data(api_url: str, token: str, output_file: str, 
                date_filter: str = None, source: str = None, limit: int = 10000):
    """Export data from API to CSV file."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    
    if date_filter:
        params["date"] = date_filter
    if source:
        params["source"] = source
    
    print(f"Fetching data from API...")
    response = requests.get(
        f"{api_url}/api/v1/charts",
        params=params,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code} - {response.text}")
        return False
    
    entries = response.json()
    print(f"Retrieved {len(entries)} entries")
    
    if not entries:
        print("No data to export")
        return False
    
    fieldnames = ["id", "date", "rank", "song", "artist", "album", 
                  "streams", "duration_ms", "source", "country", "created_at"]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in entries:
            row = {
                "id": entry.get("id"),
                "date": entry.get("date"),
                "rank": entry.get("rank"),
                "song": entry.get("song"),
                "artist": entry.get("artist"),
                "album": entry.get("album"),
                "streams": entry.get("streams"),
                "duration_ms": entry.get("duration_ms"),
                "source": entry.get("source"),
                "country": entry.get("country"),
                "created_at": entry.get("created_at")
            }
            writer.writerow(row)
    
    print(f"Data exported to {output_file}")
    return True


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
    if len(sys.argv) < 5:
        print("Usage: python export_data.py <api_url> <username> <password> <output_file> [date] [source]")
        sys.exit(1)
    
    api_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    output_file = sys.argv[4]
    date_filter = sys.argv[5] if len(sys.argv) > 5 else None
    source = sys.argv[6] if len(sys.argv) > 6 else None
    
    try:
        print("Logging in...")
        token = login(api_url, username, password)
        print("Login successful!")
        
        export_data(api_url, token, output_file, date_filter, source)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

