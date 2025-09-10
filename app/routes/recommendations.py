from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database.database import get_db
from models.user import User as DBUser
from models.recommendation import Recommendation as DBRecommendation
from models.recommendation_schema import RecommendationCreate, RecommendationOut
from services.clover_api import get_items_by_category
from helpers.merchant_helper import get_current_merchant

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)

@router.post("/coffee/{user_id}", response_model=RecommendationOut)
async def get_and_save_coffee_recommendations(
    user_id: int,
    item_id: str, # The ID of the coffee the user bought
    db: Session = Depends(get_db),
    merchant: dict = Depends(get_current_merchant)
):
    """
    Generates and saves coffee recommendations for a specific user.
    """
    # 1. Find the user in the database
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # 2. Fetch all coffees from Clover
        all_coffees = await get_items_by_category(
            merchant_id=merchant["merchant_id"],
            access_token=merchant["access_token"],
            category_name="Coffee" # Ensure this matches your Clover category name
        )

        # 3. Filter out the item the user already bought
        recommendations_list = [
            coffee for coffee in all_coffees if coffee.get("id") != item_id
        ]
        
        if not recommendations_list:
            raise HTTPException(status_code=404, detail="No other coffees found to recommend.")

        # 4. Create and save the recommendation record
        new_recommendation = DBRecommendation(
            user_id=db_user.id,
            mobile_number=db_user.mobile_number,
            recommendations=recommendations_list
        )
        db.add(new_recommendation)
        db.commit()
        db.refresh(new_recommendation)
        
        return new_recommendation

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
