# Импортируем все модели, чтобы Alembic и SQLAlchemy знали обо всех таблицах
from app.models.user import User
from app.models.skill import Skill
from app.models.project import Project
from app.models.team import Team
from app.models.associations import UserSkill, TeamMember, ProjectSkill

__all__ = [
    "User",
    "Skill",
    "Project",
    "Team",
    "UserSkill",
    "TeamMember",
    "ProjectSkill",
]
