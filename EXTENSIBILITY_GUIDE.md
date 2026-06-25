# GHOST Route Planner - Extensible Architecture Guide

## Overview

The GHOST system has been refactored for **maximum extensibility** with:
- ✅ No hardcoded file paths or coordinates
- ✅ JSON-based configuration
- ✅ Configurable inputs and outputs
- ✅ End-to-end pipeline with external variable passing
- ✅ Full integration test suite

---

## Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      External Application                    │
│                  (Variables, File Paths)                     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              ConfigManager (Configuration)                   │
│          - Reads JSON config files                           │
│          - Extracts all parameters                           │
│          - Provides file path resolution                     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│           RoutePipelineProcessor (Orchestration)             │
│          - Coordinates all components                        │
│          - Manages workflow                                  │
│          - Handles errors                                    │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────┬────────┴────────┬──────────────┐
        │            │                 │              │
┌───────▼──┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│ Data     │ │ Pathfinding │ │ AI Reasoning│ │ Route Export│
│ Loader   │ │ (A*)        │ │ Engine      │ │             │
└──────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

## How to Use (External Integration)

### Step 1: Create Configuration File

Create `config.json` with your coordinates and preferences:

```json
{
  "data_file": "path/to/ghost_segments.toon",
  "route_request": {
    "start": {
      "latitude": 12.925200,
      "longitude": 77.666125,
      "name": "Point A"
    },
    "end": {
      "latitude": 12.925253,
      "longitude": 77.667994,
      "name": "Point B"
    },
    "preferences": {
      "safety": 7,
      "cleanliness": 8,
      "noise": 7,
      "lighting": 8,
      "construction": 5
    },
    "output_file": "path/to/output.json"
  }
}
```

### Step 2: Use in Your Code

**Python Integration:**

```python
from src.pipeline import RoutePipelineProcessor

# Initialize with your config file
processor = RoutePipelineProcessor('path/to/config.json')

# Run the pipeline
result = processor.process()

# Print results
processor.print_result()

# Access specific data
path = result['route_result']['path']
distance = result['route_result']['total_distance_meters']
reasoning = result['ai_analysis']['reasoning']
```

**Command Line:**

```bash
# Run pipeline
python3 src/pipeline.py

# Run tests
python3 test_e2e.py
```

---

## Configuration Structure

### ConfigManager API

```python
from src.utils.config_manager import ConfigManager, Coordinate

# Load configuration
config = ConfigManager('config.json')

# Get paths
data_file = config.get_data_file()
output_file = config.get_output_file()

# Get coordinates (returns Coordinate objects)
start = config.get_start_point()  # Coordinate(lat, lon, name)
end = config.get_end_point()

# Get as tuples for routing
start_tuple = start.to_tuple()    # (longitude, latitude)
end_tuple = end.to_tuple()

# Get preferences
preferences = config.get_preferences()  # Dict[str, float]

# Save results
config.save_output(data, output_file)
```

---

## Coordinate Handling

### Coordinate Class

```python
from src.utils.config_manager import Coordinate

# Create coordinate
coord = Coordinate(
    latitude=12.925200,
    longitude=77.666125,
    name="Point A"
)

# Access properties
print(coord.latitude)       # 12.925200
print(coord.longitude)      # 77.666125
print(coord.name)           # "Point A"

# Convert to tuple for routing (lon, lat)
lon, lat = coord.to_tuple()

# String representation
print(coord)  # "Point A(77.666125, 12.9252)"
```

---

## End-to-End Pipeline

### RoutePipelineProcessor

```python
from src.pipeline import RoutePipelineProcessor

processor = RoutePipelineProcessor('config.json')

# Execute complete pipeline
result = processor.process()

# Result structure:
{
    "execution_timestamp": "2026-06-25T14:49:48.078265",
    "status": "success",
    "request": {
        "start": {...},
        "end": {...},
        "user_preferences": {...}
    },
    "route_result": {
        "success": True,
        "path": ["S022"],
        "total_distance_meters": 184.5,
        "segment_count": 1,
        "quality_scores": {...},
        "route_details": [...]
    },
    "ai_analysis": {
        "reasoning": "Efficient Route: The recommended path...",
        "highlights": ["✓ Safest segment: ..."]
    },
    "summary": {
        "distance_km": 0.18,
        "overall_quality": 3.4,
        "path_segments": "S022"
    }
}
```

---

## Test Input/Output

### Test Input File: `test_input.json`

```json
{
  "data_file": "ghost_segments.toon",
  "route_request": {
    "start": {
      "latitude": 12.925200,
      "longitude": 77.666125,
      "name": "Point A"
    },
    "end": {
      "latitude": 12.925253,
      "longitude": 77.667994,
      "name": "Point B"
    },
    "preferences": {
      "safety": 7,
      "cleanliness": 8,
      "noise": 7,
      "lighting": 8,
      "construction": 5
    },
    "output_file": "src/test_output.json"
  }
}
```

### Test Output File: `src/test_output.json`

Sample output showing route reasoning:

```json
{
  "execution_timestamp": "2026-06-25T14:49:55.663569",
  "status": "success",
  "route_result": {
    "path": ["S022"],
    "total_distance_meters": 184.5,
    "segment_count": 1,
    "quality_scores": {
      "safety": 1.0,
      "cleanliness": 7.0,
      "noise": 7.0,
      "lighting": 2.0,
      "construction_risk": 0
    }
  },
  "ai_analysis": {
    "reasoning": "**Efficient Route**: The recommended path covers only 184 meters, minimizing travel distance. **Clean Environment**: We've chosen cleaner roads (avg dust level: 3.0/10) for better air quality. **Quiet Route**: We've minimized noise exposure (avg level: 3.0/10), ideal for peaceful travel.",
    "highlights": [
      "✓ Safest segment: Genesis Parking Road (Crime: 9/10)",
      "⚠️ Higher crime area: Genesis Parking Road (Crime: 9/10)",
      "Primary route type: Residential"
    ]
  },
  "summary": {
    "distance_km": 0.18,
    "overall_quality": 3.4,
    "path_segments": "S022"
  }
}
```

---

## Testing

### End-to-End Test Suite

```bash
# Run all integration tests
python3 test_e2e.py
```

Tests performed:
1. ✅ Configuration Loading
2. ✅ Coordinate Extraction
3. ✅ Preferences Extraction
4. ✅ End-to-End Pipeline
5. ✅ Output File Creation
6. ✅ Output Content Verification

### Manual Testing

```bash
# Run pipeline with test input
python3 src/pipeline.py

# View output
cat src/test_output.json
```

---

## Integration Examples

### Example 1: Python Script

```python
#!/usr/bin/env python3
from src.pipeline import RoutePipelineProcessor

# Create config dynamically
config = {
    "data_file": "ghost_segments.toon",
    "route_request": {
        "start": {"latitude": 12.925200, "longitude": 77.666125, "name": "Home"},
        "end": {"latitude": 12.925253, "longitude": 77.667994, "name": "Work"},
        "preferences": {"safety": 8, "cleanliness": 7, "noise": 6, "lighting": 9, "construction": 5},
        "output_file": "route_result.json"
    }
}

# Save config
import json
with open('my_config.json', 'w') as f:
    json.dump(config, f)

# Run pipeline
processor = RoutePipelineProcessor('my_config.json')
result = processor.process()

print(f"Route: {result['summary']['path_segments']}")
print(f"Distance: {result['summary']['distance_km']} km")
print(f"Reasoning: {result['ai_analysis']['reasoning']}")
```

### Example 2: External Variables

```python
# Variables from another application
start_lon, start_lat = 77.666125, 12.925200
end_lon, end_lat = 77.667994, 12.925253
user_safety_pref = 7
user_cleanliness_pref = 8

# Create config from variables
from src.utils.config_manager import Coordinate
import json
import os

config = {
    "data_file": "ghost_segments.toon",
    "route_request": {
        "start": {
            "latitude": start_lat,
            "longitude": start_lon,
            "name": "Start"
        },
        "end": {
            "latitude": end_lat,
            "longitude": end_lon,
            "name": "End"
        },
        "preferences": {
            "safety": user_safety_pref,
            "cleanliness": user_cleanliness_pref,
            "noise": 5,
            "lighting": 5,
            "construction": 5
        },
        "output_file": "result.json"
    }
}

# Process
with open('config.json', 'w') as f:
    json.dump(config, f)

from src.pipeline import RoutePipelineProcessor
processor = RoutePipelineProcessor('config.json')
result = processor.process()
```

---

## File Structure (Extensible)

```
GHOST/
├── ghost_segments.toon          # Data file (path configurable)
├── test_input.json              # Example configuration
├── src/
│   ├── pipeline.py              # End-to-end processor
│   ├── utils/
│   │   └── config_manager.py    # Configuration handling
│   ├── api/
│   │   └── route_planner.py    # Route planning (accepts file path param)
│   ├── pathfinding/
│   │   └── astar.py            # A* algorithm
│   ├── ai/
│   │   └── reasoning_engine.py # AI reasoning
│   └── data/
│       └── data_loader.py      # Data parsing
├── test_e2e.py                  # End-to-end tests
└── src/test_output.json         # Example output
```

---

## No More Hardcoding

### Before ❌
```python
# Hardcoded paths and coordinates
planner = GHOSTRoutePlanner('ghost_segments.toon')  # Path hardcoded
route = planner.find_route(77.6675, 12.9240, 77.6715, 12.9220)  # Coords hardcoded
```

### After ✅
```python
# All from configuration
from src.pipeline import RoutePipelineProcessor

processor = RoutePipelineProcessor('config.json')  # From external file
result = processor.process()  # Paths and coords come from config
```

---

## Key Features

### 1. **ConfigManager**
- Loads JSON configuration files
- Resolves file paths (absolute/relative)
- Extracts coordinates and preferences
- Handles output file locations

### 2. **Coordinate Class**
- Type-safe geographic coordinate handling
- Automatic (lat, lon) ↔ (lon, lat) conversion
- Named locations support

### 3. **RoutePipelineProcessor**
- 5-step orchestrated pipeline:
  1. Load configuration
  2. Initialize route planner
  3. Extract parameters
  4. Compute optimal route
  5. Generate formatted output

### 4. **E2E Test Suite**
- 6 comprehensive tests
- Validates all components
- Verifies output structure
- Tests complete workflow

---

## Next Steps

### Extend the System

1. **Add more metrics** to `data_loader.py`
2. **Modify cost function** in `astar.py`
3. **Add new reasoning** in `reasoning_engine.py`
4. **Extend CLI** with new options in `cli.py`
5. **Create REST API** with Flask/FastAPI

### Integration

1. Create configuration JSON from external variables
2. Call `RoutePipelineProcessor` with config path
3. Access results from returned dictionary
4. Save output to file specified in config

### Deployment

```bash
# Production setup
pip install -r requirements.txt
python3 src/pipeline.py
```

---

## Summary

✅ **Fully Extensible Architecture**
- No hardcoded paths or coordinates
- JSON-based configuration
- External variable integration
- Complete pipeline orchestration
- Comprehensive testing framework
- Ready for production deployment

**Repository**: https://github.com/RounishC/GHOST

**Test Coordinates**: (77.666125, 12.925200) → (77.667994, 12.925253)
**Test Result**: ✅ Successful route with AI reasoning
