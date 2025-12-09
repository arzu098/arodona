"""
Data Persistence Diagnostic Script
Check for issues causing data loss on Render
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.db.connection import get_database
from app.config import ENVIRONMENT
import os

async def diagnose_data_persistence():
    """Diagnose potential data persistence issues"""
    
    print("🔍 DIAGNOSING DATA PERSISTENCE ISSUES")
    print("=" * 50)
    
    # Check environment
    print(f"\\n📋 Environment Information:")
    print(f"   ENVIRONMENT: {ENVIRONMENT}")
    print(f"   BACKEND_URL: {os.getenv('BACKEND_URL', 'Not set')}")
    print(f"   MONGODB_URL: {'Set' if os.getenv('MONGODB_URL') else 'Not set'}")
    print(f"   DATABASE_NAME: {os.getenv('DATABASE_NAME', 'Not set')}")
    
    try:
        # Get database connection
        db = get_database()
        
        # Check database connection
        print(f"\\n📊 Database Connection Test:")
        server_info = await db.command("ping")
        print(f"   ✅ MongoDB connection: OK")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"   📚 Collections found: {len(collections)}")
        for col in collections:
            count = await db[col].count_documents({})
            print(f"      - {col}: {count} documents")
        
        # Check products specifically
        print(f"\\n🛍️ Products Analysis:")
        total_products = await db.products.count_documents({})
        active_products = await db.products.count_documents({"deleted": {"$ne": True}})
        deleted_products = await db.products.count_documents({"deleted": True})
        
        print(f"   📦 Total products: {total_products}")
        print(f"   ✅ Active products: {active_products}")
        print(f"   🗑️ Deleted products: {deleted_products}")
        
        # Check recent products
        recent_products = await db.products.find(
            {"created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}
        ).to_list(None)
        
        print(f"   🕐 Products created in last 7 days: {len(recent_products)}")
        
        # Check for TTL indexes
        print(f"\\n🕒 TTL Index Analysis:")
        for collection_name in ['products', 'users', 'vendors', 'sessions']:
            if collection_name in collections:
                indexes = await db[collection_name].list_indexes().to_list(None)
                ttl_indexes = [idx for idx in indexes if 'expireAfterSeconds' in idx.get('key', {})]
                
                if ttl_indexes:
                    print(f"   ⚠️ {collection_name} has TTL indexes:")
                    for idx in ttl_indexes:
                        expire_time = idx.get('expireAfterSeconds', 'Unknown')
                        print(f"      - Expires after: {expire_time} seconds")
                else:
                    print(f"   ✅ {collection_name}: No TTL indexes")
        
        # Check vendor relationships
        print(f"\\n👥 Vendor Analysis:")
        total_vendors = await db.vendors.count_documents({})
        print(f"   👤 Total vendors: {total_vendors}")
        
        # Check orphaned products
        products_with_vendors = await db.products.aggregate([
            {
                "$lookup": {
                    "from": "vendors",
                    "localField": "vendor_id", 
                    "foreignField": "_id",
                    "as": "vendor"
                }
            },
            {
                "$match": {
                    "vendor": {"$size": 0},  # No matching vendor
                    "deleted": {"$ne": True}
                }
            }
        ]).to_list(None)
        
        print(f"   ⚠️ Orphaned products (no vendor): {len(products_with_vendors)}")
        
        # Check for patterns that might trigger cleanup
        print(f"\\n🔍 Pattern Analysis (potential cleanup triggers):")
        
        sample_patterns = [
            ("Sample in name", {"name": {"$regex": "sample", "$options": "i"}}),
            ("Test in name", {"name": {"$regex": "test", "$options": "i"}}),
            ("Demo in name", {"name": {"$regex": "demo", "$options": "i"}}),
            ("Legacy vendors", {"vendor_id": {"$regex": "^orphaned_"}}),
        ]
        
        for pattern_name, query in sample_patterns:
            count = await db.products.count_documents(query)
            if count > 0:
                print(f"   ⚠️ {pattern_name}: {count} products (might be cleaned up)")
            else:
                print(f"   ✅ {pattern_name}: {count} products")
        
        # Database size information
        print(f"\\n💾 Storage Information:")
        stats = await db.command("dbstats")
        print(f"   📁 Database size: {stats.get('dataSize', 0) / (1024*1024):.2f} MB")
        print(f"   📊 Storage size: {stats.get('storageSize', 0) / (1024*1024):.2f} MB")
        print(f"   📄 Collections: {stats.get('collections', 0)}")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        
    print(f"\\n✅ Diagnosis completed!")

if __name__ == "__main__":
    asyncio.run(diagnose_data_persistence())