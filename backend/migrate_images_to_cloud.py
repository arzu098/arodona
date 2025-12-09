"""
Migration script to move existing images from local storage to cloud storage
and update database URLs accordingly.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.db.connection import get_database
from app.utils.cloud_storage import cloud_storage
import base64
import requests
from urllib.parse import urlparse

async def migrate_images_to_cloud():
    """Migrate all existing product images to cloud storage"""
    
    print("🚀 Starting image migration to cloud storage...")
    
    # Get database connection
    db = get_database()
    products_collection = db.products
    
    # Get all products with images
    products = await products_collection.find({
        "images": {"$exists": True, "$ne": []}
    }).to_list(None)
    
    print(f"📊 Found {len(products)} products with images")
    
    updated_count = 0
    error_count = 0
    
    for product in products:
        try:
            product_id = str(product["_id"])
            print(f"\n🔄 Processing product: {product.get('name', 'Unknown')} ({product_id})")
            
            new_images = []
            
            for i, image_path in enumerate(product.get("images", [])):
                print(f"  📸 Processing image {i+1}: {image_path}")
                
                # Skip if already a cloud URL
                if image_path.startswith("https://res.cloudinary.com") or image_path.startswith("https://cloudinary.com"):
                    print(f"    ✅ Already cloud URL, skipping")
                    new_images.append(image_path)
                    continue
                
                # Try to migrate the image
                try:
                    new_url = await migrate_single_image(image_path, product_id)
                    if new_url:
                        new_images.append(new_url)
                        print(f"    ✅ Migrated to: {new_url}")
                    else:
                        # Keep original if migration fails
                        new_images.append(image_path)
                        print(f"    ⚠️  Migration failed, keeping original")
                        
                except Exception as e:
                    print(f"    ❌ Error migrating image: {e}")
                    new_images.append(image_path)  # Keep original
                    error_count += 1
            
            # Update product with new image URLs
            if new_images != product.get("images", []):
                await products_collection.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"images": new_images}}
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

async def migrate_single_image(image_path: str, product_id: str) -> str:
    """Migrate a single image to cloud storage"""
    
    try:
        # Handle different image path formats
        if image_path.startswith("/uploads"):
            # Local server path
            local_file_path = Path(__file__).parent.parent / image_path.lstrip("/")
        elif image_path.startswith("https://adorona.onrender.com"):
            # Production URL - download the image first
            return await migrate_from_url(image_path, product_id)
        elif image_path.startswith("uploads"):
            # Relative path
            local_file_path = Path(__file__).parent.parent / image_path
        else:
            # Assume it's a filename in uploads
            local_file_path = Path(__file__).parent.parent / "uploads" / image_path
        
        # Check if local file exists
        if not local_file_path.exists():
            print(f"    ❌ Local file not found: {local_file_path}")
            return None
        
        # Read and encode to base64
        with open(local_file_path, "rb") as f:
            image_data = f.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Determine image format from file extension
        file_ext = local_file_path.suffix.lower().lstrip('.')
        if file_ext in ['jpg', 'jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == 'png':
            mime_type = 'image/png'
        elif file_ext == 'webp':
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'  # Default
        
        # Create data URI
        data_uri = f"data:{mime_type};base64,{image_base64}"
        
        # Upload to cloud storage
        cloud_url = await cloud_storage.upload_image(data_uri, "products")
        
        return cloud_url
        
    except Exception as e:
        print(f"    ❌ Error migrating image {image_path}: {e}")
        return None

async def migrate_from_url(image_url: str, product_id: str) -> str:
    """Download image from URL and upload to cloud storage"""
    
    try:
        print(f"    📥 Downloading from URL: {image_url}")
        
        # Download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Convert to base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        
        # Determine content type
        content_type = response.headers.get('content-type', 'image/jpeg')
        
        # Create data URI
        data_uri = f"data:{content_type};base64,{image_base64}"
        
        # Upload to cloud storage
        cloud_url = await cloud_storage.upload_image(data_uri, "products")
        
        return cloud_url
        
    except Exception as e:
        print(f"    ❌ Error downloading from URL: {e}")
        return None

if __name__ == "__main__":
    print("🔄 Image Migration to Cloud Storage")
    print("=" * 50)
    
    # Run the migration
    asyncio.run(migrate_images_to_cloud())