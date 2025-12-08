"""
Category repository for database operations.
Handles CRUD operations for categories collection.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Tuple
from app.utils.slug_utils import make_unique_slug
from app.utils.category_utils import check_circular_parent


class CategoryRepository:
    """Repository for category-related database operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db['categories']
    
    async def create_category(
        self,
        name: str,
        slug: Optional[str] = None,
        parent_id: Optional[ObjectId] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Create a new category.
        Auto-generates slug if not provided.
        
        Args:
            name: Category name
            slug: URL-friendly slug (auto-generated if not provided)
            parent_id: Parent category ObjectId (for hierarchical categories)
            description: Optional category description
            metadata: Optional metadata object
            
        Returns:
            The created category document
        """
        # Generate unique slug if not provided
        if not slug:
            slug = await make_unique_slug(name, self.collection)
        else:
            # Ensure provided slug is unique
            slug = await make_unique_slug(name, self.collection)
        
        category_data = {
            'name': name,
            'slug': slug,
            'parent_id': parent_id,
            'description': description,
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.insert_one(category_data)
        category_data['_id'] = result.inserted_id
        return category_data
    
    async def get_category_by_id(self, category_id: str) -> Optional[dict]:
        """Get category by MongoDB ObjectId"""
        try:
            return await self.collection.find_one({'_id': ObjectId(category_id)})
        except Exception:
            return None
    
    async def get_category_by_slug(self, slug: str) -> Optional[dict]:
        """Get category by slug"""
        return await self.collection.find_one({'slug': slug})
    
    async def get_categories_by_parent(
        self,
        parent_id: Optional[ObjectId] = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[dict], int]:
        """
        Get categories by parent_id with pagination.
        
        Args:
            parent_id: Parent category ObjectId (None for root categories)
            skip: Number of documents to skip
            limit: Number of documents to return
            
        Returns:
            Tuple of (categories list, total count)
        """
        query = {'parent_id': parent_id}
        total = await self.collection.count_documents(query)
        categories = await self.collection.find(query).skip(skip).limit(limit).to_list(limit)
        return categories, total
    
    async def get_all_categories(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[dict], int]:
        """Get all categories with pagination"""
        total = await self.collection.count_documents({})
        categories = await self.collection.find({}).skip(skip).limit(limit).to_list(limit)
        return categories, total
    
    async def update_category(
        self,
        category_id: str,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        parent_id: Optional[ObjectId] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Update category details.
        Checks for circular parent assignments.
        
        Args:
            category_id: Category ObjectId as string
            name: New name (if provided)
            slug: New slug (auto-generated if name changed but slug not provided)
            parent_id: New parent ObjectId
            description: New description
            metadata: New metadata
            
        Returns:
            Updated category document or None if not found
        """
        try:
            obj_id = ObjectId(category_id)
        except Exception:
            return None
        
        # Check for circular parent assignment
        if parent_id:
            is_circular = await check_circular_parent(obj_id, parent_id, self.db)
            if is_circular:
                raise ValueError("Cannot assign category as its own descendant")
        
        update_data = {'updated_at': datetime.utcnow()}
        
        if name is not None:
            update_data['name'] = name
            # Generate new slug if name changed and slug not explicitly provided
            if slug is None:
                slug = await make_unique_slug(name, self.collection, category_id)
        
        if slug is not None:
            update_data['slug'] = slug
        
        if parent_id is not None:
            update_data['parent_id'] = parent_id
        
        if description is not None:
            update_data['description'] = description
        
        if metadata is not None:
            update_data['metadata'] = metadata
        
        result = await self.collection.find_one_and_update(
            {'_id': obj_id},
            {'$set': update_data},
            return_document=True
        )
        return result
    
    async def delete_category(self, category_id: str) -> bool:
        """
        Delete a category.
        
        Args:
            category_id: Category ObjectId as string
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.collection.delete_one({'_id': ObjectId(category_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def count_products_in_category(self, category_id: ObjectId) -> int:
        """
        Count products in this category.
        
        Args:
            category_id: Category ObjectId
            
        Returns:
            Number of products
        """
        products = self.db['products']
        count = await products.count_documents({'categories': category_id})
        return count
    
    async def create_indexes(self) -> None:
        """Create necessary indexes for performance"""
        # Unique index on slug
        await self.collection.create_index('slug', unique=True)
        # Index on parent_id for hierarchical queries
        await self.collection.create_index('parent_id')
