#!/usr/bin/env python3
"""
Simple fix for broken image URLs - replace with database API URLs or remove broken ones
"""
import asyncio
import sys
sys.path.append('.')

from app.db.connection import get_database, connect_to_mongo
from app.config import BACKEND_URL
import os

async def fix_broken_images():
    """Fix broken image URLs in products"""
    
    print("🔧 Fixing broken image URLs...")
    
    # Connect to database first
    success = await connect_to_mongo()
    if not success:
        print("❌ Failed to connect to database")
        return
    
    # Get database connection
    db = get_database()
    products_collection = db.products
    
    # Get all products with images
    products = await products_collection.find({
        "images": {"$exists": True, "$ne": []}
    }).to_list(None)
    
    print(f"📊 Found {len(products)} products with images")
    
    backend_url = BACKEND_URL or "https://adorona.onrender.com"
    updated_count = 0
    
    for product in products:
        try:
            product_id = str(product["_id"])
            product_name = product.get('name', 'Unknown')
            print(f"\n🔄 Processing: {product_name} ({product_id})")
            
            original_images = product.get("images", [])
            fixed_images = []
            needs_update = False
            
            for i, image_item in enumerate(original_images):
                if isinstance(image_item, dict):
                    # New format with url, thumbnail_url, etc.
                    image_url = image_item.get("url", "")
                    
                    # Check if it's a broken uploads URL
                    if "/uploads/" in image_url and "adorona.onrender.com" in image_url:
                        print(f"  🔧 Fixing broken uploads URL: {image_url}")
                        # For now, remove broken images or replace with placeholder
                        # Since we can't recover the lost images, we'll skip them
                        needs_update = True
                        print(f"    ❌ Removing broken image URL (file lost on Render)")
                        continue  # Skip this broken image
                    elif "/Images/" in image_url:
                        print(f"  📷 Frontend static image: {image_url}")
                        # These are frontend static images, keep them
                        fixed_images.append(image_item)
                    elif "/api/images/" in image_url:
                        print(f"  ✅ Valid database image: {image_url}")
                        # These are database images, keep them
                        fixed_images.append(image_item)
                    else:
                        print(f"  ❓ Unknown image format: {image_url}")
                        # Keep unknown formats
                        fixed_images.append(image_item)
                        
                elif isinstance(image_item, str):
                    # Old format - just a string URL
                    if "/uploads/" in image_item and "adorona.onrender.com" in image_item:
                        print(f"  🔧 Fixing broken uploads URL: {image_item}")
                        needs_update = True
                        print(f"    ❌ Removing broken image URL (file lost on Render)")
                        continue  # Skip this broken image
                    elif "/Images/" in image_item:
                        print(f"  📷 Frontend static image: {image_item}")
                        # Convert to new format
                        new_image_obj = {
                            "url": image_item,
                            "thumbnail_url": image_item,
                            "alt_text": f"{product_name} - Image {len(fixed_images)+1}",
                            "is_primary": len(fixed_images) == 0,
                            "sort_order": len(fixed_images)
                        }
                        fixed_images.append(new_image_obj)
                        needs_update = True
                    elif "/api/images/" in image_item:
                        print(f"  ✅ Valid database image: {image_item}")
                        # Convert to new format
                        new_image_obj = {
                            "url": image_item,
                            "thumbnail_url": image_item,
                            "alt_text": f"{product_name} - Image {len(fixed_images)+1}",
                            "is_primary": len(fixed_images) == 0,
                            "sort_order": len(fixed_images)
                        }
                        fixed_images.append(new_image_obj)
                        needs_update = True
                    else:
                        print(f"  ❓ Unknown image format: {image_item}")
                        # Convert to new format
                        new_image_obj = {
                            "url": image_item,
                            "thumbnail_url": image_item,
                            "alt_text": f"{product_name} - Image {len(fixed_images)+1}",
                            "is_primary": len(fixed_images) == 0,
                            "sort_order": len(fixed_images)
                        }
                        fixed_images.append(new_image_obj)
                        needs_update = True
            
            # Update product if needed
            if needs_update:
                await products_collection.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"images": fixed_images}}
                )
                updated_count += 1
                print(f"  ✅ Updated: {len(original_images)} → {len(fixed_images)} images")
            else:
                print(f"  ℹ️  No changes needed")
                
        except Exception as e:
            print(f"  ❌ Error processing product {product_id}: {e}")
    
    print(f"\n🎉 Cleanup completed!")
    print(f"   📊 Products updated: {updated_count}")
    print(f"   💡 Note: Broken upload URLs were removed (files lost on Render's ephemeral storage)")
    print(f"   💡 To add new images, upload them through the product management interface")

if __name__ == "__main__":
    asyncio.run(fix_broken_images())