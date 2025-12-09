#!/usr/bin/env python3
"""
Copy images from frontend public to backend uploads and fix database
"""
import asyncio
import shutil
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from bson import ObjectId
from pathlib import Path

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://bhoomi:bhoomi23@cluster0.wcbjoil.mongodb.net/arodona_db?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "arodona_db")

async def setup_image_serving():
    """Copy images and fix database paths"""
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("=" * 70)
        print("SETTING UP IMAGE SERVING")
        print("=" * 70)
        print()
        
        # Define paths
        frontend_images = Path("../frontend/public/Images")
        backend_uploads = Path("uploads/Images")
        
        # Create backend uploads/Images folder
        backend_uploads.mkdir(exist_ok=True, parents=True)
        
        print(f"Frontend images path: {frontend_images.absolute()}")
        print(f"Backend uploads path: {backend_uploads.absolute()}")
        print()
        
        # Copy key images from frontend to backend
        key_images = [
            "gold-ring-with-diamonds 1.jpg",
            "1.png",
            "2.png", 
            "3.png",
            "4.png",
            "5.png",
            "7.png",
            "10.png",
            "young-woman-wearing-elegant-pearl-jewelry-grey-background-closeup 2.jpg"
        ]
        
        copied_files = 0
        for image_name in key_images:
            source = frontend_images / image_name
            dest = backend_uploads / image_name
            
            if source.exists():
                shutil.copy2(source, dest)
                print(f"✅ Copied: {image_name}")
                copied_files += 1
            else:
                print(f"⚠️  Not found: {image_name}")
        
        print(f"\n📂 Copied {copied_files} images to backend uploads")
        
        # Update database to use proper upload paths
        print("\n" + "=" * 70)
        print("UPDATING DATABASE IMAGE PATHS")
        print("=" * 70)
        print()
        
        products = await db.products.find({}).to_list(None)
        
        for product in products:
            updated_images = []
            
            for image in product.get('images', []):
                if isinstance(image, dict):
                    old_url = image.get('url', '')
                    
                    # Convert /Images/filename to /uploads/Images/filename
                    if old_url.startswith('/Images/'):
                        new_url = old_url.replace('/Images/', '/uploads/Images/')
                        image['url'] = new_url
                        
                        # Update thumbnail too
                        if 'thumbnail_url' in image and image['thumbnail_url'].startswith('/Images/'):
                            image['thumbnail_url'] = image['thumbnail_url'].replace('/Images/', '/uploads/Images/')
                
                updated_images.append(image)
            
            # Update product in database
            if updated_images:
                await db.products.update_one(
                    {"_id": product['_id']},
                    {
                        "$set": {
                            "images": updated_images,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                print(f"✅ Updated image paths for: {product.get('name')}")
        
        print("\n✅ All image paths updated to use /uploads/Images/")
        
        # Test file access
        print("\n" + "=" * 70)
        print("TESTING FILE ACCESS")
        print("=" * 70)
        print()
        
        test_files = list(backend_uploads.glob("*.jpg")) + list(backend_uploads.glob("*.png"))[:3]
        
        for file_path in test_files:
            relative_path = f"/uploads/Images/{file_path.name}"
            print(f"✅ Available: {relative_path}")
        
        print(f"\n🎉 Setup complete! Backend should now serve images from /uploads/Images/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_image_serving())