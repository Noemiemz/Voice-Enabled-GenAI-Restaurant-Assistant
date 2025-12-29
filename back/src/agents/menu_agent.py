from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
import os
from typing import Optional, List, Dict
from dataclasses import dataclass
from langgraph.checkpoint.memory import MemorySaver

from tools.mongodb_tools import MongoDBTools
from langchain.agents.structured_output import ToolStrategy
from utils.utils import Context, get_prompt_content, LLMLoggingCallback, TimingCallbackHandler


@dataclass
class MenuAgentResponse:
    """Response schema for the menu agent."""
    message: str  # A message to the user
    categories: Optional[List[str]] = None  # Menu/Dish categories (if requested)
    dishes: Optional[List[Dict]] = None  # Dishes (if searched or requested)
    info: Optional[Dict] = None  # Restaurant info (if requested)
    error: Optional[str] = None  # Error message (if any)


def create_menu_agent():
    """Create and return the menu agent."""
    mongo_tools = MongoDBTools()
    menu_tools = mongo_tools.get_menu_tools()
    
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"), 
        model='mistral-small-latest',
        callbacks=[LLMLoggingCallback(agent_name="menu"), TimingCallbackHandler(agent_name="menu")]
    )
    
    system_prompt = get_prompt_content("menu_system.txt")
    
    menu_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=menu_tools,
        context_schema=Context,
        response_format=ToolStrategy(MenuAgentResponse),
        checkpointer=MemorySaver(),
    )
    
    return menu_agent