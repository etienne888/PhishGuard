# backend/test_connection.py

from app import create_app, db
from app.models import User, Analysis, WhitelistDomain

app = create_app()

with app.app_context():
    try:
        # Test database connection
        count = WhitelistDomain.query.count()
        print(f"✅ Connected to database!")
        print(f"✅ Whitelist domains: {count}")
        
        # Test user table
        user_count = User.query.count()
        print(f"✅ Users: {user_count}")
        
        print("\n🎉 Database connection is working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")