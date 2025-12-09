"""
Migration script to convert existing image URLs to database storage
Downloads existing images and stores them in MongoDB
"""
import asyncio
import sys
from pathlib import Path
import aiohttp
import base64

# Add the backend directory to Python path
sys.path.append('.')

from app.db.connection import get_database, connect_to_mongo
from app.utils.database_image_storage import DatabaseImageService
from app.config import BACKEND_URL, ENVIRONMENT
import os

async def migrate_images_to_database():
    """Migrate all existing product images to database storage"""
    
    print("🔄 Starting migration to database image storage...")
    
    # Connect to database first
    success = await connect_to_mongo()
    if not success:
        print("❌ Failed to connect to database")
        return
    
    # Get database connection
    db = get_database()
    products_collection = db.products
    image_service = DatabaseImageService(db)
    
    # Get all products with images
    products = await products_collection.find({
        "images": {"$exists": True, "$ne": []}
    }).to_list(None)
    
    print(f"📊 Found {len(products)} products with images")
    
    updated_count = 0
    error_count = 0
    
    # Get backend URL for generating new URLs
    backend_url = os.getenv("BACKEND_URL", "http://localhost:5858" if ENVIRONMENT == "development" else "https://adorona.onrender.com")
    
    for product in products:
        try:
            product_id = str(product["_id"])
            print(f"\n🔄 Processing product: {product.get('name', 'Unknown')} ({product_id})")
            
            new_image_urls = []
            
            for i, image_path in enumerate(product.get("images", [])):
                print(f"  📸 Processing image {i+1}: {image_path}")
                
                # Skip if already a database image URL
                if "/api/images/" in image_path:
                    print(f"    ✅ Already database URL, skipping")
                    new_image_urls.append(image_path)
                    continue
                
                # Try to migrate the image
                try:
                    image_id = await migrate_single_image(image_path, product_id, image_service)
                    if image_id:
                        new_url = f"{backend_url}/api/images/{image_id}"
                        new_image_urls.append(new_url)
                        print(f"    ✅ Migrated to: {new_url}")
                    else:
                        # Keep original if migration fails
                        new_image_urls.append(image_path)
                        print(f"    ⚠️  Migration failed, keeping original")
                        
                except Exception as e:
                    print(f"    ❌ Error migrating image: {e}")
                    new_image_urls.append(image_path)  # Keep original
                    error_count += 1
            
            # Update product with new image URLs
            if new_image_urls != product.get("images", []):
                await products_collection.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"images": new_image_urls}}
                )
                updated_count += 1
                print(f"  ✅ Updated product in database")
            else:
                print(f"  ℹ️  No changes needed")
                
        except Exception as e:
            print(f"  ❌ Error processing product {product_id}: {e}")
            error_count += 1
    
    print(f"\n🎉 Migration completed!")
    print(f"   📊 Products updated: {updated_count}")
    print(f"   ❌ Errors encountered: {error_count}")

async def migrate_single_image(image_path: str, product_id: str, image_service: DatabaseImageService) -> str:
    """Migrate a single image to database storage"""
    
    try:
        base64_data = None
        
        # Handle different image path formats
        if image_path.startswith("https://") or image_path.startswith("http://"):
            # Download from URL
            print(f"    📥 Downloading from URL...")
            response = requests.get(image_path, timeout=30)
            response.raise_for_status()
            
            # Convert to base64
            image_bytes = response.content
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # Determine content type
            content_type = response.headers.get('content-type', 'image/jpeg')
            
            # Create data URI
            data_uri = f"data:{content_type};base64,{base64_data}"
            
        elif image_path.startswith("/uploads") or image_path.startswith("uploads"):
            # Local file path
            local_file_path = None
            if image_path.startswith("/uploads"):
                local_file_path = Path(__file__).parent.parent / image_path.lstrip("/")
            else:
                local_file_path = Path(__file__).parent.parent / image_path
            
            if not local_file_path.exists():
                print(f"    ❌ Local file not found: {local_file_path}")
                return None
            
            # Read and encode to base64
            with open(local_file_path, "rb") as f:
                image_bytes = f.read()
            
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # Determine content type from file extension
            file_ext = local_file_path.suffix.lower().lstrip('.')
            if file_ext in ['jpg', 'jpeg']:
                content_type = 'image/jpeg'
            elif file_ext == 'png':
                content_type = 'image/png'
            elif file_ext == 'webp':
                content_type = 'image/webp'
            else:
                content_type = 'image/jpeg'  # Default
            
            # Create data URI
            data_uri = f"data:{content_type};base64,{base64_data}"
        
        else:
            print(f"    ❓ Unknown image path format: {image_path}")
            return None
        
        # Store in database
        result = await image_service.store_image(data_uri, product_id)
        return result["image_id"]
        
    except Exception as e:
        print(f"    ❌ Error migrating image {image_path}: {e}")
        return None

if __name__ == "__main__":
    print("🔄 Image Migration to Database Storage")
    print("=" * 50)
    
    # Run the migration
    asyncio.run(migrate_images_to_database())