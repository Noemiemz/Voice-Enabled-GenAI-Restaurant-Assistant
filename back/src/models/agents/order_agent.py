from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Optional, List, Dict, Any

from data.mongodb import MongoDBManager
from data.table_schemas import OrderSchema
from pathseeker import PROMPTS_DIR

import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

def create_order_agent(db: MongoDBManager):
    """Create and return the order agent."""
    
    # --- Create tools ---
    @tool("get_all_dishes")
    def get_all_dishes() -> List[Dict[str, Any]]:
        """Get all dishes from the menu."""
        return db.get_all_dishes()

    @tool("get_formulas")
    def get_formulas() -> Optional[Dict[str, Any]]:
        """Get special formulas."""
        return db.get_menu()

    @tool("get_orders")
    def get_orders(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get orders with optional filters.
        
        Args:
            filters: Optional dictionary of filters to apply
        """
        return db.get_orders(filters)
    
    @tool("create_order")
    def create_order(order_data: OrderSchema) -> Optional[Dict[str, Any]]:
        """Create a new order.
        
        Args:
            order_data: Dictionary containing order details
        """
        return db.create_order(order_data.model_dump())
    
    @tool("update_order")
    def update_order(order_id: str, update_data: OrderSchema) -> Optional[Dict[str, Any]]:
        """Update an existing order.
        
        Args:
            order_id: The unique identifier of the order
            update_data: Dictionary containing fields to update
        """
        return db.update_order(order_id, update_data.model_dump())
    
    @tool("cancel_order")
    def cancel_order(order_id: str) -> Optional[Dict[str, Any]]:
        """Cancel an order.
        
        Args:
            order_id: The unique identifier of the order to cancel
        """
        return db.cancel_order(order_id)

    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-small-latest',
        max_retries=2
    )

    prompt_path = PROMPTS_DIR / "order_agent_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()

    order_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_all_dishes,
            get_formulas,
            get_orders,
            create_order,
            update_order,
            cancel_order
        ]
    )

    return order_agent