from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
import os
from typing import Optional, List, Dict
from dataclasses import dataclass

from tools.mongodb_tools import MongoDBTools
from langchain.agents.structured_output import ToolStrategy
from utils import Context


@dataclass
class MenuAgentResponse:
    """Response schema for the menu agent."""
    message: str  # A message to the user
    categories: Optional[List[str]] = None  # Menu/Dish categories (if requested)
    dishes: Optional[List[Dict]] = None  # Dishes (if searched or requested)
    info: Optional[Dict] = None  # Restaurant info (if requested)
    error: Optional[str] = None  # Error message (if any)

SYSTEM_PROMPT_MENU = """
You are a helpful restaurant assistant connected to the menu database.
You can help users with the following tasks:
- Get the restaurant menu or menu categories
- Search for dishes by name or description
- Get dishes by category

Use the provided tools to answer user queries.
"""

def create_menu_agent():
    """Create and return the menu agent."""
    mongo_tools = MongoDBTools()
    menu_tools = mongo_tools.get_menu_tools()
    
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"), 
        model='mistral-small-latest'
    )
    
    menu_agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT_MENU,
        tools=menu_tools,
        context_schema=Context,
        response_format=ToolStrategy(MenuAgentResponse),
    )
    
    return menu_agent