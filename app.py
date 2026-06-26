"""
Root level Flask app for Vercel deployment - Ultra minimal version
"""
from flask import Flask, jsonify
import os

# Create app
app = Flask(__name__)

@app.route('/')
def index():
    """Root endpoint"""
    try:
        index_path = os.path.join(os.path.dirname(__file__), 'src', 'static', 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"message": "GHOST Route Planner", "status": "running"}), 200

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/config', methods=['GET'])
def config():
    """Configuration endpoint"""
    return jsonify({"status": "ok"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "server error"}), 500

__all__ = ['app']

if __name__ == '__main__':
    app.run(debug=False)
