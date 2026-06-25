"""
A* Pathfinding Algorithm for optimal route finding
Considers multiple factors: distance, safety, cleanliness, noise, etc.
"""

import heapq
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


@dataclass(order=True)
class Node:
    """Node for A* algorithm"""
    f_score: float
    segment_id: str = field(compare=False)
    g_score: float = field(compare=False)
    h_score: float = field(compare=False)
    parent: Optional['Node'] = field(compare=False, default=None)


class AStarPathfinder:
    """A* pathfinding algorithm with multi-factor scoring"""

    def __init__(self, segments_dict: Dict, segment_graph: Dict):
        """
        Args:
            segments_dict: Dict of segment_id -> Segment
            segment_graph: Dict of segment_id -> [connected_segment_ids]
        """
        self.segments = segments_dict
        self.graph = segment_graph

    def heuristic(self, start_coord: Tuple[float, float], 
                  end_coord: Tuple[float, float]) -> float:
        """Haversine distance heuristic"""
        lon1, lat1 = start_coord
        lon2, lat2 = end_coord
        
        # Approximate distance in meters
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # Earth radius in meters
        return c * r

    def calculate_segment_cost(self, segment, filters: Dict[str, float]) -> float:
        """
        Calculate cost of traversing a segment based on filters
        Filters: {'safety': 0-10, 'cleanliness': 0-10, 'noise': 0-10, 
                  'lighting': 0-10, 'construction': 0-10}
        
        Lower cost is better
        """
        cost = segment.length_meters  # Base cost is distance

        # Safety factor (crime_score: 0-10, lower is safer)
        if 'safety' in filters:
            safety_weight = filters['safety']  # User's safety preference (0-10)
            # If user wants safety=10 (very safe), penalize high crime segments
            safety_penalty = max(0, segment.crime_score - (10 - safety_weight)) * 10
            cost += safety_penalty

        # Cleanliness factor (dust_level: 0-10, lower is cleaner)
        if 'cleanliness' in filters:
            cleanliness_weight = filters['cleanliness']
            dust_penalty = max(0, segment.dust_level - (10 - cleanliness_weight)) * 5
            cost += dust_penalty

        # Noise factor (noise_level: 0-10, lower is quieter)
        if 'noise' in filters:
            noise_weight = filters['noise']
            noise_penalty = max(0, segment.noise_level - (10 - noise_weight)) * 5
            cost += noise_penalty

        # Lighting factor (lighting: 0-10, higher is better)
        if 'lighting' in filters:
            lighting_weight = filters['lighting']
            # Prefer well-lit paths
            lighting_bonus = max(0, (10 - segment.lighting) * (lighting_weight / 10)) * 3
            cost += lighting_bonus

        # Construction factor (construction: 0-10, lower is better)
        if 'construction' in filters:
            construction_weight = filters['construction']
            construction_penalty = segment.construction * (construction_weight / 10) * 50
            cost += construction_penalty

        return cost

    def find_path(self, start_segment_id: str, end_segment_id: str,
                  filters: Dict[str, float]) -> Optional[List[str]]:
        """
        Find optimal path using A* algorithm
        
        Args:
            start_segment_id: Starting segment ID
            end_segment_id: Ending segment ID
            filters: Dictionary of user preferences
            
        Returns:
            List of segment IDs forming the path, or None if no path found
        """
        if start_segment_id not in self.segments or end_segment_id not in self.segments:
            return None

        start_segment = self.segments[start_segment_id]
        end_segment = self.segments[end_segment_id]
        
        start_coord = start_segment.get_end_point()
        end_coord = end_segment.get_start_point()

        open_set = []
        g_scores = {start_segment_id: 0}
        f_scores = {start_segment_id: self.heuristic(start_coord, end_coord)}
        
        start_node = Node(
            f_score=f_scores[start_segment_id],
            segment_id=start_segment_id,
            g_score=0,
            h_score=f_scores[start_segment_id]
        )
        heapq.heappush(open_set, start_node)

        closed_set = set()
        parent_map = {start_segment_id: None}

        while open_set:
            current_node = heapq.heappop(open_set)
            current_id = current_node.segment_id

            if current_id in closed_set:
                continue

            if current_id == end_segment_id:
                # Reconstruct path
                path = []
                node_id = current_id
                while node_id is not None:
                    path.append(node_id)
                    node_id = parent_map[node_id]
                return path[::-1]

            closed_set.add(current_id)

            # Check neighbors
            neighbors = self.graph.get(current_id, [])
            for neighbor_id in neighbors:
                if neighbor_id in closed_set:
                    continue

                neighbor_segment = self.segments.get(neighbor_id)
                if not neighbor_segment:
                    continue

                # Calculate cost
                segment_cost = self.calculate_segment_cost(neighbor_segment, filters)
                tentative_g = g_scores[current_id] + segment_cost

                if neighbor_id not in g_scores or tentative_g < g_scores[neighbor_id]:
                    parent_map[neighbor_id] = current_id
                    g_scores[neighbor_id] = tentative_g
                    
                    neighbor_coord = neighbor_segment.get_end_point()
                    h_score = self.heuristic(neighbor_coord, end_coord)
                    f_scores[neighbor_id] = tentative_g + h_score

                    neighbor_node = Node(
                        f_score=f_scores[neighbor_id],
                        segment_id=neighbor_id,
                        g_score=tentative_g,
                        h_score=h_score
                    )
                    heapq.heappush(open_set, neighbor_node)

        return None  # No path found

    def build_graph(self) -> Dict[str, List[str]]:
        """Build adjacency graph from segments"""
        graph = {}
        
        for seg_id, segment in self.segments.items():
            graph[seg_id] = []
            end_point = segment.get_end_point()
            
            # Find segments that start near this segment's end point
            for other_id, other_segment in self.segments.items():
                if seg_id == other_id:
                    continue
                    
                start_point = other_segment.get_start_point()
                
                # Check if endpoints are very close (within 0.001 degrees ≈ 100 meters)
                # More lenient tolerance for real-world road network
                if abs(end_point[0] - start_point[0]) < 0.001 and \
                   abs(end_point[1] - start_point[1]) < 0.001:
                    graph[seg_id].append(other_id)
        
        return graph
