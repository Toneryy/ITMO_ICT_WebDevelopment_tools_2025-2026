from pydantic import BaseModel


class SkillBase(BaseModel):
    name: str
    category: str
    description: str | None = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None


class SkillRead(SkillBase):
    id: int

    class Config:
        from_attributes = True


# Схема для ответа: навык пользователя с уровнем владения
class UserSkillRead(BaseModel):
    skill: SkillRead
    proficiency_level: str

    class Config:
        from_attributes = True


class UserSkillCreate(BaseModel):
    skill_id: int
    # beginner, intermediate, expert
    proficiency_level: str


# Схема для ответа: требуемый навык проекта
class ProjectSkillRead(BaseModel):
    skill: SkillRead
    required_level: str

    class Config:
        from_attributes = True


class ProjectSkillCreate(BaseModel):
    skill_id: int
    # beginner, intermediate, expert
    required_level: str
