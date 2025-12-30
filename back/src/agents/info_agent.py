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

def create_info_agent():
    """Create and return the info agent."""
    db = MongoDBManager()
    
    # --- Create tools ---
    @tool
    def get_all_dishes() -> List[Dict[str, Any]]:
        """Get all dishes"""
        return db.get_all_dishes()
    
    @tool
    def get_dish_by_id(dish_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific dish by ID"""
        return db.get_dish(dish_id)
    
    @tool
    def get_dishes_by_category() -> Dict[str, List[Dict[str, Any]]]:
        """Get all dishes grouped by category"""
        return db.get_dishes_by_category()

    @tool
    def get_offers() -> Optional[Dict[str, Any]]:
        """Get all current offers"""
        return db.get_menu()
    
    @tool
    def get_restaurant_info() -> Dict[str, Any]:
        """Get restaurant information"""
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
            get_dish_by_id,
            get_dishes_by_category,
            get_offers,
            get_restaurant_info,
        ]
    )

    return info_agent