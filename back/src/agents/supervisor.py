from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Optional, List, Dict, Any

from agents import create_info_agent, create_order_agent, create_reservation_agent
from pathseeker import PROMPTS_DIR

import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

def create_supervisor_agent():
    """Create and return the supervisor agent."""

    info_agent = create_info_agent()
    order_agent = create_order_agent()
    reservation_agent = create_reservation_agent()
    
    # --- Create tools ---
    @tool
    def info_event(request: str) -> str:
        """
        Provide information about the restaurant, dishes, menu and offers.

        Use this when the user needs general information about the restaurant or information about dishes, menu, and offers.

        Input: Natural language request from the user (e.g., 'Where is the restaurant located?', 'Which dishes are vegan?').
        """
        response = info_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return response["message"][-1].text

    @tool
    def order_event(request: str) -> str:
        """
        Handle food ordering requests.

        Use this when the user wants to place an order, modify an order, or inquire about their order status.

        Input: Natural language request from the user (e.g., 'I want to order a pizza', 'Can I change my order?').
        """
        response = order_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return response["message"][-1].text
    
    @tool
    def reservation_event(request: str) -> str:
        """
        Manage reservation-related requests.

        Use this when the user wants to make, modify, or cancel a reservation, or inquire about reservation details.

        Input: Natural language request from the user (e.g., 'I want to book a table for two today', 'Can I change my reservation time?').
        """
        response = reservation_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return response["message"][-1].text

    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-small-latest'
    )

    prompt_path = PROMPTS_DIR / "supervisor_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()

    supervisor = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            info_event,
            order_event,
            reservation_event,
        ]
    )

    return supervisor