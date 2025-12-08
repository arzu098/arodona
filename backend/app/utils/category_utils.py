"""
Category utility functions for hierarchical category operations.
Includes category ID resolution, descendant lookup, and tree building.
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def resolve_category_ids(
    identifiers: List[str],
    db: AsyncIOMotorDatabase
) -> List[ObjectId]:
    """
    Resolve a list of category identifiers (IDs or slugs) to ObjectIds.
    
    Args:
        identifiers: List of category IDs (string) or slugs
        db: Motor database instance
        
    Returns:
        List of resolved ObjectIds
        
    Raises:
        ValueError: If any identifier cannot be resolved
    """
    categories_collection = db['categories']
    resolved_ids = []
    
    for identifier in identifiers:
        # Try to parse as ObjectId
        try:
            obj_id = ObjectId(identifier)
            category = await categories_collection.find_one({'_id': obj_id})
            if category:
                resolved_ids.append(obj_id)
                continue
        except Exception:
            pass
        
        # Try to find by slug
        category = await categories_collection.find_one({'slug': identifier})
        if category:
            resolved_ids.append(category['_id'])
            continue
        
        raise ValueError(f"Category not found: {identifier}")
    
    return resolved_ids


async def get_descendant_category_ids(
    category_id: ObjectId,
    db: AsyncIOMotorDatabase
) -> List[ObjectId]:
    """
    Get all descendant category IDs (recursive) for a given category.
    Uses BFS to traverse the tree.
    
    Args:
        category_id: ObjectId of the parent category
        db: Motor database instance
        
    Returns:
        List of all descendant ObjectIds (including the root)
    """
    categories_collection = db['categories']
    result = [category_id]
    queue = [category_id]
    
    while queue:
        current_id = queue.pop(0)
        children = await categories_collection.find(
            {'parent_id': current_id}
        ).to_list(None)
        
        for child in children:
            child_id = child['_id']
            result.append(child_id)
            queue.append(child_id)
    
    return result


async def build_category_tree(
    db: AsyncIOMotorDatabase,
    parent_id: Optional[ObjectId] = None
) -> List[Dict[str, Any]]:
    """
    Build a nested tree structure of categories.
    
    Args:
        db: Motor database instance
        parent_id: If provided, build tree starting from this parent (default: None for root categories)
        
    Returns:
        Nested list of category dicts with 'children' key
    """
    categories_collection = db['categories']
    query = {'parent_id': parent_id} if parent_id else {'parent_id': None}
    
    categories = await categories_collection.find(query).to_list(None)
    result = []
    
    for cat in categories:
        cat_dict = {
            'id': str(cat['_id']),
            'name': cat['name'],
            'slug': cat['slug'],
            'description': cat.get('description'),
            'metadata': cat.get('metadata'),
            'created_at': cat['created_at'],
            'updated_at': cat['updated_at']
        }
        
        # Recursively get children
        children = await build_category_tree(db, cat['_id'])
        if children:
            cat_dict['children'] = children
        
        result.append(cat_dict)
    
    return result


async def check_circular_parent(
    category_id: ObjectId,
    new_parent_id: Optional[ObjectId],
    db: AsyncIOMotorDatabase
) -> bool:
    """
    Check if assigning new_parent_id to category_id would create a circular dependency.
    
    Args:
        category_id: The category being updated
        new_parent_id: The proposed new parent
        db: Motor database instance
        
    Returns:
        True if circular (invalid), False if safe
    """
    if not new_parent_id:
        return False
    
    if category_id == new_parent_id:
        return True  # Category cannot be its own parent
    
    # Check if new_parent_id is a descendant of category_id
    descendants = await get_descendant_category_ids(category_id, db)
    return new_parent_id in descendants
