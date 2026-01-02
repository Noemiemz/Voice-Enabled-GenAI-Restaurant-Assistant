from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Optional, List, Dict, Any

from data.mongodb import MongoDBManager
from pathseeker import PROMPTS_DIR

import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

def create_info_agent(db: MongoDBManager):
    """Create and return the info agent."""
    
    # --- Create tools ---
    @tool("get_all_dishes")
    def get_all_dishes() -> List[Dict[str, Any]]:
        """Get all dishes from the menu."""
        return db.get_all_dishes()
    
    @tool("get_dishes_by_category")
    def get_dishes_by_category() -> Dict[str, List[Dict[str, Any]]]:
        """Get all dishes grouped by category."""
        return db.get_dishes_by_category()

    @tool("get_offers")
    def get_offers() -> Optional[Dict[str, Any]]:
        """Get all current offers and promotions."""
        return db.get_menu()
    
    @tool("get_restaurant_info")
    def get_restaurant_info() -> Dict[str, Any]:
        """Get general restaurant information including location, hours, and contact details."""
        return db.get_restaurant_info()


    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-small-latest'
    )

    prompt_path = PROMPTS_DIR / "info_agent_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()

    info_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_all_dishes,
            get_dishes_by_category,
            get_offers,
            get_restaurant_info,
        ]
    )

    return info_agent