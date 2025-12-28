from models.mongodb import MongoDBManager
from langchain_core.tools import tool
from typing import Optional, Dict, List

class MongoDBTools:
    def __init__(self):
        """Initialize MongoDB tools with the existing MongoDB manager"""
        self.db_manager = MongoDBManager()

    def get_menu_tools(self):
        """Return a list of tools for the agent to use"""

        @tool
        def get_menu() -> Dict:
            """Get the complete restaurant menu"""
            return self.db_manager.get_menu()

        @tool
        def get_menu_categories() -> List[str]:
            """Get list of menu categories"""
            menu = self.get_menu()
            if menu and "categories" in menu:
                return [category["name"] for category in menu["categories"]]
            return []

        @tool
        def search_dishes(query: str) -> List[Dict]:
            """Search dishes by name or description"""
            all_dishes = self.db_manager.get_all_dishes()
            if not all_dishes:
                return []
            query_lower = query.lower()
            return [
                dish for dish in all_dishes
                if (query_lower in dish.get("name", "").lower() or
                    query_lower in dish.get("description", "").lower())
            ]

        @tool
        def get_dishes_by_category(category_name: str) -> List[Dict]:
            """Get all dishes in a specific category"""
            return self.db_manager.get_dishes_by_category().get(category_name, [])


        @tool
        def get_available_dishes() -> List[Dict]:
            """Get all available dishes"""
            all_dishes = self.db_manager.get_all_dishes()
            return [dish for dish in all_dishes if dish.get("available", True)]

        return [
            # get_menu,
            # get_menu_categories,
            search_dishes,
            get_dishes_by_category,
            get_available_dishes,
        ]

    
    def get_reservation_tools(self):
        """Return a list of reservation-related tools for the agent to use"""

        @tool
        def get_reservations(filters: Optional[Dict] = None) -> List[Dict]:
            """Get reservations with optional filters"""
            return self.db_manager.get_reservations(filters)

        @tool
        def get_reservation_by_id(reservation_id: str) -> Dict:
            """Get a specific reservation by ID"""
            return self.db_manager.get_reservation(reservation_id)

        @tool
        def create_reservation(reservation_data: Dict) -> Dict:
            """Create a new reservation"""
            return self.db_manager.create_reservation(reservation_data)

        @tool
        def get_restaurant_info() -> Dict:
            """Get basic restaurant information"""
            return self.db_manager.get_restaurant_info()
            
        return [
            get_reservations,
            get_reservation_by_id,
            create_reservation,
            get_restaurant_info,
        ]
            
            
    def close(self):
        """Close the database connection"""
        self.db_manager.close()
