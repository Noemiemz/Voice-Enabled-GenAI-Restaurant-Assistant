"""
LangChain integration module for the restaurant assistant system.
Provides setup, configuration, and examples for using LangChain with our agents.
"""

from typing import Optional, Dict, Any
from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory
# from langchain.chat_models import ChatOpenAI
from .ui_agent_langchain import LangChainUIAgent
from .orchestrator_agent_langchain import LangChainOrchestratorAgent
from .tools.db_tool_langchain import RestaurantDBTool


def setup_langchain_agents(
    llm = None,
    memory: Optional[ConversationBufferMemory] = None,
    use_mock_db: bool = True
) -> Dict[str, Any]:
    """
    Set up all LangChain agents with proper configuration.
    
    Args:
        llm: Language model to use (if None, creates a default one)
        memory: Memory system to use (if None, creates a default one)
        use_mock_db: Whether to use mock database tool
        
    Returns:
        Dictionary containing all agents and tools
    """
    # Set up LLM if not provided
    if llm is None:
        from langchain_classic.llms.fake import FakeListLLM
        responses = [
            "I'm a mock LLM response for testing",
            "This is another mock response",
            '{"query_type": "menu", "needs_clarification": false, "clarification_questions": [], "refined_query": "Show vegetarian menu options", "key_details": {"dietary_preference": "vegetarian"}}'
        ]
        llm = FakeListLLM(responses=responses)
    
    # Set up memory if not provided
    if memory is None:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )
    
    # Create agents
    ui_agent = LangChainUIAgent(llm=llm, memory=memory)
    orchestrator = LangChainOrchestratorAgent(llm=llm, memory=memory)
    
    # Create and register tools
    if use_mock_db:
        db_tool = RestaurantDBTool()
        orchestrator.register_tool(db_tool)
        
        # Also register with UI agent for potential direct use
        ui_agent.register_tool(db_tool)
    
    return {
        "ui_agent": ui_agent,
        "orchestrator": orchestrator,
        "db_tool": db_tool if use_mock_db else None,
        "llm": llm,
        "memory": memory
    }


def create_advanced_memory_system() -> ConversationSummaryMemory:
    """Create an advanced memory system with summarization."""
    from langchain_classic.llms import OpenAI
    
    # Use a smaller model for summarization
    summary_llm = OpenAI(temperature=0, model_name="gpt-3.5-turbo")
    
    return ConversationSummaryMemory(
        llm=summary_llm,
        memory_key="chat_history",
        return_messages=True
    )


def setup_multi_agent_system() -> Dict[str, Any]:
    """Set up a complete multi-agent system with LangChain."""
    
    # Create agents with shared memory
    shared_memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Set up the system
    system = setup_langchain_agents(memory=shared_memory)
    
    # Add additional tools or configurations
    # ... (could add more tools here)
    
    return system


def example_conversation_flow():
    """Demonstrate a complete conversation flow using LangChain agents."""
    
    print("=== LangChain Restaurant Assistant Example ===\n")
    
    # Set up the system
    system = setup_multi_agent_system()
    ui_agent = system["ui_agent"]
    orchestrator = system["orchestrator"]
    
    # Example 1: Simple menu query
    print("Example 1: Menu Query")
    print("User: What vegetarian options do you have?")
    
    # Process query
    query_data = ui_agent.process_user_query("What vegetarian options do you have?")
    print(f"UI Agent Analysis: {query_data['llm_analysis']}")
    
    # Send to orchestrator
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(query_data)
    
    # Process by orchestrator
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    
    # Format for user
    ui_response = ui_agent.receive_message(orchestrator_response)
    print(f"Assistant: {ui_response['response_for_user']}\n")
    
    # Example 2: Reservation query
    print("Example 2: Reservation Query")
    print("User: I want to book a table for 4 people tonight")
    
    query_data = ui_agent.process_user_query("I want to book a table for 4 people tonight")
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(query_data)
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    ui_response = ui_agent.receive_message(orchestrator_response)
    print(f"Assistant: {ui_response['response_for_user']}\n")
    
    # Example 3: General query
    print("Example 3: General Query")
    print("User: Hello, how are you?")
    
    query_data = ui_agent.process_user_query("Hello, how are you?")
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(query_data)
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    ui_response = ui_agent.receive_message(orchestrator_response)
    print(f"Assistant: {ui_response['response_for_user']}\n")
    
    # Show memory
    print("=== Conversation Memory ===")
    memory_content = ui_agent.memory.load_memory_variables({})
    print(f"Memory content: {memory_content}")


def test_langchain_tool_usage():
    """Test direct LangChain tool usage."""
    
    print("\n=== LangChain Tool Testing ===")
    
    # Create just the DB tool
    db_tool = RestaurantDBTool()
    
    # Test queries
    test_queries = [
        {
            "description": "Vegetarian menu items",
            "query": {
                "collection": "Dish",
                "query": {"is_vegetarian": True},
                "projection": {"name": 1, "price": 1}
            }
        },
        {
            "description": "Available tables",
            "query": {
                "collection": "Table",
                "query": {"is_available": True}
            }
        }
    ]
    
    for test in test_queries:
        print(f"\nTest: {test['description']}")
        result = db_tool._run(test['query'])
        print(f"Result: {result}")


def create_custom_llm_chain():
    """Create a custom LLM chain for specific restaurant tasks."""
    
    from langchain_classic.prompts import PromptTemplate
    from langchain_classic.chains import LLMChain
    
    # Create a chain for menu recommendations
    template = """
    You are a restaurant menu expert. Given the following customer preferences:
    
    Preferences: {preferences}
    Available Menu: {menu_items}
    
    Recommend 2-3 dishes that would best match the customer's preferences.
    For each recommendation, provide:
    - Dish name
    - Why it matches the preferences
    - Any relevant dietary information
    """
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["preferences", "menu_items"]
    )
    
    # Use the same LLM as our agents
    system = setup_multi_agent_system()
    llm = system["llm"]
    
    return LLMChain(llm=llm, prompt=prompt)


def setup_langchain_with_custom_llm(llm) -> Dict[str, Any]:
    """Set up LangChain agents with a custom LLM."""
    
    # Create custom memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    return setup_langchain_agents(llm=llm, memory=memory)


def get_agent_system_with_history() -> Dict[str, Any]:
    """Get agent system with conversation history enabled."""
    
    # Create memory with history
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="input",
        output_key="output"
    )
    
    return setup_langchain_agents(memory=memory)


def demonstrate_memory_features():
    """Demonstrate LangChain memory features."""
    
    print("\n=== LangChain Memory Demonstration ===")
    
    # Set up system with memory
    system = get_agent_system_with_history()
    ui_agent = system["ui_agent"]
    memory = system["memory"]
    
    # Simulate a conversation
    queries = [
        "What vegetarian options do you have?",
        "Are there any gluten-free options?",
        "What about desserts?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nTurn {i}: User: {query}")
        
        # Process query
        query_data = ui_agent.process_user_query(query)
        message = ui_agent.send_query_to_orchestrator(query_data)
        
        # For simplicity, we'll just show the memory growth
        memory_vars = memory.load_memory_variables({})
        print(f"Memory after turn {i}: {len(memory_vars.get('chat_history', []))} messages")
        
        # Show last message in memory
        if 'chat_history' in memory_vars and memory_vars['chat_history']:
            last_message = memory_vars['chat_history'][-1]
            print(f"Last message type: {type(last_message).__name__}")


def create_agent_with_tools() -> LangChainOrchestratorAgent:
    """Create an orchestrator agent with multiple tools."""
    
    # Set up basic system
    system = setup_multi_agent_system()
    orchestrator = system["orchestrator"]
    
    # Add additional tools (could be expanded)
    # For now, we have the DB tool, but more could be added
    
    return orchestrator


def test_agent_executor():
    """Test the LangChain agent executor functionality."""
    
    print("\n=== Agent Executor Testing ===")
    
    # Set up system
    system = setup_multi_agent_system()
    orchestrator = system["orchestrator"]
    
    # Test if agent executor is available
    if orchestrator.agent_executor:
        print("Agent executor is available!")
        
        # Test a simple query
        try:
            result = orchestrator.use_agent_executor("Show me vegetarian menu options")
            print(f"Agent executor result: {result[:100]}...")  # Show first 100 chars
        except Exception as e:
            print(f"Agent executor test failed: {e}")
    else:
        print("Agent executor not available - no tools registered or setup issue")


def main():
    """Main function to demonstrate LangChain integration."""
    
    print("Starting LangChain Restaurant Assistant Integration...")
    
    # Run examples
    example_conversation_flow()
    test_langchain_tool_usage()
    demonstrate_memory_features()
    test_agent_executor()
    
    print("\n=== Integration Complete ===")
    print("The LangChain-enhanced restaurant assistant is ready to use!")


if __name__ == "__main__":
    main()