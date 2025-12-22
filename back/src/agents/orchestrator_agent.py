from smolagents.agents import CodeAgent


SYSTEM_PROMPT="""
You are the orchestrator of a restaurant assistant.

- Never answer directly. 
- Forward all user requests to the InfoAgent
"""

class OrchestratorAgent:
    """
    Simple orchestrator that delegates tasks to other more specified agents.
    """

    def __init__(self, llm, info_agent):
        self.info_agent = info_agent
        self.agent = CodeAgent(
            name="OrchestratorAgent",
            model=llm,
            tools=[]
        )

    def run(self, user_message: str) -> str:
        """
        Route user message to InfoAgent.
        """
        return self.info_agent.run(user_message)
