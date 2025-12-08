"""
Migration script to create sample products for testing.
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
    print("Starting sample products creation...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        products_col = db['products']
        categories_col = db['categories']
        
        # Check if we already have products
        product_count = await products_col.count_documents({})
        if product_count > 0:
            print(f"✓ Found {product_count} existing products. Skipping sample product creation.")
            return True
        
        # Create sample categories if they don't exist
        print("Creating sample categories...")
        categories = [
            {"name": "Rings", "slug": "rings"},
            {"name": "Necklaces", "slug": "necklaces"},
            {"name": "Earrings", "slug": "earrings"},
            {"name": "Bracelets", "slug": "bracelets"}
        ]
        
        category_ids = {}
        for cat in categories:
            # Check if category already exists
            existing = await categories_col.find_one({'slug': cat['slug']})
            if existing:
                category_ids[cat['name']] = existing['_id']
                print(f"  ✓ Category '{cat['name']}' already exists")
            else:
                # Create category
                cat_result = await categories_col.insert_one({
                    'name': cat['name'],
                    'slug': cat['slug'],
                    'parent_id': None,
                    'description': f"Beautiful {cat['name'].lower()} collection",
                    'metadata': {},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                category_ids[cat['name']] = cat_result.inserted_id
                print(f"  + Created category '{cat['name']}' -> {cat_result.inserted_id}")
        
        # Create sample products
        print("\nCreating sample products...")
        sample_products = [
            {
                "name": "Diamond Engagement Ring",
                "description": "A stunning diamond engagement ring with a 1-carat center stone",
                "price": 2300.00,
                "categories": [category_ids["Rings"]],
                "images": [],
                "rating_avg": 0.0,
                "rating_count": 0,
                "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Gold Necklace",
                "description": "Elegant gold necklace with pendant",
                "price": 450.00,
                "categories": [category_ids["Necklaces"]],
                "images": [],
                "rating_avg": 0.0,
                "rating_count": 0,
                "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Silver Earrings",
                "description": "Beautiful silver stud earrings",
                "price": 89.99,
                "categories": [category_ids["Earrings"]],
                "images": [],
                "rating_avg": 0.0,
                "rating_count": 0,
                "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Leather Bracelet",
                "description": "Stylish leather bracelet with metal accents",
                "price": 35.50,
                "categories": [category_ids["Bracelets"]],
                "images": [],
                "rating_avg": 0.0,
                "rating_count": 0,
                "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert sample products
        result = await products_col.insert_many(sample_products)
        print(f"  ✓ Created {len(result.inserted_ids)} sample products")
        print(f"  Product IDs: {[str(id) for id in result.inserted_ids]}")
        
        print("\n✅ Sample products creation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Sample products creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()
    
    return True


if __name__ == '__main__':
    result = asyncio.run(migrate())
    sys.exit(0 if result else 1)