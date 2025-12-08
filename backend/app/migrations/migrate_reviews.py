"""
Migration script for reviews system (placeholder).

This script initializes rating fields on existing products and ensures indexes.
Run this once after deploying the reviews subsystem.

Usage:
    python -m app.migrations.migrate_reviews
"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AIOMotorClient
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
    print("Starting reviews migration...")
    
    # Connect to MongoDB
    client = AIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        products_col = db['products']
        reviews_col = db['reviews']
        
        # Add default rating fields to products that don't have them
        print("\nInitializing rating fields on products...")
        result = await products_col.update_many(
            {'rating_avg': {'$exists': False}},
            {
                '$set': {
                    'rating_avg': 0.0,
                    'rating_count': 0,
                    'ratings_breakdown': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0},
                    'updated_at': datetime.utcnow()
                }
            }
        )
        print(f"  ✓ Updated {result.modified_count} products with rating fields")
        
        # Create indexes
        print("\nCreating indexes...")
        
        # Reviews indexes
        await reviews_col.create_index([('product_id', 1), ('created_at', -1)])
        print("  ✓ Created compound index on reviews (product_id, created_at)")
        
        await reviews_col.create_index('user_id')
        print("  ✓ Created index on reviews.user_id")
        
        # Products rating index
        await products_col.create_index('rating_avg')
        print("  ✓ Created index on products.rating_avg")
        
        # Optional: unique index for one-review-per-user
        # Uncomment if you want to enforce one review per user per product
        # try:
        #     await reviews_col.create_index([('product_id', 1), ('user_id', 1)], unique=True)
        #     print("  ✓ Created unique index on reviews (product_id, user_id)")
        # except Exception as e:
        #     print(f"  ⚠ Could not create unique index (may already exist): {e}")
        
        print("\n✅ Reviews migration completed successfully!")
        
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
