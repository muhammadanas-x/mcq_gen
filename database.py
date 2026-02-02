"""
MongoDB Database Configuration and Connection

Handles connection to MongoDB Atlas and provides database access.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mcq_generator")

# Synchronous client for non-async operations
_sync_client = None
_sync_db = None


def get_sync_database():
    """
    Get synchronous MongoDB database instance.
    Used for operations within the existing MCQ generator workflow.
    """
    global _sync_client, _sync_db
    
    if _sync_db is None:
        _sync_client = MongoClient(MONGODB_URI)
        _sync_db = _sync_client[MONGODB_DB_NAME]
    
    return _sync_db


def close_sync_database():
    """Close synchronous database connection"""
    global _sync_client
    if _sync_client:
        _sync_client.close()


# Async client for FastAPI endpoints
_async_client = None
_async_db = None


async def get_async_database():
    """
    Get asynchronous MongoDB database instance.
    Used for FastAPI endpoint queries and responses.
    """
    global _async_client, _async_db
    
    if _async_db is None:
        _async_client = AsyncIOMotorClient(MONGODB_URI)
        _async_db = _async_client[MONGODB_DB_NAME]
    
    return _async_db


async def close_async_database():
    """Close asynchronous database connection"""
    global _async_client
    if _async_client:
        _async_client.close()


# Collection names
COLLECTIONS = {
    "mcq_sessions": "mcq_sessions",      # Generation sessions metadata
    "mcqs": "mcqs",                       # Individual MCQs
    "concepts": "concepts",               # Extracted concepts
}
