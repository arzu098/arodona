#!/usr/bin/env python3
"""
Test and fix image storage collection issue
"""
import asyncio
import sys
sys.path.append('.')

from app.db.connection import get_database, connect_to_mongo
from app.utils.database_image_storage import DatabaseImageService
from PIL import Image
import io
import base64

async def test_and_create_image_collection():
    """Test image storage and create collection if needed"""
    
    print("🔍 Testing Image Storage Collection...")
    
    success = await connect_to_mongo()
    if not success:
        print("❌ Database connection failed")
        return
    
    db = get_database()
    
    # Check current collections
    collections = await db.list_collection_names()
    print(f"📋 Available collections: {len(collections)}")
    
    # Create a test image
    print("\n📸 Creating test image...")
    img = Image.new('RGB', (50, 50), color='green')
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
        "test_collection.png", 
        "image/png"
    )
    
    # Test image service
    print("💾 Testing DatabaseImageService...")
    image_service = DatabaseImageService(db)
    
    try:
        result = await image_service.store_image(
            image_file=mock_file,
            product_id="test_collection_123",
            vendor_id="test_vendor_123",
            image_type="product"
        )
        
        print(f"✅ Image stored successfully!")
        print(f"   Image ID: {result['image_id']}")
        print(f"   File size: {result['file_size']} bytes")
        
        # Check if collection was created
        collections_after = await db.list_collection_names()
        new_collections = set(collections_after) - set(collections)
        
        if new_collections:
            print(f"📁 New collections created: {new_collections}")
        
        # Check images collection
        if 'images' in collections_after:
            count = await db.images.count_documents({})
            print(f"📊 Images collection now has {count} documents")
            
            # Test retrieval
            retrieved = await image_service.get_image(result['image_id'])
            if retrieved:
                print(f"✅ Image retrieval successful!")
                print(f"   Content type: {retrieved['content_type']}")
                print(f"   File extension: {retrieved['file_extension']}")
            else:
                print("❌ Image retrieval failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Image storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_and_create_image_collection())