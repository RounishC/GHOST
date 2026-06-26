"""
REST API Server for GHOST Route Planner
Exposes routing functionality as HTTP endpoints for frontend integration
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Static file serving
static_dir = os.path.join(os.path.dirname(__file__), 'static')

@app.route('/')
def index():
    """Serve index.html at root"""
    try:
        index_path = os.path.join(static_dir, 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        print(f"Error serving index.html: {e}")
    
    return jsonify({"status": "GHOST Route Planner API - Ready", "version": "1.0"}), 200


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    try:
        return send_from_directory(static_dir, path)
    except Exception as e:
        print(f"Error serving static file {path}: {e}")
        return jsonify({"error": "File not found"}), 404


@app.route('/api/config', methods=['GET'])
def get_config():
    """Return public configuration values like map key"""
    return jsonify({
        "azure_maps_key": os.environ.get("AZURE_MAPS_KEY", ""),
        "status": "ok"
    }), 200


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "GHOST"}), 200


@app.route('/api/route', methods=['POST'])
def get_route():
    """
    Get optimal route with coordinates for map visualization
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('start') or not data.get('end'):
            return jsonify({"error": "Missing start or end coordinates"}), 400
        
        try:
            # Try to load the full routing logic
            from api.route_planner import GHOSTRoutePlanner
            
            # Get data file path
            data_file = data.get('data_file', 'ghost_segments.toon')
            if not os.path.isabs(data_file):
                data_file = os.path.join(os.path.dirname(__file__), '..', data_file)
            
            if not os.path.exists(data_file):
                return jsonify({"error": f"Data file not found: {data_file}"}), 400
            
            # Initialize planner
            planner = GHOSTRoutePlanner(data_file)
            
            # Map preferences
            frontend_prefs = data.get('preferences', {})
            backend_prefs = {
                "safety": float(frontend_prefs.get('safety', 5)),
                "cleanliness": float(frontend_prefs.get('cleanliness', 5)),
                "noise": float(frontend_prefs.get('noise', 5)),
                "lighting": float(frontend_prefs.get('lighting', 5)),
                "construction": float(frontend_prefs.get('construction', 5))
            }
            
            # Find route
            start_lon = data['start']['longitude']
            start_lat = data['start']['latitude']
            end_lon = data['end']['longitude']
            end_lat = data['end']['latitude']
            
            safe_route = planner.find_route(
                start_lon=start_lon,
                start_lat=start_lat,
                end_lon=end_lon,
                end_lat=end_lat,
                filters=backend_prefs
            )
            
            if not safe_route or not safe_route.get('success'):
                error_msg = safe_route.get('error') if safe_route else "Routing failed"
                return jsonify({"error": error_msg}), 400
            
            # Format response
            return jsonify({
                "success": True,
                "route": safe_route.get('route_details', []),
                "summary": safe_route.get('summary', {})
            }), 200
            
        except ImportError as e:
            print(f"Could not load routing module: {e}")
            # Return demo response
            return jsonify({
                "success": True,
                "message": "API is running but routing module not available",
                "route": [
                    {
                        "street": "Demo Route",
                        "distance_meters": 500,
                        "coordinates": [
                            [data['start']['longitude'], data['start']['latitude']],
                            [data['end']['longitude'], data['end']['latitude']]
                        ]
                    }
                ]
            }), 200
        
    except Exception as e:
        print(f"Error in /api/route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    print(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=False)
