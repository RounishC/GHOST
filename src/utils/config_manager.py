"""
Configuration Manager for GHOST Route Planner
Handles file paths, inputs, and extensible configuration
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Coordinate:
    """Represents a geographic coordinate"""
    latitude: float
    longitude: float
    name: Optional[str] = None

    def to_tuple(self) -> tuple:
        """Return as (longitude, latitude) tuple"""
        return (self.longitude, self.latitude)

    def __repr__(self) -> str:
        if self.name:
            return f"{self.name}({self.longitude}, {self.latitude})"
        return f"({self.longitude}, {self.latitude})"


class ConfigManager:
    """Manages configuration from files and environment"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize config manager
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.config = {}
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.base_dir)
        
        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file
        
        Args:
            config_file: Path to JSON configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            # Try absolute path first
            if os.path.exists(config_file):
                config_path = config_file
            # Then try relative to project root
            elif os.path.exists(os.path.join(self.project_root, config_file)):
                config_path = os.path.join(self.project_root, config_file)
            else:
                raise FileNotFoundError(f"Config file not found: {config_file}")

            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            return self.config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

    def get_data_file(self) -> str:
        """Get path to data file"""
        data_file = self.config.get('data_file', 'ghost_segments.toon')
        
        # Try to find file in multiple locations
        possible_paths = [
            data_file,
            os.path.join(self.project_root, data_file),
            os.path.join(self.base_dir, data_file),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # Return default if not found (will error later)
        return os.path.join(self.project_root, data_file)

    def get_route_request(self) -> Dict[str, Any]:
        """Get route request from config"""
        return self.config.get('route_request', {})

    def get_start_point(self) -> Coordinate:
        """Extract start point from config"""
        route_req = self.get_route_request()
        start = route_req.get('start', {})
        return Coordinate(
            latitude=start.get('latitude'),
            longitude=start.get('longitude'),
            name=start.get('name', 'Start')
        )

    def get_end_point(self) -> Coordinate:
        """Extract end point from config"""
        route_req = self.get_route_request()
        end = route_req.get('end', {})
        return Coordinate(
            latitude=end.get('latitude'),
            longitude=end.get('longitude'),
            name=end.get('name', 'End')
        )

    def get_preferences(self) -> Dict[str, float]:
        """Get user preferences from config"""
        route_req = self.get_route_request()
        preferences = route_req.get('preferences', {})
        
        # Set defaults
        defaults = {
            'safety': 5,
            'cleanliness': 5,
            'noise': 5,
            'lighting': 5,
            'construction': 5
        }
        
        # Override with provided values
        defaults.update(preferences)
        return defaults

    def get_output_file(self) -> str:
        """Get output file path from config"""
        route_req = self.get_route_request()
        output_file = route_req.get('output_file', 'route_output.json')
        
        # Resolve to project root if relative
        if not os.path.isabs(output_file):
            output_file = os.path.join(self.project_root, output_file)
        
        return output_file

    def save_output(self, data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Save output to file
        
        Args:
            data: Data to save
            output_file: Output file path (uses config if not provided)
            
        Returns:
            Path to saved file
        """
        if not output_file:
            output_file = self.get_output_file()
        
        # Create directory if needed
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file

    @staticmethod
    def create_default_config(config_file: str = 'config.json') -> None:
        """Create a default configuration file"""
        default_config = {
            "data_file": "ghost_segments.toon",
            "route_request": {
                "start": {
                    "latitude": 12.925200,
                    "longitude": 77.666125,
                    "name": "Start Location"
                },
                "end": {
                    "latitude": 12.925253,
                    "longitude": 77.667994,
                    "name": "End Location"
                },
                "preferences": {
                    "safety": 5,
                    "cleanliness": 5,
                    "noise": 5,
                    "lighting": 5,
                    "construction": 5
                },
                "output_file": "route_output.json"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✓ Default config created: {config_file}")
