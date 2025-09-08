from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_emoji_response(prompt: str):
    """Get response from OpenAI with error handling"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": f"Failed to get AI response: {str(e)}"}

def get_pizza_recommendation(preferences: str):
    """Get pizza recommendation based on user preferences"""
    prompt = f"Recommend a pizza based on these preferences: {preferences}. Include emojis."
    return get_emoji_response(prompt)
