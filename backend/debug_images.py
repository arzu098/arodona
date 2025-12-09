#!/usr/bin/env python3
"""
Debug script to check image issues
"""
import asyncio
import aiohttp
import sys
sys.path.append('.')

async def test_backend_connection():
    """Test if backend is reachable"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5858/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Backend is running: {data}")
                    return True
                else:
                    print(f"❌ Backend returned {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

async def test_database_connection():
    """Test database connection and check for existing images"""
    try:
        from app.db.connection import get_database
        
        # Get database
        db = get_database()
        if not db:
            print("❌ Database is not connected")
            return False
            
        print("✅ Database connection available")
        
        # Check if images collection exists
        collections = await db.list_collection_names()
        print(f"📋 Available collections: {collections}")
        
        if "images" in collections:
            image_count = await db.images.count_documents({})
            print(f"🖼️ Found {image_count} images in database")
            
            # Get first few images to inspect
            if image_count > 0:
                images = await db.images.find().limit(3).to_list(3)
                for img in images:
                    print(f"   Image ID: {img['_id']}")
                    print(f"   Content Type: {img.get('content_type', 'unknown')}")
                    print(f"   Product ID: {img.get('product_id', 'none')}")
                    print(f"   Data Size: {len(img.get('image_data', ''))} chars")
                    print("   ---")
        else:
            print("❌ No 'images' collection found in database")
            
        # Check products for image references
        if "products" in collections:
            product_count = await db.products.count_documents({})
            print(f"📦 Found {product_count} products in database")
            
            # Find products with image fields
            products_with_images = await db.products.find(
                {"images": {"$exists": True, "$ne": []}}, 
                {"name": 1, "images": 1}
            ).limit(3).to_list(3)
            
            if products_with_images:
                print(f"📷 Products with images:")
                for product in products_with_images:
                    print(f"   Product: {product.get('name', 'Unknown')}")
                    print(f"   Images: {product.get('images', [])}")
                    print("   ---")
            else:
                print("❌ No products found with image references")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test specific API endpoints"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test non-existent image
            url = "http://localhost:5858/api/images/test123"
            async with session.get(url) as response:
                print(f"🔍 Testing {url}")
                print(f"   Status: {response.status}")
                print(f"   Response: {await response.text()}")
                
    except Exception as e:
        print(f"❌ API test failed: {e}")

async def main():
    print("🔍 Debugging Image Issues")
    print("=" * 40)
    
    # Test backend connection
    print("\n1️⃣ Testing Backend Connection...")
    backend_ok = await test_backend_connection()
    
    if backend_ok:
        print("\n2️⃣ Testing Database Connection...")
        db_ok = await test_database_connection()
        
        if db_ok:
            print("\n3️⃣ Testing API Endpoints...")
            await test_api_endpoints()
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    asyncio.run(main())