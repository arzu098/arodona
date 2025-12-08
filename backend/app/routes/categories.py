"""
Category API endpoints.
Handles CRUD operations for categories with support for hierarchical relationships.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from bson import ObjectId
from app.databases.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryOut, CategoryListOut,
    CategoryWithChildren, CategoryProductsOut
)
from app.databases.repositories.category import CategoryRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.category_utils import (
    resolve_category_ids, get_descendant_category_ids, build_category_tree
)

router = APIRouter(prefix="/api/categories", tags=["Categories"])


async def get_category_repository() -> CategoryRepository:
    """Dependency to get category repository"""
    db = get_database()
    return CategoryRepository(db)


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repository)
):
    """
    Create a new category (Protected - Requires Authentication)
    
    - **name**: Category name (required)
    - **slug**: URL-friendly slug (auto-generated if not provided)
    - **parent_id**: Parent category ID or slug for hierarchical categories (optional)
    - **description**: Category description (optional)
    - **metadata**: Additional metadata object (optional)
    """
    try:
        # Resolve parent_id if provided
        parent_id = None
        if category_data.parent_id:
            try:
                parent_ids = await resolve_category_ids([category_data.parent_id], get_database())
                parent_id = parent_ids[0]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent category not found: {category_data.parent_id}"
                )
        
        # Create category
        category = await repo.create_category(
            name=category_data.name,
            slug=category_data.slug,
            parent_id=parent_id,
            description=category_data.description,
            metadata=category_data.metadata
        )
        
        # Format response
        return {
            '_id': str(category['_id']),
            'name': category['name'],
            'slug': category['slug'],
            'parent_id': str(category['parent_id']) if category['parent_id'] else None,
            'description': category['description'],
            'metadata': category['metadata'],
            'created_at': category['created_at'],
            'updated_at': category['updated_at']
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating category: {str(e)}"
        )


@router.get("/", response_model=CategoryListOut)
async def list_categories(
    parent_id: Optional[str] = Query(None),
    flat: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    repo: CategoryRepository = Depends(get_category_repository)
):
    """
    List categories with optional parent filtering and nesting.
    
    - **parent_id**: Filter by parent category ID or slug (optional)
    - **flat**: If true (default), return flat list; if false, return nested tree
    - **skip**: Number of items to skip (pagination)
    - **limit**: Number of items to return (pagination)
    """
    try:
        db = get_database()
        
        # Resolve parent_id if provided
        parent_obj_id = None
        if parent_id:
            try:
                parent_ids = await resolve_category_ids([parent_id], db)
                parent_obj_id = parent_ids[0]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent category not found: {parent_id}"
                )
        
        if flat:
            # Return flat list
            categories, total = await repo.get_categories_by_parent(
                parent_id=parent_obj_id,
                skip=skip,
                limit=limit
            )
            
            # If there are no categories in the database, create a small
            # set of sensible default categories so the frontend/navbar
            # has options to display.
            if total == 0:
                try:
                    default_names = [
                        'Necklaces', 'Rings', 'Earrings', 'Bracelets',
                        'Pendants', 'Brooches', 'Watches', 'Anklets', 'Chains'
                    ]
                    created = []
                    for name in default_names:
                        # Use repository create to ensure slugs and metadata are set
                        cat = await repo.create_category(name=name)
                        created.append(cat)

                    # Re-read the categories we just created (respecting pagination)
                    categories = created[skip:skip + limit]
                    total = len(created)
                except Exception as e:
                    # If creation fails, don't crash the API; return empty list
                    # with an informative message logged.
                    print(f"[list_categories] Failed to create default categories: {e}")
                    categories = []
                    total = 0

            formatted = []
            for cat in categories:
                formatted.append({
                    '_id': str(cat['_id']),
                    'name': cat['name'],
                    'slug': cat['slug'],
                    'parent_id': str(cat['parent_id']) if cat['parent_id'] else None,
                    'description': cat.get('description'),
                    'metadata': cat.get('metadata', {}),
                    'created_at': cat.get('created_at'),
                    'updated_at': cat.get('updated_at')
                })

            return {
                'total': total,
                'skip': skip,
                'limit': limit,
                'categories': formatted
            }
        else:
            # Return nested tree
            tree = await build_category_tree(db, parent_obj_id)
            return {
                'total': len(tree),
                'skip': 0,
                'limit': len(tree),
                'categories': tree
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing categories: {str(e)}"
        )


@router.get("/{slug_or_id}", response_model=CategoryOut)
async def get_category(
    slug_or_id: str,
    include_product_count: bool = Query(False),
    repo: CategoryRepository = Depends(get_category_repository)
):
    """
    Get a category by ID or slug.
    
    - **slug_or_id**: Category ID or slug
    - **include_product_count**: If true, include number of products in this category
    """
    try:
        # Try as ObjectId first
        category = None
        try:
            category = await repo.get_category_by_id(slug_or_id)
        except Exception:
            pass
        
        # Try as slug
        if not category:
            category = await repo.get_category_by_slug(slug_or_id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category not found: {slug_or_id}"
            )
        
        result = {
            '_id': str(category['_id']),
            'name': category['name'],
            'slug': category['slug'],
            'parent_id': str(category['parent_id']) if category['parent_id'] else None,
            'description': category['description'],
            'metadata': category['metadata'],
            'created_at': category['created_at'],
            'updated_at': category['updated_at']
        }
        
        if include_product_count:
            product_count = await repo.count_products_in_category(category['_id'])
            result['product_count'] = product_count
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving category: {str(e)}"
        )


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user: dict = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repository)
):
    """
    Update a category (Protected - Requires Authentication)
    
    Prevents circular parent assignments (category cannot be its own descendant).
    """
    try:
        # Resolve parent_id if provided
        parent_id = None
        if category_data.parent_id:
            try:
                parent_ids = await resolve_category_ids([category_data.parent_id], get_database())
                parent_id = parent_ids[0]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent category not found: {category_data.parent_id}"
                )
        
        # Update category
        updated = await repo.update_category(
            category_id=category_id,
            name=category_data.name,
            slug=category_data.slug,
            parent_id=parent_id,
            description=category_data.description,
            metadata=category_data.metadata
        )
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        return {
            '_id': str(updated['_id']),
            'name': updated['name'],
            'slug': updated['slug'],
            'parent_id': str(updated['parent_id']) if updated['parent_id'] else None,
            'description': updated['description'],
            'metadata': updated['metadata'],
            'created_at': updated['created_at'],
            'updated_at': updated['updated_at']
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating category: {str(e)}"
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    force: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repository)
):
    """
    Delete a category (Protected - Requires Authentication)
    
    - **category_id**: Category ID to delete
    - **force**: If true, reassign child categories to parent and remove from products
    
    Returns 400 if category has children or products and force=false.
    """
    try:
        db = get_database()
        
        # Check if category exists
        category = await repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        cat_obj_id = ObjectId(category_id)
        categories_col = db['categories']
        products_col = db['products']
        
        # Check for children
        children = await categories_col.find_one({'parent_id': cat_obj_id})
        # Check for products
        products = await products_col.find_one({'categories': cat_obj_id})
        
        if (children or products) and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with children or products. Use force=true to override."
            )
        
        if force:
            # Reassign children to this category's parent
            parent_id = category.get('parent_id')
            await categories_col.update_many(
                {'parent_id': cat_obj_id},
                {'$set': {'parent_id': parent_id}}
            )
            
            # Remove this category from products
            await products_col.update_many(
                {'categories': cat_obj_id},
                {'$pull': {'categories': cat_obj_id}}
            )
        
        # Delete the category
        deleted = await repo.delete_category(category_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete category"
            )
        
        return {
            'message': 'Category deleted successfully',
            'category_id': category_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting category: {str(e)}"
        )
