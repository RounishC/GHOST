"""
CLI Interface for GHOST Route Planner
Interactive command-line interface for route planning
"""

import sys
import json
import os
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.route_planner import GHOSTRoutePlanner


class RoutePlannerCLI:
    """Command-line interface for route planner"""

    def __init__(self, data_file: str):
        """Initialize CLI with data file"""
        try:
            self.planner = GHOSTRoutePlanner(data_file)
            print(f"\n✓ Loaded {len(self.planner.segments)} road segments")
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            sys.exit(1)

    def run(self):
        """Run the interactive CLI"""
        print("\n" + "="*60)
        print("         🛣️  GHOST ROUTE PLANNER 🛣️")
        print("      Smart Multi-Factor Route Optimization")
        print("="*60)
        
        while True:
            self.show_menu()
            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == '1':
                self.plan_route()
            elif choice == '2':
                self.compare_preferences()
            elif choice == '3':
                self.get_segment_details()
            elif choice == '4':
                self.show_help()
            elif choice == '5':
                print("\nGoodbye! 👋\n")
                break
            else:
                print("Invalid choice. Please try again.")

    def show_menu(self):
        """Display main menu"""
        print("\n" + "-"*60)
        print("Main Menu:")
        print("  1. Plan a route")
        print("  2. Compare different preferences")
        print("  3. Get segment details")
        print("  4. Help & Information")
        print("  5. Exit")
        print("-"*60)

    def plan_route(self):
        """Interactive route planning"""
        print("\n" + "="*60)
        print("PLAN A ROUTE")
        print("="*60)

        try:
            # Get coordinates
            print("\nEnter START coordinates:")
            start_lon = float(input("  Longitude: "))
            start_lat = float(input("  Latitude: "))

            print("\nEnter END coordinates:")
            end_lon = float(input("  Longitude: "))
            end_lat = float(input("  Latitude: "))

            # Get user preferences
            filters = self.get_filter_preferences()

            print("\n🔍 Searching for optimal route...")
            route = self.planner.find_route(start_lon, start_lat, end_lon, end_lat, filters)

            if route.get('success'):
                self.display_route(route)
                
                # Ask to save
                save = input("\nSave route to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"route_{route['timestamp'].replace(':', '-')}.json"
                    self.planner.export_route_to_json(route, filename)
                    print(f"✓ Route saved to {filename}")
            else:
                print(f"\n✗ Error: {route.get('error')}")

        except ValueError:
            print("✗ Invalid input. Please enter valid coordinates.")

    def get_filter_preferences(self) -> Dict[str, float]:
        """Get user preferences for filters"""
        print("\nSet your preferences (0-10 scale, 0=not important, 10=very important):")
        print("(Press Enter to use default: 5)")

        filters = {}
        filter_keys = ['safety', 'cleanliness', 'noise', 'lighting', 'construction']

        for key in filter_keys:
            while True:
                try:
                    value = input(f"  {key.capitalize()}: ")
                    if value == "":
                        filters[key] = 5
                    else:
                        filters[key] = float(value)
                        if not 0 <= filters[key] <= 10:
                            print("    Please enter a value between 0 and 10")
                            continue
                    break
                except ValueError:
                    print("    Please enter a valid number")

        return filters

    def display_route(self, route: Dict):
        """Display route details"""
        print("\n" + "="*60)
        print("✓ ROUTE FOUND!")
        print("="*60)

        print(f"\n📊 Route Statistics:")
        print(f"  • Total Distance: {route['total_distance_meters']:.0f} meters ({route['total_distance_meters']/1000:.1f} km)")
        print(f"  • Number of Segments: {route['segment_count']}")

        print(f"\n📈 Quality Scores (0-10):")
        for key, value in route['scores'].items():
            bar = "█" * int(value) + "░" * (10 - int(value))
            print(f"  • {key.capitalize():<15} [{bar}] {value}/10")

        print(f"\n💡 AI Reasoning:")
        print(f"  {route['reasoning']}")

        print(f"\n⭐ Highlights:")
        for highlight in route['highlights']:
            print(f"  • {highlight}")

        # Optional: Show detailed segment list
        show_details = input("\nShow detailed segment list? (y/n): ").strip().lower()
        if show_details == 'y':
            self.display_segment_details(route['route_details'])

    def display_segment_details(self, segments: list):
        """Display detailed segment information"""
        print("\n" + "="*60)
        print("ROUTE SEGMENTS")
        print("="*60)

        for i, seg in enumerate(segments, 1):
            print(f"\n{i}. {seg['road_name']} ({seg['highway_type']})")
            print(f"   Distance: {seg['distance_meters']:.0f}m")
            print(f"   Safety: {seg['safety']}/10 | Cleanliness: {seg['cleanliness']}/10")
            print(f"   Noise: {seg['noise']}/10 | Lighting: {seg['lighting']}/10")

    def compare_preferences(self):
        """Compare routes with different preference sets"""
        print("\n" + "="*60)
        print("COMPARE DIFFERENT PREFERENCES")
        print("="*60)

        try:
            print("\nEnter START coordinates:")
            start_lon = float(input("  Longitude: "))
            start_lat = float(input("  Latitude: "))

            print("\nEnter END coordinates:")
            end_lon = float(input("  Longitude: "))
            end_lat = float(input("  Latitude: "))

            # Define comparison scenarios
            scenarios = {
                '1': {
                    'name': 'Safety First',
                    'filters': {'safety': 10, 'cleanliness': 5, 'noise': 5, 'lighting': 8, 'construction': 5}
                },
                '2': {
                    'name': 'Comfort & Clean Air',
                    'filters': {'safety': 7, 'cleanliness': 10, 'noise': 10, 'lighting': 8, 'construction': 5}
                },
                '3': {
                    'name': 'Balanced Route',
                    'filters': {'safety': 5, 'cleanliness': 5, 'noise': 5, 'lighting': 5, 'construction': 5}
                },
                '4': {
                    'name': 'Fastest Route',
                    'filters': {'safety': 1, 'cleanliness': 1, 'noise': 1, 'lighting': 1, 'construction': 1}
                }
            }

            print("\nPre-defined scenarios:")
            for key, scenario in scenarios.items():
                print(f"  {key}. {scenario['name']}")

            print("\nSelect scenarios to compare (comma-separated, e.g., 1,2,3):")
            selection = input("  ").strip().split(',')

            filter_sets = [scenarios[s.strip()]['filters'] for s in selection if s.strip() in scenarios]

            if not filter_sets:
                print("✗ Invalid selection")
                return

            print("\n🔍 Computing routes for different preferences...")
            routes = self.planner.compare_filter_preferences(start_lon, start_lat, end_lon, end_lat, filter_sets)

            if routes:
                print("\n" + "="*60)
                print("COMPARISON RESULTS")
                print("="*60)

                for i, route_data in enumerate(routes, 1):
                    route = route_data['route']
                    filters = route_data['filters']
                    
                    print(f"\nRoute {i}:")
                    print(f"  Distance: {route['total_distance_meters']:.0f}m")
                    print(f"  Safety: {route['scores']['safety']}/10 | Cleanliness: {route['scores']['cleanliness']}/10")
                    print(f"  Noise: {route['scores']['noise']}/10 | Lighting: {route['scores']['lighting']}/10")
            else:
                print("✗ Could not find routes for comparison")

        except ValueError:
            print("✗ Invalid input")

    def get_segment_details(self):
        """Get details about a specific segment"""
        print("\n" + "="*60)
        print("GET SEGMENT DETAILS")
        print("="*60)

        segment_id = input("\nEnter Segment ID (e.g., S001): ").strip()
        
        info = self.planner.get_segment_info(segment_id)
        
        if info:
            print(f"\n{info['road_name']} - {info['highway_type']}")
            print(f"OSM ID: {info['osm_id']}")
            print(f"Surface: {info['surface']}")
            print(f"Length: {info['length_meters']:.0f} meters")
            print(f"\nMetrics:")
            for key, value in info['metrics'].items():
                print(f"  • {key.capitalize()}: {value}")
        else:
            print(f"✗ Segment {segment_id} not found")

    def show_help(self):
        """Show help and information"""
        print("\n" + "="*60)
        print("HELP & INFORMATION")
        print("="*60)
        print("""
GHOST Route Planner uses A* pathfinding algorithm combined with AI reasoning
to find the optimal route based on your preferences.

FILTERS (0-10 scale):
  • Safety (0=risky, 10=very safe): Avoids high-crime areas
  • Cleanliness (0=dusty, 10=clean): Prioritizes air quality
  • Noise (0=loud, 10=quiet): Minimizes noise exposure
  • Lighting (0=dark, 10=well-lit): Ensures visibility
  • Construction (0=avoid, 10=okay): Tolerates construction zones

COORDINATES:
  • Use decimal format (e.g., 77.6675 for longitude)
  • Positive = East/North, Negative = West/South

AI REASONING:
  The planner explains why a route is recommended and highlights
  key factors affecting your journey.

FEATURES:
  • Multi-factor optimization using A* algorithm
  • AI-generated explanations for route selection
  • Route comparison with different preferences
  • Segment-level details and metrics
  • Route export to JSON format
        """)


def main():
    """Main entry point"""
    # Try to find data file
    possible_paths = [
        'ghost_segments.toon',
        '../ghost_segments.toon',
        '../../ghost_segments.toon',
        '/Users/jiya/Downloads/GHOST/ghost_segments.toon'
    ]

    data_file = None
    for path in possible_paths:
        if os.path.exists(path):
            data_file = path
            break

    if not data_file:
        print("✗ Error: ghost_segments.toon not found")
        print("Please ensure the data file is in the working directory or parent directories")
        sys.exit(1)

    cli = RoutePlannerCLI(data_file)
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye! 👋\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
