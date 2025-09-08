from fastapi import APIRouter

router = APIRouter()

@router.post("/add")
def add_cart():
    return {"message": "add of cart"}

@router.get("/detail")
def get_cart_details():
    return {"message": "Details of cart"}

@router.patch("/update")
def update_cart_details():
    return {"message": "update of cart"}

@router.delete("/delete")
def delete_cart_details():
    return {"message": "delete of cart"}

