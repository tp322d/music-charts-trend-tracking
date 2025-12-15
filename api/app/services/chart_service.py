"""
Chart service for managing chart entries in MongoDB.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId
from app.database.mongodb import get_mongodb_db
from app.schemas.chart import (
    ChartEntryCreate,
    ChartEntryUpdate,
    ChartQueryParams,
    ChartTopQuery,
    TrendAnalysis
)


class ChartService:
    """Service for chart entry operations."""
    
    COLLECTION_NAME = "chart_entries"
    
    @staticmethod
    def _create_indexes(db: Database):
        """Create indexes on MongoDB collection."""
        collection = db[ChartService.COLLECTION_NAME]
        collection.create_index([("date", 1), ("rank", 1)])
        collection.create_index([("artist", 1)])
        collection.create_index([("song", 1)])
        collection.create_index([("source", 1)])
        collection.create_index([("country", 1)])
        collection.create_index([("created_at", 1)], expireAfterSeconds=63072000)  # 2 years TTL
    
    @staticmethod
    def create_entry(entry: ChartEntryCreate) -> Dict[str, Any]:
        """Create a single chart entry."""
        db = get_mongodb_db()
        ChartService._create_indexes(db)
        collection = db[ChartService.COLLECTION_NAME]
        
        entry_dict = entry.model_dump()
        # Convert date to string for MongoDB
        if isinstance(entry_dict.get("date"), date):
            entry_dict["date"] = entry_dict["date"].isoformat()
        entry_dict["created_at"] = datetime.utcnow()
        entry_dict["updated_at"] = datetime.utcnow()
        
        # Handle platform_data if it was added as an attribute (not in model)
        if hasattr(entry, 'platform_data') and entry.platform_data:
            entry_dict.update(entry.platform_data)
        
        result = collection.insert_one(entry_dict)
        entry_dict["_id"] = result.inserted_id
        entry_dict["id"] = str(result.inserted_id)
        return entry_dict
    
    @staticmethod
    def create_batch(entries: List[ChartEntryCreate], validate_duplicates: bool = True) -> Dict[str, Any]:
        """Create multiple chart entries in batch."""
        db = get_mongodb_db()
        ChartService._create_indexes(db)
        collection = db[ChartService.COLLECTION_NAME]
        
        imported = 0
        skipped = 0
        errors = []
        
        documents = []
        for idx, entry in enumerate(entries):
            try:
                entry_dict = entry.model_dump()
                # Convert date to string for MongoDB
                if isinstance(entry_dict.get("date"), date):
                    entry_dict["date"] = entry_dict["date"].isoformat()
                entry_dict["created_at"] = datetime.utcnow()
                entry_dict["updated_at"] = datetime.utcnow()
                
                # Handle platform_data if it was added as an attribute (not in model)
                if hasattr(entry, 'platform_data') and entry.platform_data:
                    entry_dict.update(entry.platform_data)
                
                # Check for duplicates if validation enabled
                if validate_duplicates:
                    duplicate = collection.find_one({
                        "date": entry_dict["date"],
                        "rank": entry_dict["rank"],
                        "source": entry_dict["source"],
                        "country": entry_dict.get("country", "Global")
                    })
                    if duplicate:
                        skipped += 1
                        continue
                
                documents.append(entry_dict)
            except Exception as e:
                errors.append(f"Entry {idx}: {str(e)}")
                skipped += 1
        
        if documents:
            try:
                result = collection.insert_many(documents)
                imported = len(result.inserted_ids)
            except Exception as e:
                errors.append(f"Batch insert error: {str(e)}")
                skipped += len(documents)
        
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors
        }
    
    @staticmethod
    def get_entries_direct(
        limit: int = 100,
        offset: int = 0,
        filter_date: Optional[date] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        source: Optional[str] = None,
        country: Optional[str] = None,
        artist: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get chart entries with filtering and pagination (direct parameters to avoid Pydantic issues)."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        filter_dict = {}
        # Handle date filtering: single date takes precedence, otherwise use date range
        if filter_date:
            filter_dict["date"] = filter_date.isoformat()
        elif date_from or date_to:
            if date_from and date_to:
                filter_dict["date"] = {"$gte": date_from.isoformat(), "$lte": date_to.isoformat()}
            elif date_from:
                filter_dict["date"] = {"$gte": date_from.isoformat()}
            elif date_to:
                filter_dict["date"] = {"$lte": date_to.isoformat()}
        
        if source:
            filter_dict["source"] = source
        if country:
            filter_dict["country"] = country
        if artist:
            filter_dict["artist"] = {"$regex": artist, "$options": "i"}
        
        cursor = collection.find(filter_dict).sort("date", -1).sort("rank", 1)
        cursor = cursor.skip(offset).limit(limit)
        
        entries = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            # Convert date string back to date object for Pydantic
            if "date" in doc and isinstance(doc["date"], str):
                doc["date"] = date.fromisoformat(doc["date"])
            # Convert datetime strings back to datetime objects
            if "created_at" in doc and isinstance(doc["created_at"], str):
                doc["created_at"] = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
            if "updated_at" in doc and isinstance(doc["updated_at"], str):
                doc["updated_at"] = datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00"))
            entries.append(doc)
        
        return entries
    
    @staticmethod
    def get_top_charts(query: ChartTopQuery) -> List[Dict[str, Any]]:
        """Get top charts for a specific date."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        filter_dict = {"date": query.date.isoformat()}
        if query.source:
            filter_dict["source"] = query.source.value
        if query.country:
            filter_dict["country"] = query.country
        
        cursor = collection.find(filter_dict).sort("rank", 1).limit(query.limit)
        
        entries = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            # Convert date string back to date object for Pydantic
            if "date" in doc and isinstance(doc["date"], str):
                doc["date"] = date.fromisoformat(doc["date"])
            # Convert datetime strings back to datetime objects
            if "created_at" in doc and isinstance(doc["created_at"], str):
                doc["created_at"] = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
            if "updated_at" in doc and isinstance(doc["updated_at"], str):
                doc["updated_at"] = datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00"))
            entries.append(doc)
        
        return entries
    
    @staticmethod
    def get_artist_history(artist_name: str, date_from: Optional[datetime] = None, 
                          date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get chart history for an artist."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        filter_dict = {"artist": {"$regex": artist_name, "$options": "i"}}
        if date_from:
            filter_dict["date"] = {"$gte": date_from.isoformat()}
        if date_to:
            if "date" in filter_dict:
                filter_dict["date"]["$lte"] = date_to.isoformat()
            else:
                filter_dict["date"] = {"$lte": date_to.isoformat()}
        
        cursor = collection.find(filter_dict).sort("date", -1).sort("rank", 1)
        
        entries = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            # Convert date string back to date object for Pydantic
            if "date" in doc and isinstance(doc["date"], str):
                doc["date"] = date.fromisoformat(doc["date"])
            # Convert datetime strings back to datetime objects
            if "created_at" in doc and isinstance(doc["created_at"], str):
                doc["created_at"] = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
            if "updated_at" in doc and isinstance(doc["updated_at"], str):
                doc["updated_at"] = datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00"))
            entries.append(doc)
        
        return entries
    
    @staticmethod
    def get_entry_by_id(entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a single chart entry by ID."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        try:
            doc = collection.find_one({"_id": ObjectId(entry_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                # Convert date string back to date object for Pydantic
                if "date" in doc and isinstance(doc["date"], str):
                    doc["date"] = date.fromisoformat(doc["date"])
                # Convert datetime strings back to datetime objects
                if "created_at" in doc and isinstance(doc["created_at"], str):
                    doc["created_at"] = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
                if "updated_at" in doc and isinstance(doc["updated_at"], str):
                    doc["updated_at"] = datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00"))
            return doc
        except (InvalidId, TypeError):
            return None
    
    @staticmethod
    def update_entry(entry_id: str, update_data: ChartEntryUpdate) -> Optional[Dict[str, Any]]:
        """Update a chart entry."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Handle platform_data if it was added as an attribute (not in model)
            platform_data = None
            if hasattr(update_data, 'platform_data'):
                platform_data = update_data.platform_data
            
            if not update_dict and not platform_data:
                return None
            
            if platform_data:
                for key, value in platform_data.items():
                    update_dict[f"platform_data.{key}"] = value
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = collection.find_one_and_update(
                {"_id": ObjectId(entry_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                result["id"] = str(result["_id"])
                # Convert date string back to date object for Pydantic
                if "date" in result and isinstance(result["date"], str):
                    result["date"] = date.fromisoformat(result["date"])
                # Convert datetime strings back to datetime objects
                if "created_at" in result and isinstance(result["created_at"], str):
                    result["created_at"] = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
                if "updated_at" in result and isinstance(result["updated_at"], str):
                    result["updated_at"] = datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            return result
        except (InvalidId, TypeError):
            return None
    
    @staticmethod
    def delete_entry(entry_id: str) -> bool:
        """Delete a chart entry."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        try:
            result = collection.delete_one({"_id": ObjectId(entry_id)})
            return result.deleted_count > 0
        except (InvalidId, TypeError):
            return False
    
    @staticmethod
    def get_trend_analysis(days: int = 30, source: Optional[str] = None, 
                          min_appearances: int = 1) -> List[TrendAnalysis]:
        """Get trend analysis for top artists."""
        db = get_mongodb_db()
        collection = db[ChartService.COLLECTION_NAME]
        
        from datetime import date, timedelta
        date_from_obj = date.today() - timedelta(days=days)
        date_from = date_from_obj.isoformat()
        
        match_filter = {"date": {"$gte": date_from}}
        if source:
            match_filter["source"] = source
        
        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": "$artist",
                "appearances": {"$sum": 1},
                "avg_rank": {"$avg": "$rank"},
                "best_rank": {"$min": "$rank"},
                "worst_rank": {"$max": "$rank"},
                "total_streams": {"$sum": "$streams"},
                "songs": {"$push": {"song": "$song", "rank": "$rank", "date": "$date"}}
            }},
            {"$match": {"appearances": {"$gte": min_appearances}}},
            {"$sort": {"appearances": -1, "avg_rank": 1}},
            {"$limit": 50}
        ]
        
        results = []
        for doc in collection.aggregate(pipeline):
            # Calculate trending score (simple algorithm: appearances / avg_rank)
            trending_score = doc["appearances"] / doc["avg_rank"] if doc["avg_rank"] > 0 else 0
            
            # Get top songs
            songs_sorted = sorted(doc["songs"], key=lambda x: x["rank"])[:5]
            
            trend_dict = {
                "artist": doc["_id"],
                "period_days": days,
                "total_appearances": doc["appearances"],
                "average_rank": round(doc["avg_rank"], 2),
                "best_rank": doc["best_rank"],
                "worst_rank": doc["worst_rank"],
                "total_streams": doc.get("total_streams"),
                "trending_score": round(trending_score, 2),
            }
            trend = TrendAnalysis(**trend_dict)
            # Convert to dict and add extra fields for response
            trend_result = trend.model_dump()
            trend_result["top_songs"] = songs_sorted
            trend_result["chart_history"] = doc["songs"][:20]
            results.append(trend_result)
        
        return results

