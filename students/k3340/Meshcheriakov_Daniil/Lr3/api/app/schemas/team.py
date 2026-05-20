from pydantic import BaseModel
from datetime import datetime
from app.schemas.user import UserRead


class TeamMemberRead(BaseModel):
    user: UserRead
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamMemberCreate(BaseModel):
    user_id: int
    role: str


class TeamBase(BaseModel):
    name: str
    description: str | None = None


class TeamCreate(TeamBase):
    project_id: int


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TeamRead(TeamBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TeamWithMembers(TeamRead):
    members: list[TeamMemberRead] = []

    class Config:
        from_attributes = True
