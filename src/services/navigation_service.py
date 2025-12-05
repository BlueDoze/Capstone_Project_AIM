"""
Navigation Service
Provides pathfinding and routing capabilities for campus navigation
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from heapq import heappush, heappop


class NavigationService:
    """Service for calculating navigation paths across campus"""
    
    def __init__(self):
        """Initialize navigation service with data files"""
        self.project_root = Path(__file__).parent.parent.parent
        self.navigation_data = None
        self.building_positions = None
        self.building_connections = None
        self._load_navigation_data()
    
    def _load_navigation_data(self):
        """Load navigation data from JSON files"""
        try:
            # Load all_node_data.json
            nav_data_path = self.project_root / 'LeafletJS' / 'all_node_data.json'
            with open(nav_data_path, 'r', encoding='utf-8') as f:
                self.navigation_data = json.load(f)
            
            # Load Building positions.JSON
            positions_path = self.project_root / 'LeafletJS' / 'Building positions.JSON'
            with open(positions_path, 'r', encoding='utf-8') as f:
                self.building_positions = json.load(f)
            
            # Load building_connections.JSON
            connections_path = self.project_root / 'LeafletJS' / 'building_connections.JSON'
            with open(connections_path, 'r', encoding='utf-8') as f:
                self.building_connections = json.load(f)
            
            print("✅ Navigation data loaded successfully")
            
        except Exception as e:
            print(f"⚠️ Error loading navigation data: {e}")
            self.navigation_data = {}
            self.building_positions = {}
            self.building_connections = {}
    
    def get_building_data(self, building: str, floor: str) -> Optional[Dict]:
        """Get navigation data for a specific building and floor"""
        if not self.navigation_data:
            return None
        
        building_key = f"Building {building}"
        if building_key not in self.navigation_data:
            print(f"⚠️ Building key '{building_key}' not found in navigation data")
            print(f"   Available buildings: {list(self.navigation_data.keys())}")
            return None
        
        building_data = self.navigation_data[building_key]
        floors_data = building_data.get('floors', {})
        
        if str(floor) not in floors_data:
            print(f"⚠️ Floor '{floor}' not found in building {building}")
            print(f"   Available floors: {list(floors_data.keys())}")
            return None
        
        floor_data = floors_data[str(floor)]
        print(f"✅ Successfully retrieved floor data for Building {building}, Floor {floor}")
        return floor_data
    
    def calculate_distance(self, pos1: Dict, pos2: Dict) -> float:
        """Calculate Euclidean distance between two positions"""
        lat1, lng1 = pos1.get('lat', 0), pos1.get('lng', 0)
        lat2, lng2 = pos2.get('lat', 0), pos2.get('lng', 0)
        
        return math.sqrt((lat2 - lat1)**2 + (lng2 - lng1)**2)
    
    def dijkstra(self, graph: Dict, start_node: str, end_node: str) -> Optional[List[str]]:
        """
        Dijkstra's shortest path algorithm
        
        Args:
            graph: Navigation graph with nodes and connections
            start_node: Starting node ID
            end_node: Destination node ID
        
        Returns:
            List of node IDs representing the path, or None if no path found
        """
        if start_node not in graph or end_node not in graph:
            return None
        
        # Priority queue: (distance, current_node, path)
        pq = [(0, start_node, [start_node])]
        visited = set()
        distances = {start_node: 0}
        
        while pq:
            current_dist, current_node, path = heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Found destination
            if current_node == end_node:
                return path
            
            # Get connections for current node
            node_data = graph[current_node]
            connections = node_data.get('connections', [])
            
            for neighbor in connections:
                if neighbor not in graph or neighbor in visited:
                    continue
                
                # Calculate edge weight (distance between nodes)
                if 'lat' in graph[current_node] and 'lat' in graph[neighbor]:
                    edge_weight = self.calculate_distance(
                        graph[current_node],
                        graph[neighbor]
                    )
                else:
                    edge_weight = 1  # Default weight if no position data
                
                new_dist = current_dist + edge_weight
                
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heappush(pq, (new_dist, neighbor, path + [neighbor]))
        
        return None  # No path found
    
    def find_path_single_building(self, building: str, floor: str, 
                                   start_node: str, end_node: str) -> Optional[Dict]:
        """
        Find path within a single building floor
        
        Returns:
            Dict with path information or None if no path found
        """
        floor_data = self.get_building_data(building, floor)
        if not floor_data:
            return None
        
        graph = floor_data.get('navigationGraph', {})
        path = self.dijkstra(graph, start_node, end_node)
        
        if not path:
            return None
        
        return {
            'type': 'single-building',
            'building': building,
            'floor': floor,
            'path': path,
            'nodes': [graph[node_id] for node_id in path if node_id in graph]
        }
    
    def find_building_connection(self, from_building: str, to_building: str) -> Optional[Dict]:
        """Find connection information between two buildings"""
        if not self.building_connections:
            return None
        
        connection_key = f"{from_building}-{to_building} Connector"
        reverse_key = f"{to_building}-{from_building} Connector"
        
        if connection_key in self.building_connections:
            return self.building_connections[connection_key]
        elif reverse_key in self.building_connections:
            # Reverse the connection
            conn = self.building_connections[reverse_key]
            return {
                'exit': conn.get('entry'),
                'entry': conn.get('exit')
            }
        
        return None
    
    def find_path_multi_building(self, start_building: str, start_floor: str, start_node: str,
                                  end_building: str, end_floor: str, end_node: str) -> Optional[Dict]:
        """
        Find path across multiple buildings
        
        Returns:
            Dict with multi-segment path information
        """
        # Find connection between buildings
        connection = self.find_building_connection(start_building, end_building)
        if not connection:
            return None
        
        exit_node = connection.get('exit')
        entry_node = connection.get('entry')
        
        if not exit_node or not entry_node:
            return None
        
        # Segment 1: From start to building exit
        start_floor_data = self.get_building_data(start_building, start_floor)
        if not start_floor_data:
            return None
        
        start_graph = start_floor_data.get('navigationGraph', {})
        segment1_path = self.dijkstra(start_graph, start_node, exit_node)
        
        if not segment1_path:
            return None
        
        # Segment 2: From building entry to destination
        end_floor_data = self.get_building_data(end_building, end_floor)
        if not end_floor_data:
            return None
        
        end_graph = end_floor_data.get('navigationGraph', {})
        segment2_path = self.dijkstra(end_graph, entry_node, end_node)
        
        if not segment2_path:
            return None
        
        return {
            'type': 'multi-building',
            'segments': [
                {
                    'building': start_building,
                    'floor': start_floor,
                    'path': segment1_path,
                    'nodes': [start_graph[n] for n in segment1_path if n in start_graph],
                    'description': f'Navigate to Building {end_building} connector'
                },
                {
                    'building': end_building,
                    'floor': end_floor,
                    'path': segment2_path,
                    'nodes': [end_graph[n] for n in segment2_path if n in end_graph],
                    'description': f'Navigate to destination in Building {end_building}'
                }
            ],
            'connection': {
                'exitNode': exit_node,
                'entryNode': entry_node,
                'fromBuilding': start_building,
                'toBuilding': end_building
            }
        }
    
    def find_path_multi_floor(self, building: str, start_floor: str, start_node: str,
                               end_floor: str, end_node: str) -> Optional[Dict]:
        """
        Find path across multiple floors in the same building
        Uses stairs or elevators
        
        Returns:
            Dict with multi-segment path information
        """
        # Get floor data
        start_floor_data = self.get_building_data(building, start_floor)
        end_floor_data = self.get_building_data(building, end_floor)
        
        if not start_floor_data or not end_floor_data:
            return None
        
        start_graph = start_floor_data.get('navigationGraph', {})
        end_graph = end_floor_data.get('navigationGraph', {})
        
        # Find stairs or elevator nodes on start floor
        transition_nodes = []
        for node_id, node_data in start_graph.items():
            represents = node_data.get('represents', [])
            for rep in represents:
                if rep.get('type') in ['stairs', 'elevator']:
                    goes_to = rep.get('goesTo', [])
                    # Check if this transition goes to our target floor
                    floor_key = f"{building}{end_floor}"
                    if any(floor_key in str(dest) for dest in goes_to):
                        transition_nodes.append({
                            'node': node_id,
                            'type': rep.get('type'),
                            'id': rep.get('id'),
                            'goesTo': goes_to
                        })
        
        if not transition_nodes:
            return None
        
        # Use first available transition (could be optimized to choose closest)
        transition = transition_nodes[0]
        transition_node_start = transition['node']
        
        # Find corresponding node on destination floor
        # Look for the same stairs/elevator ID on the destination floor
        transition_id = transition['id']
        transition_node_end = None
        
        for node_id, node_data in end_graph.items():
            represents = node_data.get('represents', [])
            for rep in represents:
                if rep.get('id') == transition_id:
                    transition_node_end = node_id
                    break
            if transition_node_end:
                break
        
        if not transition_node_end:
            return None
        
        # Segment 1: Start to transition on start floor
        segment1_path = self.dijkstra(start_graph, start_node, transition_node_start)
        if not segment1_path:
            return None
        
        # Segment 2: Transition to end on destination floor
        segment2_path = self.dijkstra(end_graph, transition_node_end, end_node)
        if not segment2_path:
            return None
        
        return {
            'type': 'multi-floor',
            'building': building,
            'segments': [
                {
                    'floor': start_floor,
                    'path': segment1_path,
                    'nodes': [start_graph[n] for n in segment1_path if n in start_graph],
                    'description': f'Navigate to {transition["type"]}'
                },
                {
                    'floor': end_floor,
                    'path': segment2_path,
                    'nodes': [end_graph[n] for n in segment2_path if n in end_graph],
                    'description': f'Navigate to destination on floor {end_floor}'
                }
            ],
            'transition': {
                'type': transition['type'],
                'id': transition_id,
                'startNode': transition_node_start,
                'endNode': transition_node_end
            }
        }
    
    def find_path(self, start_building: str, start_floor: str, start_node: str,
                  end_building: str, end_floor: str, end_node: str) -> Optional[Dict]:
        """
        Main pathfinding method - handles all scenarios
        
        Returns:
            Dict with path information including type and segments
        """
        # Same building, same floor
        if start_building == end_building and start_floor == end_floor:
            return self.find_path_single_building(start_building, start_floor, 
                                                   start_node, end_node)
        
        # Same building, different floors
        elif start_building == end_building and start_floor != end_floor:
            return self.find_path_multi_floor(start_building, start_floor, start_node,
                                               end_floor, end_node)
        
        # Different buildings
        else:
            return self.find_path_multi_building(start_building, start_floor, start_node,
                                                  end_building, end_floor, end_node)
    
    def get_node_info(self, building: str, floor: str, node_id: str) -> Optional[Dict]:
        """Get detailed information about a specific node"""
        floor_data = self.get_building_data(building, floor)
        if not floor_data:
            return None
        
        graph = floor_data.get('navigationGraph', {})
        return graph.get(node_id)
    
    def resolve_room_to_node(self, building: str, floor: str, room_id: str) -> Optional[str]:
        """Resolve room ID to its corresponding navigation node"""
        floor_data = self.get_building_data(building, floor)
        if not floor_data:
            return None
        
        room_to_node = floor_data.get('roomToNode', {})
        return room_to_node.get(room_id)
    
    def get_all_rooms(self, building: str, floor: str) -> Dict[str, str]:
        """Get all rooms and their corresponding nodes for a floor"""
        floor_data = self.get_building_data(building, floor)
        if not floor_data:
            return {}
        
        return floor_data.get('roomToNode', {})
    
    def get_available_buildings(self) -> List[str]:
        """Get list of all buildings with navigation data"""
        if not self.navigation_data:
            return []
        
        buildings = []
        for key in self.navigation_data.keys():
            if key.startswith('Building '):
                building_letter = key.replace('Building ', '')
                buildings.append(building_letter)
        
        return sorted(buildings)
    
    def get_available_floors(self, building: str) -> List[str]:
        """Get list of all floors for a building"""
        building_key = f"Building {building}"
        if building_key not in self.navigation_data:
            print(f"⚠️ Building '{building_key}' not found in navigation data")
            return []
        
        building_data = self.navigation_data[building_key]
        floors_data = building_data.get('floors', {})
        
        if not floors_data:
            print(f"⚠️ No floors data found for building {building}")
            return []
        
        # Get all floor keys (they are strings like "1", "2", "3")
        floors = sorted(list(floors_data.keys()), key=lambda x: int(x) if x.isdigit() else 0)
        print(f"✅ Found {len(floors)} floors for Building {building}: {floors}")
        
        return floors


# Singleton instance
_navigation_service = None

def get_navigation_service() -> NavigationService:
    """Get or create the navigation service singleton"""
    global _navigation_service
    if _navigation_service is None:
        _navigation_service = NavigationService()
    return _navigation_service
