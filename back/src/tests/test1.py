import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.tools import tool

# --- Mock MongoDBManager for testing ---
class MockMongoDBManager:
    def get_menu(self):
        return {
            "categories": [
                {"name": "Appetizers", "dishes": ["Bruschetta", "Calamari"]},
                {"name": "Main Courses", "dishes": ["Pasta", "Pizza"]},
            ]
        }

    def search_dishes(self, query):
        menu = self.get_menu()
        results = []
        for category in menu["categories"]:
            for dish in category["dishes"]:
                if query.lower() in dish.lower():
                    results.append(dish)
        return results

# --- MongoDBTools (with @tool decorators) ---
class MongoDBTools:
    def __init__(self):
        self.db_manager = MockMongoDBManager()

    @tool
    def get_menu(self):
        """Get the complete restaurant menu"""
        return self.db_manager.get_menu()

    @tool
    def search_dishes(self, query: str):
        """Search dishes by name or description"""
        return self.db_manager.search_dishes(query)

# --- Response Schema ---
@dataclass
class MenuAgentResponse:
    message: str
    menu: Optional[Dict] = None
    dishes: Optional[List[str]] = None

# --- Context Schema ---
@dataclass
class Context:
    user_id: str

# --- System Prompt ---
SYSTEM_PROMPT_MENU = """
You are a helpful restaurant assistant.
Answer user queries about the menu and dishes.
Use the provided tools to fetch information.
"""

# --- Main Test ---
def test_menu_agent():
    # Initialize tools
    mongo_tools = MongoDBTools()
    tools = [mongo_tools.get_menu, mongo_tools.search_dishes]

    # Initialize model
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest'
    )

    # Create agent
    menu_agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT_MENU,
        tools=tools,
        context_schema=Context,
        response_format=ToolStrategy(MenuAgentResponse),
    )

    # Test queries
    queries = [
        "What is on the menu?",
        "Do you have pizza?",
        "What appetizers do you offer?",
    ]

    for query in queries:
        print(f"\n--- Query: {query} ---")
        config = {"configurable": {"thread_id": "1"}}
        context = Context(user_id="1")

        response = menu_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
            context=context,
        )

        print("Response:")
        print(response['structured_response'])

# Run the test
if __name__ == "__main__":
    test_menu_agent()
