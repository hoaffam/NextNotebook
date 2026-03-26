#!/usr/bin/env python3
"""
Reset Databases Script
Clears all data from MongoDB and Zilliz Cloud (Milvus)

Usage:
    python scripts/reset_databases.py [--mongodb] [--milvus] [--all]
    
Options:
    --mongodb   Reset only MongoDB
    --milvus    Reset only Milvus/Zilliz
    --all       Reset both databases (default)
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pymongo import MongoClient
from pymilvus import connections, utility


def reset_mongodb(uri: str, db_name: str) -> bool:
    """Reset MongoDB database"""
    try:
        print(f"\n🗄️  Connecting to MongoDB...")
        client = MongoClient(uri)
        
        # Check connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB")
        
        # Get database
        db = client[db_name]
        
        # Get all collections
        collections = db.list_collection_names()
        print(f"📋 Found {len(collections)} collections: {collections}")
        
        if not collections:
            print("ℹ️  No collections to delete")
            return True
        
        # Confirm deletion
        confirm = input(f"\n⚠️  Delete all data in '{db_name}' database? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return False
        
        # Drop each collection
        for collection in collections:
            db.drop_collection(collection)
            print(f"   🗑️  Dropped collection: {collection}")
        
        print(f"\n✅ MongoDB '{db_name}' has been reset!")
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")
        return False


def reset_milvus(uri: str, token: str, collection_name: str) -> bool:
    """Reset Milvus/Zilliz Cloud collection"""
    try:
        print(f"\n🔮 Connecting to Zilliz Cloud...")
        
        # Connect to Zilliz
        connections.connect(
            alias="default",
            uri=uri,
            token=token
        )
        print(f"✅ Connected to Zilliz Cloud")
        
        # Check if collection exists
        if utility.has_collection(collection_name):
            print(f"📋 Found collection: {collection_name}")
            
            # Get collection stats
            from pymilvus import Collection
            collection = Collection(collection_name)
            stats = collection.num_entities
            print(f"   📊 Total entities: {stats}")
            
            # Confirm deletion
            confirm = input(f"\n⚠️  Delete collection '{collection_name}' with {stats} entities? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Cancelled")
                return False
            
            # Drop collection
            utility.drop_collection(collection_name)
            print(f"\n✅ Collection '{collection_name}' has been deleted!")
        else:
            print(f"ℹ️  Collection '{collection_name}' does not exist")
        
        connections.disconnect("default")
        return True
        
    except Exception as e:
        print(f"❌ Milvus Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Reset databases for NotebookLM Clone')
    parser.add_argument('--mongodb', action='store_true', help='Reset only MongoDB')
    parser.add_argument('--milvus', action='store_true', help='Reset only Milvus/Zilliz')
    parser.add_argument('--all', action='store_true', help='Reset both databases (default)')
    parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation prompts')
    args = parser.parse_args()
    
    # Default to all if no specific option
    if not args.mongodb and not args.milvus:
        args.all = True
    
    print("=" * 50)
    print("🔄 NotebookLM Clone - Database Reset Tool")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    load_dotenv(env_path)
    
    # Get settings
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    mongodb_db = os.getenv('MONGODB_DB_NAME', 'notebooklm')
    milvus_uri = os.getenv('ZILLIZ_CLOUD_URI', '')
    milvus_token = os.getenv('ZILLIZ_CLOUD_TOKEN', '')
    collection_name = os.getenv('ZILLIZ_COLLECTION_NAME', 'documents')
    
    success = True
    
    # Reset MongoDB
    if args.all or args.mongodb:
        if not reset_mongodb(mongodb_uri, mongodb_db):
            success = False
    
    # Reset Milvus
    if args.all or args.milvus:
        if not milvus_uri or not milvus_token:
            print("\n❌ Milvus/Zilliz credentials not found in .env")
            success = False
        else:
            if not reset_milvus(milvus_uri, milvus_token, collection_name):
                success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Database reset completed successfully!")
    else:
        print("⚠️  Some operations failed or were cancelled")
    print("=" * 50)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
