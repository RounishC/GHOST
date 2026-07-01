"""
REST API Server for GHOST Route Planner
Exposes routing functionality as HTTP endpoints for frontend integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os

# Add this file's own directory (src/) and the repo root to path, since the
# serverless runtime imports this module rather than executing it as __main__,
# so Python's automatic script-directory path insertion can't be relied on.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pipeline import RoutePipelineProcessor
from utils.config_manager import ConfigManager

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'), static_url_path='')
CORS(app)  # Enable CORS for frontend


# Load environment variables from .env if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    os.environ[parts[0].strip()] = parts[1].strip()


@app.route('/')
def index():
    """Serve index.html at root"""
    return app.send_static_file('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Return public configuration values like map key"""
    return jsonify({
        "azure_maps_key": os.environ.get("AZURE_MAPS_KEY", "")
    }), 200


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
        
        # Map frontend preference names to backend expected keys
        frontend_prefs = data.get('preferences', {})
        backend_prefs = {
            "safety": float(frontend_prefs.get('safety', 5)),
            "cleanliness": float(10 - frontend_prefs.get('dust_level', 5)) if 'dust_level' in frontend_prefs else float(frontend_prefs.get('cleanliness', 5)),
            "noise": float(10 - frontend_prefs.get('noise_level', 5)) if 'noise_level' in frontend_prefs else float(frontend_prefs.get('noise', 5)),
            "lighting": float(frontend_prefs.get('lighting', 5)),
            "construction": float(frontend_prefs.get('construction', 5))
        }

        # Create config from request
        config = {
            "data_file": data.get('data_file', 'ghost_segments.toon'),
            "route_request": {
                "start": data['start'],
                "end": data['end'],
                "preferences": backend_prefs,
                "output_file": "route_output.json"
            }
        }
        
        # Save config temporarily (use system temp dir - workspace is read-only in serverless deployments)
        import tempfile
        temp_dir = tempfile.gettempdir()
        config_file = os.path.join(temp_dir, "route_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Try to query the real-world Azure Maps Routing API first
        import urllib.request
        import urllib.parse
        import math
        
        azure_key = os.environ.get("AZURE_MAPS_KEY")
        start_lat = data['start']['latitude']
        start_lon = data['start']['longitude']
        end_lat = data['end']['latitude']
        end_lon = data['end']['longitude']
        
        data_file = data.get('data_file', 'ghost_segments.toon')
        if not os.path.isabs(data_file):
            data_file = os.path.join(os.path.dirname(__file__), '..', data_file)
            
        from api.route_planner import GHOSTRoutePlanner
        planner = GHOSTRoutePlanner(data_file)
        
        # 1. Calculate the Safest/GHOST route using offline A* with user preferences
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
            
        safe_route_details = safe_route['route_details']
        
        # Bridge the gap between consecutive segments in the Safe route
        for idx in range(len(safe_route_details) - 1):
            next_start = safe_route_details[idx+1]['coordinates'][0]
            if next_start not in safe_route_details[idx]['coordinates']:
                safe_route_details[idx]['coordinates'].append(next_start)
                
        safe_route_coords = [
            {
                "street": seg['road_name'] or "Local Street",
                "type": seg['highway_type'] or "residential",
                "distance_meters": seg['distance_meters'],
                "coordinates": seg['coordinates'],
                "metrics": {
                    "safety": seg['safety'],
                    "cleanliness": seg['cleanliness'],
                    "noise": seg['noise'],
                    "lighting": seg['lighting'],
                    "construction": seg['construction']
                }
            }
            for seg in safe_route_details
        ]
        
        # 2. Compute Alternative Route (Standard/Fastest route)
        # First try to get it from the Azure Maps Route directions API
        azure_route_coords = None
        url = "https://atlas.microsoft.com/route/directions/json"
        params = {
            "api-version": "1.0",
            "query": f"{start_lat},{start_lon}:{end_lat},{end_lon}",
            "subscription-key": azure_key,
            "travelMode": "pedestrian",
            "routeType": "fastest"
        }
        
        try:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            req = urllib.request.Request(full_url, method="GET")
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    routes_data = resp_data.get('routes')
                    if routes_data:
                        points = routes_data[0]['legs'][0]['points']
                        azure_route_coords = [[p['longitude'], p['latitude']] for p in points]
        except Exception as e:
            print(f"Azure Routing API call failed for alternative route: {e}")
            
        alt_route_coords = []
        if azure_route_coords:
            # Map Azure coordinates to database segments to get a realistic alternative path
            current_street = ""
            current_type = "residential"
            current_coords = []
            current_metrics = {
                "safety": 5, "cleanliness": 5, "noise": 5, "lighting": 5, "construction": 0
            }
            
            for p in azure_route_coords:
                p_lon, p_lat = p[0], p[1]
                closest_seg = None
                min_dist = float('inf')
                
                for seg in planner.segments.values():
                    for coord in seg.geometry:
                        dist = math.hypot(coord[0] - p_lon, coord[1] - p_lat)
                        if dist < min_dist:
                            min_dist = dist
                            closest_seg = seg
                            
                if min_dist < 0.001 and closest_seg:
                    street_name = closest_seg.road_name or "Local Street"
                    highway_type = closest_seg.highway_type or "residential"
                    metrics = {
                        "safety": closest_seg.crime_score,
                        "cleanliness": closest_seg.dust_level,
                        "noise": closest_seg.noise_level,
                        "lighting": closest_seg.lighting,
                        "construction": closest_seg.construction
                    }
                else:
                    street_name = "Local Street"
                    highway_type = "residential"
                    metrics = {"safety": 4, "cleanliness": 4, "noise": 4, "lighting": 6, "construction": 0}
                    
                if street_name != current_street or not current_coords:
                    if current_coords:
                        current_coords.append(p)
                        alt_route_coords.append({
                            "street": current_street,
                            "type": current_type,
                            "distance_meters": len(current_coords) * 10,
                            "coordinates": current_coords,
                            "metrics": current_metrics
                        })
                    current_street = street_name
                    current_type = highway_type
                    current_coords = [p]
                    current_metrics = metrics
                else:
                    current_coords.append(p)
            if current_coords:
                alt_route_coords.append({
                    "street": current_street,
                    "type": current_type,
                    "distance_meters": len(current_coords) * 10,
                    "coordinates": current_coords,
                    "metrics": current_metrics
                })
        else:
            # Fallback: compute distance-only shortest path using offline A*
            distance_only_prefs = {
                "safety": 0.0,
                "cleanliness": 0.0,
                "noise": 0.0,
                "lighting": 0.0,
                "construction": 0.0
            }
            alt_route = planner.find_route(
                start_lon=start_lon,
                start_lat=start_lat,
                end_lon=end_lon,
                end_lat=end_lat,
                filters=distance_only_prefs
            )
            if alt_route and alt_route.get('success'):
                alt_route_details = alt_route['route_details']
                for idx in range(len(alt_route_details) - 1):
                    next_start = alt_route_details[idx+1]['coordinates'][0]
                    if next_start not in alt_route_details[idx]['coordinates']:
                        alt_route_details[idx]['coordinates'].append(next_start)
                alt_route_coords = [
                    {
                        "street": seg['road_name'] or "Local Street",
                        "type": seg['highway_type'] or "residential",
                        "distance_meters": seg['distance_meters'],
                        "coordinates": seg['coordinates'],
                        "metrics": {
                            "safety": seg['safety'],
                            "cleanliness": seg['cleanliness'],
                            "noise": seg['noise'],
                            "lighting": seg['lighting'],
                            "construction": seg['construction']
                        }
                    }
                    for seg in alt_route_details
                ]
                
        # Return response including both paths
        total_dist_m = safe_route['total_distance_meters']
        overall_quality = round((safe_route['scores']['safety'] + 
                                 safe_route['scores']['cleanliness'] + 
                                 safe_route['scores']['noise'] + 
                                 safe_route['scores']['lighting']) / 4.0, 1)
                                 
        route_for_map = {
            "success": True,
            "start": [start_lon, start_lat],
            "end": [end_lon, end_lat],
            "streets": [seg['street'] for seg in safe_route_coords if seg['street'] != "Local Street"],
            "route_coordinates": safe_route_coords,  # GHOST Safe Route (Cyan)
            "alternative_route_coordinates": alt_route_coords,  # Standard/Fastest Route (Light Red)
            "total_distance_km": round(total_dist_m / 1000.0, 2),
            "total_distance_meters": float(total_dist_m),
            "overall_quality": overall_quality,
            "ai_reasoning": safe_route['reasoning'],
            "highlights": safe_route['highlights']
        }
        return jsonify(route_for_map), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/segments', methods=['GET'])
def get_segments():
    """Return all segments with geometry and metrics for heatmap and network rendering"""
    try:
        data_file = request.args.get('data_file', 'ghost_segments.toon')
        if not os.path.isabs(data_file):
            data_file = os.path.join(os.path.dirname(__file__), '..', data_file)
            
        from data.data_loader import DataLoader
        loader = DataLoader(data_file)
        segments = loader.load()
        
        result = []
        for seg_id, seg in segments.items():
            result.append({
                "segment_id": seg.segment_id,
                "road_name": seg.road_name,
                "highway_type": seg.highway_type,
                "length_meters": seg.length_meters,
                "lighting": seg.lighting,
                "crime_score": seg.crime_score,
                "noise_level": seg.noise_level,
                "dust_level": seg.dust_level,
                "construction": seg.construction,
                "coordinates": seg.geometry
            })
            
        return jsonify(result), 200
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
    print("\nServer running on: http://localhost:5001")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')
