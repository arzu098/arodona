"""User address management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

from ..databases.schemas.address import (
    AddressCreate, AddressUpdate, AddressResponse, AddressType
)
from ..utils.dependencies import get_current_user, get_database

router = APIRouter(prefix="/api/addresses", tags=["addresses"])


@router.get("", response_model=List[AddressResponse])
async def get_user_addresses(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all addresses for the current user."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        print(f"Fetching addresses for user: {user_id}")
        print(f"Current user data: {current_user}")
        
        addresses = await db.addresses.find(
            {"user_id": user_id}
        ).sort("is_default", -1).to_list(length=None)
        
        print(f"Found {len(addresses)} addresses")
        
        return [
            {
                "id": str(addr["_id"]),
                "user_id": addr["user_id"],
                "name": addr["name"],
                "phone": addr["phone"],
                "address": addr["address"],
                "city": addr["city"],
                "country": addr["country"],
                "address_type": addr["address_type"],
                "is_default": addr.get("is_default", False),
                "created_at": addr.get("created_at", datetime.utcnow()),
                "updated_at": addr.get("updated_at", datetime.utcnow())
            }
            for addr in addresses
        ]
    except Exception as e:
        print(f"Error fetching addresses: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch addresses: {str(e)}"
        )


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: AddressCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create a new address for the current user."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        print(f"Creating address for user: {user_id}")
        print(f"Address data: {address_data.dict()}")
        print(f"Current user data: {current_user}")
        
        # If this is set as default, unset all other default addresses
        if address_data.is_default:
            await db.addresses.update_many(
                {"user_id": user_id},
                {"$set": {"is_default": False}}
            )
        
        new_address = {
            "user_id": user_id,
            "name": address_data.name,
            "phone": address_data.phone,
            "address": address_data.address,
            "city": address_data.city,
            "country": address_data.country,
            "address_type": address_data.address_type.value if isinstance(address_data.address_type, AddressType) else address_data.address_type,
            "is_default": address_data.is_default,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        print(f"Inserting address into database: {new_address}")
        result = await db.addresses.insert_one(new_address)
        new_address["_id"] = result.inserted_id
        print(f"Address created with ID: {result.inserted_id}")
        
        return {
            "id": str(new_address["_id"]),
            "user_id": new_address["user_id"],
            "name": new_address["name"],
            "phone": new_address["phone"],
            "address": new_address["address"],
            "city": new_address["city"],
            "country": new_address["country"],
            "address_type": new_address["address_type"],
            "is_default": new_address["is_default"],
            "created_at": new_address["created_at"],
            "updated_at": new_address["updated_at"]
        }
    except Exception as e:
        print(f"Error creating address: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create address: {str(e)}"
        )


@router.put("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str,
    address_data: AddressUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update an existing address."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        
        # Verify the address belongs to the current user
        existing_address = await db.addresses.find_one({
            "_id": ObjectId(address_id),
            "user_id": user_id
        })
        
        if not existing_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # If setting as default, unset all other default addresses
        if address_data.is_default:
            user_id = current_user.get("user_id") or current_user.get("id")
            await db.addresses.update_many(
                {"user_id": user_id},
                {"$set": {"is_default": False}}
            )
        
        # Build update data
        update_data = {
            k: v for k, v in address_data.dict(exclude_none=True).items()
        }
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the address
        await db.addresses.update_one(
            {"_id": ObjectId(address_id)},
            {"$set": update_data}
        )
        
        # Fetch and return updated address
        updated_address = await db.addresses.find_one({"_id": ObjectId(address_id)})
        
        return {
            "id": str(updated_address["_id"]),
            "user_id": updated_address["user_id"],
            "name": updated_address["name"],
            "phone": updated_address["phone"],
            "address": updated_address["address"],
            "city": updated_address["city"],
            "country": updated_address["country"],
            "address_type": updated_address["address_type"],
            "is_default": updated_address.get("is_default", False),
            "created_at": updated_address.get("created_at", datetime.utcnow()),
            "updated_at": updated_address["updated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update address: {str(e)}"
        )


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete an address."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        
        # Verify the address belongs to the current user
        result = await db.addresses.delete_one({
            "_id": ObjectId(address_id),
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete address: {str(e)}"
        )


@router.put("/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    address_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Set an address as the default."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        
        # Verify the address belongs to the current user
        existing_address = await db.addresses.find_one({
            "_id": ObjectId(address_id),
            "user_id": user_id
        })
        
        if not existing_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # Unset all other default addresses
        await db.addresses.update_many(
            {"user_id": user_id},
            {"$set": {"is_default": False}}
        )
        
        # Set this address as default
        await db.addresses.update_one(
            {"_id": ObjectId(address_id)},
            {"$set": {"is_default": True, "updated_at": datetime.utcnow()}}
        )
        
        # Fetch and return updated address
        updated_address = await db.addresses.find_one({"_id": ObjectId(address_id)})
        
        return {
            "id": str(updated_address["_id"]),
            "user_id": updated_address["user_id"],
            "name": updated_address["name"],
            "phone": updated_address["phone"],
            "address": updated_address["address"],
            "city": updated_address["city"],
            "country": updated_address["country"],
            "address_type": updated_address["address_type"],
            "is_default": updated_address["is_default"],
            "created_at": updated_address.get("created_at", datetime.utcnow()),
            "updated_at": updated_address["updated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default address: {str(e)}"
        )
