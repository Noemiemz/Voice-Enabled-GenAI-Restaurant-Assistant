"""
Mock Database Tool for testing the agent system.
This tool simulates database operations without requiring an actual database connection.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
from datetime import datetime


class DBQuery(BaseModel):
    """Structure for database queries."""
    collection: str = Field(..., description="Collection to query")
    query: Dict[str, Any] = Field({}, description="Query parameters")
    projection: Optional[Dict[str, int]] = Field(None, description="Field projection")
    limit: Optional[int] = Field(None, description="Result limit")
    skip: Optional[int] = Field(None, description="Results to skip")
    sort: Optional[List[tuple]] = Field(None, description="Sort criteria")


class DBResult(BaseModel):
    """Structure for database query results."""
    success: bool = Field(..., description="Whether the query was successful")
    data: List[Dict[str, Any]] = Field([], description="Query results")
    count: int = Field(0, description="Number of results")
    message: str = Field("", description="Status message")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Query timestamp")


class MockDBTool:
    """Mock database tool for testing."""
    
    def __init__(self):
        """Initialize the mock database tool."""
        self.collections = {
            "Dish": self._load_mock_dishes(),
            "Menu": self._load_mock_menus(),
            "Reservation": self._load_mock_reservations(),
            "Order": self._load_mock_orders(),
            "Table": self._load_mock_tables()
        }
    
    def query(self, collection: str, query: Dict[str, Any] = None, 
             projection: Dict[str, int] = None, limit: int = None,
             skip: int = None, sort: List[tuple] = None) -> DBResult:
        """
        Execute a query on the mock database.
        
        Args:
            collection: Collection name
            query: Query parameters
            projection: Field projection
            limit: Result limit
            skip: Results to skip
            sort: Sort criteria
            
        Returns:
            DBResult object
        """
        try:
            # Validate collection
            if collection not in self.collections:
                return DBResult(
                    success=False,
                    message=f"Collection {collection} not found",
                    error="collection_not_found"
                )
            
            # Get collection data
            collection_data = self.collections[collection]
            
            # Apply query filters
            filtered_data = self._apply_filters(collection_data, query or {})
            
            # Apply sorting
            if sort:
                filtered_data = self._apply_sorting(filtered_data, sort)
            
            # Apply skip and limit
            if skip:
                filtered_data = filtered_data[skip:]
            if limit:
                filtered_data = filtered_data[:limit]
            
            # Apply projection
            if projection:
                filtered_data = self._apply_projection(filtered_data, projection)
            
            return DBResult(
                success=True,
                data=filtered_data,
                count=len(filtered_data),
                message=f"Successfully queried {len(filtered_data)} records from {collection}"
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
    
    def _load_mock_dishes(self) -> List[Dict[str, Any]]:
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
    
    def _load_mock_menus(self) -> List[Dict[str, Any]]:
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
    
    def _load_mock_reservations(self) -> List[Dict[str, Any]]:
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
    
    def _load_mock_orders(self) -> List[Dict[str, Any]]:
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
    
    def _load_mock_tables(self) -> List[Dict[str, Any]]:
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
        return list(self.collections.keys())
    
    def get_collection_schema(self, collection: str) -> Optional[Dict[str, Any]]:
        """Get schema for a collection."""
        if collection not in self.collections:
            return None
        
        # Return the first item as a representative schema
        if self.collections[collection]:
            return self.collections[collection][0]
        
        return {}
    
    def execute_query_object(self, db_query: DBQuery) -> DBResult:
        """Execute a query using a DBQuery object."""
        return self.query(
            collection=db_query.collection,
            query=db_query.query,
            projection=db_query.projection,
            limit=db_query.limit,
            skip=db_query.skip,
            sort=db_query.sort
        )