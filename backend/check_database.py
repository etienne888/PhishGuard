# backend/check_database.py

import psycopg2

try:
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="phishguard_db",
        user="phishguard_user",
        password="phishguard123"
    )
    
    cursor = connection.cursor()
    
    # Check all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print("📊 Tables in database:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Check row counts
    print("\n📈 Row counts:")
    for table in ['users', 'whitelist_domains', 'suspicious_keywords', 'threat_categories', 'analyses']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table}: {count} rows")
    
    # Show sample data
    print("\n📋 Sample whitelist domains:")
    cursor.execute("SELECT domain, institution, category FROM whitelist_domains LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]} → {row[1]} ({row[2]})")
    
    cursor.close()
    connection.close()
    print("\n✅ Database verification complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")