from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get(
    "/",
    response_model=list[SkillRead],
    summary="Список всех навыков",
)
def get_skills(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Skill]:
    return db.query(Skill).offset(skip).limit(limit).all()


@router.post(
    "/",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать навык",
)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Skill:
    if db.query(Skill).filter(Skill.name == skill_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill with this name already exists",
        )
    skill = Skill(**skill_data.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get(
    "/{skill_id}",
    response_model=SkillRead,
    summary="Получить навык по ID",
)
def get_skill(skill_id: int, db: Session = Depends(get_db)) -> Skill:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.put(
    "/{skill_id}",
    response_model=SkillRead,
    summary="Обновить навык",
)
def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Skill:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    for field, value in skill_data.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить навык",
)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    db.delete(skill)
    db.commit()
