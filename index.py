from app import create_app

# This file acts as the entry point for Vercel's serverless function.
# Vercel's Python runtime will automatically detect the 'app' WSGI object.

app = create_app()