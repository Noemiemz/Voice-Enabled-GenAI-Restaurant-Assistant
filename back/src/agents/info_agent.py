from smolagents.agents import TextAgent
from tools.info_tools import (
    get_menu,
    get_all_dishes,
    get_restaurant_info
)

SYSTEM_PROMPT = """
You are an information assistant for a restaurant.

Your responsibilities:
- Answer questions about the menu, dishes, and restaurant information.
- ALWAYS use tools to retrieve factual data.
- NEVER invent dishes, prices, or opening hours.
- If the information is not available, say you do not know.
- You do NOT handle reservations or orders.
"""

def create_info_agent(llm):
    return TextAgent(
        name="InfoAgent",
        model=llm,
        tools=[
            get_menu,
            get_all_dishes,
            get_restaurant_info
        ],
    )

def run_info_agent(agent, user_message: str) -> str:
    """
    Prepend system prompt dynamically before sending user message
    """
    prompt_with_system = SYSTEM_PROMPT + "\n\nUser: " + user_message
    return agent.run(prompt_with_system)
