from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from models.user import User as DBUser
from models.recommendation import Recommendation as DBRecommendation
from models.recommendation_schema import RecommendationCreate, RecommendationOut
from services.clover_api import get_item_details, get_items_by_category

# This is the corrected import statement
from helpers.merchant_helper import get_current_merchant

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)

@router.post("/{item_id}/{user_id}", response_model=RecommendationOut)
async def create_recommendations_for_user(
    item_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    merchant: dict = Depends(get_current_merchant)
):
    """
    Generates and saves recommendations for a user based on a purchased item.
    """
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # 1. Get details of the purchased item to find its category
        item = await get_item_details(
            merchant_id=merchant["merchant_id"],
            access_token=merchant["access_token"],
            item_id=item_id
        )
        
        categories = item.get("categories", {}).get("elements", [])
        if not categories:
            raise HTTPException(status_code=404, detail="Item has no category, cannot generate recommendations.")
        
        # Take the first category name
        category_name = categories[0].get("name")
        if not category_name:
            raise HTTPException(status_code=404, detail="Category name not found.")

        # 2. Get all other items in the same category
        all_items_in_category = await get_items_by_category(
            merchant_id=merchant["merchant_id"],
            access_token=merchant["access_token"],
            category_name=category_name
        )

        # 3. Filter out the original item to create the final recommendation list
        recommendations = [rec for rec in all_items_in_category if rec.get("id") != item_id]

        # 4. Save the new recommendation to the database
        db_recommendation = DBRecommendation(
            user_id=db_user.id,
            mobile_number=db_user.mobile_number,
            recommendations=recommendations
        )
        db.add(db_recommendation)
        db.commit()
        db.refresh(db_recommendation)
        
        return db_recommendation

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

