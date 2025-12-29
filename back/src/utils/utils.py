from dataclasses import dataclass
from langchain.tools import ToolRuntime
import os
from pathlib import Path


@dataclass
class Context:
    user_id: str
    verbose: bool = False
    # Add any other context fields (e.g., location, preferences)


def get_prompt_content(prompt_name: str) -> str:
    """
    Load the content of a prompt file from the data/prompts directory.
    
    Args:
        prompt_name (str): The name of the prompt file (e.g., 'faq_system.txt').
        
    Returns:
        str: The content of the prompt file.
    """
    # Get the directory of the current file (utils.py)
    current_dir = Path(__file__).parent.parent
    # Construct the path to the prompts directory
    prompts_dir = current_dir / "data" / "prompts"
    
    prompt_path = prompts_dir / prompt_name
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _thread_config_from_context(runtime: ToolRuntime[Context]):
    # Keep thread_id stable per user; helps with memory/checkpointing if enabled
    return {"configurable": {"thread_id": runtime.context.user_id}}


from langchain_core.callbacks import BaseCallbackHandler
from typing import Any, Dict, List
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
import json
from datetime import datetime
import time

class LLMLoggingCallback(BaseCallbackHandler):
    def __init__(self, agent_name: str = "unknown"):
        current_dir = Path(__file__).parent
        self.log_dir = current_dir / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.agent_name = agent_name
        self.start_time = None
        
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        self.start_time = time.time()
        self._log("on_llm_start", {"prompts": prompts})

    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        """Run when Chat Model starts running."""
        self.start_time = time.time()
        # Convert messages to serializable format
        serializable_messages = []
        for batch in messages:
            batch_msgs = []
            for msg in batch:
                batch_msgs.append({"type": msg.type, "content": msg.content})
            serializable_messages.append(batch_msgs)
            
        self._log("on_chat_model_start", {"messages": serializable_messages})

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        generations = []
        for gen_list in response.generations:
            for gen in gen_list:
                generations.append(gen.text)
        
        # Calculate and log timing
        if self.start_time:
            duration = time.time() - self.start_time
            self._log("on_llm_end", {
                "generations": generations,
                "duration_seconds": round(duration, 6),
                "model": response.llm_output.get("model", "unknown") if response.llm_output else "unknown"
            })
        else:
            self._log("on_llm_end", {"generations": generations})

    def _log(self, event: str, data: Dict[str, Any]):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": event,
            "data": data
        }
        log_file = self.log_dir / f"llm_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error logging interaction: {e}")


class TimingCallbackHandler(BaseCallbackHandler):
    """Callback handler specifically for tracking LLM timing metrics."""
    
    def __init__(self):
        self.start_time = None
        self.current_operation = None
        current_dir = Path(__file__).parent
        self.log_dir = current_dir / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        self.start_time = time.time()
        self.current_operation = "llm_call"
        
    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        """Run when Chat Model starts running."""
        self.start_time = time.time()
        self.current_operation = "chat_model_call"

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Get token count if available
            token_count = 0
            if response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        token_count += len(gen.text.split())
            
            # Log timing information
            self._log_timing("llm_api_call", duration, {
                "model": response.llm_output.get("model", "unknown") if response.llm_output else "unknown",
                "estimated_tokens": token_count,
                "generation_length": len(response.generations[0][0].text) if response.generations else 0
            })

    def _log_timing(self, operation: str, duration: float, context: Dict[str, Any]):
        """Log timing information to performance log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_seconds": round(duration, 6),
            "context": context
        }
        
        log_file = self.log_dir / f"performance_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[TIMING] Error logging LLM timing: {e}")


