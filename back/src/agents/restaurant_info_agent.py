"""
Restaurant Information Agent - Handles menu and general restaurant information
"""
from typing import Dict, Any, Optional, List
from smolagents import ToolCallingAgent
import json

class RestaurantInfoAgent(ToolCallingAgent):
    """
    Restaurant Information Agent that handles menu information and general restaurant queries.
    Provides details about dishes, ingredients, allergens, prices, and restaurant information.
    """
    
    def __init__(self, menu_data: Optional[Dict[str, Any]] = None):
        """Initialize the restaurant info agent"""
        self.menu_data = menu_data if menu_data else self._load_default_menu()
        self.restaurant_info = self._load_restaurant_info()
        self.orchestrator = None
        
    def _load_default_menu(self) -> Dict[str, Any]:
        """
        Load default menu data
        """
        return {
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {"name": "Terrine de campagne", "price": "12€", "description": "Maison avec pain grillé"},
                        {"name": "Salade niçoise", "price": "14€", "description": "Thon, œufs, olives, légumes frais"},
                        {"name": "Soupe à l'oignon", "price": "10€", "description": "Gratinée au fromage"}
                    ]
                },
                {
                    "name": "Plats principaux",
                    "items": [
                        {"name": "Boeuf bourguignon", "price": "22€", "description": "Viande fondante, champignons, carottes"},
                        {"name": "Poulet rôti", "price": "18€", "description": "Avec pommes de terre et légumes de saison"},
                        {"name": "Filet de saumon", "price": "20€", "description": "Sauce citronnée, riz basmati"}
                    ]
                },
                {
                    "name": "Desserts",
                    "items": [
                        {"name": "Tarte tatin", "price": "9€", "description": "Pommes caramélisées, crème fraîche"},
                        {"name": "Crème brûlée", "price": "8€", "description": "Vanille de Madagascar"},
                        {"name": "Mousse au chocolat", "price": "7€", "description": "Chocolat noir 70%"}
                    ]
                }
            ]
        }
    
    def _load_restaurant_info(self) -> Dict[str, Any]:
        """
        Load restaurant information
        """
        return {
            "name": "Les Pieds dans le Plat",
            "address": "1 Avenue des Champs-Elysées, 75008 Paris, France",
            "phone": "+33 1 23 45 67 89",
            "opening_hours": "11:00 AM - 01:00 AM (daily)",
            "description": "Un restaurant français traditionnel au cœur de Paris"
        }
    
    def execute(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute user input related to restaurant information
        
        Args:
            user_input: User's input text
            context: Additional context about the request
            
        Returns:
            Dictionary containing the result of the execution
        """
        if context is None:
            context = {}
            
        # Store orchestrator reference if provided
        if 'orchestrator' in context:
            self.orchestrator = context['orchestrator']
            
        intent = context.get('intent', 'general_info')
        
        try:
            if intent == 'menu_info':
                return self.handle_menu_request(user_input)
            elif intent == 'general_info':
                return self.handle_general_info_request(user_input)
            else:
                # For other intents, try to provide relevant information
                return self.handle_general_request(user_input)
                
        except Exception as e:
            print(f"[RESTAURANT_INFO_AGENT] Error processing request: {e}")
            return {
                'success': False,
                'message': f"Désolé, je n'ai pas pu obtenir les informations demandées: {str(e)}",
                'error': str(e)
            }
    
    def handle_menu_request(self, user_input: str) -> Dict[str, Any]:
        """
        Handle menu-related requests
        """
        user_input_lower = user_input.lower()
        
        # Check for specific dish requests
        dish_name = self._extract_dish_name(user_input)
        if dish_name:
            dish_info = self._get_dish_info(dish_name)
            if dish_info:
                return {
                    'success': True,
                    'message': f"Voici les informations sur {dish_name}: {dish_info['description']}. Prix: {dish_info['price']}",
                    'type': 'menu_info',
                    'data': dish_info
                }
        
        # Check for category requests
        category = self._extract_category(user_input_lower)
        if category:
            category_items = self._get_category_items(category)
            if category_items:
                items_list = ", ".join([item['name'] for item in category_items])
                return {
                    'success': True,
                    'message': f"Dans la catégorie {category}, nous avons: {items_list}",
                    'type': 'menu_info',
                    'data': {'category': category, 'items': category_items}
                }
        
        # General menu request
        return {
            'success': True,
            'message': "Voici notre menu complet:",
            'type': 'menu_info',
            'data': self.menu_data
        }
    
    def handle_general_info_request(self, user_input: str) -> Dict[str, Any]:
        """
        Handle general restaurant information requests
        """
        user_input_lower = user_input.lower()
        
        # Check for specific information requests
        if any(keyword in user_input_lower for keyword in ['adresse', 'où', 'localisation']):
            return {
                'success': True,
                'message': f"Notre restaurant {self.restaurant_info['name']} est situé à: {self.restaurant_info['address']}",
                'type': 'restaurant_info',
                'data': {'address': self.restaurant_info['address']}
            }
        
        elif any(keyword in user_input_lower for keyword in ['horaire', 'heure', 'ouvert', 'fermé']):
            return {
                'success': True,
                'message': f"Nous sommes ouverts {self.restaurant_info['opening_hours']}",
                'type': 'restaurant_info',
                'data': {'opening_hours': self.restaurant_info['opening_hours']}
            }
        
        elif any(keyword in user_input_lower for keyword in ['téléphone', 'contact', 'numéro']):
            return {
                'success': True,
                'message': f"Vous pouvez nous joindre au: {self.restaurant_info['phone']}",
                'type': 'restaurant_info',
                'data': {'phone': self.restaurant_info['phone']}
            }
        
        # General restaurant info
        return {
            'success': True,
            'message': f"Bienvenue chez {self.restaurant_info['name']}! {self.restaurant_info['description']}. Nous sommes situés à {self.restaurant_info['address']} et ouverts {self.restaurant_info['opening_hours']}.",
            'type': 'restaurant_info',
            'data': self.restaurant_info
        }
    
    def handle_general_request(self, user_input: str) -> Dict[str, Any]:
        """
        Handle general requests that might be restaurant-related
        """
        # Try to provide relevant information based on keywords
        user_input_lower = user_input.lower()
        
        if 'spécialité' in user_input_lower or 'recommandation' in user_input_lower:
            return {
                'success': True,
                'message': "Nos spécialités incluent le Boeuf bourguignon et la Tarte tatin. Puis-je vous donner plus de détails sur l'un de ces plats?",
                'type': 'restaurant_info',
                'data': {'specialties': ['Boeuf bourguignon', 'Tarte tatin']}
            }
        
        # Default response
        return {
            'success': True,
            'message': "Comment puis-je vous aider avec des informations sur notre restaurant ou notre menu?",
            'type': 'restaurant_info',
            'data': None
        }
    
    def _extract_dish_name(self, user_input: str) -> Optional[str]:
        """
        Extract dish name from user input
        """
        # Simple extraction - could be enhanced with NLP
        dish_keywords = [
            'terrine', 'salade', 'soupe', 'boeuf', 'poulet', 'saumon',
            'tarte', 'crème', 'mousse', 'niçoise', 'oignon', 'bourguignon'
        ]
        
        user_input_lower = user_input.lower()
        for keyword in dish_keywords:
            if keyword in user_input_lower:
                # Try to find the full dish name
                for category in self.menu_data['categories']:
                    for item in category['items']:
                        if keyword in item['name'].lower():
                            return item['name']
        
        return None
    
    def _get_dish_info(self, dish_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific dish
        """
        for category in self.menu_data['categories']:
            for item in category['items']:
                if item['name'].lower() == dish_name.lower():
                    return {
                        'name': item['name'],
                        'price': item['price'],
                        'description': item['description'],
                        'category': category['name']
                    }
        
        return None
    
    def _extract_category(self, user_input: str) -> Optional[str]:
        """
        Extract category from user input
        """
        categories = [category['name'].lower() for category in self.menu_data['categories']]
        user_input_lower = user_input.lower()
        
        for category in categories:
            if category in user_input_lower:
                # Return the proper case version
                for cat in self.menu_data['categories']:
                    if cat['name'].lower() == category:
                        return cat['name']
        
        return None
    
    def _get_category_items(self, category: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get items for a specific category
        """
        for cat in self.menu_data['categories']:
            if cat['name'].lower() == category.lower():
                return cat['items']
        
        return None
    
    def get_menu(self) -> Dict[str, Any]:
        """
        Get the complete menu data
        """
        return self.menu_data
        
    def get_restaurant_info(self) -> Dict[str, Any]:
        """
        Get restaurant information
        """
        return self.restaurant_info
        
    def update_menu(self, new_menu_data: Dict[str, Any]) -> None:
        """
        Update the menu data
        """
        self.menu_data = new_menu_data
        print("[RESTAURANT_INFO_AGENT] Menu updated")