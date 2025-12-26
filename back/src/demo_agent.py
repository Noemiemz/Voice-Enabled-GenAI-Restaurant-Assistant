"""
Demonstration script for the Restaurant Agent System
This shows how to use the agent with both mock and real database
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from agents.restaurant_agent import RestaurantAgent
from agents.tools.mock_mongodb_tools import MockMongoDBTool

class DemoLLM:
    """Simple demo LLM that doesn't require API calls"""
    
    def __init__(self):
        pass
        
    def generate_from_prompt(self, prompt, history=None):
        """Generate a simple response based on the prompt"""
        # Extract useful information from prompt
        if "menu_request" in prompt:
            return "Voici notre menu du jour avec des entrées, plats principaux et desserts délicieux. Nous avons une terrine de campagne maison, un boeuf bourguignon fondant, et une tarte tatin caramélisée. Souhaitez-vous plus de détails sur un plat spécifique ?"
        elif "dish_search" in prompt:
            return "J'ai trouvé des plats correspondant à votre recherche. Par exemple, nous avons un poulet rôti avec pommes de terre et légumes de saison. Ce plat est très populaire parmi nos clients. Souhaitez-vous réserver une table pour le déguster ?"
        elif "reservation_request" in prompt:
            return "Nous avons des tables disponibles pour ce soir. Voici nos réservations actuelles : Jean Dupont à 19h30 pour 4 personnes et Marie Martin à 20h00 pour 2 personnes. Souhaitez-vous réserver pour quel horaire ?"
        elif "restaurant_info" in prompt:
            return "Notre restaurant 'Les Pieds dans le Plat' est situé au 1 Avenue des Champs-Élysées, 75008 Paris. Nous sommes ouverts de 11h00 à 01h00. Vous pouvez nous joindre au +33 1 23 45 67 89. Souhaitez-vous faire une réservation ?"
        elif "category_request" in prompt:
            return "Pour les entrées, nous proposons une délicieuse terrine de campagne maison avec pain grillé, une salade niçoise fraîche avec thon et olives, et une soupe à l'oignon gratinée. Quelle entrée vous tente le plus ?"
        else:
            return "Bonjour et bienvenue au restaurant 'Les Pieds dans le Plat' ! Comment puis-je vous aider aujourd'hui ?"

def demo_agent_system():
    """Demonstrate the agent system with various user inputs"""
    print("[PLATE] Restaurant Agent System Demo")
    print("=" * 50)
    
    # Initialize agent with mock database and demo LLM
    demo_llm = DemoLLM()
    agent = RestaurantAgent(llm=demo_llm, use_mock_db=True)
    
    # Test cases
    test_cases = [
        "Bonjour, je voudrais voir le menu",
        "Je cherche un plat avec du poulet",
        "Je voudrais réserver une table pour ce soir",
        "Quelles sont vos heures d'ouverture ?",
        "Quelles entrées proposez-vous ?",
        "Merci pour votre aide !"
    ]
    
    print("\n[ROBOT] Agent responses to different user inputs:\n")
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"[USER] User: {user_input}")
        response = agent.process_user_input(user_input)
        print(f"[AGENT] Agent: {response}")
        print("-" * 60)
    
    print("\n[PARTY] Demo completed successfully!")
    
    # Show some statistics
    print(f"\n[CHART] Statistics:")
    print(f"   - Conversation history length: {len(agent.conversation_history)}")
    print(f"   - Available tools: {len(agent.available_tools)}")
    print(f"   - Using mock database: {agent.use_mock_db}")

def demo_tool_usage():
    """Demonstrate direct tool usage"""
    print("\n[TOOLS] Direct Tool Usage Demo")
    print("=" * 40)
    
    # Initialize mock tools
    tools = MockMongoDBTool()
    
    # Show menu data
    print("\n[MENU] Menu Categories:")
    categories = tools.get_menu_categories()
    for category in categories:
        print(f"   - {category}")
    
    # Show some dishes
    print("\n[DISH] Sample Dishes:")
    dishes = tools.get_available_dishes()
    for i, dish in enumerate(dishes[:3], 1):  # Show first 3 dishes
        print(f"   {i}. {dish['name']} - {dish['price']}")
        print(f"      {dish['description']}")
    
    # Show restaurant info
    print("\n[HOME] Restaurant Information:")
    info = tools.get_restaurant_info()
    print(f"   Name: {info['name']}")
    print(f"   Address: {info['address']}")
    print(f"   Phone: {info['phone']}")
    print(f"   Hours: {info['openingHours']}")

if __name__ == "__main__":
    print("[ROCKET] Starting Restaurant Agent System Demo\n")
    
    # Run the main demo
    demo_agent_system()
    
    # Run tool usage demo
    demo_tool_usage()
    
    print("\n[CHECK] All demos completed successfully!")
    print("\n[LIGHT] The agent system is ready to be integrated with:")
    print("   - Real Mistral LLM (replace DemoLLM with MistralWrapper)")
    print("   - Real MongoDB database (set use_mock_db=False)")
    print("   - Voice interface for hands-free operation")