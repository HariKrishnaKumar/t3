from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any, Optional
from models.merchant import Merchant
from models.merchant_detail import MerchantDetail
from models.merchant_token import MerchantToken
import json



class MerchantHelper:
    """Helper class for merchant database operations"""

    @staticmethod
    def get_merchant_by_clover_id(db: Session, clover_merchant_id: str) -> Optional[Merchant]:
        """Get merchant by Clover merchant ID"""
        return db.query(Merchant).filter(
            Merchant.clover_merchant_id == clover_merchant_id
        ).first()

    @staticmethod
    def create_merchant(db: Session, clover_merchant_id: str, name: str = None, email: str = None) -> Merchant:
        """Create new merchant"""
        merchant = Merchant(
            clover_merchant_id=clover_merchant_id,
            name=name,
            email=email
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def update_merchant(db: Session, merchant: Merchant, name: str = None, email: str = None) -> Merchant:
        """Update existing merchant"""
        if name:
            merchant.name = name
        if email:
            merchant.email = email
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def store_or_update_token(db: Session, merchant_id: int, access_token: str) -> None:
        """Store or update merchant access token"""
        # Check if token exists
        existing_token = db.query(MerchantToken).filter(
            MerchantToken.merchant_id == merchant_id
        ).first()

        if existing_token:
            # Update existing token
            existing_token.token = access_token
            existing_token.token_type = "bearer"
        else:
            # Create new token
            token = MerchantToken(
                merchant_id=merchant_id,
                token=access_token,
                token_type="bearer"
            )
            db.add(token)

        db.commit()

    # @staticmethod
    # def store_or_update_merchant_details(db: Session, clover_merchant_id: str, merchant_data: Dict[str, Any]) -> None:
    #     """Store or update merchant detailed information"""
    #     # Check if details exist
    #     existing_detail = db.query(MerchantDetail).filter(
    #         MerchantDetail.clover_merchant_id == clover_merchant_id
    #     ).first()
    #     print("Mechant detailxx", merchant_data)

    #     if existing_detail:
    #         # Update existing details
    #         existing_detail.name = merchant_data.get("name")
    #         existing_detail.currency = merchant_data.get("currency")
    #         existing_detail.timezone = merchant_data.get("timezone")
    #         existing_detail.email = merchant_data.get("email")
    #         existing_detail.address = merchant_data.get("address")
    #         existing_detail.city = merchant_data.get("city")
    #         existing_detail.state = merchant_data.get("state")
    #         existing_detail.country = merchant_data.get("country")
    #         existing_detail.postal_code = merchant_data.get("postal_code")
    #         existing_detail.updated_at = datetime.now()
    #     else:
    #         # Create new details
    #         detail = MerchantDetail(
    #             clover_merchant_id=clover_merchant_id,
    #             name=merchant_data.get("name"),
    #             currency=merchant_data.get("currency"),
    #             timezone=merchant_data.get("timezone"),
    #             email=merchant_data.get("email"),
    #             address=merchant_data.get("address"),
    #             city=merchant_data.get("city"),
    #             state=merchant_data.get("state"),
    #             country=merchant_data.get("country"),
    #             postal_code=merchant_data.get("postal_code")
    #         )
    #         db.add(detail)

    #     db.commit()

    @staticmethod
    def store_or_update_merchant_details(db: Session, clover_merchant_id: str, merchant_data: Dict[str, Any]) -> None:
        """Store or update merchant detailed information"""

        def safe_extract_string(data: dict, key: str, max_length: int = None) -> str:
            """Safely extract a string value from merchant data"""
            value = data.get(key)
            if value is None:
                return None

            # If it's already a string, use it
            if isinstance(value, str):
                return value[:max_length] if max_length and len(value) > max_length else value

            # If it's a dict or list, convert to JSON string (for complex fields)
            if isinstance(value, (dict, list)):
                import json
                try:
                    json_str = json.dumps(value)
                    return json_str[:max_length] if max_length and len(json_str) > max_length else json_str
                except (TypeError, ValueError):
                    return str(value)[:max_length] if max_length else str(value)

            # For other types, convert to string
            str_value = str(value)
            return str_value[:max_length] if max_length and len(str_value) > max_length else str_value

        print("Merchant detail data:", merchant_data)

        # Debug: Print each field and its type to identify problematic ones
        print("=== FIELD ANALYSIS ===")
        for key, value in merchant_data.items():
            print(f"Field '{key}': Type={type(value).__name__}, Value={repr(value)}")
            if isinstance(value, dict):
                print(f"  --> DICT DETECTED in '{key}': {value}")
            elif isinstance(value, list):
                print(f"  --> LIST DETECTED in '{key}': {value}")

        # Check if details exist
        existing_detail = db.query(MerchantDetail).filter(
            MerchantDetail.clover_merchant_id == clover_merchant_id
        ).first()

        if existing_detail:
            # Update existing details with safe extraction
            existing_detail.name = safe_extract_string(merchant_data, "name", 255)
            existing_detail.currency = safe_extract_string(merchant_data, "currency", 16)
            existing_detail.timezone = safe_extract_string(merchant_data, "timezone", 64)
            existing_detail.email = safe_extract_string(merchant_data, "email", 255)

            # Note: Clover API uses "address1" not "address"
            existing_detail.address = safe_extract_string(merchant_data, "address1", 255) or safe_extract_string(merchant_data, "address", 255)
            existing_detail.city = safe_extract_string(merchant_data, "city", 100)
            existing_detail.state = safe_extract_string(merchant_data, "state", 100)
            existing_detail.country = safe_extract_string(merchant_data, "country", 100)

            # Note: Clover API uses "zip" not "postal_code"
            existing_detail.postal_code = safe_extract_string(merchant_data, "zip", 20) or safe_extract_string(merchant_data, "postal_code", 20)
            existing_detail.updated_at = datetime.now()
        else:
            # Create new details with safe extraction
            detail = MerchantDetail(
                clover_merchant_id=clover_merchant_id,
                name=safe_extract_string(merchant_data, "name", 255),
                currency=safe_extract_string(merchant_data, "currency", 16),
                timezone=safe_extract_string(merchant_data, "timezone", 64),
                email=safe_extract_string(merchant_data, "email", 255),
                address=safe_extract_string(merchant_data, "address1", 255) or safe_extract_string(merchant_data, "address", 255),
                city=safe_extract_string(merchant_data, "city", 100),
                state=safe_extract_string(merchant_data, "state", 100),
                country=safe_extract_string(merchant_data, "country", 100),
                postal_code=safe_extract_string(merchant_data, "zip", 20) or safe_extract_string(merchant_data, "postal_code", 20)
            )
            db.add(detail)

        try:
            db.commit()
            print("✅ Merchant details stored successfully")
        except Exception as e:
            db.rollback()
            print(f"❌ Error committing to database: {str(e)}")
            raise Exception(f"Database commit failed: {str(e)}")

    @staticmethod
    def get_merchant_token(db: Session, clover_merchant_id: str) -> Optional[str]:
        """Get merchant access token"""
        result = db.execute(
            text("""
                SELECT mt.token
                FROM merchant_tokens mt
                JOIN merchants m ON mt.merchant_id = m.id
                WHERE m.clover_merchant_id = :clover_id
            """),
            {"clover_id": clover_merchant_id}
        ).fetchone()

        return result[0] if result else None

    @staticmethod
    def get_total_merchants_count(db: Session) -> int:
        """Get total number of merchants"""
        result = db.execute(text("SELECT COUNT(*) FROM merchants")).fetchone()
        return result[0] if result else 0

    @staticmethod
    def store_complete_merchant_data(
        db: Session,
        clover_merchant_id: str,
        merchant_data: Dict[str, Any],
        access_token: str
    ) -> int:
        """Complete merchant storage workflow"""
        try:
            # 1. Store/Update merchant basic info
            merchant = MerchantHelper.get_merchant_by_clover_id(db, clover_merchant_id)

            if merchant:
                # Update existing merchant
                merchant = MerchantHelper.update_merchant(
                    db, merchant,
                    name=merchant_data.get("name"),
                    email=merchant_data.get("email")
                )
            else:
                # Create new merchant
                merchant = MerchantHelper.create_merchant(
                    db, clover_merchant_id,
                    name=merchant_data.get("name"),
                    email=merchant_data.get("email")
                )

            # 2. Store/Update token
            MerchantHelper.store_or_update_token(db, merchant.id, access_token)
            print("Before merchat detail")
            # 3. Store/Update detailed information
            MerchantHelper.store_or_update_merchant_details(db, clover_merchant_id, merchant_data)

            return merchant.id

        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to store merchant data: {str(e)}")
