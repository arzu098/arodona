"""
Migration script for product collections system.

This script ensures indexes for the collections collection.
Run this once after deploying the collections subsystem.

Usage:
    python -m app.migrations.migrate_collections
"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'arodona_db')


async def migrate():
    """Run the migration"""
    print("Starting collections migration...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        collections_col = db['collections']
        
        # Create collection by inserting a dummy document (MongoDB creates collections lazily)
        dummy_collection = {
            "name": "__migration_dummy__",
            "slug": "__migration_dummy__",
            "description": "Dummy collection for migration",
            "product_ids": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert and immediately delete dummy document to ensure collection exists
        await collections_col.insert_one(dummy_collection)
        await collections_col.delete_one({"name": "__migration_dummy__"})
        
        # Create indexes
        print("\nCreating indexes...")
        
        # Unique index on slug
        await collections_col.create_index("slug", unique=True)
        print("  ✓ Created unique index on collections.slug")
        
        # Index on name for search
        await collections_col.create_index("name")
        print("  ✓ Created index on collections.name")
        
        # Index on created_at for sorting
        await collections_col.create_index([("created_at", -1)])
        print("  ✓ Created index on collections.created_at")
        
        print("\n✅ Collections migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()
    
    return True


if __name__ == '__main__':
    result = asyncio.run(migrate())
    sys.exit(0 if result else 1)