from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI

from models.agents import create_info_agent, create_order_agent, create_reservation_agent
from data.mongodb import MongoDBManager
from pathseeker import PROMPTS_DIR
from settings import AVAILABLE_VOICES

import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

# Global state to track which agent is currently handling the conversation
class ConversationState:
    def __init__(self):
        self.active_agent = None  # None, 'info', 'order', or 'reservation'
        self.conversation_history = {
            'info': [],
            'order': [],
            'reservation': []
        }
    
    def clear_history(self):
        self.conversation_history = {
            'info': [],
            'order': [],
            'reservation': []
        }
        self.active_agent = None

def create_supervisor_agent(db: MongoDBManager, conversation_state: ConversationState) -> ChatMistralAI:
    """Create and return the supervisor agent."""

    info_agent = create_info_agent(db)
    order_agent = create_order_agent(db)
    reservation_agent = create_reservation_agent(db)
    
    # --- Create tools ---
    @tool("info_event")
    def info_event(request: str) -> str:
        """
        Provide information about the restaurant, dishes, menu and offers.

        Use this when the user needs general information about the restaurant or information about dishes, menu, and offers.
        
        Args:
            request: Natural language request from the user (e.g., 'Where is the restaurant located?', 'Which dishes are vegan?')
        """
        conversation_state.active_agent = 'info'
        conversation_state.conversation_history['info'].append({"role": "user", "content": request})
        
        response = info_agent.invoke({
            "messages": conversation_state.conversation_history['info']
        })
        
        assistant_message = response["messages"][-1].text
        conversation_state.conversation_history['info'].append({"role": "assistant", "content": assistant_message})
        
        return f"Response of the info_agent:\n{assistant_message}"

    @tool("order_event")
    def order_event(request: str) -> str:
        """
        Handle food ordering requests.

        Use this when the user wants to place an order, modify an order, or inquire about their order status.
        
        Args:
            request: Natural language request from the user (e.g., 'I want to order a pizza', 'Can I change my order?')
        """
        conversation_state.active_agent = 'order'
        conversation_state.conversation_history['order'].append({"role": "user", "content": request})
        
        response = order_agent.invoke({
            "messages": conversation_state.conversation_history['order']
        })
        
        assistant_message = response["messages"][-1].text
        conversation_state.conversation_history['order'].append({"role": "assistant", "content": assistant_message})
        
        return f"Response of the order_agent:\n{assistant_message}"
    
    @tool("reservation_event")
    def reservation_event(request: str) -> str:
        """
        Manage reservation-related requests.

        Use this when the user wants to make, modify, or cancel a reservation, or inquire about reservation details.
        
        Args:
            request: Natural language request from the user (e.g., 'I want to book a table for two today', 'Can I change my reservation time?')
        """
        conversation_state.active_agent = 'reservation'
        conversation_state.conversation_history['reservation'].append({"role": "user", "content": request})
        
        response = reservation_agent.invoke({
            "messages": conversation_state.conversation_history['reservation']
        })
        
        assistant_message = response["messages"][-1].text
        conversation_state.conversation_history['reservation'].append({"role": "assistant", "content": assistant_message})
        
        return f"Response of the reservation_agent:\n{assistant_message}"

    # --- Create agent ---
    model = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model='mistral-medium-latest',
        max_retries=2
    )

    prompt_path = PROMPTS_DIR / "supervisor_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        f.close()

    system_prompt += "\nYou only support the languages corresponding to the following voices codes: " + ", ".join(AVAILABLE_VOICES)
    system_prompt += "\nIf you receive a request in a language you do not support, respond in English and start your response with: 'NOTE: Unsupported language requested. Responding in English.'"

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