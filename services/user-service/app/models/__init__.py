"""Model imports and base configuration."""
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole

# Import Base from one of the models (they should all use the same Base)
from app.models.user import Base

__all__ = ["User", "Role", "UserRole", "Base"]
