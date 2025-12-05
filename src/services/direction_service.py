"""
Direction Service
Generates human-readable turn-by-turn directions from navigation paths
"""

import math
from typing import List, Dict, Any, Optional


class DirectionService:
    """Service for generating turn-by-turn directions"""
    
    @staticmethod
    def calculate_bearing(pos1: Dict, pos2: Dict) -> float:
        """
        Calculate bearing (direction) between two positions in degrees
        0° = North, 90° = East, 180° = South, 270° = West
        """
        lat1, lng1 = pos1.get('lat', 0), pos1.get('lng', 0)
        lat2, lng2 = pos2.get('lat', 0), pos2.get('lng', 0)
        
        delta_lng = lng2 - lng1
        delta_lat = lat2 - lat1
        
        bearing = math.atan2(delta_lng, delta_lat)
        bearing_degrees = math.degrees(bearing)
        
        # Normalize to 0-360
        if bearing_degrees < 0:
            bearing_degrees += 360
        
        return bearing_degrees
    
    @staticmethod
    def get_turn_direction(bearing1: float, bearing2: float) -> str:
        """
        Determine turn direction based on change in bearing
        
        Returns: "left", "right", "straight", "sharp left", "sharp right", "u-turn"
        """
        # Calculate angle difference
        angle_diff = bearing2 - bearing1
        
        # Normalize to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        # Classify turn
        abs_diff = abs(angle_diff)
        
        if abs_diff < 20:
            return "straight"
        elif abs_diff < 45:
            return "slight right" if angle_diff > 0 else "slight left"
        elif abs_diff < 120:
            return "right" if angle_diff > 0 else "left"
        elif abs_diff < 160:
            return "sharp right" if angle_diff > 0 else "sharp left"
        else:
            return "u-turn"
    
    @staticmethod
    def get_cardinal_direction(bearing: float) -> str:
        """Convert bearing to cardinal direction"""
        directions = [
            "north", "northeast", "east", "southeast",
            "south", "southwest", "west", "northwest"
        ]
        
        index = round(bearing / 45) % 8
        return directions[index]
    
    @staticmethod
    def format_node_description(node: Dict) -> str:
        """Get human-readable description of a node"""
        represents = node.get('represents', [])
        
        if not represents:
            return "waypoint"
        
        # Use first representation
        rep = represents[0]
        node_type = rep.get('type', 'waypoint')
        node_id = rep.get('id', '')
        
        type_labels = {
            'room': f"room {node_id}",
            'bathroom': f"bathroom",
            'elevator': f"elevator",
            'stairs': f"stairs",
            'building_connection': f"building connector",
            'outside_exit': f"exit",
            'intersection': f"hallway intersection",
            'turn': f"hallway turn",
            'eatery': f"cafeteria"
        }
        
        return type_labels.get(node_type, node_type)
    
    def generate_step_description(self, prev_node: Optional[Dict], current_node: Dict, 
                                   next_node: Optional[Dict], index: int) -> str:
        """Generate description for a single step in the path"""
        
        # First step
        if prev_node is None:
            desc = self.format_node_description(current_node)
            return f"Start at {desc}"
        
        # Last step
        if next_node is None:
            desc = self.format_node_description(current_node)
            return f"Arrive at {desc}"
        
        # Middle steps - calculate turn direction
        if 'lat' in prev_node and 'lat' in current_node and 'lat' in next_node:
            bearing_in = self.calculate_bearing(prev_node, current_node)
            bearing_out = self.calculate_bearing(current_node, next_node)
            turn = self.get_turn_direction(bearing_in, bearing_out)
            
            # Get location description
            location = self.format_node_description(current_node)
            
            if turn == "straight":
                return f"Continue straight past {location}"
            elif "slight" in turn:
                return f"Bear {turn.replace('slight ', '')} at {location}"
            elif turn == "u-turn":
                return f"Make a U-turn at {location}"
            else:
                return f"Turn {turn} at {location}"
        
        # Fallback if no position data
        desc = self.format_node_description(current_node)
        return f"Continue to {desc}"
    
    def generate_directions(self, path_data: Dict) -> Dict[str, Any]:
        """
        Generate complete turn-by-turn directions from path data
        
        Args:
            path_data: Path information from NavigationService
        
        Returns:
            Dict with formatted directions and metadata
        """
        path_type = path_data.get('type')
        
        if path_type == 'single-building':
            return self._generate_single_building_directions(path_data)
        elif path_type == 'multi-building':
            return self._generate_multi_building_directions(path_data)
        elif path_type == 'multi-floor':
            return self._generate_multi_floor_directions(path_data)
        else:
            return {
                'error': 'Unknown path type',
                'steps': []
            }
    
    def _generate_single_building_directions(self, path_data: Dict) -> Dict[str, Any]:
        """Generate directions for single-building path"""
        building = path_data.get('building')
        floor = path_data.get('floor')
        nodes = path_data.get('nodes', [])
        
        if not nodes:
            return {'error': 'No path nodes', 'steps': []}
        
        steps = []
        for i, node in enumerate(nodes):
            prev_node = nodes[i - 1] if i > 0 else None
            next_node = nodes[i + 1] if i < len(nodes) - 1 else None
            
            step_desc = self.generate_step_description(prev_node, node, next_node, i)
            steps.append({
                'step': i + 1,
                'instruction': step_desc,
                'node': node,
                'building': building,
                'floor': floor
            })
        
        return {
            'type': 'single-building',
            'building': building,
            'floor': floor,
            'total_steps': len(steps),
            'steps': steps,
            'summary': f"Navigate within Building {building}, Floor {floor}"
        }
    
    def _generate_multi_building_directions(self, path_data: Dict) -> Dict[str, Any]:
        """Generate directions for multi-building path"""
        segments = path_data.get('segments', [])
        connection = path_data.get('connection', {})
        
        all_steps = []
        step_counter = 1
        
        for seg_idx, segment in enumerate(segments):
            building = segment.get('building')
            floor = segment.get('floor')
            nodes = segment.get('nodes', [])
            description = segment.get('description', '')
            
            # Add segment header
            if seg_idx > 0:
                from_building = connection.get('fromBuilding')
                to_building = connection.get('toBuilding')
                all_steps.append({
                    'step': step_counter,
                    'instruction': f"Cross from Building {from_building} to Building {to_building}",
                    'type': 'transition',
                    'building': to_building,
                    'floor': floor
                })
                step_counter += 1
            
            # Generate steps for this segment
            for i, node in enumerate(nodes):
                prev_node = nodes[i - 1] if i > 0 else None
                next_node = nodes[i + 1] if i < len(nodes) - 1 else None
                
                step_desc = self.generate_step_description(prev_node, node, next_node, i)
                all_steps.append({
                    'step': step_counter,
                    'instruction': step_desc,
                    'node': node,
                    'building': building,
                    'floor': floor,
                    'segment': seg_idx
                })
                step_counter += 1
        
        return {
            'type': 'multi-building',
            'total_steps': len(all_steps),
            'steps': all_steps,
            'segments_count': len(segments),
            'summary': f"Navigate from Building {segments[0]['building']} to Building {segments[-1]['building']}"
        }
    
    def _generate_multi_floor_directions(self, path_data: Dict) -> Dict[str, Any]:
        """Generate directions for multi-floor path"""
        building = path_data.get('building')
        segments = path_data.get('segments', [])
        transition = path_data.get('transition', {})
        
        all_steps = []
        step_counter = 1
        
        for seg_idx, segment in enumerate(segments):
            floor = segment.get('floor')
            nodes = segment.get('nodes', [])
            description = segment.get('description', '')
            
            # Add floor transition instruction
            if seg_idx > 0:
                transition_type = transition.get('type', 'stairs')
                all_steps.append({
                    'step': step_counter,
                    'instruction': f"Take the {transition_type} to Floor {floor}",
                    'type': 'floor-transition',
                    'building': building,
                    'floor': floor,
                    'transition_type': transition_type
                })
                step_counter += 1
            
            # Generate steps for this segment
            for i, node in enumerate(nodes):
                prev_node = nodes[i - 1] if i > 0 else None
                next_node = nodes[i + 1] if i < len(nodes) - 1 else None
                
                step_desc = self.generate_step_description(prev_node, node, next_node, i)
                all_steps.append({
                    'step': step_counter,
                    'instruction': step_desc,
                    'node': node,
                    'building': building,
                    'floor': floor,
                    'segment': seg_idx
                })
                step_counter += 1
        
        return {
            'type': 'multi-floor',
            'building': building,
            'total_steps': len(all_steps),
            'steps': all_steps,
            'floors': [seg['floor'] for seg in segments],
            'summary': f"Navigate from Floor {segments[0]['floor']} to Floor {segments[-1]['floor']} in Building {building}"
        }
    
    def generate_text_summary(self, directions: Dict) -> str:
        """Generate plain text summary of directions"""
        steps = directions.get('steps', [])
        summary = directions.get('summary', '')
        
        if not steps:
            return "No directions available"
        
        text = f"{summary}\n\n"
        for step in steps:
            text += f"{step['step']}. {step['instruction']}\n"
        
        return text.strip()


# Singleton instance
_direction_service = None

def get_direction_service() -> DirectionService:
    """Get or create the direction service singleton"""
    global _direction_service
    if _direction_service is None:
        _direction_service = DirectionService()
    return _direction_service
