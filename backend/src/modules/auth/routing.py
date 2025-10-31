from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.db import get_db
from src.modules.auth.schemas import UserCreate
from src.modules.auth.use_cases import RegisterUserUseCase
from src.modules.user.repository import UserRepository
from src.shared.schemas.response import SuccessResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserCreate)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    """
    user_repo = UserRepository(db)
    use_case = RegisterUserUseCase(user_repo)
    try:
        user = await use_case.execute(user_data)
        return SuccessResponse(data=user, message="User registered successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
