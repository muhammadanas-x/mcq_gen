"""
Create MongoDB indexes for optimal query performance.

This script creates indexes on frequently queried fields in all three collections.
Run this once after setting up the database.
"""

import asyncio
from database import get_async_database, COLLECTIONS


async def create_indexes():
    """Create all necessary indexes for the MCQ generator database."""
    
    db = await get_async_database()
    
    print("Creating indexes for MCQ Generator database...")
    print("=" * 60)
    
    # MCQ Sessions Collection Indexes
    print("\n1. Creating indexes for 'mcq_sessions' collection...")
    sessions_col = db[COLLECTIONS["mcq_sessions"]]
    
    # Index on session_id (unique)
    await sessions_col.create_index("session_id", unique=True)
    print("   ✓ Created unique index on session_id")
    
    # Index on subject for filtering
    await sessions_col.create_index("subject")
    print("   ✓ Created index on subject")
    
    # Index on created_at for sorting
    await sessions_col.create_index("created_at")
    print("   ✓ Created index on created_at")
    
    # Compound index on subject + created_at
    await sessions_col.create_index([("subject", 1), ("created_at", -1)])
    print("   ✓ Created compound index on (subject, created_at)")
    
    # MCQs Collection Indexes
    print("\n2. Creating indexes for 'mcqs' collection...")
    mcqs_col = db[COLLECTIONS["mcqs"]]
    
    # Index on session_id
    await mcqs_col.create_index("session_id")
    print("   ✓ Created index on session_id")
    
    # Index on subject
    await mcqs_col.create_index("subject")
    print("   ✓ Created index on subject")
    
    # Index on difficulty
    await mcqs_col.create_index("metadata.difficulty")
    print("   ✓ Created index on metadata.difficulty")
    
    # Compound index on subject + session_id
    await mcqs_col.create_index([("subject", 1), ("session_id", 1)])
    print("   ✓ Created compound index on (subject, session_id)")
    
    # Compound index on subject + difficulty
    await mcqs_col.create_index([("subject", 1), ("metadata.difficulty", 1)])
    print("   ✓ Created compound index on (subject, difficulty)")
    
    # Index on created_at
    await mcqs_col.create_index("created_at")
    print("   ✓ Created index on created_at")
    
    # Concepts Collection Indexes
    print("\n3. Creating indexes for 'concepts' collection...")
    concepts_col = db[COLLECTIONS["concepts"]]
    
    # Index on session_id
    await concepts_col.create_index("session_id")
    print("   ✓ Created index on session_id")
    
    # Index on subject
    await concepts_col.create_index("subject")
    print("   ✓ Created index on subject")
    
    # Index on concept_id (unique within a session)
    await concepts_col.create_index("concept_id")
    print("   ✓ Created index on concept_id")
    
    # Compound index on subject + session_id
    await concepts_col.create_index([("subject", 1), ("session_id", 1)])
    print("   ✓ Created compound index on (subject, session_id)")
    
    print("\n" + "=" * 60)
    print("✅ All indexes created successfully!")
    print("=" * 60)
    
    # Display all indexes
    print("\nCreated Indexes Summary:")
    print("-" * 60)
    
    print("\nmcq_sessions:")
    sessions_indexes = await sessions_col.index_information()
    for name, info in sessions_indexes.items():
        print(f"  • {name}: {info['key']}")
    
    print("\nmcqs:")
    mcqs_indexes = await mcqs_col.index_information()
    for name, info in mcqs_indexes.items():
        print(f"  • {name}: {info['key']}")
    
    print("\nconcepts:")
    concepts_indexes = await concepts_col.index_information()
    for name, info in concepts_indexes.items():
        print(f"  • {name}: {info['key']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(create_indexes())
