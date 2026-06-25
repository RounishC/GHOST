"""
Data loader for ghost_segments.toon file
Parses and structures the segment data for pathfinding
"""

import csv
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Segment:
    """Represents a road segment"""
    segment_id: str
    osm_id: str
    road_name: str
    highway_type: str
    surface: str
    lanes: str
    oneway: str
    sidewalk: str
    maxspeed: str
    length_meters: float
    lighting: int
    crime_score: int
    noise_level: int
    dust_level: int
    construction: int
    geometry: List[Tuple[float, float]]

    def get_start_point(self) -> Tuple[float, float]:
        """Get first coordinate"""
        return self.geometry[0]

    def get_end_point(self) -> Tuple[float, float]:
        """Get last coordinate"""
        return self.geometry[-1]

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'segment_id': self.segment_id,
            'road_name': self.road_name,
            'highway_type': self.highway_type,
            'length_meters': self.length_meters,
            'lighting': self.lighting,
            'crime_score': self.crime_score,
            'noise_level': self.noise_level,
            'dust_level': self.dust_level,
            'construction': self.construction,
        }


class DataLoader:
    """Loads and parses ghost segments data"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.segments: Dict[str, Segment] = {}
        self.spatial_index: Dict[str, str] = {}  # For fast lookup

    def load(self) -> Dict[str, Segment]:
        """Load data from .toon file"""
        with open(self.file_path, 'r') as f:
            lines = f.readlines()

        for line in lines[1:]:  # Skip header
            line = line.strip()
            if not line:
                continue

            parts = line.split(',', 15)  # Split into 16 parts (0-15)
            if len(parts) < 16:
                continue

            try:
                segment_id = parts[0]
                osm_id = parts[1]
                road_name = parts[2]
                highway_type = parts[3]
                surface = parts[4]
                lanes = parts[5]
                oneway = parts[6]
                sidewalk = parts[7]
                maxspeed = parts[8]
                length_meters = float(parts[9])
                lighting = int(parts[10])
                crime_score = int(parts[11])
                noise_level = int(parts[12])
                dust_level = int(parts[13])
                construction = int(parts[14])
                geometry_str = parts[15].strip('"')

                # Parse geometry (lon,lat pairs)
                coords = []
                for coord_pair in geometry_str.split(';'):
                    lon, lat = coord_pair.split(',')
                    coords.append((float(lon), float(lat)))

                segment = Segment(
                    segment_id=segment_id,
                    osm_id=osm_id,
                    road_name=road_name,
                    highway_type=highway_type,
                    surface=surface,
                    lanes=lanes,
                    oneway=oneway,
                    sidewalk=sidewalk,
                    maxspeed=maxspeed,
                    length_meters=length_meters,
                    lighting=lighting,
                    crime_score=crime_score,
                    noise_level=noise_level,
                    dust_level=dust_level,
                    construction=construction,
                    geometry=coords
                )

                self.segments[segment_id] = segment
            except (ValueError, IndexError) as e:
                print(f"Error parsing segment: {e}")
                continue

        return self.segments

    def get_segment(self, segment_id: str) -> Segment:
        """Get segment by ID"""
        return self.segments.get(segment_id)

    def find_nearby_segments(self, lon: float, lat: float, radius: float = 0.001) -> List[Segment]:
        """Find segments near a coordinate"""
        nearby = []
        for segment in self.segments.values():
            for coord in segment.geometry:
                if (abs(coord[0] - lon) < radius and abs(coord[1] - lat) < radius):
                    nearby.append(segment)
                    break
        return nearby

    def get_all_segments(self) -> List[Segment]:
        """Get all segments"""
        return list(self.segments.values())

    def save_to_json(self, output_path: str):
        """Save segments as JSON"""
        data = {seg_id: seg.to_dict() for seg_id, seg in self.segments.items()}
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
