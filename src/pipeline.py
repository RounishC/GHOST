"""
End-to-End Pipeline for GHOST Route Planner
Orchestrates the complete routing workflow with configurable inputs/outputs
"""

import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.route_planner import GHOSTRoutePlanner
from utils.config_manager import ConfigManager, Coordinate


class RoutePipelineProcessor:
    """End-to-end pipeline processor for route planning"""

    def __init__(self, config_file: str):
        """
        Initialize pipeline
        
        Args:
            config_file: Path to configuration JSON file
        """
        self.config_manager = ConfigManager(config_file)
        self.planner = None
        self.result = None

    def process(self) -> Dict[str, Any]:
        """
        Execute the complete pipeline:
        1. Load configuration
        2. Initialize route planner with data file
        3. Get start/end points and preferences
        4. Find optimal route
        5. Generate output
        6. Save to file
        
        Returns:
            Complete route result with reasoning
        """
        try:
            # Step 1: Load configuration
            data_file = self.config_manager.get_data_file()
            
            if not os.path.exists(data_file):
                raise FileNotFoundError(f"Data file not found: {data_file}")

            # Step 2: Initialize route planner
            self.planner = GHOSTRoutePlanner(data_file)

            # Step 3: Extract route parameters
            start_point = self.config_manager.get_start_point()
            end_point = self.config_manager.get_end_point()
            preferences = self.config_manager.get_preferences()

            # Step 4: Find optimal route
            route = self.planner.find_route(
                start_lon=start_point.longitude,
                start_lat=start_point.latitude,
                end_lon=end_point.longitude,
                end_lat=end_point.latitude,
                filters=preferences
            )

            if not route.get('success'):
                raise RuntimeError(f"Route finding failed: {route.get('error')}")

            # Step 5: Generate output
            self.result = self._format_output(
                route=route,
                start_point=start_point,
                end_point=end_point,
                preferences=preferences
            )

            output_file = self.config_manager.get_output_file()
            self.config_manager.save_output(self.result, output_file)

            return self.result

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _format_output(self, route: Dict, start_point: Coordinate,
                      end_point: Coordinate, preferences: Dict) -> Dict[str, Any]:
        """
        Format route output with reasoning and metadata
        
        Returns:
            Formatted output dictionary
        """
        return {
            "execution_timestamp": datetime.now().isoformat(),
            "status": "success",
            "request": {
                "start": {
                    "name": start_point.name,
                    "coordinates": {
                        "longitude": start_point.longitude,
                        "latitude": start_point.latitude
                    }
                },
                "end": {
                    "name": end_point.name,
                    "coordinates": {
                        "longitude": end_point.longitude,
                        "latitude": end_point.latitude
                    }
                },
                "user_preferences": preferences
            },
            "route_result": {
                "success": route['success'],
                "path": route['path'],
                "total_distance_meters": route['total_distance_meters'],
                "segment_count": route['segment_count'],
                "quality_scores": route['scores'],
                "route_details": route['route_details']
            },
            "ai_analysis": {
                "reasoning": route['reasoning'],
                "highlights": route['highlights']
            },
            "summary": {
                "distance_km": round(route['total_distance_meters'] / 1000, 2),
                "overall_quality": round(
                    sum(route['scores'].values()) / len(route['scores']), 1
                ),
                "path_segments": " → ".join(route['path'])
            }
        }

    def print_result(self):
        """Print a concise human-readable summary with street names"""
        if not self.result:
            print("No result to display. Run process() first.")
            return

        result = self.result
        summary = result['summary']
        ai = result['ai_analysis']
        route_details = result['route_result']['route_details']

        # Build street names list
        streets = [segment['road_name'] for segment in route_details]
        street_path = " → ".join(streets)

        print(f"\n🛣️  Streets to travel:")
        print(f"   {street_path}")
        print(f"\n📏 Distance: {summary['distance_km']} km")
        print(f"\n💡 {ai['reasoning']}\n")


def main():
    """Main entry point for pipeline"""
    config_file = 'test_input.json'
    
    try:
        # Run pipeline
        processor = RoutePipelineProcessor(config_file)
        result = processor.process()
        
        # Print concise summary
        processor.print_result()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
