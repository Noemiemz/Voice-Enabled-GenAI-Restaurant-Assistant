"""
LangChain-compatible Database Tool for the restaurant assistant system.
This tool integrates with LangChain's tool system for seamless agent operations.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from datetime import datetime
import json


class DBQuery(BaseModel):
    """Structure for database queries in LangChain format."""
    collection: str = Field(..., description="Collection to query")
    query: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    projection: Optional[Dict[str, int]] = Field(None, description="Field projection")
    limit: Optional[int] = Field(None, description="Result limit")
    skip: Optional[int] = Field(None, description="Results to skip")
    sort: Optional[List[tuple]] = Field(None, description="Sort criteria")


class DBResult(BaseModel):
    """Structure for database query results in LangChain format."""
    success: bool = Field(..., description="Whether the query was successful")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    count: int = Field(0, description="Number of results")
    message: str = Field("", description="Status message")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Query timestamp")


class RestaurantDBTool(BaseTool):
    """LangChain tool for restaurant database operations."""
    
    name: str = "restaurant_database"
    description: str = """
    Tool for querying the restaurant database. Use this tool to:
    - Get menu information (Dish collection)
    - Check table availability (Reservation and Table collections)
    - Look up order status (Order collection)
    - Retrieve menu details and pricing
    
    Input should be a JSON object with:
    - collection: Name of collection to query
    - query: MongoDB-style query object
    - projection: Optional field projection
    - limit: Optional result limit
    - skip: Optional results to skip
    - sort: Optional sort criteria
    """
    
    # Declare mock_data as a Pydantic field
    mock_data: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    
    def __init__(self, mock_data: Optional[Dict[str, List[Dict[str, Any]]]] = None, **kwargs):
        """
        Initialize the restaurant database tool.
        
        Args:
            mock_data: Optional mock data for testing
        """
        # Initialize with mock_data or load defaults
        if mock_data is None:
            print("Loading default mock data for RestaurantDBTool")
            mock_data = {
                "Dish": RestaurantDBTool._load_mock_dishes(),
                "Menu": RestaurantDBTool._load_mock_menus(),
                "Reservation": RestaurantDBTool._load_mock_reservations(),
                "Order": RestaurantDBTool._load_mock_orders(),
                "Table": RestaurantDBTool._load_mock_tables()
            }
        
        # Pass to parent constructor
        super().__init__(mock_data=mock_data, **kwargs)
    
    def _run(self, tool_input: Union[str, Dict[str, Any]]) -> str:
        """
        Execute the database tool.
        
        Args:
            tool_input: Either a string (JSON) or dictionary with query parameters
            
        Returns:
            JSON string with query results
        """
        try:
            # Parse input
            if isinstance(tool_input, str):
                query_params = json.loads(tool_input)
            else:
                query_params = tool_input
            
            # Validate and execute query
            db_query = DBQuery(**query_params)
            result = self.query(db_query)
            
            # Return as JSON string for LangChain compatibility
            return result.model_dump_json()
            
        except Exception as e:
            error_result = DBResult(
                success=False,
                message="Database tool execution failed",
                error=str(e)
            )
            return error_result.model_dump_json()
    
    def _arun(self, tool_input: Union[str, Dict[str, Any]]) -> str:
        """Async version of tool execution (not implemented)."""
        raise NotImplementedError("Async execution not supported for this tool")
    
    def query(self, db_query: DBQuery) -> DBResult:
        """
        Execute a query on the database.
        
        Args:
            db_query: DBQuery object with query parameters
            
        Returns:
            DBResult object
        """
        try:
            # Validate collection
            if db_query.collection not in self.mock_data:
                return DBResult(
                    success=False,
                    message=f"Collection {db_query.collection} not found",
                    error="collection_not_found"
                )
            
            # Get collection data
            collection_data = self.mock_data[db_query.collection]
            
            # Apply query filters
            filtered_data = self._apply_filters(collection_data, db_query.query)
            
            # Apply sorting
            if db_query.sort:
                filtered_data = self._apply_sorting(filtered_data, db_query.sort)
            
            # Apply skip and limit
            if db_query.skip:
                filtered_data = filtered_data[db_query.skip:]
            if db_query.limit:
                filtered_data = filtered_data[:db_query.limit]
            
            # Apply projection
            if db_query.projection:
                filtered_data = self._apply_projection(filtered_data, db_query.projection)
            
            return DBResult(
                success=True,
                data=filtered_data,
                count=len(filtered_data),
                message=f"Successfully queried {len(filtered_data)} records from {db_query.collection}"
            )
            
        except Exception as e:
            return DBResult(
                success=False,
                message="Database query failed",
                error=str(e)
            )
    
    def _apply_filters(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to data."""
        if not filters:
            return data
        
        filtered = []
        for item in data:
            match = True
            for key, value in filters.items():
                # Handle nested filters (like "ingredients.is_allergen")
                if '.' in key:
                    keys = key.split('.')
                    current = item
                    try:
                        for k in keys:
                            current = current[k]
                        if current != value:
                            match = False
                            break
                    except (KeyError, TypeError):
                        match = False
                        break
                else:
                    if item.get(key) != value:
                        match = False
                        break
            
            if match:
                filtered.append(item)
        
        return filtered
    
    def _apply_sorting(self, data: List[Dict[str, Any]], sort: List[tuple]) -> List[Dict[str, Any]]:
        """Apply sorting to data."""
        if not sort:
            return data
        
        # Simple sorting implementation
        for sort_field, sort_direction in reversed(sort):
            reverse = sort_direction < 0  # -1 for descending, 1 for ascending
            data.sort(key=lambda x: x.get(sort_field, ""), reverse=reverse)
        
        return data
    
    def _apply_projection(self, data: List[Dict[str, Any]], projection: Dict[str, int]) -> List[Dict[str, Any]]:
        """Apply field projection to data."""
        if not projection:
            return data
        
        projected = []
        for item in data:
            projected_item = {}
            for key, value in projection.items():
                if value == 1 and key in item:  # Include field
                    projected_item[key] = item[key]
            projected.append(projected_item)
        
        return projected
    
    # Mock data loading methods (same as original but adapted for LangChain)
    @staticmethod
    def _load_mock_dishes() -> List[Dict[str, Any]]:
        """Load mock dish data."""
        return [
            {
                "name": "Margherita Pizza",
                "category": "main",
                "price": 12.99,
                "is_vegetarian": True,
                "ingredients": [
                    {"name": "tomato sauce", "is_allergen": False, "allergen_type": None},
                    {"name": "mozzarella", "is_allergen": True, "allergen_type": "dairy"},
                    {"name": "basil", "is_allergen": False, "allergen_type": None},
                    {"name": "olive oil", "is_allergen": False, "allergen_type": None}
                ],
                "preparation_time": 15,
                "calories": 800,
                "is_gluten_free": False
            },
            {
                "name": "Grilled Salmon",
                "category": "main",
                "price": 18.99,
                "is_vegetarian": False,
                "ingredients": [
                    {"name": "salmon", "is_allergen": True, "allergen_type": "fish"},
                    {"name": "lemon", "is_allergen": False, "allergen_type": None},
                    {"name": "herbs", "is_allergen": False, "allergen_type": None},
                    {"name": "olive oil", "is_allergen": False, "allergen_type": None},
                    {"name": "garlic", "is_allergen": False, "allergen_type": None}
                ],
                "preparation_time": 20,
                "calories": 450,
                "is_gluten_free": True
            },
            {
                "name": "Chocolate Lava Cake",
                "category": "dessert",
                "price": 7.99,
                "is_vegetarian": True,
                "ingredients": [
                    {"name": "chocolate", "is_allergen": False, "allergen_type": None},
                    {"name": "flour", "is_allergen": True, "allergen_type": "gluten"},
                    {"name": "eggs", "is_allergen": True, "allergen_type": "eggs"},
                    {"name": "butter", "is_allergen": True, "allergen_type": "dairy"},
                    {"name": "sugar", "is_allergen": False, "allergen_type": None}
                ],
                "preparation_time": 10,
                "calories": 600,
                "is_gluten_free": False
            },
            {
                "name": "Caesar Salad",
                "category": "starter",
                "price": 8.99,
                "is_vegetarian": False,
                "ingredients": [
                    {"name": "romaine lettuce", "is_allergen": False, "allergen_type": None},
                    {"name": "caesar dressing", "is_allergen": True, "allergen_type": "eggs"},
                    {"name": "parmesan cheese", "is_allergen": True, "allergen_type": "dairy"},
                    {"name": "croutons", "is_allergen": True, "allergen_type": "gluten"},
                    {"name": "chicken", "is_allergen": False, "allergen_type": None}
                ],
                "preparation_time": 8,
                "calories": 350,
                "is_gluten_free": False
            },
            {
                "name": "Vegetarian Pasta",
                "category": "main",
                "price": 14.99,
                "is_vegetarian": True,
                "ingredients": [
                    {"name": "pasta", "is_allergen": True, "allergen_type": "gluten"},
                    {"name": "tomato sauce", "is_allergen": False, "allergen_type": None},
                    {"name": "mushrooms", "is_allergen": False, "allergen_type": None},
                    {"name": "bell peppers", "is_allergen": False, "allergen_type": None},
                    {"name": "olive oil", "is_allergen": False, "allergen_type": None}
                ],
                "preparation_time": 12,
                "calories": 550,
                "is_gluten_free": False
            }
        ]
    
    @staticmethod
    def _load_mock_menus() -> List[Dict[str, Any]]:
        """Load mock menu data."""
        return [
            {
                "name": "Lunch Menu",
                "description": "Available from 11:30 AM to 3:00 PM",
                "dishes": ["Margherita Pizza", "Caesar Salad", "Vegetarian Pasta"],
                "start_time": "11:30",
                "end_time": "15:00",
                "is_active": True
            },
            {
                "name": "Dinner Menu",
                "description": "Available from 5:00 PM to 10:00 PM",
                "dishes": ["Grilled Salmon", "Margherita Pizza", "Vegetarian Pasta", "Chocolate Lava Cake"],
                "start_time": "17:00",
                "end_time": "22:00",
                "is_active": True
            },
            {
                "name": "Vegetarian Menu",
                "description": "Vegetarian options available all day",
                "dishes": ["Margherita Pizza", "Vegetarian Pasta", "Chocolate Lava Cake"],
                "start_time": "11:30",
                "end_time": "22:00",
                "is_active": True
            }
        ]
    
    @staticmethod
    def _load_mock_reservations() -> List[Dict[str, Any]]:
        """Load mock reservation data."""
        return [
            {
                "reservation_id": "RES-2023-001",
                "customer_name": "John Doe",
                "date": "2023-12-25",
                "time": "19:00",
                "party_size": 4,
                "table_id": "T01",
                "status": "confirmed",
                "special_requests": "Window seat please"
            },
            {
                "reservation_id": "RES-2023-002",
                "customer_name": "Jane Smith",
                "date": "2023-12-24",
                "time": "18:30",
                "party_size": 2,
                "table_id": "T03",
                "status": "confirmed",
                "special_requests": "Quiet table"
            },
            {
                "reservation_id": "RES-2023-003",
                "customer_name": "Bob Johnson",
                "date": "2023-12-26",
                "time": "20:00",
                "party_size": 6,
                "table_id": "T05",
                "status": "pending",
                "special_requests": "High chair for baby"
            }
        ]
    
    @staticmethod
    def _load_mock_orders() -> List[Dict[str, Any]]:
        """Load mock order data."""
        return [
            {
                "order_id": "ORD-2023-001",
                "customer_name": "John Doe",
                "date": "2023-12-20",
                "time": "19:15",
                "items": [
                    {"name": "Margherita Pizza", "quantity": 1, "price": 12.99},
                    {"name": "Caesar Salad", "quantity": 2, "price": 8.99}
                ],
                "total": 30.97,
                "status": "delivered",
                "payment_method": "credit_card",
                "table_number": "T01"
            },
            {
                "order_id": "ORD-2023-002",
                "customer_name": "Jane Smith",
                "date": "2023-12-21",
                "time": "18:45",
                "items": [
                    {"name": "Grilled Salmon", "quantity": 1, "price": 18.99},
                    {"name": "Vegetarian Pasta", "quantity": 1, "price": 14.99},
                    {"name": "Chocolate Lava Cake", "quantity": 2, "price": 7.99}
                ],
                "total": 49.96,
                "status": "preparing",
                "payment_method": "credit_card",
                "table_number": "T03"
            },
            {
                "order_id": "ORD-2023-003",
                "customer_name": "Bob Johnson",
                "date": "2023-12-22",
                "time": "20:30",
                "items": [
                    {"name": "Margherita Pizza", "quantity": 2, "price": 12.99},
                    {"name": "Caesar Salad", "quantity": 1, "price": 8.99},
                    {"name": "Chocolate Lava Cake", "quantity": 1, "price": 7.99}
                ],
                "total": 42.96,
                "status": "preparing",
                "payment_method": "cash",
                "table_number": "T05"
            }
        ]
    
    @staticmethod
    def _load_mock_tables() -> List[Dict[str, Any]]:
        """Load mock table data."""
        return [
            {
                "table_id": "T01",
                "capacity": 4,
                "location": "by the window",
                "is_available": False,
                "current_reservation": "RES-2023-001"
            },
            {
                "table_id": "T02",
                "capacity": 2,
                "location": "near the bar",
                "is_available": True,
                "current_reservation": None
            },
            {
                "table_id": "T03",
                "capacity": 4,
                "location": "center",
                "is_available": False,
                "current_reservation": "RES-2023-002"
            },
            {
                "table_id": "T04",
                "capacity": 2,
                "location": "near the kitchen",
                "is_available": True,
                "current_reservation": None
            },
            {
                "table_id": "T05",
                "capacity": 6,
                "location": "private area",
                "is_available": False,
                "current_reservation": "RES-2023-003"
            }
        ]
    
    def get_collection_names(self) -> List[str]:
        """Get list of available collection names."""
        return list(self.mock_data.keys())
    
    def get_tool_description(self) -> str:
        """Get detailed description of the tool for LangChain."""
        return f"""
        Restaurant Database Tool - Version 1.0
        
        Collections available:
        - Dish: Menu items with ingredients, pricing, and dietary information
        - Menu: Complete menus with available times
        - Reservation: Table reservations with customer details
        - Order: Customer orders with status and items
        - Table: Table information with availability
        
        Example queries:
        - Menu: {{ "collection": "Dish", "query": {{ "is_vegetarian": true }} }}
        - Reservations: {{ "collection": "Reservation", "query": {{ "date": "2023-12-25" }} }}
        - Orders: {{ "collection": "Order", "query": {{ "status": "preparing" }} }}
        """
    
    def create_example_queries(self) -> Dict[str, Dict[str, Any]]:
        """Create example queries for different use cases."""
        return {
            "vegetarian_menu": {
                "collection": "Dish",
                "query": {"is_vegetarian": True},
                "projection": {"name": 1, "price": 1, "ingredients": 1}
            },
            "available_tables": {
                "collection": "Table",
                "query": {"is_available": True},
                "projection": {"table_id": 1, "capacity": 1, "location": 1}
            },
            "pending_orders": {
                "collection": "Order",
                "query": {"status": "preparing"},
                "sort": [("time", 1)]  # Sort by time ascending
            }
        }