# Open PowerShell as Administrator in the backend directory and run each command:
# Example: INSTALLATION_COMMANDS | ForEach-Object { Invoke-Expression $_ }
INSTALLATION_COMMANDS = [
    "python -m pip install --upgrade pip setuptools wheel",
    "python -m pip install --no-cache-dir psycopg2-binary==2.9.9",
    "python -m pip install Flask==2.2.5 Flask-SQLAlchemy==2.5.1 Flask-Migrate==4.0.4 Flask-CORS==3.0.10 Flask-Login==0.6.2 python-dotenv==1.0.0",
]