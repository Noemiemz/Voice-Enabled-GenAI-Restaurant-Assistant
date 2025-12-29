from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
import os
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.checkpoint.memory import MemorySaver

from utils.utils import Context, _thread_config_from_context, get_prompt_content, LLMLoggingCallback, TimingCallbackHandler
from utils.timing import TimingContext

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
        
        with TimingContext("agent_invocation", {
            "agent_name": "faq",
            "query_length": len(query),
            "query_preview": query[:50] + "..." if len(query) > 50 else query,
            "query_full": query,
            "user_id": runtime.context.user_id,
            "invoked_by": "orchestrator",
            "tool_name": "use_faq_tool"
        }) as timer:
            faq_agent = agent_manager.get_agent('faq')
            resp = faq_agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config=_thread_config_from_context(runtime),
                context=runtime.context,
            )
            response_str = str(resp["messages"][-1].content)
            timer.context["response_length"] = len(response_str)
            timer.context["response_preview"] = response_str[:100] + "..." if len(response_str) > 100 else response_str
            timer.context["response_full"] = response_str
        return response_str

    @tool
    def use_menu_tool(runtime: ToolRuntime[Context], query: str) -> str:
        """Use the menu tool to handle menu-related queries."""
        if runtime.context.verbose:
            print(f"[orchestrator -> menu_agent] query={query!r}")
        
        with TimingContext("agent_invocation", {
            "agent_name": "menu",
            "query_length": len(query),
            "query_preview": query[:50] + "..." if len(query) > 50 else query,
            "query_full": query,
            "user_id": runtime.context.user_id,
            "invoked_by": "orchestrator",
            "tool_name": "use_menu_tool"
        }) as timer:
            menu_agent = agent_manager.get_agent('menu')
            resp = menu_agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config=_thread_config_from_context(runtime),
                context=runtime.context,
            )
            
            response_str = str(resp["messages"][-1].content)
            timer.context["response_length"] = len(response_str)
            timer.context["response_preview"] = response_str[:100] + "..." if len(response_str) > 100 else response_str
            timer.context["response_full"] = response_str
        return response_str

    @tool
    def use_reservation_tool(runtime: ToolRuntime[Context], query: str) -> str:
        """Use the reservation tool to handle reservation-related queries."""
        if runtime.context.verbose:
            print(f"[orchestrator -> reservation_agent] query={query!r}")
        
        with TimingContext("agent_invocation", {
            "agent_name": "reservation",
            "query_length": len(query),
            "query_preview": query[:50] + "..." if len(query) > 50 else query,
            "query_full": query,
            "user_id": runtime.context.user_id,
            "invoked_by": "orchestrator",
            "tool_name": "use_reservation_tool"
        }) as timer:
            reservation_agent = agent_manager.get_agent('reservation')
            resp = reservation_agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config=_thread_config_from_context(runtime),
                context=runtime.context,
            )
            response_str = str(resp["messages"][-1].content)
            timer.context["response_length"] = len(response_str)
            timer.context["response_preview"] = response_str[:100] + "..." if len(response_str) > 100 else response_str
            timer.context["response_full"] = response_str
        return response_str
    
    system_prompt = get_prompt_content("orchestrator_system.txt")
    
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest',
        callbacks=[LLMLoggingCallback(agent_name="orchestrator"), TimingCallbackHandler(agent_name="orchestrator")]
    )
        
    orchestrator = create_agent(
        model=model,
        system_prompt=system_prompt, 
        tools=[use_menu_tool, use_faq_tool, use_reservation_tool],
        context_schema=Context,
        checkpointer=MemorySaver(),
    )
    
    return orchestrator