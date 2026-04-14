from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    # Категория: programming, design, management, marketing, devops и т.д.
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # many-to-many: навык — пользователи (через UserSkill)
    user_skills = relationship("UserSkill", back_populates="skill")

    # many-to-many: навык — проекты (через ProjectSkill)
    project_requirements = relationship("ProjectSkill", back_populates="skill")
