from models.llm import MistralWrapper, SmolMistralAdapter
from agents.info_agent import create_info_agent
from agents.orchestrator_agent import OrchestratorAgent

def main():
    mistral = MistralWrapper()
    llm = SmolMistralAdapter(mistral)

    info_agent = create_info_agent(llm)
    orchestrator = OrchestratorAgent(llm, info_agent)

    print("🤖 Assistant restaurant (smolagents) — tape 'exit' pour quitter")

    while True:
        user_input = input("👤 Vous: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response = orchestrator.run(user_input)
        print(f"🤖 Assistant: {response}")

if __name__ == "__main__":
    main()