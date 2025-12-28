from .tools.mongodb_tools import MongoDBTools
from .tools.mock_mongodb_tools import MockMongoDBTool
from typing import Any, Dict, List, Optional

class DatabaseAgent:
    def __init__(self, use_mock_db: bool = False):
        """
        Initialize the database agent.

        Args:
            use_mock_db: Whether to use mock database for testing
        """
        if use_mock_db:
            self.tools = MockMongoDBTool()
        else:
            self.tools = MongoDBTools()

    def get_menu(self) -> List[Dict[str, Any]]:
        """Get the restaurant menu."""
        return self.tools.get_menu()

    def search_dishes(self, query: str) -> List[Dict[str, Any]]:
        """Search dishes by query."""
        return self.tools.search_dishes(query)

    def get_reservations(self) -> List[Dict[str, Any]]:
        """Get all reservations."""
        return self.tools.get_reservations()

    def get_restaurant_info(self) -> Dict[str, Any]:
        """Get restaurant information."""
        return self.tools.get_restaurant_info()

    def get_dishes_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        """Get dishes by category."""
        return self.tools.get_dishes_by_category(category_name)

    def get_available_dishes(self) -> List[Dict[str, Any]]:
        """Get available dishes."""
        return self.tools.get_available_dishes()

    def close(self):
        """Clean up resources."""
        if hasattr(self.tools, 'close'):
            self.tools.close()
