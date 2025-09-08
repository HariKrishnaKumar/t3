from fastapi import APIRouter

router = APIRouter()

@router.get("/pizzas")
def get_pizzas():
    return {
        "pizzas": [
            {"id": 1, "name": "Margherita", "price": 299},
            {"id": 2, "name": "Farmhouse", "price": 399},
            {"id": 3, "name": "Peppy Paneer", "price": 349}
        ]
    }

@router.get("/pizzas/{pizza_id}")
def get_pizza(pizza_id: int):
    pizzas = {
        1: {"id": 1, "name": "Margherita", "price": 299},
        2: {"id": 2, "name": "Farmhouse", "price": 399},
        3: {"id": 3, "name": "Peppy Paneer", "price": 349}
    }
    return pizzas.get(pizza_id, {"error": "Pizza not found"})

@router.post("/pizzas")
def create_pizza(name: str, price: int):
    return {"message": f"Pizza {name} created with price {price}"}
