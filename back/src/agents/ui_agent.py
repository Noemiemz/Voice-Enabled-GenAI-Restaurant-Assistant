from typing import Any, Dict, Optional

from .orchestrator_agent import OrchestratorAgent
from .tools.mongodb_tools import MongoDBTools

class UIAgent:
    def __init__(
        self,
        orchestrator: Optional[OrchestratorAgent] = None,
        database: Optional[MongoDBTools] = None,
    ):
        """
        Initialize the UI agent.

        Args:
            orchestrator: Optional OrchestratorAgent instance. If None, will create one.
            database: Optional MongoDBTools instance. If None, will create one.
        """
        self.orchestrator = orchestrator or OrchestratorAgent()
        self.database = database or MongoDBTools()

    def process_user_input(self, user_input: str) -> str:
        """
        Main processing method for user input.

        Args:
            user_input: The user's input text

        Returns:
            The agent's response
        """
        print(f"[UI AGENT] Processing user input: {user_input}")

        try:
            intent, tool_name, tool_params = self.orchestrator.determine_intent_and_tool(user_input)
            print(f"[UI AGENT] Detected intent: {intent}, tool: {tool_name}")

            tool_result = None
            if tool_name:
                tool_result = self._use_database_tool(tool_name, tool_params)
                print(f"[UI AGENT] Tool result: {tool_result}")

            response = self.orchestrator.generate_response(user_input, intent, tool_name, tool_result)
            self.orchestrator.update_conversation_history(user_input, response)

            return response

        except Exception as e:
            print(f"[ERROR] UI Agent processing failed: {e}")
            return "Désolé, une erreur est survenue. Veuillez réessayer."

    def _use_database_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Use a specific database tool with given parameters.

        Args:
            tool_name: Name of the tool to use
            params: Parameters for the tool

        Returns:
            Result from the tool
        """
        tool_map = {
            "get_menu": self.database.get_menu,
            "search_dishes": lambda: self.database.search_dishes(params.get("query", "")),
            "get_reservations": self.database.get_reservations,
            "get_restaurant_info": self.database.get_restaurant_info,
            "get_dishes_by_category": lambda: self.database.get_dishes_by_category(params.get("category_name", "")),
            "get_available_dishes": self.database.get_available_dishes
        }

        if tool_name in tool_map:
            return tool_map[tool_name]()
        return None

    def close(self):
        """Clean up resources."""
        self.database.close()

    def reset_conversation(self):
        """Reset the conversation history."""
        self.orchestrator.reset_conversation()
