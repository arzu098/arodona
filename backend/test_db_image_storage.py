#!/usr/bin/env python3
"""
Debug script to test image upload directly to database
"""
import asyncio
import sys
import base64
from pathlib import Path
from PIL import Image
import io

sys.path.append('.')

from app.db.connection import get_database, connect_to_mongo
from app.utils.database_image_storage import DatabaseImageService

async def test_database_image_storage():
    """Test direct database image storage"""
    
    print("🧪 Testing Database Image Storage")
    print("=" * 40)
    
    # Connect to database
    success = await connect_to_mongo()
    if not success:
        print("❌ Failed to connect to database")
        return
    
    db = get_database()
    image_service = DatabaseImageService(db)
    
    # Create test image
    print("\n📸 Creating test image...")
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Create mock upload file
    class MockUploadFile:
        def __init__(self, data, filename, content_type):
            self.data = data
            self.filename = filename
            self.content_type = content_type
            self._position = 0
        
        async def read(self, size=-1):
            if size == -1:
                result = self.data[self._position:]
                self._position = len(self.data)
            else:
                result = self.data[self._position:self._position + size]
                self._position += len(result)
            return result
        
        async def seek(self, position):
            self._position = position
    
    mock_file = MockUploadFile(
        img_bytes.getvalue(), 
        "test_green_square.png", 
        "image/png"
    )
    
    try:
        # Store image
        print("💾 Storing image in database...")
        result = await image_service.store_image(
            image_file=mock_file,
            product_id="test_product_123",
            vendor_id="test_vendor_123",
            image_type="product"
        )
        
        print(f"✅ Image stored successfully!")
        print(f"   Image ID: {result['image_id']}")
        print(f"   File size: {result['file_size']} bytes")
        print(f"   Content type: {result['content_type']}")
        
        # Retrieve image
        print("\n🔍 Retrieving image from database...")
        retrieved = await image_service.get_image(result['image_id'])
        
        if retrieved:
            print(f"✅ Image retrieved successfully!")
            print(f"   Content type: {retrieved['content_type']}")
            print(f"   File extension: {retrieved['file_extension']}")
            print(f"   Data size: {len(retrieved['image_data'])} chars (base64)")
            
            # Test API URL construction
            from app.config import BACKEND_URL
            api_url = f"{BACKEND_URL}/api/images/{result['image_id']}"
            print(f"📡 API URL: {api_url}")
            
            return result['image_id']
        else:
            print("❌ Failed to retrieve image")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_image_api_endpoint(image_id):
    """Test the image API endpoint"""
    if not image_id:
        print("❌ No image ID to test")
        return
    
    import aiohttp
    from app.config import BACKEND_URL
    
    try:
        api_url = f"{BACKEND_URL}/api/images/{image_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                print(f"\n🌐 Testing API endpoint: {api_url}")
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', '0')
                    print(f"   ✅ Image served successfully!")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {content_length} bytes")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ API test failed: {e}")

async def main():
    """Run all tests"""
    print("🔧 Database Image Storage Test")
    
    # Test direct database storage
    image_id = await test_database_image_storage()
    
    # Test API endpoint (will fail if backend not running locally)
    if image_id:
        await test_image_api_endpoint(image_id)
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())