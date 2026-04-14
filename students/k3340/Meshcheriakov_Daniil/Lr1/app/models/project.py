from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Статусы: open, in_progress, completed, cancelled
    status = Column(String(50), default="open", nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deadline = Column(DateTime(timezone=True), nullable=True)

    # many-to-one: проект принадлежит одному пользователю
    owner = relationship("User", back_populates="owned_projects")

    # one-to-many: у проекта может быть много команд
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")

    # many-to-many: проект требует навыки (через ProjectSkill)
    required_skills = relationship("ProjectSkill", back_populates="project", cascade="all, delete-orphan")
