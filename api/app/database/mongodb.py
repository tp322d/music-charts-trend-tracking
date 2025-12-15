"""
MongoDB database connection and client management.
"""
from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings
from typing import Optional

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_mongodb_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        _client = MongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
    return _client


def get_mongodb_db() -> Database:
    """Get MongoDB database instance."""
    global _db
    if _db is None:
        client = get_mongodb_client()
        # Extract database name from URL or use default
        db_name = settings.MONGODB_URL.split("/")[-1].split("?")[0]
        if not db_name or db_name == "":
            db_name = "musiccharts"
        _db = client[db_name]
    return _db


def close_mongodb_connection():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None

