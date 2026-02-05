"""
Update MongoDB indexes to include chapter field.

This script:
1. Adds chapter field to existing documents (if missing)
2. Creates new indexes for chapter field
3. Creates compound indexes for (subject, chapter)
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mcq_generator")

# Collection names
COLLECTIONS = {
    "mcq_sessions": "mcq_sessions",
    "mcqs": "mcqs",
    "concepts": "concepts"
}


def update_indexes():
    """Update MongoDB indexes for chapter field."""
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    
    print(f"\n{'='*60}")
    print("UPDATING DATABASE INDEXES")
    print(f"{'='*60}\n")
    
    # Update each collection
    for collection_name in COLLECTIONS.values():
        print(f"\n📊 Processing collection: {collection_name}")
        collection = db[collection_name]
        
        # Add default chapter field to existing documents that don't have it
        result = collection.update_many(
            {"chapter": {"$exists": False}},
            {"$set": {"chapter": "Unknown Chapter"}}
        )
        print(f"  ✓ Updated {result.modified_count} documents with default chapter value")
        
        # Create index on chapter field
        try:
            collection.create_index("chapter")
            print(f"  ✓ Created index on 'chapter' field")
        except Exception as e:
            print(f"  ⚠ Index on 'chapter' already exists or error: {e}")
        
        # Create compound index on (subject, chapter)
        try:
            collection.create_index([("subject", 1), ("chapter", 1)])
            print(f"  ✓ Created compound index on ('subject', 'chapter')")
        except Exception as e:
            print(f"  ⚠ Compound index on ('subject', 'chapter') already exists or error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Database update completed!")
    print(f"{'='*60}\n")
    
    # List all indexes for verification
    print("\n📋 Current indexes:")
    for collection_name in COLLECTIONS.values():
        collection = db[collection_name]
        print(f"\n{collection_name}:")
        for index in collection.list_indexes():
            print(f"  - {index['name']}: {index['key']}")
    
    client.close()


if __name__ == "__main__":
    update_indexes()
