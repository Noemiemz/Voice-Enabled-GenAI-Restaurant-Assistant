import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Optional, Dict, Any
from datetime import datetime
import json

class MongoDBManager:
    """
    MongoDB connection manager for the restaurant assistant application
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        self.client = None
        self.db = None
        self.connected = False
        # Don't connect immediately - lazy load on first use
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get MongoDB connection string from environment variables
            mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "restaurant_assistant")
            
            # print(f"Connecting to MongoDB at {mongo_uri}...")
            
            # Connect to MongoDB
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test the connection
            self.client.server_info()  # This will raise an exception if connection fails
            
            # Get database
            self.db = self.client[db_name]
            
            print("[SUCCESS] Successfully connected to MongoDB")
            
            # Create collections if they don't exist
            self._initialize_collections()
            
            self.connected = True
            return  # Exit after successful connection
            
        except ConnectionFailure as e:
            print(f"[WARNING] MongoDB connection failed: {e}")
            print("[INFO] Falling back to in-memory storage")
            self.connected = False
        except OperationFailure as e:
            print(f"[WARNING] MongoDB operation failed: {e}")
            print("[INFO] Falling back to in-memory storage")
            self.connected = False
        except Exception as e:
            print(f"[WARNING] Unexpected error connecting to MongoDB: {e}")
            print("[INFO] Falling back to in-memory storage")
            self.connected = False
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        self.client = None
        self.db = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get MongoDB connection string from environment variables
            mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "restaurant_assistant")
            
            # print(f"Connecting to MongoDB at {mongo_uri}...")
            
            # Connect to MongoDB
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test the connection
            self.client.server_info()  # This will raise an exception if connection fails
            
            # Get database
            self.db = self.client[db_name]
            
            print("[SUCCESS] Successfully connected to MongoDB")
            
            # Create collections if they don't exist
            self._initialize_collections()
            
            self.connected = True
            
        except ConnectionFailure as e:
            print(f"[WARNING] MongoDB connection failed: {e}")
            print("[INFO] Falling back to in-memory storage")
            self.connected = False
        except OperationFailure as e:
            print(f"[WARNING] MongoDB operation failed: {e}")
            print("[INFO] Falling back to in-memory storage")
            self.connected = False
        except Exception as e:
            print(f"[WARNING] Unexpected error connecting to MongoDB: {e}")
            print("[INFO] Falling back to in-memory storage")
            self.connected = False
    
    def _ensure_connected(self):
        """Ensure MongoDB connection is established"""
        if not self.connected and not self.client:
            self._connect()
    
    def _initialize_collections(self):
        """Initialize collections with indexes if needed"""
        if self.db is None:
            return
        
        # Create collections
        reservations_collection = self.db["Reservation"]
        menu_collection = self.db["Menu"]
        conversations_collection = self.db["conversations"]
        users_collection = self.db["users"]
        
        # Create indexes
        reservations_collection.create_index([("date", 1), ("time", 1)])
        reservations_collection.create_index([("phone", 1)])
        reservations_collection.create_index([("createdAt", -1)])
        
        # Initialize menu if empty
        if menu_collection.count_documents({}) == 0:
            self._initialize_menu_data()
    
    def _initialize_menu_data(self):
        """Initialize default menu data"""
        default_menu = {
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {"name": "Terrine de campagne", "price": "12€", "description": "Maison avec pain grillé", "available": True},
                        {"name": "Salade niçoise", "price": "14€", "description": "Thon, œufs, olives, légumes frais", "available": True},
                        {"name": "Soupe à l'oignon", "price": "10€", "description": "Gratinée au fromage", "available": True}
                    ]
                },
                {
                    "name": "Plats principaux",
                    "items": [
                        {"name": "Boeuf bourguignon", "price": "22€", "description": "Viande fondante, champignons, carottes", "available": True},
                        {"name": "Poulet rôti", "price": "18€", "description": "Avec pommes de terre et légumes de saison", "available": True},
                        {"name": "Filet de saumon", "price": "20€", "description": "Sauce citronnée, riz basmati", "available": True}
                    ]
                },
                {
                    "name": "Desserts",
                    "items": [
                        {"name": "Tarte tatin", "price": "9€", "description": "Pommes caramélisées, crème fraîche", "available": True},
                        {"name": "Crème brûlée", "price": "8€", "description": "Vanille de Madagascar", "available": True},
                        {"name": "Mousse au chocolat", "price": "7€", "description": "Chocolat noir 70%", "available": True}
                    ]
                }
            ],
            "lastUpdated": datetime.now().isoformat()
        }
        
        self.db["Menu"].insert_one(default_menu)
        print("[INFO] Initialized default menu data")
    
    def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get a reservation by ID"""
        self._ensure_connected()
        if not self.connected or self.db is None:
            return None
        
        try:
            reservation = self.db["Reservation"].find_one({"_id": reservation_id})
            if reservation:
                reservation["_id"] = str(reservation["_id"])
            return reservation
        except Exception as e:
            print(f"Error getting reservation: {e}")
            return None
    
    def create_reservation(self, reservation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new reservation"""
        self._ensure_connected()
        if self.db is None:
            return None
        
        try:
            # Add timestamps
            reservation_data["createdAt"] = datetime.now().isoformat()
            reservation_data["updatedAt"] = datetime.now().isoformat()
            reservation_data["status"] = "confirmed"
            
            # Insert reservation
            result = self.db["Reservation"].insert_one(reservation_data)
            
            # Return the created reservation with ID
            created_reservation = self.get_reservation(str(result.inserted_id))
            return created_reservation
        except Exception as e:
            print(f"Error creating reservation: {e}")
            return None
    
    def get_reservations(self, filters: Dict[str, Any] = None) -> list:
        """Get reservations with optional filters"""
        self._ensure_connected()
        if self.db is None:
            return []
        
        try:
            query = filters or {}
            reservations = list(self.db["Reservation"].find(query).sort("createdAt", -1))
            
            # Convert ObjectId to string
            for reservation in reservations:
                reservation["_id"] = str(reservation["_id"])
            
            return reservations
        except Exception as e:
            print(f"Error getting reservations: {e}")
            return []
    
    def update_reservation(self, reservation_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a reservation"""
        self._ensure_connected()
        if self.db is None:
            return False
        
        try:
            update_data["updatedAt"] = datetime.now().isoformat()
            
            result = self.db["Reservation"].update_one(
                {"_id": reservation_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating reservation: {e}")
            return False
    
    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation"""
        self._ensure_connected()
        if self.db is None:
            return False
        
        try:
            result = self.db["Reservation"].update_one(
                {"_id": reservation_id},
                {"$set": {
                    "status": "cancelled",
                    "updatedAt": datetime.now().isoformat()
                }}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error cancelling reservation: {e}")
            return False
    
    def get_menu(self) -> Optional[Dict[str, Any]]:
        """Get the current menu"""
        self._ensure_connected()
        if self.db is None:
            return None
        
        try:
            menu = self.db["Menu"].find_one()
            if menu and "_id" in menu:
                menu["_id"] = str(menu["_id"])
            return menu
        except Exception as e:
            print(f"Error getting menu: {e}")
            return None
    
    def update_menu(self, menu_data: Dict[str, Any]) -> bool:
        """Update the menu"""
        self._ensure_connected()
        if self.db is None:
            return False
        
        try:
            menu_data["lastUpdated"] = datetime.now().isoformat()
            
            result = self.db["Menu"].replace_one(
                {},
                menu_data,
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"Error updating menu: {e}")
            return False
    
    def save_conversation(self, conversation_data: Dict[str, Any]) -> Optional[str]:
        """Save a conversation"""
        self._ensure_connected()
        if self.db is None:
            return None
        
        try:
            conversation_data["createdAt"] = datetime.now().isoformat()
            
            result = self.db["conversations"].insert_one(conversation_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return None
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID"""
        self._ensure_connected()
        if self.db is None:
            return None
        
        try:
            conversation = self.db["conversations"].find_one({"_id": conversation_id})
            if conversation:
                conversation["_id"] = str(conversation["_id"])
            return conversation
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None
    
    def get_recent_conversations(self, limit: int = 10) -> list:
        """Get recent conversations"""
        self._ensure_connected()
        if self.db is None:
            return []
        
        try:
            conversations = list(self.db["conversations"].find().sort("createdAt", -1).limit(limit))
            
            for conversation in conversations:
                conversation["_id"] = str(conversation["_id"])
            
            return conversations
        except Exception as e:
            print(f"Error getting recent conversations: {e}")
            return []
    
    def get_dishes_by_category(self) -> Dict[str, list]:
        """Get all dishes grouped by category"""
        self._ensure_connected()
        if self.db is None:
            return {}
        
        try:
            dishes = list(self.db["Dish"].find())
            # Convert ObjectId to string
            for dish in dishes:
                if "_id" in dish:
                    dish["_id"] = str(dish["_id"])
            
            # Group dishes by category
            dishes_by_category = {}
            for dish in dishes:
                category = dish.get("category", "Other")
                if category not in dishes_by_category:
                    dishes_by_category[category] = []
                dishes_by_category[category].append(dish)
            
            return dishes_by_category
        except Exception as e:
            print(f"Error getting dishes by category: {e}")
            return {}
    
    def get_all_dishes(self) -> list:
        """Get all dishes from the database"""
        self._ensure_connected()
        if self.db is None:
            return []
        
        try:
            dishes = list(self.db["Dish"].find())
            
            # Convert ObjectId to string
            for dish in dishes:
                if "_id" in dish:
                    dish["_id"] = str(dish["_id"])
            
            return dishes
        except Exception as e:
            print(f"Error getting all dishes: {e}")
            return []
    
    def get_restaurant_info(self) -> Dict[str, Any]:
        """Get restaurant information"""
        return {
            "name": "Les Pieds dans le Plat",
            "address": "1 Avenue des Champs-Élysées, 75008 Paris, France",
            "phone": "+33 1 23 45 67 89",
            "email": "contact@lespiedsdansleplat.fr",
            "openingHours": "11:00 AM - 01:00 AM",
            "description": "Un restaurant traditionnel français au cœur de Paris, offrant une cuisine raffinée dans une ambiance chaleureuse.",
            "website": "https://www.lespiedsdansleplat.fr",
            "location": {
                "latitude": 48.8700,
                "longitude": 2.3050
            }
        }
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("[INFO] MongoDB connection closed")

# Singleton instance
db = MongoDBManager()