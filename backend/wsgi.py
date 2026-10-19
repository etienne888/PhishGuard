"""Production entry point: gunicorn --workers 3 --threads 4 --bind 127.0.0.1:8000 wsgi:app"""
from app import create_app

app = create_app()
