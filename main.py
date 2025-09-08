
from fastapi import FastAPI, Query, HTTPException, Path, Header, Depends
from dotenv import load_dotenv
from openai import OpenAI
from routers import users, pizzas, ai, auth
from app.routes.clover_auth import router as clover_router
from app.routes.userCart import router as userCart
from app.routes.clover_data import router as clover_data_router, merchant_router as clover_merchant_router
from app.routes.cart import router as cart_router
from app.routes.clover_cart import router as clover_cart_router
import os
from urllib.parse import urlencode
import secrets
from typing import Optional,Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.database import get_db
from helpers.merchant_helper import MerchantHelper
from models.merchant_token import MerchantToken
from app.routes.user_preferences import router as user_preferences_router
from routers.users import router as users_router 

from utils.merchant_extractor import (
    extract_merchant_details,
    get_merchant_summary,
    validate_merchant_response,
    extract_inventory_items,
    extract_orders
)


app = FastAPI()

# Load environment variables
load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Make sure you have this in your .env file
# Get Clover configuration from environment variables
CLOVER_ACCESS_TOKEN = os.getenv("CLOVER_ACCESS_TOKEN")  # The token your colleague has
CLOVER_MERCHANT_ID = os.getenv("CLOVER_MERCHANT_ID")    # The merchant ID your colleague has
CLOVER_BASE_URL = os.getenv("CLOVER_BASE_URL", "https://apisandbox.dev.clover.com")

# Store merchant tokens (in production, use database)
merchant_tokens: Dict[str, str] = {}

class MerchantToken(BaseModel):
    merchant_id: str
    access_token: str

app = FastAPI(title="Pizza API", version="1.0.0")

# Include routers (this connects all your route files)
# app.include_router(pizzas.router, prefix="/api", tags=["pizzas"])
# app.include_router(users.router, prefix="/api", tags=["users"])
# app.include_router(ai.router, prefix="/auth", tags=["ai"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clover_router)
app.include_router(clover_data_router)
app.include_router(clover_merchant_router)
app.include_router(cart_router)
app.include_router(clover_cart_router)
app.include_router(user_preferences_router)
app.include_router(users.router, prefix="/users")
app.include_router(user_preferences_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FAST API!"}

@app.get("/merchant")
async def get_merchant_details():
    """Get merchant details - Mobile app calls this"""

    if not CLOVER_ACCESS_TOKEN or not CLOVER_MERCHANT_ID:
        raise HTTPException(
            status_code=500,
            detail="Clover credentials not configured. Check .env file."
        )

    # Call Clover API
    url = f"{CLOVER_BASE_URL}/v3/merchants/{CLOVER_MERCHANT_ID}"
    headers = {
        "Authorization": f"Bearer {CLOVER_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            return {
                "success": True,
                "data": response.json()
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error: {e.response.text}"
            )

@app.get("/merchant/properties")
async def get_merchant_properties():
    """Get merchant properties"""

    if not CLOVER_ACCESS_TOKEN or not CLOVER_MERCHANT_ID:
        raise HTTPException(status_code=500, detail="Clover credentials not configured")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{CLOVER_MERCHANT_ID}/properties"
    headers = {
        "Authorization": f"Bearer {CLOVER_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            return {
                "success": True,
                "data": response.json()
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error: {e.response.text}"
            )


async def store_merchant_in_db(
    db: Session,
    clover_merchant_id: str,
    merchant_data: Dict[str, Any],
    access_token: str
):
    """Store merchant data in database tables"""

    # 1. Store in merchants table
    merchant_query = db.execute(
        "SELECT id FROM merchants WHERE clover_merchant_id = %s",
        (clover_merchant_id,)
    )
    merchant_record = merchant_query.fetchone()

    if not merchant_record:
        # Insert new merchant
        db.execute(
            """INSERT INTO merchants (clover_merchant_id, name, email, created_at)
        VALUES (%s, %s, %s, %s)""",
            (
                clover_merchant_id,
                merchant_data.get("name"),
                merchant_data.get("email"),
                datetime.now()
            )
        )
        db.commit()

        # Get the inserted merchant ID
        merchant_id_result = db.execute(
            "SELECT id FROM merchants WHERE clover_merchant_id = %s",
            (clover_merchant_id,)
        )
        merchant_id = merchant_id_result.fetchone()[0]
    else:
        merchant_id = merchant_record[0]

        # Update existing merchant
        db.execute(
            """UPDATE merchants
        SET name = %s, email = %s
        WHERE clover_merchant_id = %s""",
            (
                merchant_data.get("name"),
                merchant_data.get("email"),
                clover_merchant_id
            )
        )

    # 2. Store/Update access token in merchant_tokens table
    token_query = db.execute(
        "SELECT id FROM merchant_tokens WHERE merchant_id = %s",
        (merchant_id,)
    )
    token_record = token_query.fetchone()

    if not token_record:
        # Insert new token
        db.execute(
            """INSERT INTO merchant_tokens (merchant_id, token, token_type, created_at)VALUES (%s, %s, %s, %s)""",
            (merchant_id, access_token, "bearer", datetime.now())
        )
    else:
        # Update existing token
        db.execute(
            """UPDATE merchant_tokens
        SET token = %s, token_type = %s
        WHERE merchant_id = %s""",
            (access_token, "bearer", merchant_id)
        )

    # 3. Store detailed merchant info in merchant_detail table
    detail_exists = db.execute(
        "SELECT id FROM merchant_detail WHERE clover_merchant_id = %s",
        (clover_merchant_id,)
    )

    if not detail_exists.fetchone():
        # Insert new merchant details
        db.execute(
            """INSERT INTO merchant_detail (
                clover_merchant_id, name, currency, timezone, email,
                address, city, state, country, postal_code, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                clover_merchant_id,
                merchant_data.get("name"),
                merchant_data.get("currency"),
                merchant_data.get("timezone"),
                merchant_data.get("email"),
                merchant_data.get("address", {}).get("address1"),
                merchant_data.get("address", {}).get("city"),
                merchant_data.get("address", {}).get("state"),
                merchant_data.get("address", {}).get("country"),
                merchant_data.get("address", {}).get("zip"),
                datetime.now()
            )
        )
    else:
        # Update existing merchant details
        db.execute(
            """UPDATE merchant_detail SET
                name = %s, currency = %s, timezone = %s, email = %s,
                address = %s, city = %s, state = %s, country = %s,
                postal_code = %s, updated_at = %s
        WHERE clover_merchant_id = %s""",
            (
                merchant_data.get("name"),
                merchant_data.get("currency"),
                merchant_data.get("timezone"),
                merchant_data.get("email"),
                merchant_data.get("address", {}).get("address1"),
                merchant_data.get("address", {}).get("city"),
                merchant_data.get("address", {}).get("state"),
                merchant_data.get("address", {}).get("country"),
                merchant_data.get("address", {}).get("zip"),
                datetime.now(),
                clover_merchant_id
            )
        )

    db.commit()
    return merchant_id


# @app.post("/merchants/add")
# async def add_merchant_token(merchant: MerchantToken):
#     """Add a merchant and their access token"""

#     # Store the token for this merchant
#     merchant_tokens[merchant.merchant_id] = merchant.access_token

#     # Test if the token works
#     url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant.merchant_id}"
#     headers = {
#         "Authorization": f"Bearer {merchant.access_token}",
#         "Content-Type": "application/json"
#     }

#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url, headers=headers)
#             response.raise_for_status()
#             merchant_data = response.json()

#             # Validate the response
#             if not validate_merchant_response(merchant_data):
#                 raise HTTPException(status_code=400, detail="Invalid merchant data received")

#             # Extract clean merchant summary
#             summary = get_merchant_summary(merchant_data)

#             return {
#                 "success": True,
#                 "message": f"✅ Merchant {merchant.merchant_id} added successfully",
#                 "merchant_info": summary,
#                 "total_merchants": len(merchant_tokens)
#             }

#         except httpx.HTTPStatusError as e:
#             # Remove the token if it doesn't work
#             merchant_tokens.pop(merchant.merchant_id, None)
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid token for merchant {merchant.merchant_id}: {e.response.text}"
#             )


# @app.post("/merchants/add")
# async def add_merchant_token(merchant: MerchantToken, db: Session = Depends(get_db)):
#     """Add a merchant and their access token with database storage"""
#     # Test if the token works first
#     url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant.merchant_id}"
#     headers = {
#         "Authorization": f"Bearer {merchant.access_token}",
#         "Content-Type": "application/json"
#     }


#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url, headers=headers)
#             response.raise_for_status()
#             merchant_data = response.json()


#             # Validate the response
#             if not validate_merchant_response(merchant_data):
#                 raise HTTPException(status_code=400, detail="Invalid merchant data received")

#             # Store in database using helper
#             merchant_id = MerchantHelper.store_complete_merchant_data(
#                 db,
#                 merchant.merchant_id,
#                 merchant_data,
#                 merchant.access_token
#             )
#             print(merchant_id)

#             # Extract clean merchant summary for response
#             summary = get_merchant_summary(merchant_data)
#             print(summary)
#             # Get total merchants count
#             total_count = MerchantHelper.get_total_merchants_count(db)

#             return {
#                 "success": True,
#                 "message": f"✅ Merchant {merchant.merchant_id} added successfully",
#                 "merchant_info": summary,
#                 "database_id": merchant_id,
#                 "total_merchants": total_count
#             }

#         except httpx.HTTPStatusError as e:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid token for merchant {merchant.merchant_id}: {e.response.text}"
#             )
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Database error: {str(e)}"
#             )

@app.post("/merchants/add")
async def add_merchant_token(merchant: MerchantToken, db: Session = Depends(get_db)):
    """Add a merchant and their access token with database storage"""

    # Test if the token works first
    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant.merchant_id}"
    headers = {
        "Authorization": f"Bearer {merchant.access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            merchant_data = response.json()

            # DEBUG: Print the merchant data structure
            # print("=== MERCHANT DATA DEBUG ===")
            # print(f"Full merchant_data type: {type(merchant_data)}")
            # print(f"Full merchant_data: {merchant_data}")

            # Check each field and its type
            for key, value in merchant_data.items():
                print(f"Field '{key}': Type={type(value).__name__}, Value={repr(value)}")
                if isinstance(value, dict):
                    print(f"  -> DICT DETECTED in field '{key}': {value}")
                elif isinstance(value, list):
                    print(f"  -> LIST DETECTED in field '{key}': {value}")

            # Validate the response
            if not validate_merchant_response(merchant_data):
                raise HTTPException(status_code=400, detail="Invalid merchant data received")


            # Store in database using helper (this is where the error occurs)
            merchant_id = MerchantHelper.store_complete_merchant_data(
                db,
                merchant.merchant_id,
                merchant_data,
                merchant.access_token
            )

            # Extract clean merchant summary for response
            summary = get_merchant_summary(merchant_data)

            # Get total merchants count
            total_count = MerchantHelper.get_total_merchants_count(db)

            return {
                "success": True,
                "message": f"✅ Merchant {merchant.merchant_id} added successfully",
                "merchant_info": summary,
                "database_id": merchant_id,
                "total_merchants": total_count
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid token for merchant {merchant.merchant_id}: {e.response.text}"
            )
        except Exception as e:
            print(f"Full error details: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )


# @app.get("/inventory/items")
# async def get_inventory_items(limit: Optional[int] = 100):
#     """Get inventory items"""

#     if not CLOVER_ACCESS_TOKEN or not CLOVER_MERCHANT_ID:
#         raise HTTPException(status_code=500, detail="Clover credentials not configured")

#     url = f"{CLOVER_BASE_URL}/v3/merchants/{CLOVER_MERCHANT_ID}/items"
#     params = {"limit": limit}
#     headers = {
#         "Authorization": f"Bearer {CLOVER_ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url, headers=headers, params=params)
#             response.raise_for_status()

#             return {
#                 "success": True,
#                 "data": response.json()
#             }

#         except httpx.HTTPStatusError as e:
#             raise HTTPException(
#                 status_code=e.response.status_code,
#                 detail=f"Clover API error: {e.response.text}"
#             )


@app.get("/merchants/{clover_merchant_id}/token")
async def get_merchant_token(clover_merchant_id: str, db: Session = Depends(get_db)):
    """Get merchant access token"""
    token = MerchantHelper.get_merchant_token(db, clover_merchant_id)
    if not token:
        raise HTTPException(status_code=404, detail="Merchant token not found")

    return {"merchant_id": clover_merchant_id, "has_token": True}


# def get_merchant_token(merchant_id: str) -> str:
#     """Helper function to get token for a merchant"""
#     if merchant_id not in merchant_tokens:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Merchant {merchant_id} not found. Please add merchant token first using POST /merchants/add"
#         )
#     return merchant_tokens[merchant_id]

@app.get("/merchants/{merchant_id}")
async def get_merchant_details_endpoint(merchant_id: str = Path(..., description="Merchant ID")):
    """Get merchant details for specific merchant"""

    access_token = await get_merchant_token(merchant_id)

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            raw_data = response.json()

            # Extract only relevant merchant details using our utility function
            cleaned_data = extract_merchant_details(raw_data)

            return {
                "success": True,
                "merchant_id": merchant_id,
                "merchant_details": cleaned_data
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error for merchant {merchant_id}: {e.response.text}"
            )

@app.get("/merchants/{merchant_id}/inventory/items")
async def get_inventory_items(
    merchant_id: str = Path(..., description="Merchant ID"),
    limit: Optional[int] = 100
):
    """Get inventory items for specific merchant"""

    access_token = get_merchant_token(merchant_id)

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/items"
    params = {"limit": limit}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            raw_data = response.json()

            # Extract and clean inventory data
            cleaned_data = extract_inventory_items(raw_data)

            return {
                "success": True,
                "merchant_id": merchant_id,
                "inventory": cleaned_data
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error for merchant {merchant_id}: {e.response.text}"
            )

@app.get("/merchants/{merchant_id}/orders")
async def get_orders(
    merchant_id: str = Path(..., description="Merchant ID"),
    limit: Optional[int] = 100
):
    """Get orders for specific merchant"""

    access_token = get_merchant_token(merchant_id)

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/orders"
    params = {"limit": limit}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            raw_data = response.json()

            # Extract and clean orders data
            cleaned_data = extract_orders(raw_data)

            return {
                "success": True,
                "merchant_id": merchant_id,
                "orders": cleaned_data
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error for merchant {merchant_id}: {e.response.text}"
            )

@app.delete("/merchants/{merchant_id}")
async def remove_merchant(merchant_id: str = Path(..., description="Merchant ID")):
    """Remove merchant and their token"""

    if merchant_id not in merchant_tokens:
        raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")

    del merchant_tokens[merchant_id]

    return {
        "success": True,
        "message": f"Merchant {merchant_id} removed successfully",
        "remaining_merchants": len(merchant_tokens)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/orders")
async def get_orders(limit: Optional[int] = 100):
    """Get orders"""

    if not CLOVER_ACCESS_TOKEN or not CLOVER_MERCHANT_ID:
        raise HTTPException(status_code=500, detail="Clover credentials not configured")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{CLOVER_MERCHANT_ID}/orders"
    params = {"limit": limit}
    headers = {
        "Authorization": f"Bearer {CLOVER_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            return {
                "success": True,
                "data": response.json()
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error: {e.response.text}"
            )

@app.post("/orders")
async def create_order(order_data: dict):
    """Create a new Clover order"""

    if not CLOVER_ACCESS_TOKEN or not CLOVER_MERCHANT_ID:
        raise HTTPException(status_code=500, detail="Clover credentials not configured")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{CLOVER_MERCHANT_ID}/orders"
    headers = {
        "Authorization": f"Bearer {CLOVER_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=order_data)
            response.raise_for_status()

            return {
                "success": True,
                "data": response.json()
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clover API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/test-connection")
async def test_clover_connection():
    """Test if Clover connection is working"""

    if not CLOVER_ACCESS_TOKEN or not CLOVER_MERCHANT_ID:
        return {
            "success": False,
            "message": "❌ Clover credentials not configured",
            "missing": {
                "token": "Set CLOVER_ACCESS_TOKEN in .env",
                "merchant_id": "Set CLOVER_MERCHANT_ID in .env"
            }
        }

    # Test connection
    url = f"{CLOVER_BASE_URL}/v3/merchants/{CLOVER_MERCHANT_ID}"
    headers = {
        "Authorization": f"Bearer {CLOVER_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            return {
                "success": True,
                "message": "✅ Clover connection working!",
                "merchant_id": CLOVER_MERCHANT_ID,
                "token_status": "Valid"
            }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "message": "❌ Clover connection failed",
                "error": e.response.text,
                "status_code": e.response.status_code
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# @app.get("/test-env")
# def test_environment():
#     api_key = os.getenv("OPENAI_API_KEY")
#     if api_key:
#         return {"status": "API key loaded", "key_preview": f"{api_key[:10]}..."}
#     else:
#         return {"status": "API key NOT loaded", "error": "Check your .env file"}


# @app.get("/start-auth")
# async def start_clover_auth():
#     """
#     STEP 1: Start the authentication process
#     This creates a URL that merchants need to visit to authorize your app
#     """
#     if not CLOVER_APP_ID:
#         raise HTTPException(
#             status_code=500,
#             detail="Clover App ID not configured. Check your .env file"
#         )

#     # Create a random state for security
#     state = secrets.token_urlsafe(32)
#     oauth_states[state] = True

#     # Create the authorization URL
#     auth_params = {
#         "client_id": CLOVER_APP_ID,
#         "response_type": "code",
#         "state": state,
#         "scope": "read:merchants"  # Permission to read merchant info
#     }

#     auth_url = f"{CLOVER_BASE_URL}/oauth/authorize?" + urlencode(auth_params)

#     return {
#         "message": "Copy this URL and open it in your browser to authorize the app",
#         "authorization_url": auth_url,
#         "instructions": [
#             "1. Copy the authorization_url above",
#             "2. Open it in your web browser",
#             "3. Log in to your Clover account",
#             "4. Authorize the app",
#             "5. You'll be redirected back with a code"
#         ]
#     }

# @app.get("/auth-callback")
# async def handle_auth_callback(
#     code: str = Query(..., description="Authorization code from Clover"),
#     state: str = Query(..., description="State parameter for security"),
#     merchant_id: str = Query(..., description="Your Clover merchant ID")
# ):
#     """
#     STEP 2: Handle the callback from Clover
#     This exchanges the authorization code for an access token
#     """

#     # Check if state is valid (security check)
#     if state not in oauth_states:
#         raise HTTPException(status_code=400, detail="Invalid state. Please restart authentication.")

#     # Remove used state
#     del oauth_states[state]

#     # Exchange code for access token
#     token_url = f"{CLOVER_BASE_URL}/oauth/token"
#     token_data = {
#         "client_id": CLOVER_APP_ID,
#         "client_secret": CLOVER_APP_SECRET,
#         "code": code,
#         "grant_type": "authorization_code"
#     }

#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.post(token_url, data=token_data)
#             response.raise_for_status()
#             token_info = response.json()

#             # Save the access token
#             access_tokens[merchant_id] = token_info["access_token"]

#             return {
#                 "message": "✅ Authentication successful!",
#                 "merchant_id": merchant_id,
#                 "status": "authenticated",
#                 "next_step": f"Now you can call /merchant/{merchant_id} to get merchant details"
#             }

#         except httpx.HTTPStatusError as e:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Authentication failed: {e.response.text}"
#             )

@app.get("/merchant/{merchant_id}")
async def get_merchant_details(merchant_id: str):
    """
    STEP 3: Get merchant details
    Use this after successful authentication
    """

    # Check if we have access token for this merchant
    if merchant_id not in access_tokens:
        raise HTTPException(
            status_code=401,
            detail=f"No access token found for merchant {merchant_id}. Please complete authentication first."
        )

#     access_token = access_tokens[merchant_id]

#     # Make API call to Clover
#     merchant_url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}"
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }

#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(merchant_url, headers=headers)
#             response.raise_for_status()
#             merchant_data = response.json()

#             return {
#                 "message": "✅ Merchant details retrieved successfully",
#                 "merchant_id": merchant_id,
#                 "merchant_info": merchant_data
#             }

#         except httpx.HTTPStatusError as e:
#             if e.response.status_code == 401:
#                 raise HTTPException(
#                     status_code=401,
#                     detail="Access token expired. Please re-authenticate."
#                 )
#             else:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Failed to get merchant details: {e.response.text}"
#                 )

# @app.get("/check-auth/{merchant_id}")
# async def check_authentication_status(merchant_id: str):
#     """Check if a merchant is already authenticated"""
#     if merchant_id in access_tokens:
#         return {
#             "merchant_id": merchant_id,
#             "status": "authenticated",
#             "message": "✅ Merchant is authenticated. You can get merchant details."
#         }
#     else:
#         return {
#             "merchant_id": merchant_id,
#             "status": "not_authenticated",
#             "message": "❌ Merchant is not authenticated. Please complete authentication first."
#         }

# # Run the app (for development)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


# old code

# test api from main file not seprate in route
# @app.get("/api/pizzas")
# def get_pizzas():
#     return {
#         "pizzas": [
#             {"id": 1, "name": "Margherita", "price": 299},
#             {"id": 2, "name": "Farmhouse", "price": 399},
#             {"id": 3, "name": "Peppy Paneer", "price": 349}
#         ]
#     }
# @app.get("/")
# def read_root():
#     return {"message": "Hello, FastAPI!"}


# @app.get("/api/emoji-pizzas")
# def get_emoji_pizzas():
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 # {"role": "user", "content": "List 3 types of pizza with emojis."}
#                 {"role": "user", "content": "Give me Pizza Receipe with emojies."}
#             ]
#         )
#         message = response.choices[0].message.content
#         return {"response": message}
#     except Exception as e:
#         return {"error": f"Failed to get response from OpenAI: {str(e)}"}


# @app.get("/api/models")
# def get_available_models():
#     try:
#         models = client.models.list()
#         return {"models": [model.id for model in models.data]}
#     except Exception as e:
#         return {"error": str(e)}

# v1
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "Hello, FastAPI!"}
