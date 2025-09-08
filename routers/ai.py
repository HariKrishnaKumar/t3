from fastapi import APIRouter
from services.openai_service import get_emoji_response

router = APIRouter()

@router.get("/emoji-pizzas")
def get_emoji_pizzas():
    return get_emoji_response("List 3 types of pizza with emojis.")

@router.get("/ai-suggest")
def suggest_pizza():
    return get_emoji_response("Suggest a creative pizza combination with emojis.")
