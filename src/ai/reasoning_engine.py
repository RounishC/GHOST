"""
AI Reasoning Engine for route explanations
Provides intelligent reasoning for recommended routes based on user preferences
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class RouteAnalysis:
    """Analysis of a recommended route"""
    path_segments: List[str]
    total_distance: float
    safety_score: float
    cleanliness_score: float
    noise_score: float
    lighting_score: float
    construction_risk: float
    reasoning: str
    highlights: List[str]


class AIReasoningEngine:
    """AI engine for generating explanations and reasoning"""

    def __init__(self, segments_dict: Dict):
        self.segments = segments_dict

    def analyze_route(self, path: List[str], filters: Dict[str, float]) -> RouteAnalysis:
        """
        Analyze a route and generate reasoning
        """
        if not path:
            return None

        # Calculate aggregate metrics
        total_distance = 0
        avg_safety = 0
        avg_cleanliness = 0
        avg_noise = 0
        avg_lighting = 0
        max_construction = 0

        valid_segments = 0
        for seg_id in path:
            segment = self.segments.get(seg_id)
            if not segment:
                continue

            valid_segments += 1
            total_distance += segment.length_meters
            avg_safety += segment.crime_score
            avg_cleanliness += segment.dust_level
            avg_noise += segment.noise_level
            avg_lighting += segment.lighting
            max_construction = max(max_construction, segment.construction)

        if valid_segments > 0:
            avg_safety /= valid_segments
            avg_cleanliness /= valid_segments
            avg_noise /= valid_segments
            avg_lighting /= valid_segments

        # Generate reasoning
        reasoning = self._generate_reasoning(
            path, filters, total_distance,
            avg_safety, avg_cleanliness, avg_noise,
            avg_lighting, max_construction
        )

        highlights = self._extract_highlights(path, filters)

        return RouteAnalysis(
            path_segments=path,
            total_distance=total_distance,
            safety_score=10 - avg_safety,  # Invert so higher is better
            cleanliness_score=10 - avg_cleanliness,
            noise_score=10 - avg_noise,
            lighting_score=avg_lighting,
            construction_risk=max_construction,
            reasoning=reasoning,
            highlights=highlights
        )

    def _generate_reasoning(self, path: List[str], filters: Dict[str, float],
                           distance: float, safety: float, cleanliness: float,
                           noise: float, lighting: float, construction: float) -> str:
        """Generate AI reasoning for the route"""
        
        reasons = []

        # Distance reasoning
        if distance < 1000:
            reasons.append(f"**Efficient Route**: The recommended path covers only {distance:.0f} meters, minimizing travel distance.")
        else:
            reasons.append(f"**Optimal Coverage**: This route spans {distance:.0f} meters, balancing distance with safety and comfort.")

        # Safety reasoning
        if 'safety' in filters and filters['safety'] >= 7:
            if safety <= 3:
                reasons.append(f"**High Safety Priority**: We've prioritized low-crime segments (avg crime score: {safety:.1f}/10). This route avoids high-risk areas.")
            elif safety <= 5:
                reasons.append(f"**Good Safety Consideration**: We've selected segments with moderate crime levels (avg: {safety:.1f}/10).")

        # Cleanliness reasoning
        if 'cleanliness' in filters and filters['cleanliness'] >= 6:
            if cleanliness <= 3:
                reasons.append(f"**Clean Environment**: We've chosen cleaner roads (avg dust level: {cleanliness:.1f}/10) for better air quality.")
            elif cleanliness <= 5:
                reasons.append(f"**Decent Cleanliness**: Average dust level is {cleanliness:.1f}/10, suitable for most users.")

        # Noise reasoning
        if 'noise' in filters and filters['noise'] >= 6:
            if noise <= 3:
                reasons.append(f"**Quiet Route**: We've minimized noise exposure (avg level: {noise:.1f}/10), ideal for peaceful travel.")
            elif noise <= 5:
                reasons.append(f"**Moderate Noise**: Average noise level is {noise:.1f}/10, acceptable for urban navigation.")

        # Lighting reasoning
        if 'lighting' in filters and filters['lighting'] >= 7:
            if lighting >= 7:
                reasons.append(f"**Well-Lit Path**: {lighting:.1f}/10 average lighting ensures good visibility throughout the journey.")
            elif lighting >= 5:
                reasons.append(f"**Decent Lighting**: Average lighting is {lighting:.1f}/10, providing reasonable visibility.")

        # Construction warning
        if construction > 5:
            reasons.append(f"⚠️ **Construction Alert**: This route has some construction activities (risk level: {construction:.1f}/10). Plan accordingly.")

        if not reasons:
            reasons.append("This route balances multiple factors to provide an optimal path based on your preferences.")

        return " ".join(reasons)

    def _extract_highlights(self, path: List[str], filters: Dict[str, float]) -> List[str]:
        """Extract key highlights about the route"""
        highlights = []

        # Find best and worst segments
        safety_scores = []
        for seg_id in path:
            segment = self.segments.get(seg_id)
            if segment:
                safety_scores.append((segment.segment_id, segment.crime_score, segment.road_name))

        if safety_scores:
            # Safest segment
            safest = min(safety_scores, key=lambda x: x[1])
            highlights.append(f"✓ Safest segment: {safest[2]} (Crime: {safest[1]}/10)")

            # Most dangerous segment
            most_crime = max(safety_scores, key=lambda x: x[1])
            if most_crime[1] > 5:
                highlights.append(f"⚠️ Higher crime area: {most_crime[2]} (Crime: {most_crime[1]}/10)")

        # Road types summary
        highway_types = {}
        for seg_id in path:
            segment = self.segments.get(seg_id)
            if segment:
                htype = segment.highway_type
                highway_types[htype] = highway_types.get(htype, 0) + 1

        if highway_types:
            main_type = max(highway_types.items(), key=lambda x: x[1])[0]
            highlights.append(f"Primary route type: {main_type.capitalize()}")

        return highlights

    def compare_routes(self, routes: List[Dict], filters: Dict[str, float]) -> str:
        """
        Compare multiple routes and generate reasoning
        """
        if not routes:
            return "No routes available for comparison."

        comparison = "**Route Comparison Analysis**:\n\n"

        for i, route in enumerate(routes, 1):
            analysis = route.get('analysis')
            if analysis:
                comparison += f"**Route {i}**:\n"
                comparison += f"- Distance: {analysis.total_distance:.0f}m\n"
                comparison += f"- Safety Score: {analysis.safety_score:.1f}/10\n"
                comparison += f"- Cleanliness: {analysis.cleanliness_score:.1f}/10\n"
                comparison += f"- Noise Level: {analysis.noise_score:.1f}/10\n\n"

        return comparison

    def validate_filters(self, filters: Dict[str, float]) -> Tuple[bool, str]:
        """Validate user filters"""
        valid_keys = {'safety', 'cleanliness', 'noise', 'lighting', 'construction'}
        
        for key in filters.keys():
            if key not in valid_keys:
                return False, f"Invalid filter: {key}. Valid filters: {valid_keys}"
            
            if not 0 <= filters[key] <= 10:
                return False, f"Filter {key} must be between 0-10"

        return True, "Filters valid"
