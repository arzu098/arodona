#!/usr/bin/env python3
"""
Simple script to check existing vendor accounts
"""
import asyncio
import sys
sys.path.append('.')

from app.db.connection import get_database, connect_to_mongo

async def check_vendors():
    """Check existing vendor accounts"""
    
    # Connect to database
    success = await connect_to_mongo()
    if not success:
        print("❌ Failed to connect to database")
        return
    
    db = get_database()
    
    # Check vendors
    vendors = await db.vendors.find().limit(5).to_list(5)
    print(f"👥 Found {len(vendors)} vendors:")
    
    for vendor in vendors:
        print(f"  📧 Email: {vendor.get('email', 'Unknown')}")
        print(f"     Name: {vendor.get('name', 'Unknown')}")
        print(f"     ID: {vendor['_id']}")
        print(f"     Status: {vendor.get('status', 'Unknown')}")
        print("  ---")
    
    # Check users who might be vendors
    users = await db.users.find({"role": "vendor"}).limit(5).to_list(5)
    print(f"\n👤 Found {len(users)} vendor users:")
    
    for user in users:
        print(f"  📧 Email: {user.get('email', 'Unknown')}")
        print(f"     Name: {user.get('name', 'Unknown')}")
        print(f"     ID: {user['_id']}")
        print(f"     Role: {user.get('role', 'Unknown')}")
        print("  ---")

if __name__ == "__main__":
    asyncio.run(check_vendors())