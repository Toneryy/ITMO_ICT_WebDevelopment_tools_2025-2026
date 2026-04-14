from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserSkill(Base):
    """
    Ассоциативная сущность: пользователь — навык.
    Поле proficiency_level характеризует связь (уровень владения навыком).
    Допустимые значения: beginner, intermediate, expert
    """
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    proficiency_level = Column(String(50), nullable=False)  # beginner / intermediate / expert

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")


class TeamMember(Base):
    """
    Ассоциативная сущность: участник команды.
    Поля role и joined_at характеризуют связь (роль и дата вступления).
    """
    __tablename__ = "team_members"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(100), nullable=False)  # developer, designer, manager, tester, devops, analyst...
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="team_memberships")
    team = relationship("Team", back_populates="members")


class ProjectSkill(Base):
    """
    Ассоциативная сущность: требования проекта к навыкам.
    Поле required_level характеризует связь (требуемый уровень навыка).
    """
    __tablename__ = "project_skills"

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    required_level = Column(String(50), nullable=False)  # beginner / intermediate / expert

    project = relationship("Project", back_populates="required_skills")
    skill = relationship("Skill", back_populates="project_requirements")
