"""
Root level Flask app for Vercel deployment
"""
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the Flask app from api_server
from api_server import app

# Make sure the app is exported
__all__ = ['app']

if __name__ == '__main__':
    app.run(debug=False)
