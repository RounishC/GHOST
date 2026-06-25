"""
Main API for the GHOST Route Planner
Integrates A* pathfinding with AI reasoning
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.data_loader import DataLoader, Segment
from pathfinding.astar import AStarPathfinder
from ai.reasoning_engine import AIReasoningEngine, RouteAnalysis


class GHOSTRoutePlanner:
    """Main route planner combining pathfinding and AI reasoning"""

    def __init__(self, data_file: str):
        """
        Initialize the route planner
        
        Args:
            data_file: Path to ghost_segments.toon file (can be absolute or relative path)
        """
        # Verify file exists
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        self.data_file = os.path.abspath(data_file)
        self.loader = DataLoader(self.data_file)
        self.segments = self.loader.load()
        
        # Build graph for pathfinding
        self.pathfinder = AStarPathfinder(self.segments, {})
        self.graph = self.pathfinder.build_graph()
        self.pathfinder.graph = self.graph
        
        self.reasoning_engine = AIReasoningEngine(self.segments)
        self.route_history = []

    def find_route(self, start_lon: float, start_lat: float,
                  end_lon: float, end_lat: float,
                  filters: Optional[Dict[str, float]] = None) -> Optional[Dict]:
        """
        Find optimal route from start to end coordinates
        
        Args:
            start_lon: Starting longitude
            start_lat: Starting latitude
            end_lon: Ending longitude
            end_lat: Ending latitude
            filters: User preferences (0-10 scale)
                   {'safety': 0-10, 'cleanliness': 0-10, 'noise': 0-10,
                    'lighting': 0-10, 'construction': 0-10}
        
        Returns:
            Dictionary with route details and reasoning, or None if no route found
        """
        
        # Default filters
        if filters is None:
            filters = {
                'safety': 5,
                'cleanliness': 5,
                'noise': 5,
                'lighting': 5,
                'construction': 5
            }

        # Validate filters
        is_valid, message = self.reasoning_engine.validate_filters(filters)
        if not is_valid:
            return {'error': message}

        # Find nearby segments for start and end points
        start_segments = self.loader.find_nearby_segments(start_lon, start_lat)
        end_segments = self.loader.find_nearby_segments(end_lon, end_lat)

        if not start_segments or not end_segments:
            return {'error': 'No road segments found near start or end coordinates'}

        # Try to find best path
        best_path = None
        best_cost = float('inf')

        for start_seg in start_segments:
            for end_seg in end_segments:
                path = self.pathfinder.find_path(
                    start_seg.segment_id,
                    end_seg.segment_id,
                    filters
                )
                
                if path:
                    # Calculate total cost for this path
                    cost = 0
                    for seg_id in path:
                        segment = self.segments[seg_id]
                        cost += self.pathfinder.calculate_segment_cost(segment, filters)
                    
                    if cost < best_cost:
                        best_cost = cost
                        best_path = path

        if not best_path:
            return {'error': 'No route found between start and end points'}

        # Analyze the route
        analysis = self.reasoning_engine.analyze_route(best_path, filters)

        result = {
            'success': True,
            'path': best_path,
            'total_distance_meters': analysis.total_distance,
            'segment_count': len(best_path),
            'scores': {
                'safety': round(analysis.safety_score, 2),
                'cleanliness': round(analysis.cleanliness_score, 2),
                'noise': round(analysis.noise_score, 2),
                'lighting': round(analysis.lighting_score, 2),
                'construction_risk': round(analysis.construction_risk, 2)
            },
            'reasoning': analysis.reasoning,
            'highlights': analysis.highlights,
            'route_details': self._get_route_details(best_path),
            'timestamp': datetime.now().isoformat()
        }

        # Store in history
        self.route_history.append(result)

        return result

    def _get_route_details(self, path: List[str]) -> List[Dict]:
        """Get detailed information about each segment in the path"""
        details = []
        for seg_id in path:
            segment = self.segments.get(seg_id)
            if segment:
                details.append({
                    'segment_id': segment.segment_id,
                    'road_name': segment.road_name,
                    'highway_type': segment.highway_type,
                    'distance_meters': segment.length_meters,
                    'safety': segment.crime_score,
                    'cleanliness': segment.dust_level,
                    'noise': segment.noise_level,
                    'lighting': segment.lighting,
                    'construction': segment.construction,
                    'coordinates': segment.geometry
                })
        return details

    def compare_filter_preferences(self, start_lon: float, start_lat: float,
                                  end_lon: float, end_lat: float,
                                  filter_sets: List[Dict[str, float]]) -> List[Dict]:
        """
        Compare multiple routes with different filter preferences
        
        Returns:
            List of routes with different preference sets
        """
        routes = []
        for filters in filter_sets:
            route = self.find_route(start_lon, start_lat, end_lon, end_lat, filters)
            if route.get('success'):
                routes.append({
                    'filters': filters,
                    'route': route
                })
        
        return routes

    def export_route_to_json(self, route: Dict, output_file: str):
        """Export route to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(route, f, indent=2)

    def get_segment_info(self, segment_id: str) -> Optional[Dict]:
        """Get information about a specific segment"""
        segment = self.segments.get(segment_id)
        if not segment:
            return None
        
        return {
            'segment_id': segment.segment_id,
            'osm_id': segment.osm_id,
            'road_name': segment.road_name,
            'highway_type': segment.highway_type,
            'surface': segment.surface,
            'length_meters': segment.length_meters,
            'metrics': {
                'safety': segment.crime_score,
                'cleanliness': segment.dust_level,
                'noise': segment.noise_level,
                'lighting': segment.lighting,
                'construction': segment.construction,
                'maxspeed': segment.maxspeed
            },
            'geometry': segment.geometry
        }


# Example usage
if __name__ == "__main__":
    # Path to data file
    data_file = "../ghost_segments.toon"

    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        exit(1)

    # Initialize planner
    planner = GHOSTRoutePlanner(data_file)
    print(f"Loaded {len(planner.segments)} segments")

    # Example: Find a route with specific preferences
    start_lon, start_lat = 77.6675, 12.9240
    end_lon, end_lat = 77.6715, 12.9220

    filters = {
        'safety': 8,        # Very important to avoid crime
        'cleanliness': 7,   # Important for air quality
        'noise': 6,         # Moderate concern
        'lighting': 9,      # Very well-lit preferred
        'construction': 5   # Neutral about construction
    }

    print("\n" + "="*50)
    print("Finding Route with Preferences:")
    print(f"Safety: {filters['safety']}/10")
    print(f"Cleanliness: {filters['cleanliness']}/10")
    print(f"Noise: {filters['noise']}/10")
    print("="*50)

    route = planner.find_route(start_lon, start_lat, end_lon, end_lat, filters)

    if route.get('success'):
        print(f"\n✓ Route found!")
        print(f"Distance: {route['total_distance_meters']:.0f} meters")
        print(f"Segments: {route['segment_count']}")
        print(f"\nScores:")
        for key, value in route['scores'].items():
            print(f"  {key.capitalize()}: {value}/10")
        print(f"\nReasoning:\n{route['reasoning']}")
        print(f"\nHighlights:")
        for highlight in route['highlights']:
            print(f"  • {highlight}")
    else:
        print(f"✗ Error: {route.get('error')}")
