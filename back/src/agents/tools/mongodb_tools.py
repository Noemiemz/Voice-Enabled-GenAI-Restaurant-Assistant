"""
MongoDB Tools for the agent system
This provides an interface between the agent and the real MongoDB database
"""

from models.mongodb import MongoDBManager

class MongoDBTools:
    def __init__(self):
        """Initialize MongoDB tools with the existing MongoDB manager"""
        self.db_manager = MongoDBManager()

    def get_menu(self):
        """Get the complete restaurant menu"""
        return self.db_manager.get_menu()

    def get_menu_categories(self):
        """Get list of menu categories"""
        menu = self.get_menu()
        if menu and "categories" in menu:
            return [category["name"] for category in menu["categories"]]
        return []

    def search_dishes(self, query):
        """Search dishes by name or description"""
        # Get all dishes from the database
        all_dishes = self.db_manager.get_all_dishes()
        
        if not all_dishes:
            return []
        
        # Search through dishes
        results = []
        query_lower = query.lower()
        
        for dish in all_dishes:
            if (query_lower in dish.get("name", "").lower() or 
                query_lower in dish.get("description", "").lower()):
                results.append(dish)
        
        return results

    def get_dishes_by_category(self, category_name):
        """Get all dishes in a specific category"""
        return self.db_manager.get_dishes_by_category().get(category_name, [])

    def get_reservations(self, filters=None):
        """Get reservations with optional filters"""
        return self.db_manager.get_reservations(filters)

    def get_reservation_by_id(self, reservation_id):
        """Get a specific reservation by ID"""
        return self.db_manager.get_reservation(reservation_id)

    def create_reservation(self, reservation_data):
        """Create a new reservation"""
        return self.db_manager.create_reservation(reservation_data)

    def get_restaurant_info(self):
        """Get basic restaurant information"""
        return self.db_manager.get_restaurant_info()

    def get_available_dishes(self):
        """Get all available dishes"""
        all_dishes = self.db_manager.get_all_dishes()
        return [dish for dish in all_dishes if dish.get("available", True)]

    def close(self):
        """Close the database connection"""
        self.db_manager.close()