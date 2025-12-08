"""
Migration script to convert product categories from strings to ObjectIds.

This script:
1. Inspects the products collection for string-based category field
2. Creates categories in the categories collection
3. Updates products to use category ObjectIds in a 'categories' array field
4. Is idempotent and safe to run multiple times

Usage:
    python -m app.migrations.migrate_products_categories

To rollback (not recommended in production):
    - Manually revert the 'categories' field back to 'category' string in products
"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
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
    print("Starting migration...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        products_col = db['products']
        categories_col = db['categories']
        
        # Count products with string category field
        products_with_string_cat = await products_col.count_documents({
            'category': {'$type': 'string'}
        })
        
        if products_with_string_cat == 0:
            print("✓ No products with string category field found. Migration may have already run.")
            print("  Checking if products have 'categories' array...")
            products_with_categories = await products_col.count_documents({
                'categories': {'$exists': True}
            })
            if products_with_categories > 0:
                print(f"  ✓ Found {products_with_categories} products with 'categories' array. Migration is complete.")
                return
            else:
                print("  ⚠ No category fields found. Please check your products collection.")
                return
        
        print(f"Found {products_with_string_cat} products with string category field")
        
        # Get all unique category names
        unique_categories = await products_col.aggregate([
            {'$match': {'category': {'$type': 'string'}}},
            {'$group': {'_id': '$category'}},
            {'$sort': {'_id': 1}}
        ]).to_list(None)
        
        print(f"Found {len(unique_categories)} unique categories: {[cat['_id'] for cat in unique_categories]}")
        
        # Create/get categories
        category_map = {}  # Map of category name -> ObjectId
        created_count = 0
        
        for cat_doc in unique_categories:
            cat_name = cat_doc['_id']
            
            # Check if category already exists
            existing = await categories_col.find_one({'name': cat_name})
            
            if existing:
                category_map[cat_name] = existing['_id']
                print(f"  ✓ Category exists: '{cat_name}' -> {existing['_id']}")
            else:
                # Create category
                from app.utils.slug_utils import generate_slug, make_unique_slug
                
                slug = await make_unique_slug(cat_name, categories_col)
                cat_result = await categories_col.insert_one({
                    'name': cat_name,
                    'slug': slug,
                    'parent_id': None,
                    'description': None,
                    'metadata': {},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                category_map[cat_name] = cat_result.inserted_id
                created_count += 1
                print(f"  + Created category: '{cat_name}' -> {cat_result.inserted_id}")
        
        print(f"\nCreated {created_count} new categories")
        
        # Update products: convert 'category' string to 'categories' array
        print("\nUpdating products...")
        updated_count = 0
        
        for cat_name, cat_id in category_map.items():
            result = await products_col.update_many(
                {'category': cat_name},
                {
                    '$set': {
                        'categories': [cat_id],
                        'updated_at': datetime.utcnow()
                    },
                    '$unset': {'category': ''}  # Remove old field
                }
            )
            updated_count += result.modified_count
            if result.modified_count > 0:
                print(f"  ✓ Updated {result.modified_count} products in category '{cat_name}'")
        
        print(f"\nTotal products updated: {updated_count}")
        
        # Create indexes
        print("\nCreating indexes...")
        await categories_col.create_index('slug', unique=True)
        print("  ✓ Created unique index on categories.slug")
        
        await categories_col.create_index('parent_id')
        print("  ✓ Created index on categories.parent_id")
        
        await products_col.create_index('categories')
        print("  ✓ Created index on products.categories")
        
        print("\n✅ Migration completed successfully!")
        print(f"   - Created {created_count} categories")
        print(f"   - Updated {updated_count} products")
        
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
