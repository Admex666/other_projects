from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth import authenticate_user, create_access_token
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "user_id": current_user.user_id
    }
