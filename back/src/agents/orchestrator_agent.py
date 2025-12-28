from models.llm import MistralWrapper
from .prompt_manager import PromptManager
from typing import Any, Dict, Optional, Tuple
import json

class OrchestratorAgent:
    def __init__(self, llm: Optional[MistralWrapper] = None):
        """
        Initialize the orchestrator agent.

        Args:
            llm: Optional MistralWrapper instance. If None, will create one.
        """
        self.llm = llm or MistralWrapper()
        self.prompt_manager = PromptManager()
        self.conversation_history = []

    def determine_intent_and_tool(self, user_input: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        Determine user intent and select appropriate tool using LLM.

        Args:
            user_input: The user's input text

        Returns:
            tuple: (intent, tool_name, tool_params)
        """
        classification_prompt = self.prompt_manager.get_formatted_prompt(
            "intent_classification",
            user_input=user_input
        )

        try:
            llm_response = self.llm.generate_from_prompt(classification_prompt, [])
            llm_response_clean = llm_response.strip()
            if llm_response_clean.startswith("```json"):
                llm_response_clean = llm_response_clean[7:]
            if llm_response_clean.startswith("```"):
                llm_response_clean = llm_response_clean[3:]
            if llm_response_clean.endswith("```"):
                llm_response_clean = llm_response_clean[:-3]
            llm_response_clean = llm_response_clean.strip()

            result = json.loads(llm_response_clean)
            intent = result.get("intent", "general_question")
            tool_name = result.get("tool_name")
            tool_params = result.get("tool_params", {})

            return intent, tool_name, tool_params

        except Exception as e:
            print(f"[ERROR] LLM-based intent detection failed: {e}")
            return "general_question", None, {}

    def generate_response(
        self,
        user_input: str,
        intent: str,
        tool_name: Optional[str],
        tool_result: Any
    ) -> str:
        """
        Generate a response using the LLM based on intent and tool results.

        Args:
            user_input: Original user input
            intent: Detected intent
            tool_name: Tool that was used
            tool_result: Result from the tool

        Returns:
            Generated response
        """
        tool_result_str = ""
        if tool_result:
            if isinstance(tool_result, dict):
                tool_result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
            elif isinstance(tool_result, list):
                tool_result_str = json.dumps({"results": tool_result}, ensure_ascii=False, indent=2)
            else:
                tool_result_str = str(tool_result)

        prompt = self.prompt_manager.get_formatted_prompt(
            "system_prompt",
            intent=intent,
            tool_name=tool_name,
            tool_result=tool_result_str,
            user_input=user_input
        )

        response = self.llm.generate_from_prompt(prompt, self.conversation_history)
        return response

    def update_conversation_history(self, user_input: str, agent_response: str):
        """
        Update conversation history with the latest exchange.

        Args:
            user_input: User's input
            agent_response: Agent's response
        """
        if len(self.conversation_history) >= 10:
            self.conversation_history = self.conversation_history[-8:]

        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": agent_response})

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
