# app/routes/cart.py
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from sqlalchemy.orm import Session
from database.database import get_db
from helpers.cart_helper import CartHelper
from helpers.merchant_helper import MerchantHelper
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import httpx
import os

router = APIRouter(prefix="/cart", tags=["Cart Management"])

CLOVER_BASE_URL = os.getenv("CLOVER_BASE_URL", "https://apisandbox.dev.clover.com")


# Pydantic models for request/response
class CreateCartRequest(BaseModel):
    merchant_id: str
    customer_id: Optional[str] = None  # Optional: for logged-in users
    session_id: Optional[str] = None   # Required: for guest users, optional for logged-in users


class AddItemRequest(BaseModel):
    clover_item_id: str
    name: str
    price: float
    quantity: int = 1
    notes: Optional[str] = None


class UpdateQuantityRequest(BaseModel):
    quantity: int


class AddModifierRequest(BaseModel):
    clover_modifier_id: str
    clover_modifier_group_id: str
    name: str
    price: float = 0.0


def _build_headers(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@router.post("/create")
async def create_cart(
    request: CreateCartRequest,
    db: Session = Depends(get_db)
):
    """Create a new empty cart for guest or logged-in user"""
    try:
        # Validate request
        if not request.session_id and not request.customer_id:
            raise HTTPException(
                status_code=400,
                detail="Either session_id (for guests) or customer_id (for logged-in users) is required"
            )

        # For logged-in users, session_id is optional but recommended
        # For guest users, session_id is required

        cart = CartHelper.create_cart(
            db=db,
            merchant_id=request.merchant_id,
            # customer_id=request.customer_id,  # Can be None for guests
            session_id=request.session_id
        )

        return {
            "success": True,
            "message": "Cart created successfully",
            "cart_id": cart.id,
            "merchant_id": cart.clover_merchant_id,
            # "customer_id": cart.customer_id,
            "session_id": cart.session_id,
            "status": cart.status,
            # "user_type": "logged_in" if cart.customer_id else "guest"
            "user_type": "logged_in" if cart.session_id else "guest"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create cart: {str(e)}")


@router.get("/{cart_id}")
async def get_cart(
    cart_id: int,
    db: Session = Depends(get_db)
):
    """Get cart details with all items and modifiers"""
    cart_summary = CartHelper.get_cart_summary(db, cart_id)
    if not cart_summary:
        raise HTTPException(status_code=404, detail="Cart not found")

    return {
        "success": True,
        "cart": cart_summary
    }


@router.post("/{cart_id}/items")
async def add_item_to_cart(
    cart_id: int,
    request: AddItemRequest,
    db: Session = Depends(get_db)
):
    """Add an item to the cart"""
    try:
        # Check if cart exists
        cart = CartHelper.get_cart_by_id(db, cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if cart.status != "active":
            raise HTTPException(status_code=400, detail="Cannot modify inactive cart")

        cart_item = CartHelper.add_item_to_cart(
            db=db,
            cart_id=cart_id,
            clover_item_id=request.clover_item_id,
            name=request.name,
            price=request.price,
            quantity=request.quantity,
            notes=request.notes
        )

        return {
            "success": True,
            "message": "Item added to cart",
            "cart_item_id": cart_item.id,
            "quantity": cart_item.quantity,
            "line_total": cart_item.line_total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add item: {str(e)}")


@router.put("/{cart_id}/items/{cart_item_id}/quantity")
async def update_item_quantity(
    cart_id: int,
    cart_item_id: int,
    request: UpdateQuantityRequest,
    db: Session = Depends(get_db)
):
    """Update quantity of a cart item"""
    try:
        cart_item = CartHelper.update_item_quantity(
            db=db,
            cart_item_id=cart_item_id,
            quantity=request.quantity
        )

        if cart_item is None and request.quantity <= 0:
            return {
                "success": True,
                "message": "Item removed from cart",
                "cart_item_id": cart_item_id
            }
        elif cart_item is None:
            raise HTTPException(status_code=404, detail="Cart item not found")

        return {
            "success": True,
            "message": "Item quantity updated",
            "cart_item_id": cart_item.id,
            "quantity": cart_item.quantity,
            "line_total": cart_item.line_total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update quantity: {str(e)}")


@router.delete("/{cart_id}/items/{cart_item_id}")
async def remove_item_from_cart(
    cart_id: int,
    cart_item_id: int,
    db: Session = Depends(get_db)
):
    """Remove an item from the cart"""
    success = CartHelper.remove_item_from_cart(db, cart_item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cart item not found")

    return {
        "success": True,
        "message": "Item removed from cart",
        "cart_item_id": cart_item_id
    }


@router.post("/{cart_id}/items/{cart_item_id}/modifiers")
async def add_modifier_to_item(
    cart_id: int,
    cart_item_id: int,
    request: AddModifierRequest,
    db: Session = Depends(get_db)
):
    """Add a modifier to a cart item"""
    try:
        modifier = CartHelper.add_modifier_to_item(
            db=db,
            cart_item_id=cart_item_id,
            clover_modifier_id=request.clover_modifier_id,
            clover_modifier_group_id=request.clover_modifier_group_id,
            name=request.name,
            price=request.price
        )

        return {
            "success": True,
            "message": "Modifier added to item",
            "modifier_id": modifier.id,
            "name": modifier.name,
            "price": modifier.price
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add modifier: {str(e)}")


@router.delete("/{cart_id}/clear")
async def clear_cart(
    cart_id: int,
    db: Session = Depends(get_db)
):
    """Clear all items from the cart"""
    success = CartHelper.clear_cart(db, cart_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cart not found")

    return {
        "success": True,
        "message": "Cart cleared successfully",
        "cart_id": cart_id
    }


@router.get("/session/{session_id}")
async def get_cart_by_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get active cart by session ID (for guest users)"""
    cart = CartHelper.get_active_cart_by_session(db, session_id)
    if not cart:
        raise HTTPException(status_code=404, detail="No active cart found for this session")

    cart_summary = CartHelper.get_cart_summary(db, cart.id)
    return {
        "success": True,
        "cart": cart_summary
    }


@router.put("/{cart_id}/assign-customer")
async def assign_customer_to_cart(
    cart_id: int,
    # customer_id: str = Query(..., description="Customer ID to assign to cart"),
    db: Session = Depends(get_db)
):
    """Assign a logged-in customer to a guest cart (when user logs in during checkout)"""
    try:
        # Check if cart exists and is active
        cart = CartHelper.get_cart_by_id(db, cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if cart.status != "active":
            raise HTTPException(status_code=400, detail="Can only assign customer to active carts")

        # if cart.customer_id:
        #     raise HTTPException(status_code=400, detail="Cart already has a customer assigned")

        # Update cart with customer ID
        # cart.customer_id = customer_id
        cart.updated_at = datetime.now()
        db.commit()

        return {
            "success": True,
            "message": "Customer assigned to cart successfully",
            "cart_id": cart.id,
            # "customer_id": cart.customer_id,
            "session_id": cart.session_id,
            "user_type": "logged_in"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign customer: {str(e)}")


@router.get("/customer/{customer_id}")
async def get_customer_carts(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get all carts for a specific customer (logged-in user)"""
    try:
        carts = CartHelper.get_carts_by_customer(db, customer_id)
        return {
            "success": True,
            "customer_id": customer_id,
            "carts": carts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer carts: {str(e)}")
