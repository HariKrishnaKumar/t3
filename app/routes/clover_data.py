from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
import os
import httpx
from database.database import get_db
from helpers.merchant_helper import MerchantHelper
from typing import Optional,Dict, Any
from models.merchant_detail import MerchantDetail

router = APIRouter(prefix="/clover/catalog", tags=["Clover Catalog"])

CLOVER_BASE_URL = os.getenv("CLOVER_BASE_URL", "https://apisandbox.dev.clover.com")


def _build_headers(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@router.get("/items")
async def list_items(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    expand: str = Query("", description="Optional expand params, e.g. categories,modifierGroups"),
    db: Session = Depends(get_db),
):
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/items"
    params = {"limit": limit, "offset": offset}
    if expand:
        params["expand"] = expand

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token), params=params)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@router.get("/categories")
async def list_categories(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/categories"
    params = {"limit": limit, "offset": offset}

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token), params=params)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@router.get("/modifier-groups")
async def list_modifier_groups(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/modifier_groups"
    params = {"limit": limit, "offset": offset}

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token), params=params)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()




@router.get("/modifier-groups/{modifier_group_id}")
async def get_modifier_group(
    modifier_group_id: str,
    merchant_id: str = Query(..., description="Clover merchant ID"),
    db: Session = Depends(get_db),
):
    """Get a specific modifier group for a merchant."""
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/modifier_groups/{modifier_group_id}/modifiers"

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token))
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


# Merchant-focused endpoints
merchant_router = APIRouter(prefix="/clover/merchant", tags=["Clover Merchant"])


@router.get("/modifier-groups/{modifier_group_id}/modifiers/{modifier_id}")
async def get_modifier(
    modifier_group_id: str,
    modifier_id: str,
    merchant_id: str = Query(..., description="Clover merchant ID"),
    db: Session = Depends(get_db),
):
    """Get a specific modifier within a modifier group for a merchant."""
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = (
        f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/modifier_groups/"
        f"{modifier_group_id}/modifiers/{modifier_id}"
    )

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token))
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@merchant_router.get("/details")
async def get_and_store_merchant_details(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    db: Session = Depends(get_db),
):
    """Get and store merchant details from Clover API"""
    try:
        access_token = MerchantHelper.get_merchant_token(db, merchant_id)
        if not access_token:
            raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

        url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/address"

        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=_build_headers(access_token))
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.text)
            merchant_data = r.json()


        # Check if merchant detail already exists
        existing_merchant = db.query(MerchantDetail).filter(
            MerchantDetail.clover_merchant_id == merchant_id
        ).first()

        print("Raw merchant data:", merchant_data.get("address1"))  # Debug print
        if existing_merchant:
            # Update existing record - extract individual fields safely
            existing_merchant.name = str(merchant_data.get("name", "")) if merchant_data.get("name") else None
            existing_merchant.address = str(merchant_data.get("address1", "")) if merchant_data.get("address1") else None
            existing_merchant.city = str(merchant_data.get("city", "")) if merchant_data.get("city") else None
            existing_merchant.state = str(merchant_data.get("state", "")) if merchant_data.get("state") else None
            existing_merchant.country = str(merchant_data.get("country", "")) if merchant_data.get("country") else None
            existing_merchant.postal_code = str(merchant_data.get("zip", "")) if merchant_data.get("zip") else None
            existing_merchant.email = str(merchant_data.get("email", "")) if merchant_data.get("email") else None
            existing_merchant.currency = str(merchant_data.get("currency", "")) if merchant_data.get("currency") else None
            existing_merchant.timezone = str(merchant_data.get("timezone", "")) if merchant_data.get("timezone") else None

            db.commit()
            db.refresh(existing_merchant)

            return {
                "success": True,
                "message": "Merchant details updated successfully",
                "merchant_details": {
                    "merchant_id": merchant_id,
                    "name": existing_merchant.name,
                    "address": existing_merchant.address,
                    "city": existing_merchant.city,
                    "state": existing_merchant.state,
                    "country": existing_merchant.country,
                    "postal_code": existing_merchant.postal_code,
                    "email": existing_merchant.email,
                    "currency": existing_merchant.currency,
                    "timezone": existing_merchant.timezone
                }
            }
        else:
            # Create new record - extract individual fields safely
            new_merchant = MerchantDetail(
                clover_merchant_id=merchant_id,
                name=str(merchant_data.get("name", "")) if merchant_data.get("name") else None,
                address=str(merchant_data.get("address1", "")) if merchant_data.get("address1") else None,
                city=str(merchant_data.get("city", "")) if merchant_data.get("city") else None,
                state=str(merchant_data.get("state", "")) if merchant_data.get("state") else None,
                country=str(merchant_data.get("country", "")) if merchant_data.get("country") else None,
                postal_code=str(merchant_data.get("zip", "")) if merchant_data.get("zip") else None,
                email=str(merchant_data.get("email", "")) if merchant_data.get("email") else None,
                currency=str(merchant_data.get("currency", "")) if merchant_data.get("currency") else None,
                timezone=str(merchant_data.get("timezone", "")) if merchant_data.get("timezone") else None
            )

            db.add(new_merchant)
            db.commit()
            db.refresh(new_merchant)

            return {
                "success": True,
                "message": "Merchant details added successfully",
                "merchant_details": {
                    "merchant_id": merchant_id,
                    "name": new_merchant.name,
                    "address": new_merchant.address,
                    "city": new_merchant.city,
                    "state": new_merchant.state,
                    "country": new_merchant.country,
                    "postal_code": new_merchant.postal_code,
                    "email": new_merchant.email,
                    "currency": new_merchant.currency,
                    "timezone": new_merchant.timezone
                }
            }

    except Exception as e:
        db.rollback()  # Rollback in case of error
        print(f"Error storing merchant details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store merchant details: {str(e)}")

# @merchant_router.get("/details")
# async def get_and_store_merchant_details(
#     merchant_id: str = Query(..., description="Clover merchant ID"),
#     db: Session = Depends(get_db),
# ):
#     # print("merchant_id",merchant_id)
#     access_token = MerchantHelper.get_merchant_token(db, merchant_id)
#     if not access_token:
#         raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

#     url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}"
#     async with httpx.AsyncClient() as client:
#         r = await client.get(url, headers=_build_headers(access_token))
#         if r.status_code >= 400:
#             raise HTTPException(status_code=r.status_code, detail=r.text)
#         merchant_data = r.json()

#     # Extract address fields for storage
#     address_fields = {
#         "name": merchant_data.get("name"),
#         "currency": merchant_data.get("currency"),
#         "timezone": merchant_data.get("timezone"),
#         "email": merchant_data.get("email"),
#         "address": merchant_data.get("address"),
#         "city": merchant_data.get("city"),
#         "state": merchant_data.get("state"),
#         "country": merchant_data.get("country"),
#         "postal_code": merchant_data.get("postal_code")
#     }

#     # Persist details into merchant_detail table
#     try:
#         MerchantHelper.store_or_update_merchant_details(db, merchant_id, address_fields)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to store merchant details: {str(e)}")

#     return {
#         "success": True,
#         "merchant_id": merchant_id,
#         "stored_fields": address_fields,
#         "full_response": merchant_data
#     }


@merchant_router.get("/address")
async def get_merchant_address(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    db: Session = Depends(get_db),
):
    """Get merchant address details specifically"""
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/address"

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token))
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        merchant_data = r.json()
    print(merchant_data)
    # Extract only address-related fields
    address_data = {
        "merchant_id": merchant_id,
        "name": merchant_data.get("name"),
        "address": merchant_data.get("address1"),
        "city": merchant_data.get("city"),
        "state": merchant_data.get("state"),
        "country": merchant_data.get("country"),
        "postal_code": merchant_data.get("zip"),
        "email": merchant_data.get("email"),
        "currency": merchant_data.get("currency"),
        "timezone": merchant_data.get("timezone")
    }

    return {"success": True, "address_details": address_data}


@merchant_router.get("/properties")
async def get_merchant_properties(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    db: Session = Depends(get_db),
):
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/properties"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token))
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@router.get("/item-stocks")
async def get_item_stocks(
    merchant_id: str = Query(..., description="Clover merchant ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    item_id: str | None = Query(None, description="Optional Clover item ID to filter"),
    db: Session = Depends(get_db),
):
    access_token = MerchantHelper.get_merchant_token(db, merchant_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="Merchant token not found. Add the merchant first.")

    url = f"{CLOVER_BASE_URL}/v3/merchants/{merchant_id}/item_stocks"
    params = {"limit": limit, "offset": offset}
    if item_id:
        params["itemId"] = item_id

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_build_headers(access_token), params=params)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()
