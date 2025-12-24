from mistralai import Mistral
from smolagents import Model
import json
from smolagents.models import ChatMessage

class MistralWrapper():
    def __init__(self, api_key: str = None):
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-2506"
        import os
        # Construct absolute path to system prompt file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "..", "data", "prompts", "system_prompt.txt")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()
            f.close()

    def generate_from_prompt(self, user_prompt: str, history: list[dict[str, str]] = [], **kwargs) -> str:
        print("Generating response from Mistral LLM to prompt:", user_prompt)
        try:
            if history == []:
                history = [{"role": "system", "content": self.system_prompt}]
            history.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat.complete(
                model=self.model,
                messages=history,
            )
            text_response = response.choices[0].message.content

            history.append({"role": "assistant", "content": text_response})
            
            return text_response
            
        except Exception as e:
            print(f"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nError in LLM generation: {e}")
            # Return a fallback response and the original history
            fallback_response = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            history.append({"role": "assistant", "content": fallback_response})
            return fallback_response

    def generate_from_messages(self, messages: list[ChatMessage], **kwargs) -> str:
        print("Generating response from Mistral LLM to messages:", messages)
        msg_formatted = [msg.dict() for msg in messages]
        for msg in msg_formatted:
            msg['role'] = msg['role'].value
            
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=msg_formatted,
            )
            text_response = response.choices[0].message.content
            return text_response
            
        except Exception as e:
            print(f"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nError in LLM generation: {e}")
            # Return a fallback response
            fallback_response = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            return fallback_response


class MistralModel(Model):
    # Required attributes for smolagents tool calling
    tool_name_key = "name"
    tool_description_key = "description"
    tool_parameters_key = "parameters"
    tool_choice_key = "tool_choice"
    
    def __init__(self, api_key: str = None):
        self.llm = MistralWrapper(api_key=api_key)
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-2506"

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        txt = self.llm.generate_from_messages(messages, **kwargs)
        return ChatMessage(role="assistant", content=txt)
    
    def __call__(self, messages, tools=None, **kwargs):
        """
        Call method for tool calling support in smolagents.
        """
        # Convert ChatMessage objects to dict format if needed
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({
                    "role": msg.role.value if hasattr(msg.role, 'value') else msg.role,
                    "content": msg.content
                })
            else:
                formatted_messages.append(msg)
        
        # If tools are provided, use Mistral's tool calling API
        if tools:
            response = self.client.chat.complete(
                model=self.model,
                messages=formatted_messages,
                tools=tools,
                **kwargs
            )
        else:
            response = self.client.chat.complete(
                model=self.model,
                messages=formatted_messages,
                **kwargs
            )
        
        return ChatMessage(
            role="assistant",
            content=response.choices[0].message.content if response.choices[0].message.content else "",
            tool_calls=response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None
        )