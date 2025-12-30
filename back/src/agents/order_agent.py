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

def create_order_agent():
    """Create and return the order agent."""
    db = MongoDBManager()
    
    # --- Create tools ---
    @tool
    def get_orders(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get orders with optional filters"""
        return db.get_orders(filters)
    
    @tool
    def create_order(order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order"""
        return db.create_order(order_data)
    
    @tool
    def update_order(order_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing order"""
        return db.update_order(order_id, update_data)
    
    @tool
    def cancel_order(order_id: str) -> Optional[Dict[str, Any]]:
        """Cancel an order"""
        return db.cancel_order(order_id)

    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-small-latest'
    )

    prompt_path = PROMPTS_DIR / "order_agent_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()

    order_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_orders,
            create_order,
            update_order,
            cancel_order
        ]
    )

    return order_agent