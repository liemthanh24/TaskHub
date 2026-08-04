from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import UserModel
from app.repositories.user import UserRepository
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def get_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    repo: UserRepository = Depends(get_repo),
):
    existing = await repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await repo.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    return Token(access_token=create_access_token(user.id))


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    repo: UserRepository = Depends(get_repo),
):
    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(user: UserModel = Depends(get_current_user)):
    return user
