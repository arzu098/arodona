from pymongo import MongoClient
from pymongo.errors import BulkWriteError, ConnectionFailure, ServerSelectionTimeoutError
from urllib.parse import quote_plus
import time
from datetime import datetime

# === CONFIGURATION ===
# SOURCE Atlas (where data comes from)
# Example: "mongodb+srv://<username>:<password>@source-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority"
SOURCE_ATLAS_URI = "mongodb+srv://amit24ve:Amit%402403.@trading.70xxozj.mongodb.net/?retryWrites=true&w=majority&appName=trading"

# TARGET Atlas (where data goes to)  
# Example: "mongodb+srv://<username>:<password>@target-cluster.yyyyy.mongodb.net/?retryWrites=true&w=majority"
TARGET_ATLAS_URI = "mongodb+srv://bhoomi:bhoomi23@cluster0.wcbjoil.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Alternative: TARGET Localhost (uncomment if migrating to localhost instead)
# TARGET_LOCALHOST_URI = "mongodb://localhost:27017/"

DB_NAME = "arodona_db"  # Database name to migrate

# === MIGRATION SETTINGS ===
BATCH_SIZE = 1000  # Number of documents to process in each batch
FORCE_OVERWRITE = True  # Set to True to overwrite existing data in target

def test_connection(uri, name):
    """Test connection to MongoDB Atlas cluster"""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        print(f"✅ {name} connection successful")
        client.close()
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ {name} connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ {name} connection error: {e}")
        return False

def migrate_data_atlas_to_atlas(source_uri, target_uri, db_name, force=False):
    start_time = datetime.now()
    print(f"🔄 Starting Atlas-to-Atlas migration of database: {db_name}")
    print(f"🕐 Started at: {start_time}")
    
    # Test connections first
    print("\n🔗 Testing connections...")
    if not test_connection(source_uri, "Source Atlas"):
        return False
    if not test_connection(target_uri, "Target Atlas"):
        return False
    
    try:
        # Connect to source Atlas
        print("\n📤 Connecting to source Atlas...")
        source_client = MongoClient(source_uri, serverSelectionTimeoutMS=30000)
        source_db = source_client[db_name]

        # Connect to target Atlas
        print("📥 Connecting to target Atlas...")
        target_client = MongoClient(target_uri, serverSelectionTimeoutMS=30000)
        target_db = target_client[db_name]

        print(f"\n✅ Connected successfully to both Atlas clusters")
        
        # List all collections in source DB
        collections = source_db.list_collection_names()
        print(f"📁 Found collections in source: {collections}")

        if not collections:
            print("⚠️ No collections found in source database!")
            return

        for collection_name in collections:
            print(f"➡️ Migrating collection: {collection_name}")
            source_collection = source_db[collection_name]
            target_collection = target_db[collection_name]

            # Get document count from source
            source_count = source_collection.count_documents({})
            print(f"📊 Source collection '{collection_name}' has {source_count} documents")

            if source_count == 0:
                print("⚠️ No documents found in source collection, skipping...")
                continue

            # If force=True, drop target collection first
            if force:
                print(f"🗑️ Force mode: Dropping target collection '{collection_name}'")
                target_collection.drop()

            # Process documents in batches for better memory management
            batch_size = BATCH_SIZE
            total_inserted = 0
            
            try:
                cursor = source_collection.find().batch_size(batch_size)
                batch = []
                
                for doc in cursor:
                    # Remove _id field to avoid duplicate key error
                    doc.pop("_id", None)
                    batch.append(doc)
                    
                    if len(batch) >= batch_size:
                        # Insert batch
                        result = target_collection.insert_many(batch, ordered=False)
                        total_inserted += len(result.inserted_ids)
                        print(f"📦 Batch inserted: {len(result.inserted_ids)} documents (Total: {total_inserted})")
                        batch = []
                
                # Insert remaining documents in final batch
                if batch:
                    result = target_collection.insert_many(batch, ordered=False)
                    total_inserted += len(result.inserted_ids)
                    print(f"📦 Final batch inserted: {len(result.inserted_ids)} documents")
                
                print(f"✅ Successfully inserted {total_inserted} documents into target Atlas.")
                
                # Verify the migration
                target_count = target_collection.count_documents({})
                print(f"🔍 Target collection now has {target_count} documents")
                
            except BulkWriteError as bwe:
                print(f"❌ Bulk write error in collection '{collection_name}':")
                for error in bwe.details.get('writeErrors', []):
                    print(f"   - {error}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error with collection '{collection_name}': {e}")
                continue

        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 Atlas-to-Atlas migration complete!")
        print(f"🕐 Completed at: {end_time}")
        print(f"⏱️ Total duration: {duration}")
        
        # Close connections
        source_client.close()
        target_client.close()
        
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Ensure both Atlas URIs are configured
    if not SOURCE_ATLAS_URI:
        print("❌ Please set SOURCE_ATLAS_URI in the configuration section")
        exit(1)
    
    if not TARGET_ATLAS_URI:
        print("❌ Please set TARGET_ATLAS_URI in the configuration section")
        exit(1)
    
    print("🚀 Starting Atlas-to-Atlas migration...")
    print(f"📊 Database: {DB_NAME}")
    
    # Run the migration
    success = migrate_data_atlas_to_atlas(SOURCE_ATLAS_URI, TARGET_ATLAS_URI, DB_NAME, force=FORCE_OVERWRITE)
    
    if success:
        print("\n🎯 Migration completed successfully!")
    else:
        print("\n💥 Migration failed. Check the logs above for details.")
        exit(1)