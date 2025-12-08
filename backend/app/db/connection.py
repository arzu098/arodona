from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import MONGODB_URL, DATABASE_NAME

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        print(f"Connecting to MongoDB: {MONGODB_URL}")
        print(f"Database name: {DATABASE_NAME}")
        mongodb.client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        mongodb.db = mongodb.client[DATABASE_NAME]
        # Test the connection
        server_info = await mongodb.client.admin.command('ismaster')
        print(f"✅ Connected to MongoDB successfully")
        print(f"✅ Using database: {DATABASE_NAME}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print(f"❌ Connection string: {MONGODB_URL[:50]}...")
        mongodb.client = None
        mongodb.db = None
        # Don't raise the exception, let the app start without DB
        return False

async def close_mongo_connection():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
    print("Closed MongoDB connection")

def get_database() -> AsyncIOMotorDatabase:
    """Get the current database instance"""
    if mongodb.db is None:
        raise RuntimeError("Database not connected. Please check MongoDB configuration.")
    return mongodb.db
