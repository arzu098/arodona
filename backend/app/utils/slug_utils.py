"""
Slug generation utilities for categories.
Generates URL-friendly slugs and ensures uniqueness by appending numeric suffixes.
"""

import re
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection


def generate_slug(name: str) -> str:
    """
    Generate a slug from a name.
    Converts to lowercase, replaces spaces and special chars with hyphens.
    
    Args:
        name: The text to slugify
        
    Returns:
        A URL-friendly slug
    """
    # Convert to lowercase and strip whitespace
    slug = name.lower().strip()
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove any non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Replace multiple hyphens with single hyphen
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


async def make_unique_slug(
    name: str,
    collection: AsyncIOMotorCollection,
    existing_id: Optional[str] = None,
    slug_field: str = 'slug'
) -> str:
    """
    Generate a unique slug for a category name.
    If the slug already exists, appends numeric suffixes (-1, -2, etc.) until unique.
    
    Args:
        name: The category name
        collection: MongoDB categories collection
        existing_id: ObjectId of the document being updated (exclude from uniqueness check)
        slug_field: The field name to check uniqueness on (default: 'slug')
        
    Returns:
        A unique slug
    """
    base_slug = generate_slug(name)
    
    # Check if slug exists
    query = {slug_field: base_slug}
    if existing_id:
        # Exclude the current document if updating
        from bson import ObjectId
        try:
            query['_id'] = {'$ne': ObjectId(existing_id)}
        except Exception:
            pass
    
    existing = await collection.find_one(query)
    
    if not existing:
        return base_slug
    
    # If slug exists, append numeric suffix
    counter = 1
    while True:
        candidate = f"{base_slug}-{counter}"
        query = {slug_field: candidate}
        if existing_id:
            from bson import ObjectId
            try:
                query['_id'] = {'$ne': ObjectId(existing_id)}
            except Exception:
                pass
        
        existing = await collection.find_one(query)
        if not existing:
            return candidate
        counter += 1
