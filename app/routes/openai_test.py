# app/routes/openai_test.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.openai_service import ask_openai

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/ask-openai")
def ask_openai_route(request: PromptRequest):
    try:
        answer = ask_openai(request.prompt)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
