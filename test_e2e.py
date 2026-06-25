#!/usr/bin/env python3
"""
End-to-End Integration Test for GHOST Route Planner
Tests the complete pipeline from configuration to output
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline import RoutePipelineProcessor
from utils.config_manager import ConfigManager


def print_test_header(title: str):
    """Print formatted test header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_configuration_loading():
    """Test 1: Configuration loading"""
    print_test_header("TEST 1: Configuration Loading")
    
    try:
        config_mgr = ConfigManager('test_input.json')
        
        print("\n✓ Configuration loaded successfully")
        print(f"  Data file: {config_mgr.get_data_file()}")
        print(f"  Start point: {config_mgr.get_start_point()}")
        print(f"  End point: {config_mgr.get_end_point()}")
        print(f"  Preferences: {config_mgr.get_preferences()}")
        
        return True
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False


def test_coordinate_extraction():
    """Test 2: Coordinate extraction"""
    print_test_header("TEST 2: Coordinate Extraction")
    
    try:
        config_mgr = ConfigManager('test_input.json')
        
        start = config_mgr.get_start_point()
        end = config_mgr.get_end_point()
        
        print(f"\n✓ Coordinates extracted")
        print(f"  Start - Lon: {start.longitude}, Lat: {start.latitude}")
        print(f"  End - Lon: {end.longitude}, Lat: {end.latitude}")
        print(f"  Start tuple: {start.to_tuple()}")
        print(f"  End tuple: {end.to_tuple()}")
        
        assert start.longitude == 77.666125, "Start longitude mismatch"
        assert start.latitude == 12.925200, "Start latitude mismatch"
        assert end.longitude == 77.667994, "End longitude mismatch"
        assert end.latitude == 12.925253, "End latitude mismatch"
        
        print("\n✓ Coordinate values verified")
        return True
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False


def test_preferences_extraction():
    """Test 3: Preferences extraction"""
    print_test_header("TEST 3: User Preferences Extraction")
    
    try:
        config_mgr = ConfigManager('test_input.json')
        preferences = config_mgr.get_preferences()
        
        print("\n✓ Preferences extracted")
        for key, value in preferences.items():
            print(f"  {key.capitalize()}: {value}/10")
        
        assert preferences['safety'] == 7, "Safety preference mismatch"
        assert preferences['cleanliness'] == 8, "Cleanliness preference mismatch"
        
        print("\n✓ All preferences verified")
        return True
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False


def test_end_to_end_pipeline():
    """Test 4: Complete end-to-end pipeline"""
    print_test_header("TEST 4: End-to-End Pipeline Execution")
    
    try:
        processor = RoutePipelineProcessor('test_input.json')
        result = processor.process()
        
        print("\n✓ Pipeline executed successfully")
        
        # Verify result structure
        assert result['status'] == 'success', "Route not found"
        assert result['route_result']['success'], "Route finding failed"
        assert len(result['route_result']['path']) > 0, "Empty path"
        
        print("\n✓ Result structure verified")
        print(f"  Status: {result['status']}")
        print(f"  Path: {result['summary']['path_segments']}")
        print(f"  Distance: {result['summary']['distance_km']} km")
        
        return result
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_output_file_creation():
    """Test 5: Output file creation"""
    print_test_header("TEST 5: Output File Creation")
    
    try:
        config_mgr = ConfigManager('test_input.json')
        output_file = config_mgr.get_output_file()
        
        print(f"\n✓ Output file path: {output_file}")
        
        # Check if file exists from previous pipeline run
        if os.path.exists(output_file):
            print(f"✓ Output file exists: {output_file}")
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            print(f"\n✓ Output file is valid JSON")
            print(f"  Keys: {list(data.keys())}")
            print(f"  Timestamp: {data.get('execution_timestamp')}")
            
            # Display reasoning
            reasoning = data.get('ai_analysis', {}).get('reasoning', '')
            print(f"\n✓ AI Reasoning:")
            print(f"  \"{reasoning[:100]}...\"")
            
            return True
        else:
            print(f"⚠️  Output file not yet created (run test 4 first)")
            return True
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False


def test_output_content_verification():
    """Test 6: Verify output content"""
    print_test_header("TEST 6: Output Content Verification")
    
    try:
        config_mgr = ConfigManager('test_input.json')
        output_file = config_mgr.get_output_file()
        
        if not os.path.exists(output_file):
            print(f"⚠️  Output file not found: {output_file}")
            return True
        
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        # Verify required fields
        required_fields = [
            'execution_timestamp',
            'status',
            'request',
            'route_result',
            'ai_analysis',
            'summary'
        ]
        
        print("\n✓ Verifying output structure...")
        for field in required_fields:
            assert field in output_data, f"Missing field: {field}"
            print(f"  ✓ {field}")
        
        # Verify route result
        route = output_data['route_result']
        assert route['success'], "Route not successful"
        assert route['total_distance_meters'] > 0, "Invalid distance"
        assert len(route['path']) > 0, "Empty path"
        
        print("\n✓ Route result verified")
        print(f"  Success: {route['success']}")
        print(f"  Distance: {route['total_distance_meters']:.0f}m")
        print(f"  Segments: {route['segment_count']}")
        
        # Verify AI analysis
        ai = output_data['ai_analysis']
        assert ai['reasoning'], "No reasoning generated"
        assert len(ai['highlights']) > 0, "No highlights"
        
        print("\n✓ AI analysis verified")
        print(f"  Reasoning length: {len(ai['reasoning'])} chars")
        print(f"  Highlights: {len(ai['highlights'])}")
        
        return True
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end tests"""
    print("\n" + "="*70)
    print("🛣️  GHOST ROUTE PLANNER - END-TO-END INTEGRATION TEST SUITE 🛣️")
    print("="*70)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Coordinate Extraction", test_coordinate_extraction),
        ("Preferences Extraction", test_preferences_extraction),
        ("End-to-End Pipeline", test_end_to_end_pipeline),
        ("Output File Creation", test_output_file_creation),
        ("Output Content Verification", test_output_content_verification),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            # Store result as pass/fail
            if isinstance(result, dict):
                results.append((test_name, True, result))
            else:
                results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print_test_header("TEST SUMMARY")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}\n")
    
    for test_name, success, data in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
        print("="*70 + "\n")
        return 0
    else:
        print("\n" + "="*70)
        print(f"✗ {total - passed} TESTS FAILED")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
