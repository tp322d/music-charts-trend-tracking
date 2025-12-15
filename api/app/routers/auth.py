"""
Authentication router for user registration, login, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.postgres import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, TokenRefresh
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 characters, alphanumeric)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    - **role**: User role (admin, editor, or viewer)
    """
    auth_service = AuthService()
    user = auth_service.register_user(db, user_create)
    return user


@router.post("/token", response_model=Token, include_in_schema=True)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Obtain access and refresh tokens.
    
    Uses OAuth2 password flow. Returns JWT tokens for authentication.
    
    **Note:** Use the "Authorize" button above to login via Swagger UI.
    - Enter only **username** and **password**
    - Leave **client_id** and **client_secret** EMPTY
    
    For API calls, send form data:
    - **username**: User's username
    - **password**: User's password
    - **client_id**: (optional, can be empty)
    - **client_secret**: (optional, can be empty)
    
    Returns access_token and refresh_token for API authentication.
    """
    # OAuth2PasswordRequestForm automatically handles form data
    # and provides username, password, client_id (optional), client_secret (optional)
    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required"
        )
    
    # Create UserLogin schema from OAuth2 form data
    user_login = UserLogin(username=form_data.username, password=form_data.password)
    auth_service = AuthService()
    user = auth_service.authenticate_user(db, user_login)
    tokens = auth_service.create_tokens(user)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(token_refresh: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access_token and refresh_token pair.
    """
    auth_service = AuthService()
    tokens = auth_service.refresh_access_token(token_refresh.refresh_token, db)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    Requires valid authentication token.
    """
    return current_user

