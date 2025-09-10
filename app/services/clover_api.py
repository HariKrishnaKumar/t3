import httpx
from fastapi import HTTPException
from typing import Dict, Any, List

async def get_all_categories(merchant_id: str, access_token: str) -> List[Dict[str, Any]]:
    """
    Fetches all item categories from Clover for a given merchant.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    base_url = "https://sandbox.dev.clover.com/v3/merchants"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/{merchant_id}/categories", headers=headers)
            response.raise_for_status()
            return response.json().get("elements", [])
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Clover API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


async def get_items_by_category(merchant_id: str, access_token: str, category_name: str) -> List[Dict[str, Any]]:
    """
    Fetches all items from Clover belonging to a specific category.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    base_url = "https://sandbox.dev.clover.com/v3/merchants"

    category_id = None
    async with httpx.AsyncClient() as client:
        try:
            # First, get all available categories
            categories = await get_all_categories(merchant_id, access_token)
            
            # Find the ID of the category that matches the requested name
            for category in categories:
                if category.get("name", "").lower() == category_name.lower():
                    category_id = category.get("id")
                    break
            
            if not category_id:
                raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found.")

            # Then, fetch all items for that specific category ID
            item_response = await client.get(
                f"{base_url}/{merchant_id}/categories/{category_id}/items", 
                headers=headers
            )
            item_response.raise_for_status()
            items = item_response.json().get("elements", [])
            return items

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Clover API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


async def get_item_details(merchant_id: str, access_token: str, item_id: str) -> Dict[str, Any]:
    """
    Fetches the details of a single item from Clover, including its category.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # To get category info, we must expand it in the request
    url = f"https://sandbox.dev.clover.com/v3/merchants/{merchant_id}/items/{item_id}?expand=categories"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Clover API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


async def create_clover_item(merchant_id: str, access_token: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new item (product) in Clover.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    base_url = "https://sandbox.dev.clover.com/v3/merchants"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{base_url}/{merchant_id}/items", headers=headers, json=item_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("message", e.response.text)
            raise HTTPException(status_code=e.response.status_code, detail=f"Clover API error: {error_detail}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

