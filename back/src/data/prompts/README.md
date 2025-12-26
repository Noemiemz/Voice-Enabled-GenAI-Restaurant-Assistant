# Restaurant Agent Prompts

This directory contains all prompt templates used by the restaurant agent system.

## Available Prompts

- `response_generation.txt` - Main prompt for generating responses to user queries

## Usage

Prompts use Python string formatting syntax with the following variables:

- `{intent}` - Detected user intent
- `{tool_name}` - Name of tool used (if any)
- `{tool_result_str}` - JSON string of tool result
- `{user_input}` - Original user input

## Adding New Prompts

1. Create a new `.txt` file with the prompt template
2. Use descriptive variable names in `{curly_braces}`
3. Update the `PromptManager` class to load the new prompt
4. Modify the agent to use the new prompt when appropriate

## Example

To create a new prompt for greeting users:

1. Create `greeting.txt`:
   ```
   Hello! Welcome to {restaurant_name}. How can I help you today?
   ```

2. Use it in the agent:
   ```python
   greeting_prompt = prompt_manager.get_formatted_prompt("greeting", restaurant_name="Le Bistro")
   ```