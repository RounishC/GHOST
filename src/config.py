"""
Configuration for GHOST Route Planner
"""

# Data file path
DATA_FILE = "ghost_segments.toon"

# Default filter preferences (0-10 scale)
DEFAULT_FILTERS = {
    'safety': 5,
    'cleanliness': 5,
    'noise': 5,
    'lighting': 5,
    'construction': 5
}

# Coordinate precision (degrees, ~10 meters for 0.0001)
COORDINATE_TOLERANCE = 0.0001

# A* algorithm parameters
ASTAR_CONFIG = {
    'max_iterations': 10000,
    'timeout_seconds': 30,
    'heuristic': 'haversine'  # Distance metric
}

# Scoring weights (can be adjusted for different emphasis)
SCORING_WEIGHTS = {
    'distance': 1.0,
    'safety': 1.0,
    'cleanliness': 0.8,
    'noise': 0.8,
    'lighting': 0.6,
    'construction': 0.9
}

# Coordinate bounds for valid area (Bangalore, India)
BOUNDS = {
    'min_lon': 77.6600,
    'max_lon': 77.6800,
    'min_lat': 12.9180,
    'max_lat': 12.9300
}

# Filter validation
FILTER_CONSTRAINTS = {
    'safety': {'min': 0, 'max': 10},
    'cleanliness': {'min': 0, 'max': 10},
    'noise': {'min': 0, 'max': 10},
    'lighting': {'min': 0, 'max': 10},
    'construction': {'min': 0, 'max': 10}
}

# Metric ranges (for normalization)
METRIC_RANGES = {
    'crime_score': {'min': 0, 'max': 10},
    'dust_level': {'min': 0, 'max': 10},
    'noise_level': {'min': 0, 'max': 10},
    'lighting': {'min': 0, 'max': 10},
    'construction': {'min': 0, 'max': 10},
    'length_meters': {'min': 0, 'max': 2000}
}

# Output format
OUTPUT_FORMAT = 'json'  # Options: 'json', 'csv', 'geojson'

# Logging
LOG_LEVEL = 'INFO'  # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_FILE = 'ghost_planner.log'

# Cache settings
ENABLE_CACHE = True
CACHE_DIR = '.cache'
CACHE_EXPIRY_HOURS = 24
