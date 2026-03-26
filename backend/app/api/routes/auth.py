"""
Authentication Routes
Handle user registration, login, and profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...models.user import UserCreate, UserLogin, UserResponse, Token
from ...services.shared.auth_service import get_auth_service, AuthService
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Authentication"])

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth_service.get_user_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account
    
    - **email**: Valid email address (unique)
    - **username**: 3-50 characters (unique)
    - **password**: Minimum 6 characters
    - **full_name**: Optional full name
    """
    user, access_token = await auth_service.register(user_data)
    
    logger.info(f"New user registered: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password
    
    Returns JWT access token for authenticated requests
    """
    user, access_token = await auth_service.login(
        credentials.email,
        credentials.password
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current user profile
    
    Requires authentication (Bearer token)
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Logout current user
    
    Note: JWT tokens are stateless, so this is mainly for client-side cleanup
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}
