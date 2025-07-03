"""Model imports and base configuration."""
from app.models.module import Module, DifficultyLevel, ModuleCategory
from app.models.question import Question
from app.models.followup_template import FollowUpTemplate
from app.models.session import Session, SessionStatus, SessionMode
from app.models.response import Response

# Import Base from one of the models (they should all use the same Base)
from app.models.module import Base

__all__ = [
    "Module", "Question", "FollowUpTemplate", "Session", "Response",
    "DifficultyLevel", "ModuleCategory", "SessionStatus", "SessionMode", 
    "Base"
]
