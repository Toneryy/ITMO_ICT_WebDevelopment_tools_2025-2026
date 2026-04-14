from pydantic import BaseModel
from datetime import datetime
from app.schemas.skill import ProjectSkillRead, ProjectSkillCreate  # noqa: F401


class ProjectBase(BaseModel):
    title: str
    description: str | None = None
    # open, in_progress, completed, cancelled
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


# GET /projects/{id} — с вложенными требованиями к навыкам (many-to-many)
class ProjectWithDetails(ProjectRead):
    required_skills: list[ProjectSkillRead] = []

    class Config:
        from_attributes = True
