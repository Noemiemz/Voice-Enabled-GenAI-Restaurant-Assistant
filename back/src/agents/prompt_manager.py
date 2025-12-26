"""
Prompt Manager for Restaurant Agent System
Manages loading and formatting of prompt templates from external files
"""

import os
from typing import Dict, Optional

class PromptManager:
    def __init__(self, prompts_dir: str = "back/src/data/prompts"):
        """
        Initialize the prompt manager
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = prompts_dir
        self.prompts_cache: Dict[str, str] = {}

    def load_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Load a prompt from file
        
        Args:
            prompt_name: Name of the prompt file (without extension)
            
        Returns:
            Prompt content or None if not found
        """
        if prompt_name in self.prompts_cache:
            return self.prompts_cache[prompt_name]

        # Construct absolute path to prompts directory
        if not os.path.isabs(self.prompts_dir):
            # If relative path, make it absolute based on the current file location
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(current_file_dir, '..', 'data', 'prompts', f"{prompt_name}.txt")
        else:
            prompt_path = os.path.join(self.prompts_dir, f"{prompt_name}.txt")

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read().strip()
                self.prompts_cache[prompt_name] = prompt_content
                return prompt_content
        except FileNotFoundError:
            print(f"[WARNING] Prompt file {prompt_name}.txt not found at {prompt_path}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to load prompt {prompt_name}: {e}")
            return None

    def get_formatted_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a formatted prompt with variables replaced
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            Formatted prompt string
        """
        prompt_template = self.load_prompt(prompt_name)
        if not prompt_template:
            return self._get_default_prompt(prompt_name, **kwargs)

        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            print(f"[WARNING] Missing variable {e} in prompt {prompt_name}")
            # Fall back to default prompt
            return self._get_default_prompt(prompt_name, **kwargs)

    def _get_default_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a default prompt when the specified one is not available
        
        Args:
            prompt_name: Name of the requested prompt
            **kwargs: Available variables
            
        Returns:
            Default prompt string
        """
        # Basic fallback prompt
        return f"""You are a helpful restaurant assistant.

User Input: "{kwargs.get('user_input', '')}"

Please provide a helpful response in French based on this information."""