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
        print("\n" + "="*70)
        print("GHOST ROUTE PLANNER - END-TO-END PIPELINE")
        print("="*70)

        try:
            # Step 1: Load configuration
            print("\n[1/5] Loading configuration...")
            data_file = self.config_manager.get_data_file()
            print(f"  ✓ Data file: {data_file}")
            
            if not os.path.exists(data_file):
                raise FileNotFoundError(f"Data file not found: {data_file}")

            # Step 2: Initialize route planner
            print("\n[2/5] Initializing route planner...")
            self.planner = GHOSTRoutePlanner(data_file)
            print(f"  ✓ Loaded {len(self.planner.segments)} segments")
            print(f"  ✓ Graph connectivity: {sum(1 for s in self.planner.graph.values() if s)}/40 segments")

            # Step 3: Extract route parameters
            print("\n[3/5] Extracting route parameters...")
            start_point = self.config_manager.get_start_point()
            end_point = self.config_manager.get_end_point()
            preferences = self.config_manager.get_preferences()

            print(f"  ✓ Start: {start_point}")
            print(f"  ✓ End: {end_point}")
            print(f"  ✓ Preferences: {preferences}")

            # Step 4: Find optimal route
            print("\n[4/5] Computing optimal route...")
            route = self.planner.find_route(
                start_lon=start_point.longitude,
                start_lat=start_point.latitude,
                end_lon=end_point.longitude,
                end_lat=end_point.latitude,
                filters=preferences
            )

            if not route.get('success'):
                raise RuntimeError(f"Route finding failed: {route.get('error')}")

            print(f"  ✓ Route found!")
            print(f"  ✓ Distance: {route['total_distance_meters']:.0f}m")
            print(f"  ✓ Segments: {route['segment_count']}")

            # Step 5: Generate output
            print("\n[5/5] Generating output...")
            self.result = self._format_output(
                route=route,
                start_point=start_point,
                end_point=end_point,
                preferences=preferences
            )

            output_file = self.config_manager.get_output_file()
            saved_path = self.config_manager.save_output(self.result, output_file)
            print(f"  ✓ Output saved to: {saved_path}")

            print("\n" + "="*70)
            print("✓ PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
            print("="*70 + "\n")

            return self.result

        except Exception as e:
            print(f"\n✗ Pipeline error: {e}")
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
        """Print the result in human-readable format"""
        if not self.result:
            print("No result to display. Run process() first.")
            return

        result = self.result
        req = result['request']
        route = result['route_result']
        ai = result['ai_analysis']
        summary = result['summary']

        print("\n" + "="*70)
        print("ROUTE PLANNING RESULT")
        print("="*70)

        print(f"\n📍 REQUEST:")
        print(f"  Start: {req['start']['name']} ({req['start']['coordinates']['longitude']}, {req['start']['coordinates']['latitude']})")
        print(f"  End: {req['end']['name']} ({req['end']['coordinates']['longitude']}, {req['end']['coordinates']['latitude']})")

        print(f"\n🎯 USER PREFERENCES:")
        for key, value in req['user_preferences'].items():
            print(f"  {key.capitalize()}: {value}/10")

        print(f"\n✓ ROUTE FOUND:")
        print(f"  Distance: {summary['distance_km']} km ({route['total_distance_meters']:.0f}m)")
        print(f"  Segments: {route['segment_count']}")
        print(f"  Path: {summary['path_segments']}")

        print(f"\n📊 QUALITY SCORES:")
        for metric, score in route['quality_scores'].items():
            bar = "█" * int(score) + "░" * (10 - int(score))
            print(f"  {metric.capitalize():<18} [{bar}] {score:.1f}/10")

        print(f"\n💡 AI REASONING:")
        print(f"  {ai['reasoning']}")

        print(f"\n⭐ HIGHLIGHTS:")
        for highlight in ai['highlights']:
            print(f"  • {highlight}")

        print(f"\n📈 OVERALL QUALITY: {summary['overall_quality']}/10")
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point for pipeline"""
    config_file = 'test_input.json'
    
    try:
        # Run pipeline
        processor = RoutePipelineProcessor(config_file)
        result = processor.process()
        
        # Print human-readable output
        processor.print_result()
        
        # Also show JSON output
        print("\n" + "="*70)
        print("JSON OUTPUT (saved to file):")
        print("="*70)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
