"""
Migration script for cart system (placeholder).

This script ensures indexes for the carts collection.
Run this once after deploying the cart subsystem.

Usage:
    python -m app.migrations.migrate_cart
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
    print("Starting cart migration...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        carts_col = db['carts']
        
        # Create collection by inserting a dummy document (MongoDB creates collections lazily)
        dummy_cart = {
            "user_id": "__migration_dummy__",
            "items": [],
            "coupon": None,
            "subtotal": 0.0,
            "discount": 0.0,
            "tax": 0.0,
            "delivery_fee": 0.0,
            "total_amount": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert and immediately delete dummy document to ensure collection exists
        await carts_col.insert_one(dummy_cart)
        await carts_col.delete_one({"user_id": "__migration_dummy__"})
        
        # Create indexes
        print("\nCreating indexes...")
        
        # Unique index on user_id (one cart per user)
        await carts_col.create_index("user_id", unique=True)
        print("  ✓ Created unique index on carts.user_id")
        
        # Index on items.product_id for analytics
        await carts_col.create_index("items.product_id")
        print("  ✓ Created index on carts.items.product_id")
        
        # Optional: index on created_at for cleanup operations
        await carts_col.create_index([("created_at", -1)])
        print("  ✓ Created index on carts.created_at")
        
        print("\n✅ Cart migration completed successfully!")
        
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