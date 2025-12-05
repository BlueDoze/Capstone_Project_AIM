"""
Test Navigation Services
Tests for pathfinding, API endpoints, and navigation functionality
"""

import pytest
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.navigation_service import NavigationService, get_navigation_service
from src.services.direction_service import DirectionService, get_direction_service


class TestNavigationService:
    """Test NavigationService pathfinding and data loading"""
    
    @pytest.fixture
    def nav_service(self):
        """Get navigation service instance"""
        return get_navigation_service()
    
    def test_navigation_data_loaded(self, nav_service):
        """Test that navigation data is loaded correctly"""
        assert nav_service.navigation_data is not None
        assert nav_service.building_positions is not None
        assert nav_service.building_connections is not None
    
    def test_get_available_buildings(self, nav_service):
        """Test getting list of available buildings"""
        buildings = nav_service.get_available_buildings()
        assert isinstance(buildings, list)
        assert len(buildings) > 0
        assert 'M' in buildings or 'H' in buildings
    
    def test_get_available_floors(self, nav_service):
        """Test getting floors for a building"""
        floors = nav_service.get_available_floors('M')
        assert isinstance(floors, list)
        assert len(floors) > 0
        assert '1' in floors
    
    def test_get_building_data(self, nav_service):
        """Test retrieving building floor data"""
        data = nav_service.get_building_data('M', '1')
        assert data is not None
        assert 'navigationGraph' in data
        assert 'roomToNode' in data
    
    def test_resolve_room_to_node(self, nav_service):
        """Test resolving room ID to navigation node"""
        # Test with Building M, Floor 1, Room 1003 (if it exists)
        node = nav_service.resolve_room_to_node('M', '1', '1003')
        # Node might be None if room doesn't exist, that's OK for this test
        if node:
            assert isinstance(node, str)
    
    def test_get_all_rooms(self, nav_service):
        """Test getting all rooms for a floor"""
        rooms = nav_service.get_all_rooms('M', '1')
        assert isinstance(rooms, dict)
    
    def test_calculate_distance(self, nav_service):
        """Test distance calculation between two points"""
        pos1 = {'lat': 0, 'lng': 0}
        pos2 = {'lat': 3, 'lng': 4}
        distance = nav_service.calculate_distance(pos1, pos2)
        assert abs(distance - 5.0) < 0.001  # 3-4-5 triangle
    
    def test_dijkstra_pathfinding(self, nav_service):
        """Test Dijkstra's algorithm on a simple graph"""
        # Create a simple test graph
        graph = {
            'A': {
                'connections': ['B', 'C'],
                'lat': 0,
                'lng': 0
            },
            'B': {
                'connections': ['A', 'D'],
                'lat': 1,
                'lng': 0
            },
            'C': {
                'connections': ['A', 'D'],
                'lat': 0,
                'lng': 1
            },
            'D': {
                'connections': ['B', 'C'],
                'lat': 1,
                'lng': 1
            }
        }
        
        path = nav_service.dijkstra(graph, 'A', 'D')
        assert path is not None
        assert path[0] == 'A'
        assert path[-1] == 'D'
    
    def test_find_path_single_building(self, nav_service):
        """Test pathfinding within a single building"""
        # Get navigation graph for Building M, Floor 1
        floor_data = nav_service.get_building_data('M', '1')
        if not floor_data:
            pytest.skip("Building M Floor 1 data not available")
        
        graph = floor_data.get('navigationGraph', {})
        if len(graph) < 2:
            pytest.skip("Not enough nodes to test pathfinding")
        
        # Get first two nodes
        nodes = list(graph.keys())
        start_node = nodes[0]
        end_node = nodes[1]
        
        result = nav_service.find_path_single_building('M', '1', start_node, end_node)
        
        if result:  # Path might not exist between arbitrary nodes
            assert result['type'] == 'single-building'
            assert result['building'] == 'M'
            assert result['floor'] == '1'
            assert isinstance(result['path'], list)
    
    def test_find_building_connection(self, nav_service):
        """Test finding connection between buildings"""
        # Test M-H connection if it exists
        connection = nav_service.find_building_connection('M', 'H')
        
        if connection:
            assert 'exit' in connection or 'entry' in connection


class TestDirectionService:
    """Test DirectionService for turn-by-turn directions"""
    
    @pytest.fixture
    def dir_service(self):
        """Get direction service instance"""
        return get_direction_service()
    
    def test_calculate_bearing(self, dir_service):
        """Test bearing calculation between points"""
        pos1 = {'lat': 0, 'lng': 0}
        pos2 = {'lat': 1, 'lng': 0}  # Due north
        
        bearing = dir_service.calculate_bearing(pos1, pos2)
        assert 0 <= bearing < 360
    
    def test_get_turn_direction(self, dir_service):
        """Test turn direction classification"""
        # Straight ahead
        turn = dir_service.get_turn_direction(0, 0)
        assert turn == "straight"
        
        # Right turn
        turn = dir_service.get_turn_direction(0, 90)
        assert "right" in turn.lower()
        
        # Left turn
        turn = dir_service.get_turn_direction(0, -90)
        assert "left" in turn.lower()
    
    def test_get_cardinal_direction(self, dir_service):
        """Test cardinal direction from bearing"""
        assert dir_service.get_cardinal_direction(0) == "north"
        assert dir_service.get_cardinal_direction(90) == "east"
        assert dir_service.get_cardinal_direction(180) == "south"
        assert dir_service.get_cardinal_direction(270) == "west"
    
    def test_format_node_description(self, dir_service):
        """Test node description formatting"""
        # Room node
        node = {
            'represents': [{'type': 'room', 'id': '1003'}]
        }
        desc = dir_service.format_node_description(node)
        assert 'room' in desc.lower()
        
        # Elevator node
        node = {
            'represents': [{'type': 'elevator', 'id': 'Elevator-M'}]
        }
        desc = dir_service.format_node_description(node)
        assert 'elevator' in desc.lower()
    
    def test_generate_directions_single_building(self, dir_service):
        """Test direction generation for single building path"""
        path_data = {
            'type': 'single-building',
            'building': 'M',
            'floor': '1',
            'path': ['M1_1', 'M1_2', 'M1_3'],
            'nodes': [
                {'lat': 0, 'lng': 0, 'represents': [{'type': 'room', 'id': '1003'}]},
                {'lat': 1, 'lng': 0, 'represents': [{'type': 'intersection', 'id': 'Int1'}]},
                {'lat': 1, 'lng': 1, 'represents': [{'type': 'room', 'id': '1018'}]}
            ]
        }
        
        directions = dir_service.generate_directions(path_data)
        
        assert directions['type'] == 'single-building'
        assert 'steps' in directions
        assert len(directions['steps']) > 0
        assert directions['total_steps'] == 3
    
    def test_generate_text_summary(self, dir_service):
        """Test text summary generation"""
        directions = {
            'summary': 'Test route',
            'steps': [
                {'step': 1, 'instruction': 'Start at room 1003'},
                {'step': 2, 'instruction': 'Turn left'},
                {'step': 3, 'instruction': 'Arrive at room 1018'}
            ]
        }
        
        text = dir_service.generate_text_summary(directions)
        
        assert isinstance(text, str)
        assert 'Test route' in text
        assert 'Start at room 1003' in text
        assert 'Turn left' in text
        assert 'Arrive at room 1018' in text


class TestIntegration:
    """Integration tests combining navigation and direction services"""
    
    @pytest.fixture
    def nav_service(self):
        return get_navigation_service()
    
    @pytest.fixture
    def dir_service(self):
        return get_direction_service()
    
    def test_full_navigation_workflow(self, nav_service, dir_service):
        """Test complete navigation workflow from request to directions"""
        # Get Building M data
        floor_data = nav_service.get_building_data('M', '1')
        if not floor_data:
            pytest.skip("Building M Floor 1 data not available")
        
        graph = floor_data.get('navigationGraph', {})
        nodes = list(graph.keys())
        
        if len(nodes) < 2:
            pytest.skip("Not enough nodes for integration test")
        
        # Find a path
        start_node = nodes[0]
        end_node = nodes[min(5, len(nodes) - 1)]  # Use node 5 or last available
        
        path_result = nav_service.find_path('M', '1', start_node, 'M', '1', end_node)
        
        if not path_result:
            pytest.skip("No path found between test nodes")
        
        # Generate directions
        directions = dir_service.generate_directions(path_result)
        
        assert directions is not None
        assert 'steps' in directions
        assert len(directions['steps']) > 0
        
        # Generate text summary
        text = dir_service.generate_text_summary(directions)
        assert isinstance(text, str)
        assert len(text) > 0


def test_navigation_json_files_exist():
    """Test that required JSON files exist"""
    project_root = Path(__file__).parent.parent
    
    files = [
        project_root / 'LeafletJS' / 'all_node_data.json',
        project_root / 'LeafletJS' / 'Building positions.JSON',
        project_root / 'LeafletJS' / 'building_connections.JSON'
    ]
    
    for file_path in files:
        assert file_path.exists(), f"Required file not found: {file_path}"


def test_navigation_json_valid():
    """Test that JSON files are valid and loadable"""
    project_root = Path(__file__).parent.parent
    
    # Test all_node_data.json
    with open(project_root / 'LeafletJS' / 'all_node_data.json', 'r', encoding='utf-8') as f:
        node_data = json.load(f)
        assert isinstance(node_data, dict)
        # Should have building entries
        assert any('Building' in key for key in node_data.keys())
    
    # Test Building positions.JSON
    with open(project_root / 'LeafletJS' / 'Building positions.JSON', 'r', encoding='utf-8') as f:
        positions = json.load(f)
        assert isinstance(positions, dict)
    
    # Test building_connections.JSON
    with open(project_root / 'LeafletJS' / 'building_connections.JSON', 'r', encoding='utf-8') as f:
        connections = json.load(f)
        assert isinstance(connections, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
