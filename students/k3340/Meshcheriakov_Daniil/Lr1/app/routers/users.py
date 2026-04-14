from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.associations import UserSkill
from app.models.user import User
from app.schemas.skill import UserSkillCreate, UserSkillRead
from app.schemas.user import UserRead, UserUpdate, UserWithSkills

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=list[UserRead],
    summary="Список всех пользователей",
)
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


@router.get(
    "/me",
    response_model=UserWithSkills,
    summary="Информация о текущем пользователе",
)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put(
    "/me",
    response_model=UserRead,
    summary="Обновление профиля текущего пользователя",
)
def update_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get(
    "/search",
    response_model=list[UserWithSkills],
    summary="Поиск пользователей по навыку и уровню",
)
def search_users(
    skill_id: Optional[int] = Query(None, description="ID навыка"),
    proficiency_level: Optional[str] = Query(None, description="beginner | intermediate | expert"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[User]:
    query = db.query(User)
    if skill_id is not None or proficiency_level is not None:
        query = query.join(User.skills)
        if skill_id is not None:
            query = query.filter(UserSkill.skill_id == skill_id)
        if proficiency_level is not None:
            query = query.filter(UserSkill.proficiency_level == proficiency_level)
    return query.all()


@router.get(
    "/{user_id}",
    response_model=UserWithSkills,
    summary="Профиль пользователя с навыками",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# --- Управление навыками текущего пользователя ---

@router.post(
    "/me/skills",
    response_model=UserSkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить навык в профиль",
)
def add_my_skill(
    skill_data: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSkill:
    existing = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_data.skill_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill already added to your profile",
        )
    user_skill = UserSkill(
        user_id=current_user.id,
        skill_id=skill_data.skill_id,
        proficiency_level=skill_data.proficiency_level,
    )
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return user_skill


@router.delete(
    "/me/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить навык из профиля",
)
def remove_my_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_id,
    ).first()
    if not user_skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found in your profile")
    db.delete(user_skill)
    db.commit()
