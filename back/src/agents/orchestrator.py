from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
import os
from langchain_core.tools import tool
from langchain.tools import ToolRuntime

from utils import Context, _thread_config_from_context, get_prompt_content
from agents.menu_agent import create_menu_agent
from agents.faq_agent import create_faq_agent

import dotenv
dotenv.load_dotenv()

# Initialize the sub-agents at module level (they'll be created once)
_menu_agent = None
_faq_agent = None


def _get_menu_agent():
    """Lazy initialization of menu agent."""
    global _menu_agent
    if _menu_agent is None:
        _menu_agent = create_menu_agent()
    return _menu_agent


def _get_faq_agent():
    """Lazy initialization of FAQ agent."""
    global _faq_agent
    if _faq_agent is None:
        _faq_agent = create_faq_agent()
    return _faq_agent


@tool
def use_faq_tool(runtime: ToolRuntime[Context], query: str) -> str:
    """Use the FAQ tool to answer general questions."""
    if runtime.context.verbose:
        print(f"[orchestrator -> faq_agent] query={query!r}")
    faq_agent = _get_faq_agent()
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
    menu_agent = _get_menu_agent()
    resp = menu_agent.invoke(
        {"messages": [{"role": "user", "content": query}]},
        config=_thread_config_from_context(runtime),
        context=runtime.context,
    )
    return str(resp)


def create_orchestrator_agent():
    """Create and return the orchestrator agent."""
    system_prompt = get_prompt_content("orchestrator_system.txt")
    
    model = ChatMistralAI(
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-small-latest'
    )
        
    orchestrator = create_agent(
        model=model,
        system_prompt=system_prompt, 
        tools=[use_menu_tool, use_faq_tool],
        context_schema=Context,
    )
    
    return orchestrator