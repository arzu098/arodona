"""Comprehensive Jewelry Product Management API routes."""

from fastapi import APIRouter, HTTPException, Depends, status, Query, File, UploadFile, Form
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from ..databases.repositories.product import ProductRepository
from ..databases.repositories.vendor import VendorRepository
from ..databases.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductStatus,
    JewelryType, MetalType, GemstoneType, ProductCondition
)
from ..utils.dependencies import get_current_user, get_database
from ..utils.security import get_password_hash, verify_password
from ..utils.file_utils import file_manager, validate_file_type, ALLOWED_IMAGE_TYPES

router = APIRouter(prefix="/api/products", tags=["products"])
security = HTTPBearer()

# Vendor product endpoints (protected)
@router.post("", response_model=Dict[str, Any])
async def create_product(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database),
    # Basic Information
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    subcategory: Optional[str] = Form(None),
    jewelry_type: Optional[str] = Form(None),  # Added to match frontend
    
    # Pricing
    price: float = Form(...),
    original_price: Optional[float] = Form(None),
    discount_percentage: Optional[float] = Form(None),
    
    # Inventory
    stock: int = Form(...),
    sku: str = Form(...),
    
    # Jewelry Specific
    metal_type: Optional[str] = Form(None),
    stone_type: Optional[str] = Form(None),
    weight: Optional[float] = Form(None),
    dimensions: Optional[str] = Form(None),
    
    # Status
    is_active: bool = Form(True),
    
    # Images
    images: List[UploadFile] = File(None)
):
    """Create a new jewelry product with image upload support (vendor only)."""
    try:
        # Debug logging
        print(f"[CREATE_PRODUCT] Received request from user: {current_user.get('user_id')}")
        print(f"[CREATE_PRODUCT] Form data - name: {name}, category: {category}, price: {price}, stock: {stock}, sku: {sku}")
        print(f"[CREATE_PRODUCT] Images count: {len(images) if images else 0}")
        
        print(f"[CREATE_PRODUCT] Initializing repositories...")
        product_repo = ProductRepository(db)
        print(f"[CREATE_PRODUCT] ProductRepository initialized")
        vendor_repo = VendorRepository(db)
        print(f"[CREATE_PRODUCT] VendorRepository initialized")
        
        # Validate required fields
        if not name or not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product name is required"
            )
        
        if not description or not description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product description is required"
            )
        
        if not sku or not sku.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU is required"
            )
        
        if price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0"
            )
        
        if stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock cannot be negative"
            )
        
        # Get vendor for current user
        print(f"[CREATE_PRODUCT] Getting vendor for user_id: {current_user['user_id']}")
        vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
        if not vendor:
            print(f"[CREATE_PRODUCT] ERROR: Vendor not found for user_id: {current_user['user_id']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only approved vendors can create products"
            )
        
        vendor_id = vendor.id
        print(f"[CREATE_PRODUCT] Vendor found: {vendor_id}, status: {vendor.status}")
        
        # Check vendor status
        if vendor.status not in ["active", "approved"]:
            print(f"[CREATE_PRODUCT] ERROR: Vendor status is '{vendor.status}', not active/approved")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vendor account must be active to create products"
            )
        
        # Check for duplicate SKU
        print(f"[CREATE_PRODUCT] Checking for duplicate SKU: {sku}")
        existing_product = await db.products.find_one({"sku": sku, "deleted": {"$ne": True}})
        if existing_product:
            print(f"[CREATE_PRODUCT] ERROR: Duplicate SKU found: {sku}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A product with SKU '{sku}' already exists"
            )
        
        print(f"[CREATE_PRODUCT] No duplicate SKU, proceeding with product creation")
        # Prepare product data
        from bson import ObjectId
        
        # Auto-calculate discount if not provided
        calculated_discount = discount_percentage
        if original_price and price and original_price > price:
            if not discount_percentage or discount_percentage == 0:
                calculated_discount = round(((original_price - price) / original_price * 100), 2)
        
        # Normalize category/jewelry_type to match enum values
        # Handle plural forms, capitalization, etc.
        # Map frontend category values to valid JewelryType enum values
        category_mapping = {
            # Necklaces
            "necklaces": "necklace",
            "necklace": "necklace",
            # Rings
            "rings": "ring",
            "ring": "ring",
            # Earrings
            "earrings": "earrings",
            "earring": "earrings",
            # Bracelets & Bangles
            "bracelets": "bracelet",
            "bracelet": "bracelet",
            "bangles": "bracelet",  # Map bangles to bracelet
            "bangle": "bracelet",
            # Pendants
            "pendants": "pendant",
            "pendant": "pendant",
            # Brooches
            "brooches": "brooch",
            "brooch": "brooch",
            # Watches
            "watches": "watch",
            "watch": "watch",
            # Anklets
            "anklets": "anklet",
            "anklet": "anklet",
            # Chains
            "chains": "chain",
            "chain": "chain",
            # Charms
            "charms": "charm",
            "charm": "charm",
            # Cufflinks
            "cufflinks": "cufflinks",
            "cufflink": "cufflinks",
            # Tiaras
            "tiaras": "tiara",
            "tiara": "tiara",
            # Additional common terms
            "jewellery": "other",
            "jewelry": "other",
            "accessories": "other",
            "ornaments": "other"
        }
        
        # Normalize the category value (convert to lowercase and map)
        normalized_category = category_mapping.get(category.lower(), "other") if category else "other"
        jewelry_type_value = normalized_category
        
        # Normalize metal_type if provided
        metal_type_mapping = {
            "gold": "18k_gold",  # Default gold to 18k
            "14k gold": "14k_gold",
            "14k_gold": "14k_gold",
            "18k gold": "18k_gold",
            "18k_gold": "18k_gold",
            "22k gold": "22k_gold",
            "22k_gold": "22k_gold",
            "24k gold": "24k_gold",
            "24k_gold": "24k_gold",
            "white gold": "white_gold",
            "white_gold": "white_gold",
            "rose gold": "rose_gold",
            "rose_gold": "rose_gold",
            "silver": "sterling_silver",  # Default silver to sterling
            "sterling silver": "sterling_silver",
            "sterling_silver": "sterling_silver",
            "platinum": "platinum",
            "palladium": "palladium",
            "titanium": "titanium",
            "stainless steel": "stainless_steel",
            "stainless_steel": "stainless_steel",
            "copper": "copper",
            "brass": "brass"
        }
        
        normalized_metal_type = None
        if metal_type:
            normalized_metal_type = metal_type_mapping.get(metal_type.lower(), None)
        
        # Normalize stone_type if provided
        stone_type_mapping = {
            "diamond": "diamond",
            "diamonds": "diamond",
            "emerald": "emerald",
            "emeralds": "emerald",
            "ruby": "ruby",
            "rubies": "ruby",
            "sapphire": "sapphire",
            "sapphires": "sapphire",
            "pearl": "pearl",
            "pearls": "pearl",
            "amethyst": "amethyst",
            "aquamarine": "aquamarine",
            "citrine": "citrine",
            "garnet": "garnet",
            "opal": "opal",
            "peridot": "peridot",
            "topaz": "topaz",
            "turquoise": "turquoise",
            "onyx": "onyx",
            "jade": "jade",
            "coral": "coral",
            "moonstone": "moonstone",
            "tanzanite": "tanzanite",
            "cubic zirconia": "cubic_zirconia",
            "cubic_zirconia": "cubic_zirconia",
            "cz": "cubic_zirconia"
        }
        
        normalized_stone_type = None
        if stone_type:
            normalized_stone_type = stone_type_mapping.get(stone_type.lower(), None)
        
        product_data = {
            "vendor_id": vendor_id,
            "name": name,
            "description": description,
            "category": normalized_category,  # Store normalized category
            "subcategory": subcategory,
            "jewelry_type": jewelry_type_value,  # Add jewelry_type field
            "price": float(price),
            "original_price": float(original_price) if original_price else None,
            "discount_percentage": float(calculated_discount) if calculated_discount else 0,
            "stock": int(stock),
            "stock_quantity": int(stock),  # Alias
            "sku": sku,
            "metal_type": normalized_metal_type,  # Use normalized metal type
            "stone_type": normalized_stone_type,  # Use normalized stone type
            "weight": float(weight) if weight else None,
            "dimensions": dimensions,  # Store as string for simple products
            "is_active": is_active,
            "status": "active" if is_active else "draft",
            "condition": "new",  # Add default condition
            "track_inventory": True,  # Add track_inventory field
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "view_count": 0,
            "favorite_count": 0,
            "rating_avg": 0,
            "rating_count": 0,
            "images": [],
            "deleted": False
        }
        
        # Insert product
        print(f"[CREATE_PRODUCT] Inserting product into database...")
        result = await db.products.insert_one(product_data)
        product_id = str(result.inserted_id)
        print(f"[CREATE_PRODUCT] Product inserted successfully with ID: {product_id}")
        
        # Handle image uploads if provided
        uploaded_images = []
        if images and len(images) > 0:
            # Filter out any None or empty files
            valid_images = [img for img in images if img and img.filename]
            
            for idx, image in enumerate(valid_images):
                if not validate_file_type(image, ALLOWED_IMAGE_TYPES):
                    print(f"Skipping invalid image type: {image.filename}")
                    continue
                
                try:
                    # Validate file size (10MB max)
                    content = await image.read()
                    await image.seek(0)  # Reset file pointer
                    
                    if len(content) > 10 * 1024 * 1024:  # 10MB
                        print(f"Image {image.filename} too large, skipping")
                        continue
                    
                    image_info = await file_manager.save_product_image(
                        image, vendor_id, product_id
                    )
                    print(f"[CREATE_PRODUCT] Image saved: {image_info}")
                    uploaded_images.append({
                        "url": image_info["original"],
                        "thumbnail_url": image_info["thumbnail"],
                        "alt_text": f"{name} - Image {idx + 1}",
                        "is_primary": idx == 0,
                        "sort_order": idx
                    })
                    print(f"[CREATE_PRODUCT] Added image to list: url={image_info['original']}, thumbnail={image_info['thumbnail']}")
                    print(f"[CREATE_PRODUCT] Full image object: {uploaded_images[-1]}")
                except Exception as img_err:
                    print(f"Error uploading image {idx} ({image.filename}): {img_err}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Update product with images
        if uploaded_images:
            print(f"[CREATE_PRODUCT] Updating product with {len(uploaded_images)} images")
            print(f"[CREATE_PRODUCT] Images to save: {uploaded_images}")
            result = await db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"images": uploaded_images}}
            )
            print(f"[CREATE_PRODUCT] Database update result: matched={result.matched_count}, modified={result.modified_count}")
        else:
            print(f"[CREATE_PRODUCT] No images to update")
        
        # Get the created product
        created_product = await db.products.find_one({"_id": ObjectId(product_id)})
        print(f"[CREATE_PRODUCT] Retrieved product has {len(created_product.get('images', []))} images")
        if created_product.get('images'):
            print(f"[CREATE_PRODUCT] First image URL: {created_product['images'][0].get('url')}")
        
        print(f"[CREATE_PRODUCT] Formatting product response...")
        formatted_response = {
            "message": "Product created successfully",
            "product": product_repo.format_product_response(created_product, include_vendor_info=True)
        }
        print(f"[CREATE_PRODUCT] Product created successfully, returning response")
        return formatted_response
    except HTTPException as http_exc:
        print(f"[CREATE_PRODUCT] HTTPException: {http_exc.status_code} - {http_exc.detail}")
        raise
    except Exception as e:
        print(f"[CREATE_PRODUCT] Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get("/my-products", response_model=Dict[str, Any])
async def get_my_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ProductStatus] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get current vendor's products."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    products, total = await product_repo.get_vendor_products(
        vendor.id, skip, limit, status
    )
    
    return {
        "products": [product_repo.format_product_response(p, include_vendor_info=True) for p in products],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/my-products/{product_id}", response_model=ProductResponse)
async def get_my_product(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get specific product for current vendor."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    product = await product_repo.get_product_by_id(product_id)
    
    if not product or product["vendor_id"] != vendor.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product_repo.format_product_response(product, include_vendor_info=True)


@router.put("/my-products/{product_id}", response_model=Dict[str, Any])
async def update_my_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update vendor's product (JSON body)."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    try:
        updated_product = await product_repo.update_product(
            product_id, vendor.id, product_update
        )
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return {
            "message": "Product updated successfully",
            "product": product_repo.format_product_response(updated_product, include_vendor_info=True)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.put("/my-products/{product_id}/form", response_model=Dict[str, Any])
async def update_my_product_with_form(
    product_id: str,
    # Basic Information
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    subcategory: Optional[str] = Form(None),
    
    # Pricing
    price: Optional[float] = Form(None),
    original_price: Optional[float] = Form(None),
    discount_percentage: Optional[float] = Form(None),
    
    # Inventory
    stock: Optional[int] = Form(None),
    sku: Optional[str] = Form(None),
    
    # Jewelry Specific
    metal_type: Optional[str] = Form(None),
    stone_type: Optional[str] = Form(None),
    weight: Optional[float] = Form(None),
    dimensions: Optional[str] = Form(None),
    
    # Status
    is_active: Optional[bool] = Form(None),
    
    # Images
    images: List[UploadFile] = File(None),
    existing_images: Optional[str] = Form(None),  # JSON string of existing image URLs
    
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update vendor's product with form data and image upload support."""
    try:
        product_repo = ProductRepository(db)
        vendor_repo = VendorRepository(db)
        
        # Get vendor for current user
        vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vendor not found"
            )
        
        # Verify product ownership
        product = await product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_vendor_id = str(product.get("vendor_id"))
        if product_vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this product"
            )
        
        # Process image uploads
        image_urls = []
        
        # Keep existing images if provided
        if existing_images:
            import json
            try:
                existing_image_list = json.loads(existing_images)
                print(f"Processing existing images: {existing_image_list}")
                
                # Extract and normalize the URLs
                for idx, img in enumerate(existing_image_list):
                    url = None
                    alt_text = None
                    is_primary = idx == 0
                    
                    if isinstance(img, str):
                        url = img
                    elif isinstance(img, dict):
                        url = img.get('url')
                        alt_text = img.get('alt_text')
                        is_primary = img.get('is_primary', idx == 0)
                    
                    if url:
                        # Keep the URL as-is if it already has /uploads/ prefix
                        # Only add /uploads/ if it's missing and it's a relative path
                        if not url.startswith('/uploads/') and not url.startswith('http'):
                            # Check if it's just the relative path
                            if url.startswith('products/') or url.startswith('uploads/'):
                                # Remove 'uploads/' prefix if present, then add '/uploads/'
                                url = url.replace('uploads/', '', 1) if url.startswith('uploads/') else url
                                url = f"/uploads/{url}"
                            elif url.startswith('/static/'):
                                # Replace /static/ with /uploads/ for legacy data
                                url = url.replace('/static/', '/uploads/')
                            elif url.startswith('static/'):
                                # Replace static/ with /uploads/ for legacy data
                                url = url.replace('static/', '/uploads/')
                            elif not url.startswith('/'):
                                url = f"/uploads/{url}"
                        
                        image_urls.append({
                            "url": url,
                            "alt_text": alt_text or f"{name or product.get('name')} - Image {len(image_urls) + 1}",
                            "is_primary": is_primary,
                            "sort_order": len(image_urls)
                        })
                        print(f"Added existing image: {image_urls[-1]}")
                        
            except json.JSONDecodeError as e:
                print(f"Error parsing existing_images JSON: {e}")
                pass
        
        # Upload new images
        if images and len(images) > 0 and images[0].filename:
            print(f"Uploading {len(images)} new images...")
            for idx, image_file in enumerate(images):
                # Validate file type - pass the UploadFile object, not just the filename
                if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image type for {image_file.filename}. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
                    )
                
                # Save the image
                try:
                    file_data = await file_manager.save_product_image(
                        image_file,
                        vendor_id=vendor.id,
                        product_id=product_id
                    )
                    print(f"Saved image {idx}: {file_data}")
                    
                    # save_product_image returns a dict with 'original' and 'thumbnail' keys
                    file_url = file_data.get('original') if isinstance(file_data, dict) else file_data
                    
                    # Ensure URL has /uploads/ prefix (get_file_url should already add it)
                    # If not present, add it. Also handle legacy /static/ prefix
                    if file_url.startswith('/static/'):
                        file_url = file_url.replace('/static/', '/uploads/')
                    elif not file_url.startswith('/uploads/') and not file_url.startswith('http'):
                        if file_url.startswith('/'):
                            file_url = f"/uploads{file_url}"
                        else:
                            file_url = f"/uploads/{file_url}"
                    
                    image_urls.append({
                        "url": file_url,
                        "alt_text": f"{name or product.get('name')} - Image {len(image_urls) + 1}",
                        "is_primary": len(image_urls) == 0,
                        "sort_order": len(image_urls)
                    })
                    print(f"Added new image to list: {image_urls[-1]}")
                    
                except Exception as e:
                    print(f"Error saving image {image_file.filename}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to save image: {str(e)}"
                    )
        
        # Build update data
        update_data = {}
        
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if category is not None:
            update_data["category"] = category
        if subcategory is not None:
            update_data["subcategory"] = subcategory
        if price is not None:
            update_data["price"] = price
        if original_price is not None:
            update_data["compare_at_price"] = original_price
        if stock is not None:
            update_data["stock"] = stock
            update_data["stock_quantity"] = stock
        if sku is not None:
            update_data["sku"] = sku
        if metal_type is not None:
            update_data["metal_type"] = metal_type
        if stone_type is not None:
            update_data["stone_type"] = stone_type
        if weight is not None:
            update_data["weight"] = weight
        if dimensions is not None:
            update_data["dimensions"] = dimensions
        if is_active is not None:
            update_data["is_active"] = is_active
        
        if image_urls:
            update_data["images"] = image_urls
            print(f"Setting product images to: {image_urls}")
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the product
        from bson import ObjectId
        result = await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        print(f"Product update result: matched={result.matched_count}, modified={result.modified_count}")
        
        # Get updated product
        updated_product = await product_repo.get_product_by_id(product_id)
        print(f"Updated product images: {updated_product.get('images')}")
        
        formatted_product = product_repo.format_product_response(updated_product, include_vendor_info=True)
        print(f"Formatted product images: {formatted_product.images if hasattr(formatted_product, 'images') else 'No images attr'}")
        
        return {
            "message": "Product updated successfully",
            "product": formatted_product
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.patch("/my-products/{product_id}", response_model=Dict[str, Any])
async def patch_my_product(
    product_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Partially update vendor's product (e.g., toggle is_active)."""
    try:
        product_repo = ProductRepository(db)
        vendor_repo = VendorRepository(db)
        
        # Get vendor for current user
        vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Verify product ownership
        product = await product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_vendor_id = str(product.get("vendor_id"))
        
        if product_vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this product"
            )
        
        # Update only allowed fields
        allowed_fields = ["is_active", "stock", "price", "original_price", "featured"]
        filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Add updated timestamp
        filtered_update["updated_at"] = datetime.utcnow()
        
        # Update the product
        from bson import ObjectId
        result = await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": filtered_update}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to product"
            )
        
        # Get updated product
        updated_product = await product_repo.get_product_by_id(product_id)
        
        return {
            "message": "Product updated successfully",
            "product": product_repo.format_product_response(updated_product, include_vendor_info=True)
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.patch("/{product_id}", response_model=Dict[str, Any])
async def patch_product(
    product_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Partially update product (e.g., toggle is_active)."""
    try:
        product_repo = ProductRepository(db)
        vendor_repo = VendorRepository(db)
        
        # Get vendor for current user
        vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Verify product ownership
        product = await product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_vendor_id = str(product.get("vendor_id"))
        
        if product_vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this product"
            )
        
        # Update only allowed fields
        allowed_fields = ["is_active", "stock", "price", "original_price", "featured"]
        filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Add updated timestamp
        filtered_update["updated_at"] = datetime.utcnow()
        
        # Update the product
        from bson import ObjectId
        result = await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": filtered_update}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to product"
            )
        
        # Get updated product
        updated_product = await product_repo.get_product_by_id(product_id)
        
        return {
            "message": "Product updated successfully",
            "product": product_repo.format_product_response(updated_product, include_vendor_info=True)
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.post("/my-products/{product_id}/images")
async def upload_product_images(
    product_id: str,
    images: List[UploadFile] = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Upload images for vendor's product."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Verify product ownership
    product = await product_repo.get_product_by_id(product_id)
    if not product or product["vendor_id"] != vendor.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Upload images
    uploaded_images = []
    for image in images:
        if not validate_file_type(image, ALLOWED_IMAGE_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for {image.filename}"
            )
        
        image_info = await file_manager.save_product_image(
            image, vendor.id, product_id
        )
        uploaded_images.append({
            "url": image_info["original"],
            "thumbnail_url": image_info["thumbnail"],
            "alt_text": f"{product['name']} - {len(uploaded_images) + 1}",
            "is_primary": len(uploaded_images) == 0,
            "sort_order": len(uploaded_images)
        })
    
    return {
        "message": f"Uploaded {len(uploaded_images)} images successfully",
        "images": uploaded_images
    }


@router.put("/my-products/{product_id}/inventory")
async def update_product_inventory(
    product_id: str,
    stock_quantity: int = Form(...),
    size: Optional[str] = Form(None),
    variant_id: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update product inventory."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    updated_product = await product_repo.update_inventory(
        product_id, vendor.id, stock_quantity, size, variant_id
    )
    
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or update failed"
        )
    
    return {
        "message": "Inventory updated successfully",
        "product": product_repo.format_product_response(updated_product, include_vendor_info=True)
    }


@router.delete("/my-products/{product_id}")
async def delete_my_product(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Soft delete vendor's product."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    success = await product_repo.delete_product(product_id, vendor.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"message": "Product deleted successfully"}


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete product by ID (vendor ownership verified)."""
    try:
        product_repo = ProductRepository(db)
        vendor_repo = VendorRepository(db)
        
        # Get vendor for current user
        vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Verify product ownership
        product = await product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_vendor_id = str(product.get("vendor_id"))
        
        if product_vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this product"
            )
        
        # Soft delete the product
        from bson import ObjectId
        result = await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "deleted": True,
                    "deleted_at": datetime.utcnow(),
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete product"
            )
        
        return {"message": "Product deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )

# Public product browsing endpoints
@router.get("/test-images", response_model=Dict[str, Any])
async def test_images(db = Depends(get_database)):
    """Test endpoint to verify image data structure."""
    product_repo = ProductRepository(db)
    
    # Get one product with images
    product = await db.products.find_one({"images": {"$exists": True, "$ne": []}})
    
    if not product:
        return {
            "message": "No products with images found",
            "raw_product": None,
            "formatted_product": None
        }
    
    # Format the product
    formatted = product_repo.format_product_response(product)
    formatted_dict = formatted.dict() if hasattr(formatted, 'dict') else formatted.model_dump()
    
    return {
        "message": "Product with images found",
        "product_id": str(product["_id"]),
        "product_name": product.get("name"),
        "raw_images_count": len(product.get("images", [])),
        "raw_images": product.get("images", []),
        "formatted_images_count": len(formatted_dict.get("images", [])) if formatted_dict.get("images") else 0,
        "formatted_images": formatted_dict.get("images", []),
        "full_formatted_product": formatted_dict
    }

# Public product browsing endpoints
@router.get("", response_model=Dict[str, Any])
async def browse_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    jewelry_type: Optional[JewelryType] = Query(None),
    metal_type: Optional[MetalType] = Query(None),
    category: Optional[str] = Query(None, description="Single category filter"),
    categories: Optional[str] = Query(None, description="Comma-separated category IDs"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    featured_only: bool = Query(False),
    in_stock_only: bool = Query(True),
    sort_by: str = Query("created_at", pattern="^(created_at|price|rating_avg|name|view_count)$"),
    sort_order: int = Query(-1, ge=-1, le=1),
    search: Optional[str] = Query(None, min_length=2),
    db = Depends(get_database)
):
    """Browse products with comprehensive filtering including vendor filter."""
    product_repo = ProductRepository(db)
    
    # Parse categories - support both singular 'category' and plural 'categories'
    category_list = None
    if category:
        # Single category from 'category' parameter
        category_list = [category.strip()]
    elif categories:
        # Multiple categories from 'categories' parameter
        category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
    
    products, total = await product_repo.get_products(
        skip=skip,
        limit=limit,
        vendor_id=vendor_id,
        jewelry_type=jewelry_type,
        metal_type=metal_type,
        categories=category_list,
        min_price=min_price,
        max_price=max_price,
        featured_only=featured_only,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        sort_order=sort_order,
        search_query=search
    )
    
    # If no products exist at all and no specific filters are applied, seed some sample products
    if total == 0 and not any([vendor_id, jewelry_type, metal_type, category_list, min_price, max_price, search, featured_only]):
        try:
            print("[browse_products] No products in database, creating sample products across categories...")
            
            # Create a default vendor if none exists
            vendor_id_default = None
            default_vendor = await db.vendors.find_one({"business_name": "Sample Jewelry Store"})
            if not default_vendor:
                from bson import ObjectId
                vendor_data = {
                    "user_id": "dummy_user_id",
                    "business_name": "Sample Jewelry Store",
                    "business_email": "sample@jewelrystore.com",
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                vendor_result = await db.vendors.insert_one(vendor_data)
                vendor_id_default = str(vendor_result.inserted_id)
            else:
                vendor_id_default = str(default_vendor["_id"])
            
            # Create sample products across multiple categories
            sample_products = [
                {"name": "Gold Chain Necklace", "cat": "necklaces", "price": 299.99, "metal": "18k_gold", "stone": None},
                {"name": "Diamond Engagement Ring", "cat": "rings", "price": 1299.99, "metal": "platinum", "stone": "diamond"},
                {"name": "Diamond Stud Earrings", "cat": "earrings", "price": 499.99, "metal": "white_gold", "stone": "diamond"},
                {"name": "Tennis Bracelet", "cat": "bracelets", "price": 799.99, "metal": "white_gold", "stone": "diamond"},
                {"name": "Heart Pendant", "cat": "pendants", "price": 179.99, "metal": "rose_gold", "stone": None},
                {"name": "Floral Brooch", "cat": "brooches", "price": 159.99, "metal": "sterling_silver", "stone": "cubic_zirconia"},
                {"name": "Diamond Bezel Watch", "cat": "watches", "price": 2499.99, "metal": "stainless_steel", "stone": "diamond"},
                {"name": "Chain Anklet", "cat": "anklets", "price": 89.99, "metal": "sterling_silver", "stone": None},
                {"name": "Rope Chain", "cat": "chains", "price": 199.99, "metal": "18k_gold", "stone": None},
                {"name": "Pearl Strand Necklace", "cat": "necklaces", "price": 199.99, "metal": "sterling_silver", "stone": "pearl"},
                {"name": "Gold Wedding Band", "cat": "rings", "price": 399.99, "metal": "18k_gold", "stone": None},
                {"name": "Pearl Drop Earrings", "cat": "earrings", "price": 149.99, "metal": "sterling_silver", "stone": "pearl"},
            ]
            
            created_products = []
            for idx, item_data in enumerate(sample_products):
                cat_key = item_data["cat"]
                
                # Generate placeholder images for the product
                product_images = [
                    {
                        "url": f"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=800&auto=format&fit=crop&q=80&ixid={idx+1}",
                        "thumbnail_url": f"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=200&auto=format&fit=crop&q=80&ixid={idx+1}",
                        "alt_text": f"{item_data['name']} - Main Image",
                        "is_primary": True,
                        "sort_order": 0
                    },
                    {
                        "url": f"https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=800&auto=format&fit=crop&q=80&ixid={idx+2}",
                        "thumbnail_url": f"https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=200&auto=format&fit=crop&q=80&ixid={idx+2}",
                        "alt_text": f"{item_data['name']} - Detail View",
                        "is_primary": False,
                        "sort_order": 1
                    },
                    {
                        "url": f"https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=800&auto=format&fit=crop&q=80&ixid={idx+3}",
                        "thumbnail_url": f"https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=200&auto=format&fit=crop&q=80&ixid={idx+3}",
                        "alt_text": f"{item_data['name']} - Alternate Angle",
                        "is_primary": False,
                        "sort_order": 2
                    }
                ]
                
                product_doc = {
                    "vendor_id": vendor_id_default,
                    "name": item_data["name"],
                    "description": f"Beautiful {item_data['name'].lower()} crafted with precision and care. Perfect for any occasion.",
                    "category": cat_key,
                    "jewelry_type": cat_key.rstrip('s') if cat_key.endswith('s') and cat_key != 'earrings' else cat_key,
                    "price": item_data["price"],
                    "original_price": round(item_data["price"] * 1.2, 2),
                    "discount_percentage": 17,
                    "stock": 15,
                    "stock_quantity": 15,
                    "sku": f"SAMPLE-{idx+1:04d}",
                    "metal_type": item_data["metal"],
                    "stone_type": item_data["stone"],
                    "weight": 5.5,
                    "is_active": True,
                    "status": "active",
                    "condition": "new",
                    "track_inventory": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "view_count": 0,
                    "favorite_count": 0,
                    "rating_avg": 4.5,
                    "rating_count": 12,
                    "images": product_images,
                    "deleted": False
                }
                result = await db.products.insert_one(product_doc)
                product_doc["_id"] = result.inserted_id
                created_products.append(product_doc)
            
            print(f"[browse_products] Created {len(created_products)} sample products")
            
            # Return the newly created products
            products = created_products[skip:skip + limit]
            total = len(created_products)
            
        except Exception as e:
            print(f"[browse_products] Failed to create sample products: {e}")
            import traceback
            traceback.print_exc()
            products = []
            total = 0
    
    # Format products and convert to dict for JSON serialization
    formatted_products = []
    for p in products:
        product_response = product_repo.format_product_response(p)
        # Convert Pydantic model to dict to ensure proper serialization
        product_dict = product_response.dict() if hasattr(product_response, 'dict') else product_response.model_dump()
        formatted_products.append(product_dict)
    
    return {
        "products": formatted_products,
        "total": total,
        "skip": skip,
        "limit": limit,
        "filters": {
            "vendor_id": vendor_id,
            "jewelry_type": jewelry_type.value if jewelry_type else None,
            "metal_type": metal_type.value if metal_type else None,
            "categories": category_list,
            "price_range": [min_price, max_price],
            "featured_only": featured_only,
            "in_stock_only": in_stock_only,
            "search": search
        }
    }

@router.get("/featured", response_model=List[ProductResponse])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50),
    jewelry_type: Optional[JewelryType] = Query(None),
    db = Depends(get_database)
):
    """Get featured jewelry products."""
    product_repo = ProductRepository(db)
    
    products = await product_repo.get_featured_products(limit=limit, jewelry_type=jewelry_type)
    
    return [product_repo.format_product_response(p) for p in products]


@router.get("/trending", response_model=List[ProductResponse])
async def get_trending_products(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db = Depends(get_database)
):
    """Get trending products based on recent activity."""
    product_repo = ProductRepository(db)
    
    products = await product_repo.get_trending_products(days=days, limit=limit)
    
    return [product_repo.format_product_response(p) for p in products]


@router.get("/categories/{category}/products", response_model=Dict[str, Any])
async def get_products_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1, ge=-1, le=1),
    db = Depends(get_database)
):
    """Get products in a specific category."""
    product_repo = ProductRepository(db)
    
    products, total = await product_repo.get_products(
        skip=skip,
        limit=limit,
        categories=[category],
        sort_by=sort_by,
        sort_order=sort_order,
        in_stock_only=True
    )
    
    # If no products exist for this category, create dummy products
    if total == 0:
        try:
            print(f"[get_products_by_category] No products found for category '{category}', creating dummy products...")
            
            # Create a default vendor if none exists
            vendor_id = None
            default_vendor = await db.vendors.find_one({"business_name": "Sample Jewelry Store"})
            if not default_vendor:
                from bson import ObjectId
                vendor_data = {
                    "user_id": "dummy_user_id",
                    "business_name": "Sample Jewelry Store",
                    "business_email": "sample@jewelrystore.com",
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                vendor_result = await db.vendors.insert_one(vendor_data)
                vendor_id = str(vendor_result.inserted_id)
            else:
                vendor_id = str(default_vendor["_id"])
            
            # Define dummy products for this category
            category_products = {
                "necklaces": [
                    {"name": "Gold Chain Necklace", "price": 299.99, "metal": "18k_gold", "stone": None},
                    {"name": "Diamond Pendant Necklace", "price": 599.99, "metal": "white_gold", "stone": "diamond"},
                    {"name": "Pearl Strand Necklace", "price": 199.99, "metal": "sterling_silver", "stone": "pearl"}
                ],
                "rings": [
                    {"name": "Diamond Engagement Ring", "price": 1299.99, "metal": "platinum", "stone": "diamond"},
                    {"name": "Gold Wedding Band", "price": 399.99, "metal": "18k_gold", "stone": None},
                    {"name": "Sapphire Cocktail Ring", "price": 899.99, "metal": "white_gold", "stone": "sapphire"}
                ],
                "earrings": [
                    {"name": "Diamond Stud Earrings", "price": 499.99, "metal": "white_gold", "stone": "diamond"},
                    {"name": "Pearl Drop Earrings", "price": 149.99, "metal": "sterling_silver", "stone": "pearl"},
                    {"name": "Gold Hoop Earrings", "price": 249.99, "metal": "18k_gold", "stone": None}
                ],
                "bracelets": [
                    {"name": "Tennis Bracelet", "price": 799.99, "metal": "white_gold", "stone": "diamond"},
                    {"name": "Gold Chain Bracelet", "price": 349.99, "metal": "18k_gold", "stone": None},
                    {"name": "Charm Bracelet", "price": 199.99, "metal": "sterling_silver", "stone": None}
                ],
                "pendants": [
                    {"name": "Heart Pendant", "price": 179.99, "metal": "rose_gold", "stone": None},
                    {"name": "Emerald Pendant", "price": 549.99, "metal": "18k_gold", "stone": "emerald"},
                    {"name": "Cross Pendant", "price": 129.99, "metal": "sterling_silver", "stone": None}
                ],
                "brooches": [
                    {"name": "Floral Brooch", "price": 159.99, "metal": "sterling_silver", "stone": "cubic_zirconia"},
                    {"name": "Vintage Cameo Brooch", "price": 229.99, "metal": "18k_gold", "stone": None},
                    {"name": "Pearl Cluster Brooch", "price": 189.99, "metal": "white_gold", "stone": "pearl"}
                ],
                "watches": [
                    {"name": "Diamond Bezel Watch", "price": 2499.99, "metal": "stainless_steel", "stone": "diamond"},
                    {"name": "Gold Dress Watch", "price": 1599.99, "metal": "18k_gold", "stone": None},
                    {"name": "Silver Sport Watch", "price": 899.99, "metal": "stainless_steel", "stone": None}
                ],
                "anklets": [
                    {"name": "Chain Anklet", "price": 89.99, "metal": "sterling_silver", "stone": None},
                    {"name": "Charm Anklet", "price": 119.99, "metal": "18k_gold", "stone": None},
                    {"name": "Beaded Anklet", "price": 69.99, "metal": "sterling_silver", "stone": "turquoise"}
                ],
                "chains": [
                    {"name": "Rope Chain", "price": 199.99, "metal": "18k_gold", "stone": None},
                    {"name": "Cuban Link Chain", "price": 349.99, "metal": "18k_gold", "stone": None},
                    {"name": "Box Chain", "price": 129.99, "metal": "sterling_silver", "stone": None}
                ]
            }
            
            # Normalize category name to match keys
            cat_key = category.lower()
            dummy_products_data = category_products.get(cat_key, [
                {"name": f"Sample {category} Item 1", "price": 199.99, "metal": "18k_gold", "stone": None},
                {"name": f"Sample {category} Item 2", "price": 299.99, "metal": "sterling_silver", "stone": None},
                {"name": f"Sample {category} Item 3", "price": 399.99, "metal": "white_gold", "stone": "diamond"}
            ])
            
            created_products = []
            for idx, item_data in enumerate(dummy_products_data):
                # Generate placeholder images for the product
                product_images = [
                    {
                        "url": f"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=800&auto=format&fit=crop&q=80&ixid={idx+1}",
                        "thumbnail_url": f"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=200&auto=format&fit=crop&q=80&ixid={idx+1}",
                        "alt_text": f"{item_data['name']} - Main Image",
                        "is_primary": True,
                        "sort_order": 0
                    },
                    {
                        "url": f"https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=800&auto=format&fit=crop&q=80&ixid={idx+2}",
                        "thumbnail_url": f"https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=200&auto=format&fit=crop&q=80&ixid={idx+2}",
                        "alt_text": f"{item_data['name']} - Detail View",
                        "is_primary": False,
                        "sort_order": 1
                    },
                    {
                        "url": f"https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=800&auto=format&fit=crop&q=80&ixid={idx+3}",
                        "thumbnail_url": f"https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=200&auto=format&fit=crop&q=80&ixid={idx+3}",
                        "alt_text": f"{item_data['name']} - Alternate Angle",
                        "is_primary": False,
                        "sort_order": 2
                    }
                ]
                
                product_doc = {
                    "vendor_id": vendor_id,
                    "name": item_data["name"],
                    "description": f"Beautiful {item_data['name'].lower()} crafted with precision and care.",
                    "category": cat_key,
                    "jewelry_type": cat_key.rstrip('s') if cat_key.endswith('s') and cat_key != 'earrings' else cat_key,
                    "price": item_data["price"],
                    "original_price": item_data["price"] * 1.2,
                    "discount_percentage": 17,
                    "stock": 10,
                    "stock_quantity": 10,
                    "sku": f"SAMPLE-{cat_key.upper()}-{idx+1:03d}",
                    "metal_type": item_data["metal"],
                    "stone_type": item_data["stone"],
                    "weight": 5.5,
                    "is_active": True,
                    "status": "active",
                    "condition": "new",
                    "track_inventory": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "view_count": 0,
                    "favorite_count": 0,
                    "rating_avg": 4.5,
                    "rating_count": 12,
                    "images": product_images,
                    "deleted": False
                }
                result = await db.products.insert_one(product_doc)
                product_doc["_id"] = result.inserted_id
                created_products.append(product_doc)
            
            print(f"[get_products_by_category] Created {len(created_products)} dummy products for category '{category}'")
            
            # Return the newly created products
            products = created_products[skip:skip + limit]
            total = len(created_products)
            
        except Exception as e:
            print(f"[get_products_by_category] Failed to create dummy products: {e}")
            import traceback
            traceback.print_exc()
            # If creation fails, return empty result instead of crashing
            products = []
            total = 0
    
    # Format products and convert to dict for JSON serialization
    formatted_products = []
    for p in products:
        product_response = product_repo.format_product_response(p)
        # Convert Pydantic model to dict to ensure proper serialization
        product_dict = product_response.dict() if hasattr(product_response, 'dict') else product_response.model_dump()
        formatted_products.append(product_dict)
    
    return {
        "products": formatted_products,
        "total": total,
        "skip": skip,
        "limit": limit,
        "category": category
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_details(
    product_id: str,
    increment_views: bool = Query(True),
    db = Depends(get_database)
):
    """Get detailed product information."""
    product_repo = ProductRepository(db)
    
    product = await product_repo.get_product_by_id(
        product_id, 
        increment_views=increment_views
    )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Only show active products to public
    if product.get("status") != ProductStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product_repo.format_product_response(product)


@router.get("/vendors/{vendor_id}/products", response_model=Dict[str, Any])
async def get_vendor_storefront_products(
    vendor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    jewelry_type: Optional[JewelryType] = Query(None),
    featured_only: bool = Query(False),
    db = Depends(get_database)
):
    """Get products from a specific vendor's storefront."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Verify vendor exists and is active
    vendor = await vendor_repo.get_vendor_by_id(vendor_id)
    if not vendor or vendor.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    products, total = await product_repo.get_products(
        skip=skip,
        limit=limit,
        vendor_id=vendor_id,
        jewelry_type=jewelry_type,
        featured_only=featured_only,
        in_stock_only=True,
        status=ProductStatus.ACTIVE
    )
    
    return {
        "vendor": {
            "id": vendor.id,
            "business_name": vendor.business_name,
            "storefront": vendor.storefront or {}
        },
        "products": [product_repo.format_product_response(p) for p in products],
        "total": total,
        "skip": skip,
        "limit": limit
    }


# Search and filtering endpoints
@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    db = Depends(get_database)
):
    """Get search suggestions based on product names and tags."""
    product_repo = ProductRepository(db)
    
    # Simple text search for suggestions
    pipeline = [
        {
            "$match": {
                "status": ProductStatus.ACTIVE.value,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"search_keywords": {"$regex": query, "$options": "i"}},
                    {"tags": {"$regex": query, "$options": "i"}}
                ]
            }
        },
        {
            "$project": {
                "name": 1,
                "jewelry_type": 1,
                "metal_type": 1,
                "price": 1
            }
        },
        {"$limit": limit}
    ]
    
    suggestions = await product_repo.collection.aggregate(pipeline).to_list(limit)
    
    return {
        "query": query,
        "suggestions": [
            {
                "id": str(s["_id"]),
                "name": s["name"],
                "jewelry_type": s["jewelry_type"],
                "metal_type": s["metal_type"],
                "price": s["price"]
            }
            for s in suggestions
        ]
    }


# Analytics endpoints for vendors
@router.get("/my-products/analytics/overview")
async def get_product_analytics_overview(
    days: int = Query(30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get product analytics overview for vendor."""
    product_repo = ProductRepository(db)
    vendor_repo = VendorRepository(db)
    
    # Get vendor for current user
    vendor = await vendor_repo.get_vendor_by_user_id(current_user["user_id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Get vendor's products analytics
    since_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
    
    pipeline = [
        {"$match": {"vendor_id": vendor.id}},
        {
            "$group": {
                "_id": None,
                "total_products": {"$sum": 1},
                "active_products": {
                    "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                },
                "total_views": {"$sum": "$view_count"},
                "total_favorites": {"$sum": "$favorite_count"},
                "avg_rating": {"$avg": "$rating_avg"},
                "low_stock_count": {
                    "$sum": {
                        "$cond": [
                            {"$lte": ["$stock_quantity", "$low_stock_threshold"]},
                            1,
                            0
                        ]
                    }
                }
            }
        }
    ]
    
    result = await product_repo.collection.aggregate(pipeline).to_list(1)
    analytics = result[0] if result else {
        "total_products": 0,
        "active_products": 0,
        "total_views": 0,
        "total_favorites": 0,
        "avg_rating": 0,
        "low_stock_count": 0
    }
    
    # Get low stock products
    low_stock_products = await product_repo.get_low_stock_products(vendor.id)
    
    return {
        "overview": analytics,
        "low_stock_products": [
            {
                "id": str(p["_id"]),
                "name": p["name"],
                "sku": p.get("sku"),
                "stock_quantity": p["stock_quantity"],
                "low_stock_threshold": p["low_stock_threshold"]
            }
            for p in low_stock_products[:5]  # Top 5 low stock items
        ]
    }


