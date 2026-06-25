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
        Calculate cost of traversing a segment based on filters.
        Filters: {'safety': 0-10, 'cleanliness': 0-10, 'noise': 0-10, 
                  'lighting': 0-10, 'construction': 0-10,
                  'dust_level': 0-10, 'noise_level': 0-10}
        
        Lower cost is better. Weights are scaled dynamically.
        """
        cost = segment.length_meters  # Base cost is distance

        # 1. Safety Factor (crime_score: 0-10, lower crime is safer)
        safety_pref = filters.get('safety', 5)
        safety_threshold = 10 - safety_pref
        # Higher safety pref means lower tolerance for crime (lower threshold) and higher penalty weight
        dynamic_safety_weight = safety_pref * 12.0
        safety_penalty = max(0, segment.crime_score - safety_threshold) * dynamic_safety_weight
        cost += safety_penalty

        # 2. Cleanliness/Dust Factor (dust_level: 0-10, lower dust is cleaner)
        # Handle both backend 'cleanliness' and frontend 'dust_level' keys
        if 'dust_level' in filters:
            dust_threshold = filters['dust_level']
        else:
            dust_threshold = 10 - filters.get('cleanliness', 5)
        # A lower preferred dust level means higher sensitivity/weight and lower threshold
        dynamic_dust_weight = (10 - dust_threshold) * 8.0
        dust_penalty = max(0, segment.dust_level - dust_threshold) * dynamic_dust_weight
        cost += dust_penalty

        # 3. Noise Factor (noise_level: 0-10, lower noise is quieter)
        if 'noise_level' in filters:
            noise_threshold = filters['noise_level']
            dynamic_noise_weight = (10 - noise_threshold) * 8.0
        else:
            noise_pref = filters.get('noise', 5)
            noise_threshold = 10 - noise_pref
            dynamic_noise_weight = noise_pref * 8.0
        noise_penalty = max(0, segment.noise_level - noise_threshold) * dynamic_noise_weight
        cost += noise_penalty

        # 4. Lighting Factor (lighting: 0-10, higher is better lit)
        lighting_threshold = filters.get('lighting', 5)
        # Higher lighting preference means higher threshold for acceptable light
        dynamic_lighting_weight = lighting_threshold * 8.0
        lighting_penalty = max(0, lighting_threshold - segment.lighting) * dynamic_lighting_weight
        cost += lighting_penalty

        # 5. Construction Factor (construction: 0-10, lower construction is better)
        construction_threshold = filters.get('construction', 5)
        # Lower construction threshold means less tolerance, higher penalty
        dynamic_construction_weight = (10 - construction_threshold) * 10.0
        construction_penalty = max(0, segment.construction - construction_threshold) * dynamic_construction_weight
        cost += construction_penalty

        return cost

    def find_path(self, start_segment_id: str, end_segment_id: str,
                  filters: Dict[str, float],
                  start_coord: Optional[Tuple[float, float]] = None,
                  end_coord: Optional[Tuple[float, float]] = None) -> Optional[List[str]]:
        """
        Find optimal path using A* algorithm
        
        Args:
            start_segment_id: Starting segment ID
            end_segment_id: Ending segment ID
            filters: Dictionary of user preferences
            start_coord: Optional target start coordinate tuple (lon, lat)
            end_coord: Optional target end coordinate tuple (lon, lat)
            
        Returns:
            List of segment IDs forming the path, or None if no path found
        """
        if start_segment_id not in self.segments or end_segment_id not in self.segments:
            return None

        start_segment = self.segments[start_segment_id]
        end_segment = self.segments[end_segment_id]
        
        if start_coord is None:
            start_coord = start_segment.get_end_point()
        if end_coord is None:
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
        """Build adjacency graph from segments, supporting bidirectional connections"""
        graph = {}
        tolerance = 0.00025  # ≈ 25 meters connection tolerance
        
        for seg_id, segment in self.segments.items():
            graph[seg_id] = []
            
            for other_id, other_segment in self.segments.items():
                if seg_id == other_id:
                    continue
                    
                # Check if any vertex of A is close to any vertex of B
                connected = False
                for p1 in segment.geometry:
                    for p2 in other_segment.geometry:
                        if abs(p1[0] - p2[0]) < tolerance and \
                           abs(p1[1] - p2[1]) < tolerance:
                            connected = True
                            break
                    if connected:
                        break
                        
                if connected:
                    graph[seg_id].append(other_id)
        
        return graph
