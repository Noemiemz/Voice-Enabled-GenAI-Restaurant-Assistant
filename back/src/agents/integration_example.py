"""
Integration Example
This shows how to integrate the orchestrator agent with the existing Flask application.
"""

from .orchestrator_agent import OrchestratorAgent
from .ui_agent import UIAgent
from .base_agent import BaseAgent
from typing import Dict, Any


class RestaurantInfoAgent(BaseAgent):
    """Agent that handles restaurant information and menu requests"""
    
    def __init__(self, menu_data=None):
        super().__init__("RestaurantInfoAgent", "Handles restaurant information and menu")
        self.menu_data = menu_data or {
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {"name": "Terrine de campagne", "price": "12€"},
                        {"name": "Salade niçoise", "price": "14€"}
                    ]
                },
                {
                    "name": "Plats principaux",
                    "items": [
                        {"name": "Boeuf bourguignon", "price": "22€"},
                        {"name": "Poulet rôti", "price": "18€"}
                    ]
                }
            ]
        }
        
    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        if context is None:
            context = {}
            
        task_lower = task.lower()
        
        if "menu" in task_lower or "dish" in task_lower:
            return self._get_menu_info()
        elif "info" in task_lower or "restaurant" in task_lower:
            return self._get_restaurant_info()
        else:
            return {"message": "I can provide information about our menu and restaurant"}
            
    def _get_menu_info(self) -> Dict[str, Any]:
        """Get menu information"""
        menu_items = []
        for category in self.menu_data["categories"]:
            for item in category["items"]:
                menu_items.append(f"{item['name']} - {item['price']}")
        
        return {
            "menu": self.menu_data,
            "menu_items": menu_items,
            "message": "Here is our menu"
        }
        
    def _get_restaurant_info(self) -> Dict[str, Any]:
        """Get restaurant information"""
        return {
            "name": "Le Bistro Gourmand",
            "hours": "12:00 - 22:00",
            "phone": "+33 1 23 45 67 89",
            "address": "123 Rue de Paris, 75001 Paris",
            "message": "Welcome to Le Bistro Gourmand!"
        }
    
    def can_handle(self, task: str) -> bool:
        keywords = ["menu", "dish", "food", "restaurant", "info", "hours", "address"]
        return any(keyword in task.lower() for keyword in keywords)


class ReservationAgent(BaseAgent):
    """Agent that handles reservations"""
    
    def __init__(self):
        super().__init__("ReservationAgent", "Handles table reservations")
        self.reservations = []
        
    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        if context is None:
            context = {}
            
        task_lower = task.lower()
        
        if "make reservation" in task_lower or "book" in task_lower:
            return self._make_reservation(context)
        elif "check reservation" in task_lower or "status" in task_lower:
            return self._check_reservation(context)
        elif "cancel" in task_lower:
            return self._cancel_reservation(context)
        else:
            return {"message": "I can help with reservations"}
            
    def _make_reservation(self, context: Dict) -> Dict[str, Any]:
        """Make a new reservation"""
        # Extract reservation details from context
        name = context.get("name", "Guest")
        guests = context.get("guests", 2)
        time = context.get("time", "19:00")
        date = context.get("date", "today")
        
        reservation = {
            "name": name,
            "guests": guests,
            "time": time,
            "date": date,
            "status": "confirmed"
        }
        
        self.reservations.append(reservation)
        
        return {
            "reservation": reservation,
            "message": f"Reservation confirmed for {guests} people at {time}"
        }
    
    def _check_reservation(self, context: Dict) -> Dict[str, Any]:
        """Check existing reservation"""
        name = context.get("name", "")
        
        if not name:
            return {"message": "Please provide a name to check the reservation"}
            
        # Find reservation by name
        user_reservations = [r for r in self.reservations if r["name"].lower() == name.lower()]
        
        if user_reservations:
            return {
                "reservations": user_reservations,
                "message": f"Found {len(user_reservations)} reservation(s) for {name}"
            }
        else:
            return {"message": f"No reservations found for {name}"}
    
    def _cancel_reservation(self, context: Dict) -> Dict[str, Any]:
        """Cancel a reservation"""
        name = context.get("name", "")
        
        if not name:
            return {"message": "Please provide a name to cancel the reservation"}
            
        # Find and remove reservation
        initial_count = len(self.reservations)
        self.reservations = [r for r in self.reservations if r["name"].lower() != name.lower()]
        
        if len(self.reservations) < initial_count:
            return {"message": f"Reservation for {name} has been cancelled"}
        else:
            return {"message": f"No reservation found for {name} to cancel"}
    
    def can_handle(self, task: str) -> bool:
        keywords = ["reservation", "book", "table", "cancel", "reserve"]
        return any(keyword in task.lower() for keyword in keywords)


def create_agent_system(menu_data=None):
    """
    Create and configure the complete agent system
    
    Args:
        menu_data (dict): Optional menu data to use
        
    Returns:
        tuple: (orchestrator, ui_agent)
    """
    # Create orchestrator
    orchestrator = OrchestratorAgent()
    
    # Create specialized agents
    restaurant_agent = RestaurantInfoAgent(menu_data)
    reservation_agent = ReservationAgent()
    
    # Register agents with orchestrator
    orchestrator.register_agent(restaurant_agent)
    orchestrator.register_agent(reservation_agent)
    
    # Create UI agent and connect to orchestrator
    ui_agent = UIAgent()
    ui_agent.connect_to_orchestrator(orchestrator)
    
    # Also register UI agent with orchestrator for bidirectional communication
    orchestrator.register_agent(ui_agent)
    
    return orchestrator, ui_agent


def example_usage():
    """Example usage of the agent system"""
    
    print("=== Agent System Integration Example ===\n")
    
    # Create the agent system
    orchestrator, ui_agent = create_agent_system()
    
    # Example menu data (could come from your existing app)
    example_menu = {
        "categories": [
            {
                "name": "Specials",
                "items": [
                    {"name": "Chef's Special", "price": "28€", "description": "Today's special dish"}
                ]
            }
        ]
    }
    
    # Test scenarios
    test_scenarios = [
        {
            "user_input": "What's on the menu today?",
            "context": {"user_id": "customer1", "interface": "voice"}
        },
        {
            "user_input": "I want to make a reservation for 4 people at 7 PM",
            "context": {"user_id": "customer1", "name": "John Doe", "guests": 4, "time": "19:00"}
        },
        {
            "user_input": "What are your opening hours?",
            "context": {"user_id": "customer2"}
        },
        {
            "user_input": "Display the menu in a nice format",
            "context": {"user_id": "customer1", "format": "fancy"}
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Scenario {i}:")
        print(f"  User: {scenario['user_input']}")
        
        # Process through UI agent
        result = ui_agent.execute(scenario['user_input'], scenario['context'])
        
        print(f"  System: {result.get('message', result)}")
        print(f"  Type: {result.get('type', 'unknown')}")
        print()
    
    # Show system status
    print("System Status:")
    status = orchestrator.get_agent_status()
    print(f"  Registered agents: {len(status['orchestrator']['registered_agents'])}")
    print(f"  Tasks processed: {status['orchestrator']['total_tasks_processed']}")
    print()
    
    print("=== Example Complete ===")


if __name__ == "__main__":
    example_usage()