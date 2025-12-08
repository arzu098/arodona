"""
Migration script for order system.

This script ensures indexes for the orders and order_returns collections.
Run this once after deploying the order subsystem.

Usage:
    python -m app.migrations.migrate_orders
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
    print("Starting order migration...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        orders_col = db['orders']
        returns_col = db['order_returns']
        
        # Create collections by inserting dummy documents
        dummy_order = {
            "user_id": "__migration_dummy__",
            "items": [],
            "subtotal": 0.0,
            "tax": 0.0,
            "shipping_cost": 0.0,
            "discount": 0.0,
            "total_amount": 0.0,
            "status": "pending",
            "shipping_address": {},
            "payment_method": "dummy",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        dummy_return = {
            "order_id": "__migration_dummy__",
            "user_id": "__migration_dummy__",
            "items": [],
            "reason": "dummy",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert and immediately delete dummy documents to ensure collections exist
        await orders_col.insert_one(dummy_order)
        await orders_col.delete_one({"user_id": "__migration_dummy__"})
        
        await returns_col.insert_one(dummy_return)
        await returns_col.delete_one({"user_id": "__migration_dummy__"})
        
        # Create indexes for orders collection
        print("\nCreating indexes for orders...")
        
        # Index on user_id for user-specific queries
        await orders_col.create_index("user_id")
        print("  ✓ Created index on orders.user_id")
        
        # Index on status for filtering by status
        await orders_col.create_index("status")
        print("  ✓ Created index on orders.status")
        
        # Compound index on user_id and created_at for user order history
        await orders_col.create_index([("user_id", 1), ("created_at", -1)])
        print("  ✓ Created compound index on orders.user_id and orders.created_at")
        
        # Index on created_at for sorting
        await orders_col.create_index([("created_at", -1)])
        print("  ✓ Created index on orders.created_at")
        
        # Create indexes for returns collection
        print("\nCreating indexes for order returns...")
        
        # Index on order_id
        await returns_col.create_index("order_id")
        print("  ✓ Created index on order_returns.order_id")
        
        # Index on user_id
        await returns_col.create_index("user_id")
        print("  ✓ Created index on order_returns.user_id")
        
        # Index on status
        await returns_col.create_index("status")
        print("  ✓ Created index on order_returns.status")
        
        print("\n✅ Order migration completed successfully!")
        
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