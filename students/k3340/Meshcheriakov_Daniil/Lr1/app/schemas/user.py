from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.schemas.skill import UserSkillRead


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str | None = None
    bio: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    bio: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# GET /users/{id} — с вложенными навыками (many-to-many)
class UserWithSkills(UserRead):
    skills: list[UserSkillRead] = []

    class Config:
        from_attributes = True
