#!/usr/bin/env python3
"""
Check specific vendor account and test product creation
"""
import asyncio
import sys
sys.path.append('.')

from app.db.connection import get_database, connect_to_mongo

async def check_vendor_account():
    """Check the specific vendor account"""
    
    # Connect to database
    success = await connect_to_mongo()
    if not success:
        print("❌ Failed to connect to database")
        return None
    
    db = get_database()
    
    # Check in users collection
    user = await db.users.find_one({"email": "vendor1@gmail.com"})
    if user:
        print(f"✅ Found user account:")
        print(f"   📧 Email: {user.get('email')}")
        print(f"   👤 Name: {user.get('name', 'Unknown')}")
        print(f"   🆔 ID: {user['_id']}")
        print(f"   🎭 Role: {user.get('role', 'Unknown')}")
        print(f"   ✅ Status: {user.get('is_active', 'Unknown')}")
        return user
    
    # Check in vendors collection
    vendor = await db.vendors.find_one({"email": "vendor1@gmail.com"})
    if vendor:
        print(f"✅ Found vendor account:")
        print(f"   📧 Email: {vendor.get('email')}")
        print(f"   👤 Name: {vendor.get('name', 'Unknown')}")
        print(f"   🆔 ID: {vendor['_id']}")
        print(f"   📊 Status: {vendor.get('status', 'Unknown')}")
        return vendor
    
    print("❌ No account found with email: vendor1@gmail.com")
    
    # Show available accounts for reference
    print("\n📋 Available accounts:")
    users = await db.users.find({"role": "vendor"}).limit(10).to_list(10)
    for user in users:
        print(f"   📧 {user.get('email', 'Unknown')}")
    
    return None

async def test_product_creation():
    """Test creating a product with the vendor account"""
    
    account = await check_vendor_account()
    if not account:
        return
    
    db = get_database()
    
    # Check existing products for this vendor
    vendor_id = str(account['_id'])
    products = await db.products.find({"vendor_id": vendor_id}).to_list(10)
    
    print(f"\n📦 Found {len(products)} existing products for this vendor:")
    for product in products:
        print(f"   🔸 {product.get('name', 'Unknown')} - Images: {len(product.get('images', []))}")
    
    # Show the most recent product details
    if products:
        latest_product = products[-1]
        print(f"\n🔍 Latest product details:")
        print(f"   Name: {latest_product.get('name')}")
        print(f"   ID: {latest_product['_id']}")
        print(f"   Images: {latest_product.get('images', [])}")
        
        # Check if images are properly formatted
        images = latest_product.get('images', [])
        if images:
            print(f"\n📸 Image details:")
            for i, img in enumerate(images):
                print(f"   Image {i+1}:")
                if isinstance(img, dict):
                    print(f"     URL: {img.get('url', 'No URL')}")
                    print(f"     Thumbnail: {img.get('thumbnail_url', 'No thumbnail')}")
                    print(f"     Alt text: {img.get('alt_text', 'No alt text')}")
                else:
                    print(f"     Direct URL: {img}")

if __name__ == "__main__":
    asyncio.run(test_product_creation())