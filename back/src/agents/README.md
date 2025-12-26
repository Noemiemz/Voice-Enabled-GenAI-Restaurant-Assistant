# Restaurant Agent System

This directory contains the agent system for the Voice-Enabled GenAI Restaurant Assistant.

## Overview

The agent system provides an intelligent interface between users and the restaurant's database. It can:

- Understand user intent from natural language input
- Query the MongoDB database using appropriate tools
- Generate helpful responses using the LLM
- Maintain conversation history for context

## Architecture

```
User Input → RestaurantAgent → Intent Detection → Tool Selection → Database Query → LLM Response Generation → User
```

## Components

### 1. RestaurantAgent (`restaurant_agent.py`)

The main agent class that coordinates the entire process:

- **Intent Detection**: Determines what the user wants (menu, reservations, etc.)
- **Tool Selection**: Chooses the appropriate database tool
- **Response Generation**: Uses the LLM to create natural responses
- **Conversation Management**: Maintains conversation history

### 2. Tools (`tools/`)

Database interface tools:

- **MockMongoDBTool**: In-memory database for testing and development
- **MongoDBTools**: Interface to the real MongoDB database

### 3. Integration

The agent integrates with:

- **LLM**: Uses `MistralWrapper` from `models/llm.py`
- **Database**: Uses `MongoDBManager` from `models/mongodb.py`

## Usage

### Basic Usage

```python
from agents.restaurant_agent import RestaurantAgent
from models.llm import MistralWrapper

# Initialize with real LLM and mock database
llm = MistralWrapper(api_key="your_api_key")
agent = RestaurantAgent(llm=llm, use_mock_db=True)

# Process user input
response = agent.process_user_input("Je voudrais voir le menu")
print(response)

# Close when done
agent.close()
```

### Testing Mode

```python
# Use mock LLM for testing
class MockLLM:
    def generate_from_prompt(self, prompt, history=None):
        return "Test response"

agent = RestaurantAgent(llm=MockLLM(), use_mock_db=True)
```

### Real Database Mode

```python
# Use real MongoDB (requires MongoDB server running)
agent = RestaurantAgent(use_mock_db=False)
```

## Supported Intents

The agent can handle these types of requests:

1. **Menu Requests**: "Je veux voir le menu", "Quels plats avez-vous ?"
2. **Dish Search**: "Je cherche un plat avec du poulet", "Avez-vous des plats végétariens ?"
3. **Reservation Requests**: "Je veux réserver une table", "Avez-vous des places pour ce soir ?"
4. **Restaurant Info**: "Quelles sont vos heures d'ouverture ?", "Où êtes-vous situés ?"
5. **Category Requests**: "Quelles entrées proposez-vous ?", "Montrez-moi les desserts"
6. **General Questions**: Any other questions

## Testing

Run the test suite:

```bash
cd back/src
python tests/agents/test_mock_mongodb_tools.py
python tests/agents/test_restaurant_agent.py
```

## Demo

Run the demo to see the agent in action:

```bash
cd back/src
python demo_agent.py
```

## Integration with Voice Interface

To integrate with the voice interface:

1. **Speech-to-Text**: Convert voice input to text
2. **Agent Processing**: Pass text to `agent.process_user_input()`
3. **Text-to-Speech**: Convert agent response to voice

Example:

```python
# Pseudocode for voice integration
voice_input = stt.convert_voice_to_text()
text_response = agent.process_user_input(voice_input)
voice_output = tts.convert_text_to_voice(text_response)
```

## File Structure

```
agents/
├── __init__.py              # Package initialization
├── restaurant_agent.py     # Main agent class
├── tools/
│   ├── __init__.py          # Tools package initialization
│   ├── mongodb_tools.py     # Real MongoDB tools
│   └── mock_mongodb_tools.py # Mock database for testing
└── README.md               # This file
```

## Future Enhancements

- Add more sophisticated intent detection
- Implement memory for multi-turn conversations
- Add error recovery and retry logic
- Support for more complex queries
- Integration with additional data sources

## Dependencies

- Python 3.7+
- Mistral AI API (for real LLM)
- MongoDB (for real database)
- pymongo (for MongoDB connectivity)

The system is designed to work with the existing project infrastructure and can be easily extended.