#!/usr/bin/env python3
"""
Debug script to test image upload issues in production
"""
import asyncio
import aiohttp
import json
from pathlib import Path
from PIL import Image
import io
import base64

async def test_image_upload_debug():
    """Test image upload with detailed debugging"""
    
    # Create a simple test image
    print("📸 Creating test image...")
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Test data for product creation
    test_product_data = {
        'name': 'DEBUG Test Product',
        'description': 'This is a test product for debugging image upload',
        'category': 'ring',
        'jewelry_type': 'ring',
        'price': '123.45',
        'stock': '10',
        'sku': 'DEBUG_SKU_001',
        'metal_type': '18k_gold'
    }
    
    # Login credentials (you may need to update these)
    login_data = {
        "email": "vendor1@gmail.com",
        "password": "vendor123"  # Update with actual password
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Login
            print("🔐 Attempting login...")
            async with session.post("https://adorona.onrender.com/api/auth/login", json=login_data) as response:
                print(f"Login Status: {response.status}")
                
                if response.status != 200:
                    response_text = await response.text()
                    print(f"❌ Login failed: {response_text}")
                    return
                
                login_result = await response.json()
                token = login_result.get("access_token")
                
                if not token:
                    print("❌ No token received")
                    return
                
                print("✅ Login successful")
                
                # Step 2: Test product creation WITHOUT images first
                print("\n📦 Testing product creation WITHOUT images...")
                
                headers = {"Authorization": f"Bearer {token}"}
                data = aiohttp.FormData()
                
                for key, value in test_product_data.items():
                    data.add_field(key, value)
                
                async with session.post("https://adorona.onrender.com/api/products", data=data, headers=headers) as response:
                    print(f"Product creation (no images) status: {response.status}")
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:
                        result = await response.json() if response.content_type == 'application/json' else {}
                        print("✅ Product created successfully without images")
                        product_id = result.get("product", {}).get("id") or result.get("id")
                        print(f"Product ID: {product_id}")
                    else:
                        print(f"❌ Product creation failed: {response_text}")
                        return
                
                # Step 3: Test product creation WITH images
                print("\n📷 Testing product creation WITH images...")
                
                test_product_data['name'] = 'DEBUG Test Product WITH IMAGE'
                test_product_data['sku'] = 'DEBUG_SKU_002'
                
                data = aiohttp.FormData()
                for key, value in test_product_data.items():
                    data.add_field(key, value)
                
                # Add image
                data.add_field('images', img_bytes.getvalue(), filename='test_debug.png', content_type='image/png')
                
                async with session.post("https://adorona.onrender.com/api/products", data=data, headers=headers) as response:
                    print(f"Product creation (with images) status: {response.status}")
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:
                        result = await response.json() if response.content_type == 'application/json' else {}
                        print("✅ Product created successfully with images")
                        
                        product_id = result.get("product", {}).get("id") or result.get("id")
                        print(f"Product ID: {product_id}")
                        
                        # Check if product has images
                        if product_id:
                            async with session.get(f"https://adorona.onrender.com/api/products/{product_id}") as get_response:
                                if get_response.status == 200:
                                    product_details = await get_response.json()
                                    images = product_details.get("images", [])
                                    print(f"🔍 Product images count: {len(images)}")
                                    
                                    if images:
                                        for i, img in enumerate(images):
                                            print(f"   Image {i+1}: {img}")
                                    else:
                                        print("❌ No images found in created product!")
                                else:
                                    print(f"❌ Failed to get product details: {get_response.status}")
                    else:
                        print(f"❌ Product creation with images failed: {response_text}")
                        
                        # Parse error for more details
                        try:
                            error_json = json.loads(response_text)
                            print(f"Error details: {error_json}")
                        except:
                            pass
        
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_upload_debug())