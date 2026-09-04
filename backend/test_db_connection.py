# backend/test_db_connection.py

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "phishguard_db"),
        user=os.getenv("POSTGRES_USER", "phishguard_user"),
        password=os.getenv("POSTGRES_PASSWORD", "phishguard123"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    print("✅ Successfully connected to PostgreSQL!")
    
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM whitelist_domains")
    count = cursor.fetchone()[0]
    print(f"✅ Whitelist domains count: {count}")
    
    cursor.execute("SELECT COUNT(*) FROM threat_categories")
    count = cursor.fetchone()[0]
    print(f"✅ Threat categories count: {count}")
    
    cursor.close()
    connection.close()
    print("\n🎉 Database is ready for development!")
    
except Exception as error:
    print(f"❌ Error: {error}")