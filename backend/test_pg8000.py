# backend/test_pg8000.py

import pg8000

try:
    conn = pg8000.connect(
        user="phishguard_user",
        password="phishguard123",
        host="localhost",
        port=5432,
        database="phishguard_db"
    )
    print("✅ Connected successfully with pg8000!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    print(f"✅ PostgreSQL version: {version[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM whitelist_domains")
    count = cursor.fetchone()[0]
    print(f"✅ Whitelist domains count: {count}")
    
    cursor.close()
    conn.close()
    print("\n🎉 Database connection is working!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")