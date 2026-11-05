"""
NEXHOST CLOUD - Optional MongoDB Integration
Author: @Harsh_54x (https://t.me/Harsh_54x)
Tagline: Your Bots. Your Cloud.

Provides high-speed document storage for bot activity events,
audit telemetry, and Telegram session data. Gracefully bypasses
if MONGO_URI is not provided.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from config import MONGO_URI

logger = logging.getLogger("NEXHOST-MONGO")

_mongo_client = None
_mongo_db = None

def get_mongo_db():
    """Retrieve or lazily initialize the MongoDB database connection."""
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    
    if not MONGO_URI:
        return None
    
    try:
        from pymongo import MongoClient
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
        # Verify connection
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client.get_database("nexhost_cloud")
        logger.info("Connected to MongoDB successfully.")
        return _mongo_db
    except Exception as e:
        logger.warning(f"MongoDB connection skipped or unavailable: {e}")
        _mongo_client = None
        _mongo_db = None
        return None

class MongoLogger:
    """Helper to log Telegram bot events and deployment actions to MongoDB."""
    
    @staticmethod
    def is_available() -> bool:
        return get_mongo_db() is not None

    @staticmethod
    def log_event(event_type: str, data: Dict[str, Any]) -> bool:
        db = get_mongo_db()
        if db is None:
            return False
        try:
            record = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc),
                **data
            }
            db["activity_logs"].insert_one(record)
            return True
        except Exception as e:
            logger.error(f"Failed to record MongoDB log event: {e}")
            return False

    @staticmethod
    def log_telegram_action(telegram_id: int, username: str, action: str, details: Optional[Dict[str, Any]] = None) -> bool:
        return MongoLogger.log_event("telegram_action", {
            "telegram_id": telegram_id,
            "username": username,
            "action": action,
            "details": details or {}
        })

    @staticmethod
    def log_bot_deployment(user_id: int, project_id: int, bot_name: str, status: str, source: str) -> bool:
        return MongoLogger.log_event("bot_deployment", {
            "user_id": user_id,
            "project_id": project_id,
            "bot_name": bot_name,
            "status": status,
            "source": source
        })

    @staticmethod
    def get_recent_activity(limit: int = 50) -> List[Dict[str, Any]]:
        db = get_mongo_db()
        if db is None:
            return []
        try:
            return list(db["activity_logs"].find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        except Exception as e:
            logger.error(f"Failed to query MongoDB logs: {e}")
            return []
