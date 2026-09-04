from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting PhishGuard-AI Backend...")
    print("📡 API will be available at: http://localhost:5000")
    print("📊 Database: phishguard_db")
    print("🔑 Press Ctrl+C to stop")
    app.run(debug=True, port=5000, host='0.0.0.0')