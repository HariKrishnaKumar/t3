from fastapi import APIRouter, Depends, Request
import httpx
import os

router = APIRouter(prefix="/clover", tags=["Clover Auth"])

CLIENT_ID = os.getenv("CLOVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLOVER_CLIENT_SECRET")
REDIRECT_URI = os.getenv("CLOVER_REDIRECT_URI")
TOKEN_URL = os.getenv("CLOVER_TOKEN_URL")
AUTH_URL = os.getenv("CLOVER_AUTH_URL")


# @router.get("/login")
def clover_login():
    """Redirect user to Clover OAuth page"""
    return {
        "url": f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
    }


# @router.get("/callback")
async def clover_callback(request: Request, code: str):
    """OAuth2 callback to exchange code for access + refresh tokens"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        data = resp.json()
        # store tokens securely (DB/Redis)
        return data


# @router.post("/token")
async def clover_token(code: str):
    """Directly exchange authorization code for tokens (no redirect flow)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return resp.json()


# @router.post("/refresh")
async def clover_refresh(refresh_token: str):
    """Refresh expired access token"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return resp.json()
