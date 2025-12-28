from dataclasses import dataclass
from langchain.tools import ToolRuntime


@dataclass
class Context:
    user_id: str
    verbose: bool = False
    # Add any other context fields (e.g., location, preferences)



def _thread_config_from_context(runtime: ToolRuntime[Context]):
    # Keep thread_id stable per user; helps with memory/checkpointing if enabled
    return {"configurable": {"thread_id": runtime.context.user_id}}


