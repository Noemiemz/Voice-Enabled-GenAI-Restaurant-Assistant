from smolagents import tool
from models.mongodb import db


@tool
def get_menu() -> dict:
    """
    Returns the restaurant menu.
    """
    menu = db.get_menu()
    return menu if menu else {}


@tool
def get_all_dishes() -> list:
    """
    Returns all available dishes.
    """
    return db.get_all_dishes()


@tool
def get_restaurant_info() -> dict:
    """
    Returns general restaurant information.
    """
    return db.get_restaurant_info()
