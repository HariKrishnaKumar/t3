from pydantic import BaseModel
from typing import List, Dict, Any

class RecommendationBase(BaseModel):
    user_id: int
    mobile_number: str
    recommendations: List[Dict[str, Any]]

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationOut(RecommendationBase):
    id: int

    class Config:
        from_attributes = True
