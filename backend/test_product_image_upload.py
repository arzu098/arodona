#!/usr/bin/env python3
"""
Test script to verify image upload functionality with new products
"""
import asyncio
import aiohttp
import sys
import json
from pathlib import Path
from PIL import Image
import io
import base64

sys.path.append('.')

# Test configuration
BACKEND_URL = "http://localhost:5858"
TEST_IMAGE_PATH = "test_product_image.png"

async def create_test_image():
    """Create a simple test image"""
    # Create a simple 200x200 blue square PNG image
    img = Image.new('RGB', (200, 200), color='blue')
    img.save(TEST_IMAGE_PATH)
    print(f"✅ Created test image: {TEST_IMAGE_PATH}")
    return TEST_IMAGE_PATH

async def test_product_creation_with_image():
    """Test creating a product with image upload"""
    
    # First create test image
    image_path = await create_test_image()
    
    try:
        # Login first (you'll need to use actual vendor credentials)
        login_data = {
            "email": "test@example.com",  # Replace with actual vendor email
            "password": "test123"         # Replace with actual password
        }
        
        async with aiohttp.ClientSession() as session:
            # Login to get token
            print("🔐 Attempting login...")
            async with session.post(f"{BACKEND_URL}/api/auth/login", json=login_data) as login_response:
                if login_response.status != 200:
                    print(f"❌ Login failed: {login_response.status}")
                    response_text = await login_response.text()
                    print(f"Response: {response_text}")
                    return
                
                login_result = await login_response.json()
                token = login_result.get("access_token")
                
                if not token:
                    print("❌ No token received from login")
                    return
                
                print(f"✅ Login successful, got token")
                
                # Prepare headers with authentication
                headers = {
                    "Authorization": f"Bearer {token}"
                }
                
                # Prepare form data for product creation
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Create FormData
                data = aiohttp.FormData()
                data.add_field('name', 'Test Product with Image')
                data.add_field('description', 'This is a test product with image upload')
                data.add_field('category', 'ring')
                data.add_field('jewelry_type', 'ring')
                data.add_field('price', '999.99')
                data.add_field('stock', '5')
                data.add_field('sku', f'TEST_SKU_{int(asyncio.get_event_loop().time())}')
                data.add_field('metal_type', '18k_gold')
                data.add_field('images', image_data, filename='test_image.png', content_type='image/png')
                
                # Create product
                print("📦 Creating product with image...")
                async with session.post(f"{BACKEND_URL}/api/products", data=data, headers=headers) as create_response:
                    print(f"📡 Response status: {create_response.status}")
                    
                    if create_response.status == 200 or create_response.status == 201:
                        result = await create_response.json()
                        print(f"✅ Product created successfully!")
                        
                        # Check if product has images
                        product_id = result.get("product", {}).get("id") or result.get("id")
                        if product_id:
                            print(f"📋 Product ID: {product_id}")
                            
                            # Get the created product to check images
                            async with session.get(f"{BACKEND_URL}/api/products/{product_id}") as get_response:
                                if get_response.status == 200:
                                    product_data = await get_response.json()
                                    images = product_data.get("images", [])
                                    print(f"📸 Product has {len(images)} images:")
                                    
                                    for i, img in enumerate(images):
                                        if isinstance(img, dict):
                                            img_url = img.get("url", "")
                                            print(f"  Image {i+1}: {img_url}")
                                            
                                            # Test if image URL works
                                            if img_url:
                                                async with session.get(img_url) as img_response:
                                                    print(f"    Status: {img_response.status}")
                                                    if img_response.status == 200:
                                                        print(f"    ✅ Image accessible!")
                                                        content_type = img_response.headers.get('content-type', '')
                                                        content_length = img_response.headers.get('content-length', '0')
                                                        print(f"    Content-Type: {content_type}")
                                                        print(f"    Size: {content_length} bytes")
                                                    else:
                                                        print(f"    ❌ Image not accessible")
                                        else:
                                            print(f"  Image {i+1}: {img} (string format)")
                                else:
                                    print(f"❌ Failed to get product details: {get_response.status}")
                        else:
                            print("⚠️ No product ID in response")
                            print(f"Full response: {result}")
                    else:
                        response_text = await create_response.text()
                        print(f"❌ Product creation failed: {create_response.status}")
                        print(f"Response: {response_text}")
                        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if Path(image_path).exists():
            Path(image_path).unlink()
            print(f"🧹 Cleaned up test image")

async def main():
    """Run the test"""
    print("🧪 Testing Product Creation with Image Upload")
    print("=" * 50)
    
    await test_product_creation_with_image()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())