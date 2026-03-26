"""
Authentication Service
Handle user registration, login, and JWT token management
"""

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from bson import ObjectId
from fastapi import HTTPException, status

from app.config import get_settings
from app.database.mongodb_client import get_mongodb
from app.models.user import UserCreate, UserInDB, UserResponse, TokenPayload
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AuthService:
    """Authentication service for user management"""

    def __init__(self):
        self.mongodb = get_mongodb()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def _create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenPayload(**payload)
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    async def register(self, user_data: UserCreate) -> tuple[UserResponse, str]:
        """Register a new user"""
        # Check if email exists
        existing_user = self.mongodb.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username exists
        existing_username = self.mongodb.users.find_one({"username": user_data.username})
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Create user document
        now = datetime.now(timezone.utc)
        user_doc = {
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "hashed_password": self._hash_password(user_data.password),
            "created_at": now,
            "updated_at": now,
            "is_active": True
        }

        # Insert to MongoDB
        result = self.mongodb.users.insert_one(user_doc)
        user_id = str(result.inserted_id)

        logger.info(f"User registered: {user_data.email}")

        # Create response
        user_response = UserResponse(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            created_at=now
        )

        # Create token
        access_token = self._create_access_token(user_id)

        return user_response, access_token

    async def login(self, email: str, password: str) -> tuple[UserResponse, str]:
        """Login user and return token"""
        # Find user by email
        user_doc = self.mongodb.users.find_one({"email": email})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        if not self._verify_password(password, user_doc["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is active
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )

        user_id = str(user_doc["_id"])
        logger.info(f"User logged in: {email}")

        # Create response
        user_response = UserResponse(
            id=user_id,
            email=user_doc["email"],
            username=user_doc["username"],
            full_name=user_doc.get("full_name"),
            created_at=user_doc["created_at"],
            updated_at=user_doc.get("updated_at")
        )

        # Create token
        access_token = self._create_access_token(user_id)

        return user_response, access_token

    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            user_doc = self.mongodb.users.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                return None

            return UserResponse(
                id=str(user_doc["_id"]),
                email=user_doc["email"],
                username=user_doc["username"],
                full_name=user_doc.get("full_name"),
                created_at=user_doc["created_at"],
                updated_at=user_doc.get("updated_at")
            )
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None


# Global instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
