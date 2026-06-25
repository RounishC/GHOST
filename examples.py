"""
Example usage of GHOST Route Planner
Demonstrates various features and use cases
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.route_planner import GHOSTRoutePlanner
import json


def example_1_basic_route():
    """Example 1: Find a basic route"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Route Planning")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    # Find route with default preferences
    route = planner.find_route(
        start_lon=77.6675, start_lat=12.9240,
        end_lon=77.6715, end_lat=12.9220
    )

    if route.get('success'):
        print(f"\n✓ Route found!")
        print(f"  Distance: {route['total_distance_meters']:.0f}m")
        print(f"  Segments: {route['segment_count']}")
        print(f"  Safety Score: {route['scores']['safety']}/10")
    else:
        print(f"✗ Error: {route.get('error')}")


def example_2_safety_first():
    """Example 2: Safety-first routing"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Safety-First Route")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    # High safety preference
    filters = {
        'safety': 10,       # Maximum safety
        'cleanliness': 5,
        'noise': 5,
        'lighting': 8,      # Well-lit
        'construction': 5
    }

    route = planner.find_route(
        start_lon=77.6675, start_lat=12.9240,
        end_lon=77.6715, end_lat=12.9220,
        filters=filters
    )

    if route.get('success'):
        print(f"\n✓ Safety-optimized route found!")
        print(f"  Total Distance: {route['total_distance_meters']:.0f}m")
        print(f"\n  Route Quality Scores:")
        for metric, score in route['scores'].items():
            print(f"    {metric.capitalize():<15}: {score:>5.1f}/10")
        print(f"\n  AI Reasoning:")
        print(f"    {route['reasoning']}")
        print(f"\n  Route Highlights:")
        for highlight in route['highlights']:
            print(f"    • {highlight}")


def example_3_comfort_route():
    """Example 3: Comfort and air quality focused"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Comfort & Clean Air Route")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    filters = {
        'safety': 7,
        'cleanliness': 10,    # Maximum cleanliness priority
        'noise': 10,          # Quiet areas priority
        'lighting': 8,
        'construction': 5
    }

    route = planner.find_route(
        start_lon=77.6675, start_lat=12.9240,
        end_lon=77.6715, end_lat=12.9220,
        filters=filters
    )

    if route.get('success'):
        print(f"\n✓ Comfort-optimized route found!")
        print(f"  Total Distance: {route['total_distance_meters']:.0f}m")
        print(f"  Cleanliness Score: {route['scores']['cleanliness']}/10")
        print(f"  Noise Score: {route['scores']['noise']}/10")


def example_4_compare_preferences():
    """Example 4: Compare multiple preference scenarios"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Comparing Multiple Route Preferences")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    scenarios = [
        {
            'name': 'Safety First',
            'filters': {'safety': 10, 'cleanliness': 5, 'noise': 5, 'lighting': 8, 'construction': 5}
        },
        {
            'name': 'Clean Air Priority',
            'filters': {'safety': 7, 'cleanliness': 10, 'noise': 10, 'lighting': 8, 'construction': 5}
        },
        {
            'name': 'Balanced',
            'filters': {'safety': 5, 'cleanliness': 5, 'noise': 5, 'lighting': 5, 'construction': 5}
        }
    ]

    filter_sets = [s['filters'] for s in scenarios]
    routes = planner.compare_filter_preferences(
        start_lon=77.6675, start_lat=12.9240,
        end_lon=77.6715, end_lat=12.9220,
        filter_sets=filter_sets
    )

    print(f"\nComparing {len(routes)} different routing preferences:\n")

    for i, (scenario, route_data) in enumerate(zip(scenarios, routes)):
        route = route_data['route']
        if route.get('success'):
            print(f"\n{i+1}. {scenario['name']}")
            print(f"   Distance: {route['total_distance_meters']:.0f}m")
            print(f"   Safety: {route['scores']['safety']:>5.1f}/10")
            print(f"   Cleanliness: {route['scores']['cleanliness']:>5.1f}/10")
            print(f"   Noise: {route['scores']['noise']:>5.1f}/10")


def example_5_segment_details():
    """Example 5: Get details about specific segments"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Segment Details")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    # Get info for segment S001
    info = planner.get_segment_info('S001')

    if info:
        print(f"\nSegment: {info['road_name']}")
        print(f"Type: {info['highway_type']}")
        print(f"Length: {info['length_meters']:.0f}m")
        print(f"\nMetrics:")
        for key, value in info['metrics'].items():
            print(f"  {key.capitalize():<15}: {value}")
    else:
        print("Segment not found")


def example_6_export_route():
    """Example 6: Export route to JSON"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Exporting Route to JSON")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    filters = {
        'safety': 8,
        'cleanliness': 7,
        'noise': 6,
        'lighting': 9,
        'construction': 5
    }

    route = planner.find_route(
        start_lon=77.6675, start_lat=12.9240,
        end_lon=77.6715, end_lat=12.9220,
        filters=filters
    )

    if route.get('success'):
        # Export to file
        output_file = 'example_route.json'
        planner.export_route_to_json(route, output_file)
        print(f"\n✓ Route exported to {output_file}")
        
        # Show preview
        print(f"\nRoute Summary:")
        print(f"  Distance: {route['total_distance_meters']:.0f}m")
        print(f"  Segments: {route['segment_count']}")
        print(f"  File size: {os.path.getsize(output_file)} bytes")


def example_7_route_analysis():
    """Example 7: Detailed route analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Detailed Route Analysis")
    print("="*70)

    planner = GHOSTRoutePlanner('ghost_segments.toon')

    filters = {
        'safety': 8,
        'cleanliness': 8,
        'noise': 7,
        'lighting': 8,
        'construction': 5
    }

    route = planner.find_route(
        start_lon=77.6675, start_lat=12.9240,
        end_lon=77.6715, end_lat=12.9220,
        filters=filters
    )

    if route.get('success'):
        print(f"\n✓ Analyzing route...\n")
        print(f"Route Statistics:")
        print(f"  Total Distance: {route['total_distance_meters']:.0f}m")
        print(f"  Total Segments: {route['segment_count']}")
        print(f"  Average Segment Length: {route['total_distance_meters']/route['segment_count']:.0f}m")

        print(f"\nQuality Assessment:")
        scores = route['scores']
        avg_score = sum(scores.values()) / len(scores)
        print(f"  Average Quality Score: {avg_score:.1f}/10")
        
        best_metric = max(scores.items(), key=lambda x: x[1])
        worst_metric = min(scores.items(), key=lambda x: x[1])
        
        print(f"  Best Metric: {best_metric[0].capitalize()} ({best_metric[1]:.1f}/10)")
        print(f"  Worst Metric: {worst_metric[0].capitalize()} ({worst_metric[1]:.1f}/10)")

        print(f"\nTop 3 Route Segments:")
        for i, seg in enumerate(route['route_details'][:3], 1):
            print(f"  {i}. {seg['road_name']} ({seg['distance_meters']:.0f}m)")
            print(f"     Type: {seg['highway_type']}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print(" "*15 + "🛣️  GHOST ROUTE PLANNER EXAMPLES 🛣️")
    print("="*70)

    examples = [
        ("Basic Route Planning", example_1_basic_route),
        ("Safety-First Routing", example_2_safety_first),
        ("Comfort & Clean Air", example_3_comfort_route),
        ("Compare Preferences", example_4_compare_preferences),
        ("Segment Details", example_5_segment_details),
        ("Export Route", example_6_export_route),
        ("Route Analysis", example_7_route_analysis),
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
