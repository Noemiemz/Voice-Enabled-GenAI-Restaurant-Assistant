import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.tools import tool

# --- Mock MongoDBManager for testing ---
class MockMongoDBManager:
    def get_reservations(self, filters=None):
        # Mock reservation data
        return [
            {
                "_id": "1",
                "name": "John Doe",
                "date": "2024-01-15",
                "time": "19:00",
                "partySize": 4,
                "status": "confirmed"
            },
            {
                "_id": "2",
                "name": "Jane Smith",
                "date": "2024-01-16",
                "time": "20:00",
                "partySize": 2,
                "status": "confirmed"
            }
        ]

    def get_reservation(self, reservation_id):
        reservations = self.get_reservations()
        for res in reservations:
            if res["_id"] == reservation_id:
                return res
        return None

    def create_reservation(self, reservation_data):
        # Mock creation - just return the data with an ID
        reservation_data["_id"] = "3"
        reservation_data["status"] = "confirmed"
        return reservation_data

    def get_restaurant_info(self):
        return {
            "name": "Test Restaurant",
            "address": "123 Main St",
            "phone": "555-1234"
        }

# --- MongoDBTools (with @tool decorators) ---
class MongoDBTools:
    def __init__(self):
        self.db_manager = MockMongoDBManager()

    def get_reservation_tools(self):
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

# --- Response Schema ---
@dataclass
class ReservationAgentResponse:
    """Response schema for the reservation agent."""
    message: str  # A message to the user
    reservations: Optional[List[Dict]] = None  # Reservations (if requested)
    reservation: Optional[Dict] = None  # Specific reservation (if requested)
    restaurant_info: Optional[Dict] = None  # Restaurant info (if requested)
    error: Optional[str] = None  # Error message (if any)

# --- Context Schema ---
@dataclass
class Context:
    user_id: str

# --- System Prompt ---
SYSTEM_PROMPT_RESERVATION = """
You are a helpful restaurant assistant for managing reservations.
You can help users with the following tasks:
- Get existing reservations with optional filters
- Get specific reservation details by ID
- Create new reservations
- Get basic restaurant information

Use the provided tools to handle reservation-related queries.
"""

# --- Main Test ---
def test_reservation_agent():
    # Initialize tools
    mongo_tools = MongoDBTools()
    reservation_tools = mongo_tools.get_reservation_tools()

    # Initialize model
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest'
    )

    # Create agent
    reservation_agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT_RESERVATION,
        tools=reservation_tools,
        context_schema=Context,
        response_format=ToolStrategy(ReservationAgentResponse),
    )

    # Test queries
    queries = [
        "What reservations do we have?",
        "Can you get me details for reservation ID 1?",
        "I want to make a new reservation for 4 people on January 20th at 8 PM under the name Sarah Johnson",
        "What's the restaurant's contact information?"
    ]

    for query in queries:
        print(f"\n--- Query: {query} ---")
        config = {"configurable": {"thread_id": "1"}}
        context = Context(user_id="1")

        response = reservation_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
            context=context,
        )

        print("Response:")
        print(response['structured_response'])

# Run the test
if __name__ == "__main__":
    test_reservation_agent()