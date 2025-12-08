"""Router for jewelry product management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.connection import get_database
from app.databases.repositories.jewelry import JewelryRepository
from app.databases.schemas.jewelry import (
    JewelryCreate,
    JewelryOut,
    JewelryCollection,
    JewelryVariant,
    JewelryInventoryUpdateBulk,
    JewelryCertification,
    JewelryCustomization
)
from app.utils.security import verify_admin

router = APIRouter(prefix="/api", tags=["jewelry"])

def get_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> JewelryRepository:
    return JewelryRepository(db)

@router.post("/admin/products", response_model=JewelryOut, status_code=status.HTTP_201_CREATED, responses={400: {"model": dict}})
async def create_product(
    product: JewelryCreate,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
) -> JewelryOut:
    """Create a new jewelry product."""
    # Convert to dict for validation
    product_dict = product.model_dump()
    
    # Validate required fields
    required_fields = ["name", "description", "price", "category_id", "sku", "attributes"]
    missing_fields = [field for field in required_fields if field not in product_dict or not product_dict[field]]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": [f"Missing required field: {field}" for field in missing_fields]}
        )

    # Validate price
    if product_dict["price"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": ["Price must be positive"]}
        )

    return await repo.create_product(product)

@router.get("/products/search", response_model=dict)
async def search_products(
    repo: JewelryRepository = Depends(get_repository),
    metal: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    diamond_carat_min: Optional[float] = None,
    diamond_clarity: Optional[str] = None,
    sort: str = "price_desc",
    limit: int = 10,
    offset: int = 0
):
    """Search jewelry products with filters."""
    results = await repo.search_products(
        metal=metal,
        min_price=min_price,
        max_price=max_price,
        diamond_carat_min=diamond_carat_min,
        diamond_clarity=diamond_clarity,
        sort=sort,
        limit=limit,
        offset=offset
    )
    return {
        "products": results.get("products", []),
        "total": results.get("total", 0)
    }

@router.post("/admin/products/collections", status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection: JewelryCollection,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
):
    """Create a new jewelry collection."""
    result = await repo.create_collection(collection)
    result["collection_id"] = str(result.get("_id"))
    return result

@router.post("/admin/products/variants", response_model=dict)
async def create_variants(
    data: dict,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
):
    """Create variants for a jewelry product."""
    if not all(k in data for k in ["base_sku", "variants"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Missing required fields"}
        )

    variants = [JewelryVariant(**v) for v in data["variants"]]
    result = await repo.create_product_variants(data["base_sku"], variants)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return {"variants": result}

@router.put("/admin/products/{sku}/inventory", response_model=dict)
async def update_inventory(
    sku: str,
    inventory: dict,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
):
    """Update inventory for a jewelry product."""
    if "stock_updates" not in inventory:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Missing stock_updates field"}
        )
    
    # Convert to Pydantic model
    try:
        inventory_model = JewelryInventoryUpdateBulk(**inventory)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e)}
        )
        
    result = await repo.update_inventory(sku, inventory_model)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return {
        "total_stock": sum(update.quantity for update in inventory_model.stock_updates),
        "stock_by_size": {update.size: update.quantity for update in inventory_model.stock_updates}
    }

@router.post("/admin/products/{sku}/certification", response_model=dict)
async def add_certification(
    sku: str,
    certification: JewelryCertification,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
):
    """Add certification details to a jewelry product."""
    result = await repo.add_certification(sku, certification)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return {
        "certification": {
            **result,
            "verification_url": f"https://example.com/verify/{result['number']}"
        }
    }

@router.post("/admin/products/{sku}/customization")
async def set_customization_options(
    sku: str,
    options: JewelryCustomization,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
):
    """Set customization options for a jewelry product."""
    result = await repo.set_customization_options(sku, options)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.post("/admin/products/bulk", response_model=dict)
async def bulk_create_products(
    data: dict,
    repo: JewelryRepository = Depends(get_repository),
    admin: bool = Depends(verify_admin)
):
    """Bulk create jewelry products."""
    if "products" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "No products provided"}
        )

    try:
        products = []
        validation_errors = []
        for idx, p in enumerate(data["products"]):
            try:
                # Add required fields if missing with defaults
                if "stock_quantity" not in p:
                    p["stock_quantity"] = 0
                if "images" not in p:
                    p["images"] = []
                products.append(JewelryCreate(**p))
            except Exception as e:
                validation_errors.append(f"Product {idx}: {str(e)}")
        
        if validation_errors:
            return {
                "created": [],
                "errors": validation_errors
            }

        result = await repo.bulk_create_products(products)
        return {
            "created": result.get("created", []),
            "errors": result.get("errors", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e)}
        )