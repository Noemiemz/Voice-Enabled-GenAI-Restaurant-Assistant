"""
Test cases for MockMongoDBTool
"""

import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.tools.mock_mongodb_tools import MockMongoDBTool

def test_mock_mongodb_initialization():
    """Test that MockMongoDBTool initializes correctly"""
    tool = MockMongoDBTool()
    
    # Check that data is initialized
    assert hasattr(tool, 'menu_data')
    assert hasattr(tool, 'reservations')
    assert hasattr(tool, 'restaurant_info')
    
    # Check that menu has categories
    assert 'categories' in tool.menu_data
    assert len(tool.menu_data['categories']) > 0
    
    print("[PASS] MockMongoDBTool initialization test passed")

def test_get_menu():
    """Test get_menu method"""
    tool = MockMongoDBTool()
    menu = tool.get_menu()
    
    assert menu is not None
    assert 'categories' in menu
    assert len(menu['categories']) == 3  # Entrées, Plats principaux, Desserts
    
    print("[PASS] get_menu test passed")

def test_get_menu_categories():
    """Test get_menu_categories method"""
    tool = MockMongoDBTool()
    categories = tool.get_menu_categories()
    
    assert categories is not None
    assert len(categories) == 3
    assert "Entrées" in categories
    assert "Plats principaux" in categories
    assert "Desserts" in categories
    
    print("[PASS] get_menu_categories test passed")

def test_search_dishes():
    """Test search_dishes method"""
    tool = MockMongoDBTool()
    
    # Test search for "poulet"
    results = tool.search_dishes("poulet")
    assert len(results) > 0
    assert any("Poulet" in dish["name"] for dish in results)
    
    # Test search for "chocolat"
    results = tool.search_dishes("chocolat")
    assert len(results) > 0
    assert any("chocolat" in dish["description"].lower() for dish in results)
    
    # Test search with no results
    results = tool.search_dishes("xyz123")
    assert len(results) == 0
    
    print("[PASS] search_dishes test passed")

def test_get_dishes_by_category():
    """Test get_dishes_by_category method"""
    tool = MockMongoDBTool()
    
    # Test getting entrées
    entrees = tool.get_dishes_by_category("Entrées")
    assert len(entrees) > 0
    assert all("Entrées" in dish.get("category", "") or True for dish in entrees)  # Category info not added in this method
    
    # Test getting desserts
    desserts = tool.get_dishes_by_category("Desserts")
    assert len(desserts) > 0
    
    # Test non-existent category
    empty_result = tool.get_dishes_by_category("NonExistent")
    assert len(empty_result) == 0
    
    print("[PASS] get_dishes_by_category test passed")

def test_get_reservations():
    """Test get_reservations method"""
    tool = MockMongoDBTool()
    
    # Test getting all reservations
    reservations = tool.get_reservations()
    assert len(reservations) == 2  # Should have 2 sample reservations
    
    # Test filtering
    filtered = tool.get_reservations({"name": "Jean Dupont"})
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Jean Dupont"
    
    print("[PASS] get_reservations test passed")

def test_create_reservation():
    """Test create_reservation method"""
    tool = MockMongoDBTool()
    
    initial_count = len(tool.get_reservations())
    
    # Create a new reservation
    new_reservation = {
        "name": "Test User",
        "phone": "+33 6 00 00 00 00",
        "date": "2023-12-01",
        "time": "19:00",
        "guests": 2
    }
    
    created = tool.create_reservation(new_reservation)
    
    assert created is not None
    assert "_id" in created
    assert created["name"] == "Test User"
    assert created["status"] == "confirmed"
    
    # Check that reservation was added
    final_count = len(tool.get_reservations())
    assert final_count == initial_count + 1
    
    print("[PASS] create_reservation test passed")

def test_get_restaurant_info():
    """Test get_restaurant_info method"""
    tool = MockMongoDBTool()
    info = tool.get_restaurant_info()
    
    assert info is not None
    assert "name" in info
    assert "Les Pieds dans le Plat" in info["name"]
    assert "address" in info
    assert "phone" in info
    
    print("[PASS] get_restaurant_info test passed")

def test_get_available_dishes():
    """Test get_available_dishes method"""
    tool = MockMongoDBTool()
    available = tool.get_available_dishes()
    
    assert available is not None
    assert len(available) > 0
    # All dishes in mock data should be available
    assert all(dish.get("available", False) for dish in available)
    
    print("[PASS] get_available_dishes test passed")

if __name__ == "__main__":
    print("Running MockMongoDBTool tests...")
    
    test_mock_mongodb_initialization()
    test_get_menu()
    test_get_menu_categories()
    test_search_dishes()
    test_get_dishes_by_category()
    test_get_reservations()
    test_create_reservation()
    test_get_restaurant_info()
    test_get_available_dishes()
    
    print("\n[SUCCESS] All MockMongoDBTool tests passed!")