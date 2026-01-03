import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Optional, Dict, Any, List
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

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
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get MongoDB connection string from environment variables
            mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "Restaurant_DB")
            
            # Connect to MongoDB
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test the connection
            self.client.server_info()  # This will raise an exception if connection fails
            
            # Get database
            self.db = self.client[db_name]
            self.connected=True
            print("[SUCCESS] Successfully connected to MongoDB")
            
        except (ConnectionFailure, OperationFailure) as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            self.connected = False
        except Exception as e:
            print(f"[ERROR] Unexpected error connecting to MongoDB: {e}")
            self.connected = False

    def _ensure_connected(self):
        if not self.connected:
            self._connect()

    # ===== Collection Accessors =====
    @property
    def reservations(self):
        self._ensure_connected()
        return self.db["Reservation"] if self.db is not None else None


    @property
    def menu(self):
        self._ensure_connected()
        return self.db["Menu"] if self.db is not None else None


    @property
    def dishes(self):
        self._ensure_connected()
        return self.db["Dish"] if self.db is not None else None


    @property
    def tables(self):
        self._ensure_connected()
        return self.db["Table"] if self.db is not None else None


    @property
    def orders(self):
        self._ensure_connected()
        return self.db["Order"] if self.db is not None else None

    

    # ===== CRUD Methods for Reservation =====
    def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        if self.reservations is None:
            return None
        try:
            reservation = self.reservations.find_one({"_id": ObjectId(reservation_id)})
            if reservation:
                reservation["_id"] = str(reservation["_id"])
            return reservation
        except Exception as e:
            print(f"Error getting reservation: {e}")
            return None

    def create_reservation(self, reservation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.reservations is None:
            return None
        try:
            result = self.reservations.insert_one(reservation_data)
            return self.get_reservation(str(result.inserted_id))
        except Exception as e:
            print(f"Error creating reservation: {e}")
            return None

    def update_reservation(self, reservation_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.reservations is None:
            return None
        try:
            result = self.reservations.update_one(
                {"_id": ObjectId(reservation_id)},
                {"$set": update_data}
            )
            return self.get_reservation(reservation_id)
        except Exception as e:
            print(f"Error updating reservation: {e}")
            return None

    def cancel_reservation(self, reservation_id: str) -> Optional[bool]:
        if self.reservations is None:
            return None
        try:
            result = self.reservations.delete_one(
                {"_id": ObjectId(reservation_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error cancelling reservation: {e}")
            return None
        
    def get_reservations(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if self.reservations is None:
            return []
        try:
            query = filters or {}
            reservations = list(self.reservations.find(query))
            for r in reservations:
                r["_id"] = str(r["_id"])
            return reservations
        except Exception as e:
            print(f"Error getting reservations: {e}")
            return []
        
    # ===== Dish Methods =====
    def get_all_dishes(self) -> List[Dict[str, Any]]:
        if self.dishes is None:
            return []
        try:
            dishes = list(self.dishes.find())
            for d in dishes:
                d["_id"] = str(d["_id"])
            
            return dishes
        except Exception as e:
            print(f"Error getting dishes: {e}")
            return []

    def get_dish(self, dish_id: str) -> Optional[Dict[str, Any]]:
        if self.dishes is None:
            return None
        try:
            dish = self.dishes.find_one({"_id": ObjectId(dish_id)})
            if dish:
                dish["_id"] = str(dish["_id"])
            return dish
        except Exception as e:
            print(f"Error getting dish: {e}")
            return None

    def get_dishes_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        if self.dishes is None:
            return {}
        try:
            dishes = list(self.dishes.find())
            categories = {}
            for dish in dishes:
                dish["_id"] = str(dish["_id"])
                cat = dish.get("category", "Other")
                categories.setdefault(cat, []).append(dish)
            return categories
        except Exception as e:
            print(f"Error getting dishes by category: {e}")
            return {}

    # ===== Table Methods =====
    def get_tables(self) -> List[Dict[str, Any]]:
        if self.tables is None:
            return []
        try:
            tables = list(self.tables.find())
            for t in tables:
                t["_id"] = str(t["_id"])
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []

    # ===== Order Methods =====
    def get_orders(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if self.orders is None:
            return []
        try:
            query = filters or {}
            orders = list(self.orders.find(query).sort("delivery_time", 1))
            for o in orders:
                o["_id"] = str(o["_id"])
            return orders
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.orders is None:
            return None
        try:
            result = self.orders.insert_one(order_data)
            order = self.orders.find_one({"_id": result.inserted_id})
            if order:
                order["_id"] = str(order["_id"])
            return order
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
    
    def update_order(self, order_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.orders is None:
            return None
        try:
            result = self.orders.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": update_data}
            )
            order = self.orders.find_one({"_id": ObjectId(order_id)})
            if order:
                order["_id"] = str(order["_id"])
            return order
        except Exception as e:
            print(f"Error updating order: {e}")
            return None
        
    def cancel_order(self, order_id: str) -> Optional[bool]:
        if self.orders is None:
            return None
        try:
            result = self.orders.delete_one(
                {"_id": ObjectId(order_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return None

    # ===== CRUD Methods for Menu =====
    def get_menu(self) -> Optional[Dict[str, Any]]:
        if self.menu is None:
            return None
        try:
            menu = self.menu.find_one()
            if menu and "_id" in menu:
                menu["_id"] = str(menu["_id"])
            return menu
        except Exception as e:
            print(f"Error getting menu: {e}")
            return None

    def update_menu(self, menu_data: Dict[str, Any]) -> bool:
        if self.menu is None:
            return False
        try:
            result = self.menu.replace_one({}, menu_data)
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating menu: {e}")
            return False
        

    
    # ===== Restaurant Info =====
    def get_restaurant_info(self) -> Dict[str, Any]:
        """Static restaurant information (not in DB)"""
        return {
            "name": "Les Pieds dans le Plat",
            "address": "1 Avenue des Champs-Élysées, 75008 Paris, France",
            "phone": "+33 1 23 45 67 89",
            "email": "contact@lespiedsdansleplat.fr",
            "openingHours": "11:00 AM - 01:00 AM",
            "description": "Un restaurant traditionnel français au cœur de Paris, offrant une cuisine raffinée dans une ambiance chaleureuse.",
            "website": "https://www.lespiedsdansleplat.fr",
            "location": {"latitude": 48.8700, "longitude": 2.3050}
        }
    
    # ===== Close Connection =====
    def close(self):
        if self.client:
            self.client.close()
            print("[INFO] MongoDB connection closed")

# Singleton instance
db = MongoDBManager()