from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Optional, List, Dict, Any
from datetime import datetime

from data.mongodb import MongoDBManager
from data.table_schemas import TableSchema, ReservationSchema
from pathseeker import PROMPTS_DIR
from utils.logger import log_execution

import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

def create_reservation_agent(db: MongoDBManager):
    """Create and return the reservation agent."""
    
    # --- Create tools ---
    @tool("get_reservations")
    @log_execution(message="Retrieving reservations with filters", object_name="agent_reservation")
    def get_reservations(filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get reservations with optional filters.
        
        Args:
            filters: Optional dictionary of filters to apply
        """
        return db.get_reservations(filters)

    @tool("get_tables")
    @log_execution(message="Fetching available tables", object_name="agent_reservation")
    def get_tables() -> List[TableSchema]:
        """Get all available tables in the restaurant."""
        return db.get_tables()

    @tool("create_reservation")
    @log_execution(message="Creating new reservation", object_name="agent_reservation")
    def create_reservation(reservation_data: ReservationSchema) -> Optional[Dict[str, Any]]:
        """Create a new reservation.
        
        Args:
            reservation_data: Dictionary containing reservation details
        """
        return db.create_reservation(reservation_data.model_dump())
    
    @tool("update_reservation")
    @log_execution(message="Updating existing reservation", object_name="agent_reservation")
    def update_reservation(reservation_id: str, update_data: ReservationSchema) -> Optional[Dict[str, Any]]:
        """Update an existing reservation.
        
        Args:
            reservation_id: The unique identifier of the reservation
            update_data: Dictionary containing fields to update
        """
        return db.update_reservation(reservation_id, update_data.model_dump())

    @tool("cancel_reservation")
    @log_execution(message="Cancelling reservation", object_name="agent_reservation")
    def cancel_reservation(reservation_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a reservation.
        
        Args:
            reservation_id: The unique identifier of the reservation to cancel
        """
        return db.cancel_reservation(reservation_id)

    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-medium-latest',
        max_retries=2
    )

    prompt_path = PROMPTS_DIR / "reservation_agent_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()
    
    # Add current date and time to the prompt
    current_datetime = datetime.now().strftime("%A, %B %d, %Y at %H:%M")
    system_prompt = f"CURRENT DATE AND TIME: {current_datetime}\n\n{system_prompt}"

    reservation_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_reservations,
            get_tables,
            create_reservation,
            update_reservation,
            cancel_reservation
        ]
    )

    return reservation_agent