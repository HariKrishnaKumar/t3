"""
Merchant Data Extractor Utilities for Clover API

This module contains functions to extract and clean merchant data
from Clover API responses, making them more suitable for mobile apps.
"""

from datetime import datetime
from typing import Dict, Any, Optional


def extract_merchant_details(clover_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only essential merchant details from Clover API response
    This function can be reused for any merchant API response

    Args:
        clover_response: Raw response from Clover merchant API

    Returns:
        Cleaned merchant details with only relevant information
    """

    def convert_timestamp(timestamp_ms: Optional[int]) -> Optional[str]:
        """Convert millisecond timestamp to readable date string"""
        if timestamp_ms:
            try:
                return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return None
        return None

    # Extract basic merchant info
    merchant_details = {
        "merchant_id": clover_response.get("id"),
        "merchant_name": clover_response.get("name"),
        "created_date": convert_timestamp(clover_response.get("createdTime")),
        "merchant_plan_id": clover_response.get("merchantPlan", {}).get("id"),
        "reseller_id": clover_response.get("reseller", {}).get("id"),
        "owner_info": {
            "owner_id": clover_response.get("owner", {}).get("id"),
        } if clover_response.get("owner") else None,
        "available_endpoints": {
            "address": clover_response.get("address", {}).get("href"),
            "orders": clover_response.get("orders", {}).get("href"),
            "payments": clover_response.get("payments", {}).get("href"),
            "tenders": clover_response.get("tenders", {}).get("href"),
            "tax_rates": clover_response.get("taxRates", {}).get("href"),
            "printers": clover_response.get("printers", {}).get("href"),
            "modifier_groups": clover_response.get("modifierGroups", {}).get("href"),
            "order_types": clover_response.get("orderTypes", {}).get("href"),
            "opening_hours": clover_response.get("opening_hours", {}).get("href"),
            "shifts": clover_response.get("shifts", {}).get("href")
        }
    }

    # Remove None values to keep response clean
    cleaned_details = {k: v for k, v in merchant_details.items() if v is not None}

    return cleaned_details


def get_merchant_summary(clover_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get minimal merchant summary (just basic info)
    Perfect for listing multiple merchants

    Args:
        clover_response: Raw response from Clover merchant API

    Returns:
        Minimal merchant summary
    """
    created_date = None
    if clover_response.get("createdTime"):
        try:
            created_date = datetime.fromtimestamp(
                clover_response.get("createdTime", 0) / 1000
            ).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            created_date = None

    return {
        "merchant_id": clover_response.get("id"),
        "merchant_name": clover_response.get("name"),
        "status": "active",
        "created_date": created_date
    }


def validate_merchant_response(clover_response: Dict[str, Any]) -> bool:
    """
    Validate if the response contains required merchant data

    Args:
        clover_response: Raw response from Clover merchant API

    Returns:
        True if valid merchant response, False otherwise
    """
    required_fields = ["id", "name"]
    return all(field in clover_response and clover_response[field] for field in required_fields)


def extract_inventory_items(clover_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and clean inventory items from Clover API response

    Args:
        clover_response: Raw response from Clover inventory API

    Returns:
        Cleaned inventory data
    """
    items = clover_response.get("elements", [])

    cleaned_items = []
    for item in items:
        cleaned_item = {
            "item_id": item.get("id"),
            "name": item.get("name"),
            "price": item.get("price", 0) / 100 if item.get("price") else 0,  # Convert cents to dollars
            "price_type": item.get("priceType"),
            "sku": item.get("sku"),
            "category": item.get("categories", {}).get("elements", [{}])[0].get("name") if item.get("categories") else None,
            "hidden": item.get("hidden", False),
            "available": not item.get("hidden", False)
        }

        # Remove None values
        cleaned_items.append({k: v for k, v in cleaned_item.items() if v is not None})

    return {
        "total_items": len(cleaned_items),
        "items": cleaned_items
    }


def extract_orders(clover_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and clean orders from Clover API response

    Args:
        clover_response: Raw response from Clover orders API

    Returns:
        Cleaned orders data
    """
    orders = clover_response.get("elements", [])

    cleaned_orders = []
    for order in orders:
        # Convert timestamp
        created_time = None
        if order.get("createdTime"):
            try:
                created_time = datetime.fromtimestamp(
                    order.get("createdTime", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                created_time = None

        cleaned_order = {
            "order_id": order.get("id"),
            "state": order.get("state"),
            "total": order.get("total", 0) / 100 if order.get("total") else 0,  # Convert cents to dollars
            "tax_amount": order.get("taxAmount", 0) / 100 if order.get("taxAmount") else 0,
            "created_time": created_time,
            "employee_id": order.get("employee", {}).get("id") if order.get("employee") else None,
            "device_name": order.get("device", {}).get("name") if order.get("device") else None,
            "line_items_count": len(order.get("lineItems", {}).get("elements", []))
        }

        # Remove None values
        cleaned_orders.append({k: v for k, v in cleaned_order.items() if v is not None})

    return {
        "total_orders": len(cleaned_orders),
        "orders": cleaned_orders
    }


# Test function - you can remove this in production
if __name__ == "__main__":
    # Test data (your actual response)
    sample_response = {
        "href": "https://sandbox.dev.clover.com/v3/merchants/HNFBG81HGMYD1",
        "id": "HNFBG81HGMYD1",
        "name": "Test Merchant",
        "owner": {
            "href": "https://sandbox.dev.clover.com/v3/merchants/HNFBG81HGMYD1/employees/R8P0PVVRPBFHR",
            "id": "R8P0PVVRPBFHR"
        },
        "createdTime": 1755867916000,
        "merchantPlan": {"id": "9JVJFSQ8DDVC0"},
        "reseller": {"id": "55ZBBW12EAF2W"}
    }

    print("=== Testing Extraction Functions ===")
    print("\nFull Details:")
    print(extract_merchant_details(sample_response))

    print("\nSummary:")
    print(get_merchant_summary(sample_response))

    print("\nValidation:")
    print(f"Valid: {validate_merchant_response(sample_response)}")
