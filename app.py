"""
Root level Flask app for Vercel deployment
"""
import sys
import os
from flask import Flask, jsonify

# Create app instance first
app = Flask(__name__)

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Try to import the full app from api_server
    from api_server import app as api_app
    # If successful, use the api_app instead
    app = api_app
except Exception as e:
    # If import fails, provide a fallback minimal app
    print(f"Warning: Could not load full API app: {e}")
    
    # Create minimal health check routes
    @app.route('/')
    def index():
        """Serve index.html at root"""
        try:
            index_path = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'r') as f:
                    return f.read(), 200, {'Content-Type': 'text/html'}
        except:
            pass
        return jsonify({"status": "GHOST Route Planner API"}), 200
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Return public configuration values"""
        return jsonify({
            "azure_maps_key": os.environ.get("AZURE_MAPS_KEY", ""),
            "status": "ok"
        }), 200
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({"status": "healthy"}), 200

# Export app
__all__ = ['app']

if __name__ == '__main__':
    app.run(debug=False)
