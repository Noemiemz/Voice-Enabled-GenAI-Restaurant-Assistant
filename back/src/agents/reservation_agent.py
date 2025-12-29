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
class ReservationAgentResponse:
    """Response schema for the reservation agent."""
    message: str  # A message to the user
    reservations: Optional[List[Dict]] = None  # Reservations (if requested)
    reservation: Optional[Dict] = None  # Specific reservation (if requested)
    restaurant_info: Optional[Dict] = None  # Restaurant info (if requested)
    error: Optional[str] = None  # Error message (if any)


def create_reservation_agent():
    """Create and return the reservation agent."""
    mongo_tools = MongoDBTools()
    reservation_tools = mongo_tools.get_reservation_tools()
    
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"), 
        model='mistral-small-latest',
        callbacks=[LLMLoggingCallback(agent_name="reservation"), TimingCallbackHandler(agent_name="reservation")]
    )
    
    system_prompt = get_prompt_content("reservation_system.txt")
    
    reservation_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=reservation_tools,
        context_schema=Context,
        response_format=ToolStrategy(ReservationAgentResponse),
        checkpointer=MemorySaver(),
    )
    
    return reservation_agent