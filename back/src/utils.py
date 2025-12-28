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
    current_dir = Path(__file__).parent
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


