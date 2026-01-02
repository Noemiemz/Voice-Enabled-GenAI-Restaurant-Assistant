from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class IngredientSchema(BaseModel):
    name: str = Field(description="Name of the ingredient")
    is_allergen: bool = Field(description="Indicates if the ingredient is a common allergen")
    allergen_type: Optional[str] = Field(default=None, description="Type of allergen if applicable")

class DishSchema(BaseModel):
    name: str = Field(description="Name of the dish")
    category: str = Field(description="Category of the dish, e.g., starter, main course, dessert or drink")
    ingredients: List[IngredientSchema] = Field(description="List of ingredients in the dish")
    is_vegetarian: bool = Field(description="Indicates if the dish is vegetarian")
    price: float = Field(description="Price of the dish in EUR")

class OfferSchema(BaseModel):
    name: str = Field(description="Name of the offer")
    starters: List[DishSchema] = Field(description="List of starter dishes in the offer")
    main_courses: List[DishSchema] = Field(description="List of main course dishes in the offer")
    desserts: List[DishSchema] = Field(description="List of dessert dishes in the offer")
    price: float = Field(description="Total price of the offer in EUR")

class OrderSchema(BaseModel):
    customer_name: str = Field(description="Name of the customer placing the order")
    customer_phone: str = Field(description="Phone number of the customer")
    items: List[DishSchema] = Field(description="List of dishes ordered")
    order_type: Literal["takeaway", "delivery"] = Field(description="Type of the order: takeaway or delivery")
    status: Literal["pending", "preparing", "ready", "on the way", "delivered", "cancelled"] = Field(description="Current status of the order")
    delivery_address: Optional[str] = Field(default=None, description="Delivery address if the order type is delivery")
    total_price: float = Field(description="Total price of the order in EUR")

class ReservationSchema(BaseModel):
    date_time: str = Field(description="Date and time of the reservation in ISO format")
    customer_name: str = Field(description="Name of the customer making the reservation")
    customer_phone: str = Field(description="Phone number of the customer")
    nb_person: int = Field(description="Number of persons for the reservation")
    table_id: str = Field(description="Table ID assigned for the reservation")
    special_requests: Optional[str] = Field(default=None, description="Any special requests for the reservation (e.g. High chair, wheelchair access)")

class TableSchema(BaseModel):
    nb_seats: int = Field(description="Number of seats available at the table")
    location: str = Field(description="Location of the table within the restaurant, e.g., indoor, outdoor") 