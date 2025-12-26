from mistralai import Mistral
from smolagents import Model
import json
from smolagents.models import ChatMessage
from datetime import datetime
import os

class MistralWrapper():
    def __init__(self, api_key: str = None):
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-2506"
        # Construct absolute path to system prompt file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "..", "data", "prompts", "system_prompt.txt")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()
            f.close()
        
        # Setup logging directory
        self.log_dir = os.path.join(current_dir, "..", "data", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _log_interaction(self, method_name: str, input_data: dict, output_data: str):
        """Log LLM interactions to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method_name,
            "model": self.model,
            "input": input_data,
            "output": output_data
        }
        
        log_file = os.path.join(self.log_dir, f"llm_log_{datetime.now().strftime('%Y%m%d')}.jsonl")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error logging interaction: {e}")

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
            
            # Log the interaction
            self._log_interaction(
                method_name="generate_from_prompt",
                input_data={"user_prompt": user_prompt, "history": history[:-1], "kwargs": kwargs},
                output_data=text_response
            )
            
            return text_response
            
        except Exception as e:
            print(f"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nError in LLM generation: {e}")
            # Return a fallback response and the original history
            fallback_response = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            history.append({"role": "assistant", "content": fallback_response})
            # Log the error
            self._log_interaction(
                method_name="generate_from_prompt",
                input_data={"user_prompt": user_prompt, "history": history[:-1], "kwargs": kwargs, "error": str(e)},
                output_data=fallback_response
            )
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
            
            # Log the interaction
            self._log_interaction(
                method_name="generate_from_messages",
                input_data={"messages": msg_formatted, "kwargs": kwargs},
                output_data=text_response
            )
            
            return text_response
            
        except Exception as e:
            print(f"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nError in LLM generation: {e}")
            # Return a fallback response
            fallback_response = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            # Log the error
            self._log_interaction(
                method_name="generate_from_messages",
                input_data={"messages": msg_formatted, "kwargs": kwargs, "error": str(e)},
                output_data=fallback_response
            )
            return fallback_response

    def generate(self, text: str, history: list[dict[str, str]] = []) -> tuple[str, list[dict[str, str]]]:
        """
        Generate a response from text input (compatibility method for direct usage)
        
        Args:
            text: User input text
            history: Conversation history
            
        Returns:
            tuple: (response_text, updated_history)
        """
        print("Generating response from Mistral LLM to text:", text)
        try:
            # Combine system prompt with user input
            if history == []:
                history = [{"role": "system", "content": self.system_prompt}]
            
            # Add user message
            history.append({"role": "user", "content": text})
            
            # Generate response
            response = self.client.chat.complete(
                model=self.model,
                messages=history,
            )
            text_response = response.choices[0].message.content
            
            # Update history with assistant response
            history.append({"role": "assistant", "content": text_response})
            
            # Log the interaction
            self._log_interaction(
                method_name="generate",
                input_data={"text": text, "history": history[:-1]},
                output_data=text_response
            )
            
            return text_response, history
            
        except Exception as e:
            print(f"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nError in LLM generation: {e}")
            # Return a fallback response and the original history
            fallback_response = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            history.append({"role": "assistant", "content": fallback_response})
            # Log the error
            self._log_interaction(
                method_name="generate",
                input_data={"text": text, "history": history[:-1], "error": str(e)},
                output_data=fallback_response
            )
            return fallback_response, history


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
        
        # Setup logging directory (shared with MistralWrapper)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(current_dir, "..", "data", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _log_interaction(self, method_name: str, input_data: dict, output_data: dict):
        """Log LLM interactions to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method_name,
            "model": self.model,
            "input": input_data,
            "output": output_data
        }
        
        log_file = os.path.join(self.log_dir, f"llm_log_{datetime.now().strftime('%Y%m%d')}.jsonl")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error logging interaction: {e}")

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
        
        result = ChatMessage(
            role="assistant",
            content=response.choices[0].message.content if response.choices[0].message.content else "",
            tool_calls=response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None
        )
        
        # Log the interaction
        self._log_interaction(
            method_name="__call__",
            input_data={
                "messages": formatted_messages,
                "tools": tools,
                "kwargs": kwargs
            },
            output_data={
                "content": result.content,
                "tool_calls": str(result.tool_calls) if result.tool_calls else None
            }
        )
        
        return result