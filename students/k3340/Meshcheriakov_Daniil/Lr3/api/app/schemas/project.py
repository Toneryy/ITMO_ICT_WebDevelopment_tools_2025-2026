from pydantic import BaseModel
from datetime import datetime
from app.schemas.skill import ProjectSkillRead, ProjectSkillCreate  # noqa: F401


class ProjectBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "open"
    deadline: datetime | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    deadline: datetime | None = None


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectWithDetails(ProjectRead):
    required_skills: list[ProjectSkillRead] = []

    class Config:
        from_attributes = True
