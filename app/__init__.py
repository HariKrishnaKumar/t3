from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

# Access the API key
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/")
def read_root():
    return {"OpenAI Key Exists": openai_api_key is not None}
