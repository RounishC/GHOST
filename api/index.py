"""
Vercel entry point for GHOST API
"""
from src.api_server import app

# Export the app for Vercel
__all__ = ['app']
