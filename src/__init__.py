"""
GHOST - Geospatial Heuristic Optimal Segment Tracker
Smart multi-factor route planning with A* algorithm and AI reasoning
"""

__version__ = "1.0.0"
__author__ = "GHOST Team"
__description__ = "Intelligent multi-factor route planning system"

from .api.route_planner import GHOSTRoutePlanner
from .pathfinding.astar import AStarPathfinder
from .ai.reasoning_engine import AIReasoningEngine

__all__ = [
    'GHOSTRoutePlanner',
    'AStarPathfinder',
    'AIReasoningEngine'
]
