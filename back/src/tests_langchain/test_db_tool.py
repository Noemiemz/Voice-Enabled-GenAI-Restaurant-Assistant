"""
Test cases for the mock database tool.
"""

import pytest
from agents_langchain.tools.db_tool import MockDBTool, DBQuery, DBResult


def test_db_tool_initialization():
    """Test DB tool initialization."""
    db_tool = MockDBTool()
    
    assert hasattr(db_tool, 'collections')
    assert len(db_tool.collections) == 5
    assert 'Dish' in db_tool.collections
    assert 'Menu' in db_tool.collections
    assert 'Reservation' in db_tool.collections
    assert 'Order' in db_tool.collections
    assert 'Table' in db_tool.collections


def test_get_collection_names():
    """Test getting collection names."""
    db_tool = MockDBTool()
    names = db_tool.get_collection_names()
    
    assert len(names) == 5
    assert 'Dish' in names
    assert 'Menu' in names


def test_simple_query():
    """Test simple database query."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Dish")
    
    assert isinstance(result, DBResult)
    assert result.success == True
    assert len(result.data) == 5
    assert result.count == 5
    assert "Margherita Pizza" in [dish["name"] for dish in result.data]


def test_query_with_filters():
    """Test query with filters."""
    db_tool = MockDBTool()
    
    # Test vegetarian filter
    result = db_tool.query("Dish", query={"is_vegetarian": True})
    
    assert result.success == True
    assert len(result.data) == 3  # Should return 3 vegetarian dishes
    
    # Verify all returned dishes are vegetarian
    for dish in result.data:
        assert dish["is_vegetarian"] == True


def test_query_with_projection():
    """Test query with field projection."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Dish", projection={"name": 1, "price": 1})
    
    assert result.success == True
    for dish in result.data:
        assert "name" in dish
        assert "price" in dish
        assert "ingredients" not in dish  # Should be projected out


def test_query_with_limit():
    """Test query with limit."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Dish", limit=2)
    
    assert result.success == True
    assert len(result.data) == 2
    assert result.count == 2


def test_query_with_skip():
    """Test query with skip."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Dish", skip=2, limit=2)
    
    assert result.success == True
    assert len(result.data) == 2


def test_query_with_sort():
    """Test query with sorting."""
    db_tool = MockDBTool()
    
    # Sort by price ascending
    result = db_tool.query("Dish", sort=[("price", 1)])
    
    assert result.success == True
    prices = [dish["price"] for dish in result.data]
    assert prices == sorted(prices)  # Should be in ascending order
    
    # Sort by price descending
    result = db_tool.query("Dish", sort=[("price", -1)])
    
    prices = [dish["price"] for dish in result.data]
    assert prices == sorted(prices, reverse=True)  # Should be in descending order


def test_nested_filter():
    """Test query with nested filters."""
    db_tool = MockDBTool()
    
    # Filter for dishes without allergens
    result = db_tool.query("Dish", query={"ingredients.is_allergen": False})
    
    assert result.success == True
    # This should return dishes where all ingredients have is_allergen=False
    # In our mock data, this should return some dishes


def test_invalid_collection():
    """Test query with invalid collection name."""
    db_tool = MockDBTool()
    
    result = db_tool.query("InvalidCollection")
    
    assert result.success == False
    assert "not found" in result.message
    assert result.error == "collection_not_found"


def test_menu_query():
    """Test querying menu collection."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Menu")
    
    assert result.success == True
    assert len(result.data) == 3
    assert any(menu["name"] == "Lunch Menu" for menu in result.data)


def test_reservation_query():
    """Test querying reservation collection."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Reservation")
    
    assert result.success == True
    assert len(result.data) == 3
    assert any(res["status"] == "confirmed" for res in result.data)


def test_order_query():
    """Test querying order collection."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Order")
    
    assert result.success == True
    assert len(result.data) == 3
    assert any(order["status"] == "delivered" for order in result.data)


def test_table_query():
    """Test querying table collection."""
    db_tool = MockDBTool()
    
    result = db_tool.query("Table")
    
    assert result.success == True
    assert len(result.data) == 5
    assert any(table["is_available"] for table in result.data)


def test_get_collection_schema():
    """Test getting collection schema."""
    db_tool = MockDBTool()
    
    # Test valid collection
    schema = db_tool.get_collection_schema("Dish")
    assert schema is not None
    assert "name" in schema
    assert "price" in schema
    
    # Test invalid collection
    schema = db_tool.get_collection_schema("Invalid")
    assert schema is None


def test_query_object_execution():
    """Test executing query using DBQuery object."""
    db_tool = MockDBTool()
    
    db_query = DBQuery(
        collection="Dish",
        query={"category": "main"},
        projection={"name": 1, "price": 1},
        limit=2
    )
    
    result = db_tool.execute_query_object(db_query)
    
    assert result.success == True
    assert len(result.data) == 2
    for dish in result.data:
        assert dish["category"] == "main"
        assert "name" in dish
        assert "price" in dish
        assert "ingredients" not in dish


def test_complex_query():
    """Test complex query with multiple parameters."""
    db_tool = MockDBTool()
    
    result = db_tool.query(
        collection="Dish",
        query={"is_vegetarian": True, "category": "main"},
        projection={"name": 1, "price": 1, "preparation_time": 1},
        sort=[("price", 1)],
        limit=2
    )
    
    assert result.success == True
    assert len(result.data) == 2
    
    # Check that results meet all criteria
    for dish in result.data:
        assert dish["is_vegetarian"] == True
        assert dish["category"] == "main"
        assert "name" in dish
        assert "price" in dish
        assert "preparation_time" in dish
        assert "ingredients" not in dish
    
    # Check sorting
    prices = [dish["price"] for dish in result.data]
    assert prices == sorted(prices)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])