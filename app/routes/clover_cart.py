# app/routes/clover_cart.py
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from sqlalchemy.orm import Session
from database.database import get_db
from helpers.cart_helper import CartHelper
from helpers.merchant_helper import MerchantHelper
from models.cart import Cart
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
from datetime import datetime

router = APIRouter(prefix="/clover-cart", tags=["Clover Cart Integration"])

CLOVER_BASE_URL = os.getenv("CLOVER_BASE_URL", "https://apisandbox.dev.clover.com")


class SyncCartRequest(BaseModel):
    cart_id: int


class CreateCloverOrderRequest(BaseModel):
    cart_id: int
    order_type: Optional[str] = "first_party_delivery"  # or "pickup", "delivery", etc.


def _build_headers(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@router.post("/sync-to-clover")
async def sync_cart_to_clover_order(
    request: SyncCartRequest,
    db: Session = Depends(get_db)
):
    """
    Step 1: Create empty Clover order from cart
    POST /v3/merchants/{mId}/orders
    """
    try:
        # Get cart details
        cart = CartHelper.get_cart_by_id(db, request.cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if cart.status != "active":
            raise HTTPException(status_code=400, detail="Can only sync active carts")

        # Get merchant token
        access_token = MerchantHelper.get_merchant_token(db, cart.clover_merchant_id)
        if not access_token:
            raise HTTPException(status_code=404, detail="Merchant token not found")

        # Create empty order in Clover
        clover_order_data = {
            "orderType": {
                "id": "FIRST_PARTY_DELIVERY"  # or other order types
            },
            "state": "OPEN",
            "note": f"Order created from cart {cart.id}"
        }

        url = f"{CLOVER_BASE_URL}/v3/merchants/{cart.clover_merchant_id}/orders"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=_build_headers(access_token),
                json=clover_order_data
            )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Clover API error: {response.text}"
                )

            clover_order = response.json()
            clover_order_id = clover_order.get("id")

        # Update cart with Clover order ID
        cart.clover_order_id = clover_order_id
        cart.status = "synced"
        cart.synced_at = datetime.now()
        db.commit()

        return {
            "success": True,
            "message": "Cart synced to Clover order",
            "cart_id": cart.id,
            "clover_order_id": clover_order_id,
            "clover_order": clover_order
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to sync cart: {str(e)}")


@router.post("/sync-items")
async def sync_cart_items_to_clover(
    request: SyncCartRequest,
    db: Session = Depends(get_db)
):
    """
    Step 2: Add line items to Clover order
    POST /v3/merchants/{mId}/orders/{orderId}/line_items
    """
    try:
        # Get cart with items
        cart = CartHelper.get_cart_by_id(db, request.cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if not cart.clover_order_id:
            raise HTTPException(status_code=400, detail="Cart not synced to Clover. Run sync-to-clover first.")

        # Get merchant token
        access_token = MerchantHelper.get_merchant_token(db, cart.clover_merchant_id)
        if not access_token:
            raise HTTPException(status_code=404, detail="Merchant token not found")

        synced_items = []

        # Add each cart item as line item in Clover
        for cart_item in cart.items:
            line_item_data = {
                "item": {
                    "id": cart_item.clover_item_id
                },
                "unitQty": cart_item.quantity,
                "note": cart_item.notes or ""
            }

            url = f"{CLOVER_BASE_URL}/v3/merchants/{cart.clover_merchant_id}/orders/{cart.clover_order_id}/line_items"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=_build_headers(access_token),
                    json=line_item_data
                )

                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to add line item: {response.text}"
                    )

                clover_line_item = response.json()
                clover_line_item_id = clover_line_item.get("id")

                # Update cart item with Clover line item ID
                cart_item.clover_line_item_id = clover_line_item_id

                synced_items.append({
                    "cart_item_id": cart_item.id,
                    "clover_line_item_id": clover_line_item_id,
                    "name": cart_item.name,
                    "quantity": cart_item.quantity
                })

        db.commit()

        return {
            "success": True,
            "message": "Cart items synced to Clover order",
            "cart_id": cart.id,
            "clover_order_id": cart.clover_order_id,
            "synced_items": synced_items
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to sync items: {str(e)}")


@router.post("/add-modifiers")
async def sync_cart_modifiers_to_clover(
    request: SyncCartRequest,
    db: Session = Depends(get_db)
):
    """
    Step 3: Add modifiers to line items in Clover order
    POST /v3/merchants/{mId}/orders/{orderId}/line_items/{lineItemId}/modifications
    """
    try:
        # Get cart with items and modifiers
        cart = CartHelper.get_cart_by_id(db, request.cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if not cart.clover_order_id:
            raise HTTPException(status_code=400, detail="Cart not synced to Clover")

        # Get merchant token
        access_token = MerchantHelper.get_merchant_token(db, cart.clover_merchant_id)
        if not access_token:
            raise HTTPException(status_code=404, detail="Merchant token not found")

        synced_modifiers = []

        # Add modifiers for each cart item
        for cart_item in cart.items:
            if not cart_item.clover_line_item_id:
                continue  # Skip items not synced yet

            for modifier in cart_item.modifiers:
                modification_data = {
                    "modifier": {
                        "id": modifier.clover_modifier_id
                    },
                    "amount": int(modifier.price * 100)  # Convert to cents
                }

                url = (
                    f"{CLOVER_BASE_URL}/v3/merchants/{cart.clover_merchant_id}/orders/"
                    f"{cart.clover_order_id}/line_items/{cart_item.clover_line_item_id}/modifications"
                )

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        headers=_build_headers(access_token),
                        json=modification_data
                    )

                    if response.status_code >= 400:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Failed to add modifier: {response.text}"
                        )

                    clover_modification = response.json()

                    synced_modifiers.append({
                        "cart_item_id": cart_item.id,
                        "modifier_id": modifier.id,
                        "clover_modification_id": clover_modification.get("id"),
                        "name": modifier.name,
                        "price": modifier.price
                    })

        return {
            "success": True,
            "message": "Modifiers synced to Clover order",
            "cart_id": cart.id,
            "clover_order_id": cart.clover_order_id,
            "synced_modifiers": synced_modifiers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync modifiers: {str(e)}")


@router.get("/order-status/{cart_id}")
async def get_clover_order_status(
    cart_id: int,
    db: Session = Depends(get_db)
):
    """
    Step 4: Get current order status from Clover
    GET /v3/merchants/{mId}/orders/{orderId}
    """
    try:
        # Get cart
        cart = CartHelper.get_cart_by_id(db, cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if not cart.clover_order_id:
            raise HTTPException(status_code=400, detail="Cart not synced to Clover")

        # Get merchant token
        access_token = MerchantHelper.get_merchant_token(db, cart.clover_merchant_id)
        if not access_token:
            raise HTTPException(status_code=404, detail="Merchant token not found")

        url = f"{CLOVER_BASE_URL}/v3/merchants/{cart.clover_merchant_id}/orders/{cart.clover_order_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=_build_headers(access_token))

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Clover API error: {response.text}"
                )

            clover_order = response.json()

        return {
            "success": True,
            "cart_id": cart.id,
            "clover_order_id": cart.clover_order_id,
            "order_status": clover_order
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order status: {str(e)}")


@router.post("/complete-order")
async def complete_order_flow(
    request: SyncCartRequest,
    db: Session = Depends(get_db)
):
    """
    Complete workflow: Create order + Add items + Add modifiers
    """
    try:
        # Step 1: Sync cart to Clover order
        await sync_cart_to_clover_order(request, db)

        # Step 2: Sync items
        await sync_cart_items_to_clover(request, db)

        # Step 3: Sync modifiers
        await sync_cart_modifiers_to_clover(request, db)

        # Get final cart status
        cart = CartHelper.get_cart_by_id(db, request.cart_id)
        cart.status = "completed"
        db.commit()

        return {
            "success": True,
            "message": "Order completed successfully",
            "cart_id": cart.id,
            "clover_order_id": cart.clover_order_id,
            "status": "completed"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete order: {str(e)}")
