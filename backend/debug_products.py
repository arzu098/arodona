#!/usr/bin/env python3
"""
Debug script to check product data structure and image URLs
"""
import asyncio
import aiohttp
import sys
sys.path.append('.')

async def check_products():
    """Check the actual product data structure"""
    try:
        from app.db.connection import get_database
        
        # Get database
        db = get_database()
        if not db:
            print("❌ Database is not connected")
            return
            
        print("✅ Database connection available")
        
        # Get a few products to inspect their image structure
        products = await db.products.find().limit(3).to_list(3)
        
        print(f"🔍 Found {len(products)} products to inspect")
        
        for i, product in enumerate(products, 1):
            print(f"\n📦 Product {i}: {product.get('name', 'Unknown')}")
            print(f"   ID: {product['_id']}")
            print(f"   Price: {product.get('price', 'N/A')}")
            
            # Check image data
            if 'images' in product:
                images = product['images']
                print(f"   Images field: {type(images)} - {images}")
                if isinstance(images, list) and len(images) > 0:
                    for j, img in enumerate(images[:2]):  # Show first 2 images
                        print(f"     Image {j+1}: {type(img)} - {img}")
            else:
                print("   No 'images' field found")
                
            if 'image' in product:
                print(f"   Single image field: {product['image']}")
            else:
                print("   No 'image' field found")
                
            # Show all fields that might be related to images
            image_fields = [k for k in product.keys() if 'image' in k.lower()]
            if image_fields:
                print(f"   Image-related fields: {image_fields}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error checking products: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_static_serving():
    """Test if static files are being served correctly"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test the known image path
            image_url = "http://localhost:5858/uploads/products/6937b8f2b28ae58aaee4f367/6937d8ab3b14d9a5008737a9/products_6937b8f2b28ae58aaee4f367_6937d8ab3b14d9a5008737a9_09d3c413-b9bc-4de6-891d-6e0d0e49f091.png"
            
            async with session.get(image_url) as response:
                print(f"\n🌐 Testing image serving:")
                print(f"   URL: {image_url}")
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {response.headers.get('content-length')}")
                
                if response.status == 200:
                    print("   ✅ Image is being served correctly!")
                else:
                    print(f"   ❌ Image serving failed: {await response.text()}")
                    
    except Exception as e:
        print(f"❌ Static serving test failed: {e}")

async def main():
    print("🔍 Debugging Product Image Issues")
    print("=" * 50)
    
    # Check product data structure
    print("\n1️⃣ Checking Product Data Structure...")
    await check_products()
    
    # Test static file serving
    print("\n2️⃣ Testing Static File Serving...")
    await test_static_serving()
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    asyncio.run(main())