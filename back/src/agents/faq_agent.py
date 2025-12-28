from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from langchain_core.tools import tool
import os

from utils import Context


@tool
def answer_faq(question: str) -> str:
    """Answer common questions about the restaurant."""
    # Common FAQ responses
    faqs = {
        "hours": "We are open from 11:00 AM to 1:00 AM every day.",
        "location": "We are located at 1 Avenue des Champs-Élysées, 75008 Paris, France.",
        "phone": "You can reach us at +33 1 23 45 67 89.",
        "parking": "We have valet parking available, and there is also public parking nearby.",
        "dress_code": "We have a smart casual dress code.",
        "payment": "We accept all major credit cards, cash, and contactless payments.",
        "wifi": "Yes, we offer free WiFi for all our guests.",
        "takeout": "Yes, we offer takeout and delivery services.",
    }
    
    # Simple keyword matching
    question_lower = question.lower()
    for key, answer in faqs.items():
        if key in question_lower or any(word in question_lower for word in key.split("_")):
            return answer
    
    # Default response
    return "I'm sorry, I don't have the information you're looking for."


SYSTEM_PROMPT_FAQ = """
You are a helpful restaurant assistant that answers general questions about our restaurant.
The restaurant is located in Paris, France, and offers a fine dining experience with French cuisine.
It is called 'Les Pieds dans le Plat' and is situated at 1 Avenue des Champs-Élysées, 75008 Paris, France.

Use this context to answer user questions about the restaurant's hours, location, menu, reservations, and policies.
"""


def create_faq_agent():
    """Create and return the FAQ agent."""
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest'
    )
    
    faq_agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT_FAQ,
        tools=[answer_faq],
        context_schema=Context,
    )
    
    return faq_agent
