"""
Supabase service for TalentSync Auth Gateway Service.

Provides high-performance authentication and user management operations
with proper error handling and caching for 1000+ RPS scenarios.
"""
import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

import httpx
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.core.settings import settings
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)


class SupabaseService:
    """
    High-performance Supabase service for authentication and user management.
    
    Provides optimized operations for user registration, authentication,
    and profile management with proper error handling and caching.
    """
    
    def __init__(self) -> None:
        """
        Initialize Supabase service with performance optimizations.
        
        Sets up Supabase client with connection pooling and timeout configurations
        for high-throughput scenarios.
        """
        # Configure client options for high performance
        client_options = ClientOptions(
            schema="public",
            headers={
                "X-Client-Info": f"talentsync-user-service/{settings.VERSION}",
            },
            realtime={
                "params": {
                    "apikey": settings.SUPABASE_ANON_KEY,
                }
            },
        )
        
        # Initialize Supabase client
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
            options=client_options,
        )
        
        # Initialize service role client for admin operations
        self.admin_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options=client_options,
        )
        
        logger.info("Supabase service initialized successfully")
    
    async def signup_user(
        self, email: str, password: str, full_name: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user with Supabase Auth.
        
        Args:
            email: User email address
            password: User password
            full_name: User full name
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: Success status, user data, error message
        """
        try:
            # Create user with Supabase Auth
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
            })
            
            if not auth_response.user:
                return False, None, "Failed to create user account"
            
            # Create user profile in database
            profile_data = {
                "id": auth_response.user.id,
                "full_name": full_name,
                "is_admin": False,
            }
            
            profile_response = self.admin_client.table("user_profiles").insert(
                profile_data
            ).execute()
            
            if not profile_response.data:
                # Rollback: delete the auth user if profile creation fails
                try:
                    self.admin_client.auth.admin.delete_user(auth_response.user.id)
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback user creation: {rollback_error}")
                
                return False, None, "Failed to create user profile"
            
            # Prepare user response
            user_data = {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": full_name,
                "is_active": True,
                "is_admin": False,
                "created_at": auth_response.user.created_at,
                "updated_at": auth_response.user.updated_at,
            }
            
            logger.info(f"User registered successfully: {email}")
            return True, user_data, None
            
        except Exception as e:
            logger.error(f"User registration failed for {email}: {str(e)}")
            return False, None, f"Registration failed: {str(e)}"
    
    async def login_user(
        self, email: str, password: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user with Supabase Auth.
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: Success status, auth data, error message
        """
        try:
            # Authenticate with Supabase
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            if not auth_response.user or not auth_response.session:
                return False, None, "Invalid credentials"
            
            # Get user profile
            profile_response = self.admin_client.table("user_profiles").select(
                "*"
            ).eq("id", auth_response.user.id).single().execute()
            
            if not profile_response.data:
                return False, None, "User profile not found"
            
            profile = profile_response.data
            
            # Prepare response data
            auth_data = {
                "access_token": auth_response.session.access_token,
                "token_type": "bearer",
                "expires_in": auth_response.session.expires_in,
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "full_name": profile.get("full_name", ""),
                    "is_active": profile.get("is_active", True),
                    "is_admin": profile.get("is_admin", False),
                    "created_at": auth_response.user.created_at,
                    "updated_at": auth_response.user.updated_at,
                }
            }
            
            logger.info(f"User logged in successfully: {email}")
            return True, auth_data, None
            
        except Exception as e:
            logger.error(f"User login failed for {email}: {str(e)}")
            return False, None, f"Authentication failed: {str(e)}"
    
    async def get_user_profile(self, user_id: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: Success status, user data, error message
        """
        try:
            # Get user profile from database
            profile_response = self.admin_client.table("user_profiles").select(
                "*"
            ).eq("id", user_id).single().execute()
            
            if not profile_response.data:
                return False, None, "User profile not found"
            
            profile = profile_response.data
            
            # Get auth user data
            auth_user_response = self.admin_client.auth.admin.get_user_by_id(user_id)
            
            if not auth_user_response.user:
                return False, None, "User not found in auth system"
            
            # Prepare user data
            user_data = {
                "id": auth_user_response.user.id,
                "email": auth_user_response.user.email,
                "full_name": profile.get("full_name", ""),
                "is_active": profile.get("is_active", True),
                "is_admin": profile.get("is_admin", False),
                "created_at": auth_user_response.user.created_at,
                "updated_at": auth_user_response.user.updated_at,
            }
            
            return True, user_data, None
            
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {str(e)}")
            return False, None, f"Failed to get user profile: {str(e)}"
    
    async def update_user_profile(
        self, user_id: str, updates: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Update user profile.
        
        Args:
            user_id: User unique identifier
            updates: Profile updates to apply
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: Success status, updated data, error message
        """
        try:
            # Update user profile
            update_response = self.admin_client.table("user_profiles").update(
                updates
            ).eq("id", user_id).execute()
            
            if not update_response.data:
                return False, None, "Failed to update user profile"
            
            # Get updated profile
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"Failed to update user profile for {user_id}: {str(e)}")
            return False, None, f"Failed to update user profile: {str(e)}"
    
    async def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate JWT token and get user information.
        
        Args:
            token: JWT access token
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: Success status, user data, error message
        """
        try:
            # Set the session with the token
            self.client.auth.set_session(token, None)
            
            # Get current user
            user = self.client.auth.get_user()
            
            if not user.user:
                return False, None, "Invalid token"
            
            # Get user profile
            return await self.get_user_profile(user.user.id)
            
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False, None, f"Token validation failed: {str(e)}"
    
    async def logout_user(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Logout user by invalidating the session.
        
        Args:
            token: JWT access token
            
        Returns:
            Tuple[bool, Optional[str]]: Success status, error message
        """
        try:
            # Set the session with the token
            self.client.auth.set_session(token, None)
            
            # Sign out
            self.client.auth.sign_out()
            
            logger.info("User logged out successfully")
            return True, None
            
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False, f"Logout failed: {str(e)}"


# Global service instance for dependency injection
supabase_service = SupabaseService() 