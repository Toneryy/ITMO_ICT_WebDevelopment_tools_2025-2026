from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # one-to-many: один пользователь — много проектов (где он владелец)
    owned_projects = relationship("Project", back_populates="owner")

    # many-to-many: пользователь — навыки (через UserSkill)
    skills = relationship("UserSkill", back_populates="user")

    # many-to-many: пользователь — команды (через TeamMember)
    team_memberships = relationship("TeamMember", back_populates="user")
