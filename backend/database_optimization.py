"""
Database optimization script for CLIENT SERVICES Platform
Adds indexes for frequently queried fields to improve performance
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def optimize_database():
    """Add indexes to improve query performance"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🚀 Starting database optimization...")
    
    # Users collection indexes
    print("Adding indexes to users collection...")
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", sparse=True)
    await db.users.create_index("role")
    await db.users.create_index("status")
    await db.users.create_index("is_active")
    await db.users.create_index([("role", 1), ("is_active", 1)])
    
    # Locations collection indexes
    print("Adding indexes to locations collection...")
    await db.locations.create_index("name")
    await db.locations.create_index("is_active")
    
    # Templates collection indexes
    print("Adding indexes to templates collection...")
    await db.templates.create_index("name")
    await db.templates.create_index("is_active")
    await db.templates.create_index("assigned_locations")
    await db.templates.create_index([("is_active", 1), ("assigned_locations", 1)])
    
    # Submissions collection indexes (most important for performance)
    print("Adding indexes to submissions collection...")
    await db.submissions.create_index("template_id")
    await db.submissions.create_index("location_id") 
    await db.submissions.create_index("user_id")
    await db.submissions.create_index("status")
    await db.submissions.create_index("month_year")
    await db.submissions.create_index("created_at")
    
    # Compound indexes for common query patterns
    await db.submissions.create_index([("template_id", 1), ("status", 1)])
    await db.submissions.create_index([("location_id", 1), ("month_year", 1)])
    await db.submissions.create_index([("user_id", 1), ("created_at", -1)])
    await db.submissions.create_index([("status", 1), ("created_at", -1)])
    await db.submissions.create_index([("template_id", 1), ("location_id", 1), ("month_year", 1)])
    
    # Roles collection indexes
    print("Adding indexes to roles collection...")
    await db.roles.create_index("name", unique=True)
    await db.roles.create_index("system_role")
    
    # Files collection indexes (if exists)
    print("Adding indexes to files collection...")
    await db.files.create_index("filename")
    await db.files.create_index("submission_id")
    await db.files.create_index("uploaded_at")
    
    print("✅ Database optimization completed!")
    
    # Show index information
    print("\n📊 Index Summary:")
    collections = ['users', 'locations', 'templates', 'submissions', 'roles', 'files']
    
    for collection_name in collections:
        collection = db[collection_name]
        indexes = await collection.list_indexes().to_list(length=None)
        print(f"\n{collection_name}: {len(indexes)} indexes")
        for idx in indexes:
            if idx['name'] != '_id_':  # Skip default _id index
                keys = list(idx['key'].keys())
                print(f"  - {idx['name']}: {keys}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(optimize_database())