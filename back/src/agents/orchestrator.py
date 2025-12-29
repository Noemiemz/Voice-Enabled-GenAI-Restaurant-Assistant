from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
import os
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.checkpoint.memory import MemorySaver

from utils.utils import Context, _thread_config_from_context, get_prompt_content, LLMLoggingCallback, TimingCallbackHandler

import dotenv
dotenv.load_dotenv()


def create_orchestrator_agent(agent_manager):
    """Create and return the orchestrator agent.
    
    Args:
        agent_manager: An instance of AgentManager to access sub-agents
        
    Returns:
        The configured orchestrator agent
    """
    
    @tool
    def use_faq_tool(runtime: ToolRuntime[Context], query: str) -> str:
        """Use the FAQ tool to answer general questions."""
        if runtime.context.verbose:
            print(f"[orchestrator -> faq_agent] query={query!r}")
        faq_agent = agent_manager.get_agent('faq')
        resp = faq_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=_thread_config_from_context(runtime),
            context=runtime.context,
        )
        return str(resp)

    @tool
    def use_menu_tool(runtime: ToolRuntime[Context], query: str) -> str:
        """Use the menu tool to handle menu-related queries."""
        if runtime.context.verbose:
            print(f"[orchestrator -> menu_agent] query={query!r}")
        menu_agent = agent_manager.get_agent('menu')
        resp = menu_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=_thread_config_from_context(runtime),
            context=runtime.context,
        )
        return str(resp)

    @tool
    def use_reservation_tool(runtime: ToolRuntime[Context], query: str) -> str:
        """Use the reservation tool to handle reservation-related queries."""
        if runtime.context.verbose:
            print(f"[orchestrator -> reservation_agent] query={query!r}")
        reservation_agent = agent_manager.get_agent('reservation')
        resp = reservation_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=_thread_config_from_context(runtime),
            context=runtime.context,
        )
        return str(resp)
    
    system_prompt = get_prompt_content("orchestrator_system.txt")
    
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest',
        callbacks=[LLMLoggingCallback(agent_name="orchestrator"), TimingCallbackHandler()]
    )
        
    orchestrator = create_agent(
        model=model,
        system_prompt=system_prompt, 
        tools=[use_menu_tool, use_faq_tool, use_reservation_tool],
        context_schema=Context,
        checkpointer=MemorySaver(),
    )
    
    return orchestrator