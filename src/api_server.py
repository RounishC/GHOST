"""
REST API Server for GHOST Route Planner
Exposes routing functionality as HTTP endpoints for frontend integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline import RoutePipelineProcessor
from utils.config_manager import ConfigManager

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend


@app.route('/api/route', methods=['POST'])
def get_route():
    """
    Get optimal route with coordinates for map visualization
    
    Expected JSON:
    {
        "start": {"longitude": 77.666125, "latitude": 12.925200},
        "end": {"longitude": 77.667994, "latitude": 12.925253},
        "preferences": {
            "safety": 7,
            "cleanliness": 8,
            "noise": 7,
            "lighting": 8,
            "construction": 5
        },
        "data_file": "ghost_segments.toon"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('start') or not data.get('end'):
            return jsonify({"error": "Missing start or end coordinates"}), 400
        
        # Create config from request
        config = {
            "data_file": data.get('data_file', 'ghost_segments.toon'),
            "route_request": {
                "start": data['start'],
                "end": data['end'],
                "preferences": data.get('preferences', {
                    "safety": 5,
                    "cleanliness": 5,
                    "noise": 5,
                    "lighting": 5,
                    "construction": 5
                }),
                "output_file": "route_output.json"
            }
        }
        
        # Save config temporarily
        config_file = "/tmp/route_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Run pipeline
        processor = RoutePipelineProcessor(config_file)
        result = processor.process()
        
        # Extract map-friendly format
        route_for_map = {
            "success": result['status'] == 'success',
            "start": result['request']['start']['coordinates'],
            "end": result['request']['end']['coordinates'],
            "streets": [seg['road_name'] for seg in result['route_result']['route_details']],
            "route_coordinates": [
                {
                    "street": seg['road_name'],
                    "type": seg['highway_type'],
                    "distance_meters": seg['distance_meters'],
                    "coordinates": seg['coordinates'],  # Array of [longitude, latitude]
                    "metrics": {
                        "safety": seg['safety'],
                        "cleanliness": seg['cleanliness'],
                        "noise": seg['noise'],
                        "lighting": seg['lighting'],
                        "construction": seg['construction']
                    }
                }
                for seg in result['route_result']['route_details']
            ],
            "total_distance_km": result['summary']['distance_km'],
            "total_distance_meters": result['route_result']['total_distance_meters'],
            "overall_quality": result['summary']['overall_quality'],
            "ai_reasoning": result['ai_analysis']['reasoning'],
            "highlights": result['ai_analysis']['highlights']
        }
        
        return jsonify(route_for_map), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "GHOST Route Planner"}), 200


@app.route('/api/example', methods=['GET'])
def example():
    """Return example request format"""
    return jsonify({
        "example_request": {
            "start": {"longitude": 77.666125, "latitude": 12.925200},
            "end": {"longitude": 77.667994, "latitude": 12.925253},
            "preferences": {
                "safety": 7,
                "cleanliness": 8,
                "noise": 7,
                "lighting": 8,
                "construction": 5
            },
            "data_file": "ghost_segments.toon"
        },
        "response_format": {
            "start": [77.666125, 12.925200],
            "end": [77.667994, 12.925253],
            "streets": ["Street 1", "Street 2"],
            "route_coordinates": [
                {
                    "street": "Street Name",
                    "type": "residential",
                    "distance_meters": 184.5,
                    "coordinates": [[77.668, 12.926], [77.667, 12.926]],
                    "metrics": {
                        "safety": 9,
                        "cleanliness": 3,
                        "noise": 3,
                        "lighting": 2,
                        "construction": 0
                    }
                }
            ],
            "total_distance_km": 0.18,
            "overall_quality": 3.4,
            "ai_reasoning": "Route explanation",
            "highlights": ["Highlight 1", "Highlight 2"]
        }
    }), 200


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 GHOST Route Planner API Server")
    print("="*70)
    print("\nEndpoints:")
    print("  POST /api/route        - Get optimal route with coordinates")
    print("  GET  /api/health       - Health check")
    print("  GET  /api/example      - Example request/response format")
    print("\nServer running on: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
