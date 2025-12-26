"""
Mock MongoDB Tools for testing the agent system
This provides a simple in-memory database for development and testing
"""

class MockMongoDBTool:
    def __init__(self):
        """Initialize mock database with sample data"""
        self.menu_data = {
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {
                            "name": "Terrine de campagne", 
                            "price": "12€", 
                            "description": "Maison avec pain grillé",
                            "available": True
                        },
                        {
                            "name": "Salade niçoise", 
                            "price": "14€", 
                            "description": "Thon, œufs, olives, légumes frais",
                            "available": True
                        },
                        {
                            "name": "Soupe à l'oignon", 
                            "price": "10€", 
                            "description": "Gratinée au fromage",
                            "available": True
                        }
                    ]
                },
                {
                    "name": "Plats principaux",
                    "items": [
                        {
                            "name": "Boeuf bourguignon", 
                            "price": "22€", 
                            "description": "Viande fondante, champignons, carottes",
                            "available": True
                        },
                        {
                            "name": "Poulet rôti", 
                            "price": "18€", 
                            "description": "Avec pommes de terre et légumes de saison",
                            "available": True
                        },
                        {
                            "name": "Filet de saumon", 
                            "price": "20€", 
                            "description": "Sauce citronnée, riz basmati",
                            "available": True
                        }
                    ]
                },
                {
                    "name": "Desserts",
                    "items": [
                        {
                            "name": "Tarte tatin", 
                            "price": "9€", 
                            "description": "Pommes caramélisées, crème fraîche",
                            "available": True
                        },
                        {
                            "name": "Crème brûlée", 
                            "price": "8€", 
                            "description": "Vanille de Madagascar",
                            "available": True
                        },
                        {
                            "name": "Mousse au chocolat", 
                            "price": "7€", 
                            "description": "Chocolat noir 70%",
                            "available": True
                        }
                    ]
                }
            ],
            "lastUpdated": "2023-11-15T10:00:00"
        }
        
        self.reservations = [
            {
                "_id": "resv_001",
                "name": "Jean Dupont",
                "phone": "+33 6 12 34 56 78",
                "date": "2023-11-20",
                "time": "19:30",
                "guests": 4,
                "status": "confirmed",
                "createdAt": "2023-11-15T14:30:00"
            },
            {
                "_id": "resv_002", 
                "name": "Marie Martin",
                "phone": "+33 6 23 45 67 89",
                "date": "2023-11-21",
                "time": "20:00",
                "guests": 2,
                "status": "confirmed",
                "createdAt": "2023-11-16T11:15:00"
            }
        ]
        
        self.restaurant_info = {
            "name": "Les Pieds dans le Plat",
            "address": "1 Avenue des Champs-Élysées, 75008 Paris, France",
            "phone": "+33 1 23 45 67 89",
            "openingHours": "11:00 AM - 01:00 AM"
        }

    def get_menu(self):
        """Get the complete restaurant menu"""
        return self.menu_data

    def get_menu_categories(self):
        """Get list of menu categories"""
        return [category["name"] for category in self.menu_data["categories"]]

    def search_dishes(self, query):
        """Search dishes by name or description"""
        results = []
        query_lower = query.lower()
        
        for category in self.menu_data["categories"]:
            for item in category["items"]:
                if (query_lower in item["name"].lower() or 
                    query_lower in item["description"].lower()):
                    # Add category info to the result
                    dish_result = item.copy()
                    dish_result["category"] = category["name"]
                    results.append(dish_result)
        
        return results

    def get_dishes_by_category(self, category_name):
        """Get all dishes in a specific category"""
        category_name_lower = category_name.lower()
        
        for category in self.menu_data["categories"]:
            if category["name"].lower() == category_name_lower:
                return category["items"]
        
        return []

    def get_reservations(self, filters=None):
        """Get reservations with optional filters"""
        if filters is None:
            return self.reservations
        
        filtered = []
        for reservation in self.reservations:
            match = True
            for key, value in filters.items():
                if str(reservation.get(key, "")) != str(value):
                    match = False
                    break
            if match:
                filtered.append(reservation)
        
        return filtered

    def get_reservation_by_id(self, reservation_id):
        """Get a specific reservation by ID"""
        for reservation in self.reservations:
            if reservation["_id"] == reservation_id:
                return reservation
        return None

    def create_reservation(self, reservation_data):
        """Create a new reservation"""
        # Generate a simple ID
        new_id = f"resv_{len(self.reservations) + 1:03d}"
        reservation_data["_id"] = new_id
        reservation_data["status"] = "confirmed"
        
        # Add timestamps
        from datetime import datetime
        reservation_data["createdAt"] = datetime.now().isoformat()
        reservation_data["updatedAt"] = datetime.now().isoformat()
        
        self.reservations.append(reservation_data)
        return reservation_data

    def get_restaurant_info(self):
        """Get basic restaurant information"""
        return self.restaurant_info

    def get_available_dishes(self):
        """Get all available dishes"""
        available = []
        for category in self.menu_data["categories"]:
            for item in category["items"]:
                if item.get("available", True):
                    dish_result = item.copy()
                    dish_result["category"] = category["name"]
                    available.append(dish_result)
        return available