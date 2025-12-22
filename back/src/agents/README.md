# Agents System

This directory contains the agent-based architecture for the restaurant assistant system.

## Overview

The agent system follows a modular architecture with:

- **BaseAgent**: Foundation class for all agents
- **OrchestratorAgent**: Central coordinator that routes tasks to appropriate agents
- **UIAgent**: Handles communication with user interfaces
- **Specialized Agents**: Domain-specific agents (e.g., RestaurantInfoAgent, ReservationAgent)

## Key Components

### 1. BaseAgent

The foundation class that all agents inherit from. Provides:

- Basic agent structure (name, description, tools)
- Core methods: `execute()`, `can_handle()`
- Tool management

### 2. OrchestratorAgent

The central coordinator that:

- **Receives requests** from UI agents
- **Routes tasks** to appropriate specialized agents
- **Aggregates responses** from multiple agents
- **Returns final answers** to UI agents
- **Maintains task history** for auditing

### 3. UIAgent

Handles user interface communication:

- Receives user input (voice, text, etc.)
- Sends requests to orchestrator
- Formats responses for display
- Maintains conversation history

## Usage Example

```python
from agents.orchestrator_agent import OrchestratorAgent
from agents.ui_agent import UIAgent
from agents.base_agent import BaseAgent

# Create orchestrator
orchestrator = OrchestratorAgent()

# Create specialized agents
class MenuAgent(BaseAgent):
    def execute(self, task, context=None):
        return {"menu": ["Pasta", "Pizza", "Salad"]}
    
    def can_handle(self, task):
        return "menu" in task.lower()

# Register agents
orchestrator.register_agent(MenuAgent())

# Create and connect UI agent
ui_agent = UIAgent()
ui_agent.connect_to_orchestrator(orchestrator)

# Process user request
result = ui_agent.execute("Show me the menu", {"user_id": "customer1"})
print(result)
```

## Integration with Existing System

The agent system can be integrated with the existing Flask application:

1. **Initialize agents** when the app starts
2. **Route user requests** through the UI agent
3. **Use existing data sources** (menu data, reservations, etc.)
4. **Return formatted responses** to the frontend

### Example Integration

```python
# In your Flask app initialization
from agents.integration_example import create_agent_system

# Create agent system with your menu data
orchestrator, ui_agent = create_agent_system(menu_data=app_menu_data)

@app.route('/api/agent-process', methods=['POST'])
def agent_process():
    data = request.get_json()
    user_input = data.get('message')
    context = data.get('context', {})
    
    # Process through agent system
    result = ui_agent.execute(user_input, context)
    
    return jsonify({
        "response": result.get('message'),
        "data": result.get('data'),
        "type": result.get('type')
    })
```

## Agent Communication Flow

```
User → UI Agent → Orchestrator → Specialized Agents
                     ↑
User ← UI Agent ← Orchestrator ← Specialized Agents
```

1. User sends request to UI Agent
2. UI Agent forwards to Orchestrator with context
3. Orchestrator routes to appropriate Specialized Agent
4. Specialized Agent processes task and returns result
5. Orchestrator aggregates results if needed
6. Orchestrator returns to UI Agent
7. UI Agent formats response for user

## Creating Custom Agents

To create a new specialized agent:

```python
from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyCustomAgent", "Handles custom tasks")
        
    def execute(self, task, context=None):
        # Your task processing logic
        return {"result": "processed"}
        
    def can_handle(self, task):
        # Return True if this agent can handle the task
        return "custom" in task.lower()

# Register with orchestrator
orchestrator.register_agent(MyCustomAgent())
```

## Testing

Run the test script to verify the agent system:

```bash
cd back/src
python agents/test_orchestrator_fixed.py
```

## Files

- `base_agent.py`: Base agent class
- `orchestrator_agent.py`: Central orchestrator agent
- `ui_agent.py`: User interface agent
- `integration_example.py`: Example integration with existing system
- `test_orchestrator_fixed.py`: Test script
- `__init__.py`: Package initialization

## Future Enhancements

- Add `smolagents` integration for advanced agent capabilities
- Implement async task processing
- Add agent health monitoring
- Support for agent priorities and load balancing
- Integration with existing LLM and database systems