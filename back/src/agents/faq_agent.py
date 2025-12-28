from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from langchain_core.tools import tool
import os

from utils import Context, get_prompt_content


def create_faq_agent():
    """Create and return the FAQ agent."""
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest'
    )
    
    system_prompt = get_prompt_content("faq_system.txt")
    
    faq_agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        context_schema=Context,
    )
    
    return faq_agent
