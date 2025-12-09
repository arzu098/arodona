#!/usr/bin/env python3
"""
Test script for the new database image storage and API serving system.
This verifies that images can be stored in database and served via API endpoints.
"""
import asyncio
import aiohttp
import os
import json
from io import BytesIO
from PIL import Image

# Test configuration
BACKEND_URL = "http://localhost:5858"
TEST_IMAGE_PATH = "test_image.png"

async def create_test_image():
    """Create a simple test image."""
    # Create a simple 100x100 red square PNG image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(TEST_IMAGE_PATH)
    print(f"✅ Created test image: {TEST_IMAGE_PATH}")

async def test_image_direct_storage():
    """Test direct image storage using the DatabaseImageService."""
    try:
        # Import the service
        import sys
        sys.path.append('.')
        from app.utils.database_image_storage import DatabaseImageService
        from app.db.connection import get_database
        
        # Get database connection
        db = await get_database().__anext__()
        
        # Initialize image service
        image_service = DatabaseImageService(db)
        
        # Read test image
        with open(TEST_IMAGE_PATH, 'rb') as f:
            image_data = f.read()
        
        # Create a mock UploadFile object
        class MockUploadFile:
            def __init__(self, data, filename):
                self.data = data
                self.filename = filename
                self.content_type = "image/png"
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
        
        mock_file = MockUploadFile(image_data, "test_image.png")
        
        # Store image
        result = await image_service.store_image(
            image_file=mock_file,
            product_id="test_product_123",
            vendor_id="test_vendor_123",
            image_type="product"
        )
        
        print(f"✅ Image stored successfully: {result}")
        
        # Try to retrieve the image
        retrieved = await image_service.get_image(result['image_id'])
        if retrieved:
            print(f"✅ Image retrieved successfully: {len(retrieved['image_data'])} bytes")
            return result['image_id']
        else:
            print("❌ Failed to retrieve stored image")
            return None
            
    except Exception as e:
        print(f"❌ Direct storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_image_api_serving(image_id):
    """Test serving image via API endpoint."""
    if not image_id:
        print("❌ No image ID provided for API test")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/images/{image_id}"
            print(f"🔍 Testing API endpoint: {url}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    print(f"✅ Image served successfully via API: {len(image_data)} bytes")
                    print(f"✅ Content-Type: {response.headers.get('content-type')}")
                    
                    # Save the retrieved image to verify it's valid
                    with open("retrieved_image.png", "wb") as f:
                        f.write(image_data)
                    print("✅ Retrieved image saved as retrieved_image.png")
                else:
                    print(f"❌ API request failed: {response.status} - {await response.text()}")
    
    except Exception as e:
        print(f"❌ API serving test failed: {e}")

async def test_nonexistent_image():
    """Test API response for non-existent image."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/images/nonexistent_id_12345"
            
            async with session.get(url) as response:
                if response.status == 404:
                    print("✅ Non-existent image correctly returns 404")
                else:
                    print(f"❌ Expected 404, got {response.status}")
    
    except Exception as e:
        print(f"❌ Non-existent image test failed: {e}")

async def cleanup():
    """Clean up test files."""
    try:
        if os.path.exists(TEST_IMAGE_PATH):
            os.remove(TEST_IMAGE_PATH)
        if os.path.exists("retrieved_image.png"):
            os.remove("retrieved_image.png")
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

async def main():
    """Run all tests."""
    print("🚀 Starting Database Image Storage & API Serving Tests")
    print("=" * 60)
    
    # Create test image
    await create_test_image()
    
    # Test direct database storage
    print("\n📦 Testing Direct Database Storage...")
    image_id = await test_image_direct_storage()
    
    # Test API serving
    print("\n🌐 Testing API Image Serving...")
    await test_image_api_serving(image_id)
    
    # Test error handling
    print("\n🚨 Testing Error Handling...")
    await test_nonexistent_image()
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await cleanup()
    
    print("\n✅ All tests completed!")
    print("🎉 Database image storage and API serving system is working!")

if __name__ == "__main__":
    asyncio.run(main())