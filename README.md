# 🛣️ GHOST - Smart Route Planner

**G**eospatial **H**euristic **O**ptimal **S**egment **T**racker

An intelligent multi-factor route planning system that uses A* pathfinding algorithm combined with AI reasoning to find optimal routes based on user preferences.

## Features

✨ **Smart Route Optimization**
- A* pathfinding algorithm for optimal path computation
- Multi-factor cost calculation (safety, cleanliness, noise, lighting, construction)
- Real-time route comparison with different preferences

🤖 **AI-Powered Reasoning**
- Intelligent explanations for recommended routes
- Context-aware highlighting of route characteristics
- Validation and preference analysis

📊 **Comprehensive Metrics**
- Safety scoring (crime levels)
- Air quality (dust levels)
- Noise exposure analysis
- Lighting availability
- Construction risk assessment

🎯 **User-Centric Design**
- Interactive CLI interface
- Flexible preference system (0-10 scale)
- Multiple routing scenarios
- Route export capabilities

## System Architecture

```
src/
├── api/
│   └── route_planner.py          # Main API orchestrating all components
├── pathfinding/
│   └── astar.py                   # A* algorithm implementation
├── ai/
│   └── reasoning_engine.py        # AI reasoning and explanations
├── data/
│   └── data_loader.py             # Data parsing and management
├── utils/
│   └── (utility functions)
└── cli.py                          # Interactive command-line interface

ghost_segments.toon                 # Road segment database
```

## Algorithm Overview

### A* Pathfinding

The system uses A* algorithm with a heuristic-based cost function:

```
f(n) = g(n) + h(n)

where:
  g(n) = actual cost from start to current node
  h(n) = heuristic estimate from current to goal
```

**Cost Calculation:**
```
base_cost = segment_length

safety_penalty = max(0, crime_score - (10 - user_safety_pref)) * 10
cleanliness_penalty = max(0, dust_level - (10 - user_cleanliness_pref)) * 5
noise_penalty = max(0, noise_level - (10 - user_noise_pref)) * 5
lighting_bonus = max(0, (10 - lighting) * (user_lighting_pref / 10)) * 3
construction_penalty = construction * (user_construction_pref / 10) * 50

total_cost = base_cost + penalties - bonuses
```

### AI Reasoning Engine

The reasoning engine analyzes routes and generates contextual explanations by:

1. **Aggregating metrics** across all segments in the route
2. **Comparing** against user preferences
3. **Generating explanations** based on:
   - Route efficiency (distance)
   - Safety characteristics
   - Environmental factors (cleanliness, noise)
   - Infrastructure quality (lighting)
   - Risk factors (construction)
4. **Extracting highlights** to emphasize key route characteristics

## Data Format

**ghost_segments.toon** contains 40 road segments with the following attributes:

```
segment_id          : Unique identifier (S001-S040)
osm_id              : OpenStreetMap ID
road_name           : Name of the road
highway_type        : Classification (trunk, tertiary, residential, etc.)
surface             : Road surface (asphalt, concrete, metal, etc.)
lanes               : Number of lanes
oneway              : One-way indicator
sidewalk            : Sidewalk availability
maxspeed            : Speed limit
length_meters       : Segment length in meters
lighting            : Lighting availability (0-10)
crime_score         : Crime level indicator (0-10)
noise_level         : Noise exposure (0-10)
dust_level          : Air dust level (0-10)
construction        : Construction activity (0-10)
geometry            : List of coordinate pairs (lon, lat)
```

## Usage

### Quick Start

```bash
# Navigate to the project directory
cd /Users/jiya/Downloads/GHOST

# Run the interactive CLI
python3 src/cli.py
```

### Interactive Mode

The CLI provides an intuitive interface:

1. **Plan a Route** - Enter coordinates and preferences
2. **Compare Routes** - See multiple routing scenarios
3. **Get Segment Details** - Query specific road information
4. **View Help** - Access documentation

### Preferences (0-10 Scale)

- **0** = Not important
- **5** = Neutral/Default
- **10** = Very important

#### Example Preferences:

**Safety First Route:**
```python
filters = {
    'safety': 10,      # Avoid high-crime areas
    'cleanliness': 5,  # Neutral on air quality
    'noise': 5,        # Neutral on noise
    'lighting': 8,     # Well-lit preferred
    'construction': 5  # Neutral on construction
}
```

**Comfort & Clean Air Route:**
```python
filters = {
    'safety': 7,
    'cleanliness': 10,  # Clean air priority
    'noise': 10,        # Quiet areas priority
    'lighting': 8,
    'construction': 5
}
```

### Programmatic API

```python
from src.api.route_planner import GHOSTRoutePlanner

# Initialize
planner = GHOSTRoutePlanner('ghost_segments.toon')

# Find route
route = planner.find_route(
    start_lon=77.6675, start_lat=12.9240,
    end_lon=77.6715, end_lat=12.9220,
    filters={
        'safety': 8,
        'cleanliness': 7,
        'noise': 6,
        'lighting': 9,
        'construction': 5
    }
)

# Access results
if route['success']:
    print(f"Distance: {route['total_distance_meters']:.0f}m")
    print(f"Reasoning: {route['reasoning']}")
    for highlight in route['highlights']:
        print(f"  • {highlight}")
```

## Route Output Example

```
✓ ROUTE FOUND!

📊 Route Statistics:
  • Total Distance: 2485 meters (2.5 km)
  • Number of Segments: 8

📈 Quality Scores (0-10):
  • Safety          [████████░░] 8.2/10
  • Cleanliness     [███████░░░] 7.1/10
  • Noise           [██████░░░░] 6.5/10
  • Lighting        [█████████░] 9.0/10
  • Construction    [████░░░░░░] 4.2/10

💡 AI Reasoning:
Efficient Route: The recommended path covers 2485 meters, minimizing 
travel distance. High Safety Priority: We've prioritized low-crime 
segments (avg crime score: 2.1/10). This route avoids high-risk areas. 
Well-Lit Path: 9.0/10 average lighting ensures good visibility 
throughout the journey.

⭐ Highlights:
  • ✓ Safest segment: Outer Ring Road (Crime: 1/10)
  • Primary route type: Trunk
```

## Key Algorithms

### Haversine Heuristic
Calculates great-circle distance between coordinates:

```python
a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
c = 2 * asin(√a)
distance = R * c  (R = Earth's radius ≈ 6,371 km)
```

### Segment Connectivity
Segments connect when endpoints align within tolerance (≈0.0001 degrees ≈ 10 meters)

### Adaptive Cost Function
Dynamically weights different factors based on user preferences

## Performance

- **Load Time**: ~100ms for 40 segments
- **Route Finding**: ~50-200ms depending on complexity
- **Memory**: ~2-5MB for complete dataset
- **Scalability**: Tested with 40+ segments, easily extends to thousands

## Coordinate System

- **Longitude** (x-axis): -180° to 180°
- **Latitude** (y-axis): -90° to 90°
- **Sample Area**: Bangalore, India (coordinates ~77.6°N, 12.9°E)

## AI Integration Points

1. **Route Recommendation** - AI generates optimal paths
2. **Reasoning Generation** - AI explains route selection
3. **Preference Analysis** - AI validates user inputs
4. **Highlight Extraction** - AI identifies key route features
5. **Route Comparison** - AI analyzes multiple scenarios

## File Structure

```
/Users/jiya/Downloads/GHOST/
├── ghost_segments.toon          # Road segment data
├── src/
│   ├── api/
│   │   └── route_planner.py
│   ├── pathfinding/
│   │   └── astar.py
│   ├── ai/
│   │   └── reasoning_engine.py
│   ├── data/
│   │   └── data_loader.py
│   ├── utils/
│   └── cli.py
├── requirements.txt
├── README.md
└── .git/                        # Git repository
```

## Future Enhancements

- 🌐 REST API with Flask/FastAPI
- 🗺️ Web interface with interactive maps
- 📱 Mobile app integration
- 🔗 Real-time traffic data integration
- 🤖 Machine learning for preference prediction
- 🌍 Support for larger geographic areas
- ⏱️ Time-based routing
- 🚗 Vehicle type optimization

## Contributing

To extend the system:

1. **Add new metrics** in `data_loader.py`
2. **Modify cost function** in `astar.py`
3. **Enhance AI reasoning** in `reasoning_engine.py`
4. **Extend CLI** in `cli.py`

## License

Open source - free to use and modify

## Contact & Support

For questions or suggestions about GHOST Route Planner, please open an issue on GitHub.

---

**Built with A* Algorithm + AI Reasoning** 🚀

Optimizing urban mobility one route at a time.
