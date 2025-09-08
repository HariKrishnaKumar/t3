# app/routes/clover_auth.py
from fastapi import APIRouter
from app.utils.pkce_utils import generate_code_verifier, generate_code_challenge

router = APIRouter(prefix="/clover", tags=["Clover Auth"])

# Store verifier temporarily (in real case, save in DB or session store)
TEMP_STORAGE = {}

@router.get("/login")
def clover_login():
    verifier = generate_code_verifier(method="random")   # or "urandom" / "uuid"
    challenge = generate_code_challenge(verifier)

    # save verifier for later token exchange
    TEMP_STORAGE["code_verifier"] = verifier

    auth_url = (
        f"https://sandbox.dev.clover.com/oauth/authorize"
        f"?client_id=YOUR_CLIENT_ID"
        f"&response_type=code"
        f"&redirect_uri=https://your-ngrok-url.ngrok-free.app/clover/callback"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )

    return {"auth_url": auth_url, "verifier": verifier, "challenge": challenge}


# import os, base64

# def generate_code_verifier():
#     random_bytes = os.urandom(64)   # 64 bytes ~ 86 chars after encoding
#     return base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

# print(generate_code_verifier())
