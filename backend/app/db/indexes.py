"""Create indexes for collections"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL

async def create_indexes():
    """Create indexes for all collections"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    
    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index([("oauth_accounts.provider", 1), ("oauth_accounts.provider_id", 1)])
    await db.users.create_index([("first_name", "text"), ("last_name", "text"), ("email", "text")])
    
    # User activities collection indexes
    await db.user_activities.create_index([("user_id", 1), ("timestamp", -1)])
    await db.user_activities.create_index("timestamp")
    
    # Sessions collection indexes
    await db.sessions.create_index([("user_id", 1), ("created_at", -1)])
    await db.sessions.create_index("token", unique=True)
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)
    
    print("Successfully created database indexes")