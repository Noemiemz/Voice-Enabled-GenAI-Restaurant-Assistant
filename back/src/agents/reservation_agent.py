from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Optional, List, Dict

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
    @tool
    def get_reservations(filters: Optional[Dict] = None) -> List[Dict]:
        """Get reservations with optional filters"""
        return db.get_reservations(filters)
    
    @tool
    def get_reservation_by_id(reservation_id: str) -> Dict:
        """Get a specific reservation by ID"""
        return db.get_reservation(reservation_id)

    @tool
    def get_tables() -> List[Dict]:
        """Get all tables"""
        return db.get_tables()

    @tool
    def create_reservation(reservation_data: Dict) -> Dict:
        """Create a new reservation"""
        return db.create_reservation(reservation_data)
    
    @tool
    def update_reservation(reservation_id: str, update_data: Dict) -> Dict:
        """Update an existing reservation"""
        return db.update_reservation(reservation_id, update_data)

    @tool
    def cancel_reservation(reservation_id: str) -> Dict:
        """Cancel a reservation"""
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