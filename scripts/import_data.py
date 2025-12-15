#!/usr/bin/env python3
"""
Script to import chart data from CSV file to the API.
"""
import csv
import requests
import sys
from typing import List, Dict
from datetime import datetime


def read_csv(file_path: str) -> List[Dict]:
    """Read chart entries from CSV file."""
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries


def convert_to_api_format(csv_row: Dict) -> Dict:
    """Convert CSV row to API format."""
    entry = {
        "date": csv_row.get("date", ""),
        "rank": int(csv_row.get("rank", 0)),
        "song": csv_row.get("song", ""),
        "artist": csv_row.get("artist", ""),
        "album": csv_row.get("album"),
        "source": csv_row.get("source", "Spotify"),
        "country": csv_row.get("country", "Global")
    }
    
    # Optional fields
    if csv_row.get("streams"):
        entry["streams"] = int(csv_row.get("streams"))
    if csv_row.get("duration_ms"):
        entry["duration_ms"] = int(csv_row.get("duration_ms"))
    
    return entry


def import_data(api_url: str, token: str, entries: List[Dict], batch_size: int = 100):
    """Import data to API in batches."""
    headers = {"Authorization": f"Bearer {token}"}
    total = len(entries)
    imported = 0
    failed = 0
    
    print(f"Starting import of {total} entries...")
    
    # Process in batches
    for i in range(0, total, batch_size):
        batch = entries[i:i + batch_size]
        batch_formatted = [convert_to_api_format(entry) for entry in batch]
        
        try:
            response = requests.post(
                f"{api_url}/api/v1/charts/batch",
                json={"entries": batch_formatted, "validate_duplicates": True},
                headers=headers
            )
            
            if response.status_code == 201:
                result = response.json()
                batch_imported = result.get("imported", 0)
                batch_skipped = result.get("skipped", 0)
                imported += batch_imported
                failed += batch_skipped
                print(f"Batch {i//batch_size + 1}: Imported {batch_imported}, Skipped {batch_skipped}")
            else:
                print(f"Error in batch {i//batch_size + 1}: {response.status_code} - {response.text}")
                failed += len(batch)
        except Exception as e:
            print(f"Exception in batch {i//batch_size + 1}: {str(e)}")
            failed += len(batch)
    
    print(f"\nImport completed: {imported} imported, {failed} skipped/failed")


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
        print("Usage: python import_data.py <api_url> <username> <password> <csv_file>")
        sys.exit(1)
    
    api_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    csv_file = sys.argv[4]
    
    try:
        # Login
        print("Logging in...")
        token = login(api_url, username, password)
        print("Login successful!")
        
        # Read CSV
        print(f"Reading CSV file: {csv_file}")
        entries = read_csv(csv_file)
        print(f"Found {len(entries)} entries")
        
        # Import data
        import_data(api_url, token, entries)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

