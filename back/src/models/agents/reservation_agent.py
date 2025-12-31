from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Optional, List, Dict, Any

from models.mongodb import MongoDBManager
from pathseeker import PROMPTS_DIR

import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

def create_reservation_agent():
    """Create and return the reservation agent."""
    db = MongoDBManager()
    
    # --- Create tools ---
    @tool("get_reservations")
    def get_reservations(filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get reservations with optional filters.
        
        Args:
            filters: Optional dictionary of filters to apply
        """
        return db.get_reservations(filters)
    
    @tool("get_reservation_by_id")
    def get_reservation_by_id(reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific reservation by ID.
        
        Args:
            reservation_id: The unique identifier of the reservation
        """
        return db.get_reservation(reservation_id)

    @tool("get_tables")
    def get_tables() -> List[Dict[str, Any]]:
        """Get all available tables in the restaurant."""
        return db.get_tables()

    @tool("create_reservation")
    def create_reservation(reservation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new reservation.
        
        Args:
            reservation_data: Dictionary containing reservation details
        """
        return db.create_reservation(reservation_data)
    
    @tool("update_reservation")
    def update_reservation(reservation_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing reservation.
        
        Args:
            reservation_id: The unique identifier of the reservation
            update_data: Dictionary containing fields to update
        """
        return db.update_reservation(reservation_id, update_data)

    @tool("cancel_reservation")
    def cancel_reservation(reservation_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a reservation.
        
        Args:
            reservation_id: The unique identifier of the reservation to cancel
        """
        return db.cancel_reservation(reservation_id)

    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-small-latest'
    )

    prompt_path = PROMPTS_DIR / "reservation_agent_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()

    reservation_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_reservations,
            get_reservation_by_id,
            get_tables,
            create_reservation,
            update_reservation,
            cancel_reservation
        ]
    )

    return reservation_agent