from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.associations import ProjectSkill
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectWithDetails
from app.schemas.skill import ProjectSkillCreate, ProjectSkillRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "/",
    response_model=list[ProjectRead],
    summary="Список проектов (с фильтром по статусу)",
)
def get_projects(
    skip: int = 0,
    limit: int = 100,
    project_status: Optional[str] = Query(None, alias="status", description="open | in_progress | completed | cancelled"),
    db: Session = Depends(get_db),
) -> list[Project]:
    query = db.query(Project)
    if project_status:
        query = query.filter(Project.status == project_status)
    return query.offset(skip).limit(limit).all()


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать проект",
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = Project(**project_data.model_dump(), owner_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get(
    "/search",
    response_model=list[ProjectWithDetails],
    summary="Поиск проектов по навыку и статусу",
)
def search_projects(
    skill_id: Optional[int] = Query(None, description="ID требуемого навыка"),
    project_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> list[Project]:
    query = db.query(Project)
    if skill_id is not None:
        query = query.join(Project.required_skills).filter(ProjectSkill.skill_id == skill_id)
    if project_status:
        query = query.filter(Project.status == project_status)
    return query.all()


@router.get(
    "/{project_id}",
    response_model=ProjectWithDetails,
    summary="Детали проекта с требуемыми навыками",
)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Обновить проект (только для владельца)",
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this project")
    for field, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить проект (только для владельца)",
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this project")
    db.delete(project)
    db.commit()


# --- Управление требованиями к навыкам проекта ---

@router.post(
    "/{project_id}/skills",
    response_model=ProjectSkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить требуемый навык к проекту",
)
def add_project_skill(
    project_id: int,
    skill_data: ProjectSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectSkill:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    existing = db.query(ProjectSkill).filter(
        ProjectSkill.project_id == project_id,
        ProjectSkill.skill_id == skill_data.skill_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill already required for this project")
    project_skill = ProjectSkill(
        project_id=project_id,
        skill_id=skill_data.skill_id,
        required_level=skill_data.required_level,
    )
    db.add(project_skill)
    db.commit()
    db.refresh(project_skill)
    return project_skill


@router.delete(
    "/{project_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить требуемый навык из проекта",
)
def remove_project_skill(
    project_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    project_skill = db.query(ProjectSkill).filter(
        ProjectSkill.project_id == project_id,
        ProjectSkill.skill_id == skill_id,
    ).first()
    if not project_skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill requirement not found")
    db.delete(project_skill)
    db.commit()
