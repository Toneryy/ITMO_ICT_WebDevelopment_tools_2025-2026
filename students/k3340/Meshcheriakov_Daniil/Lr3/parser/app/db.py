import os

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:superuser@db:5432/teamfinder_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Skill(Base):
    """Та же таблица, что в api-сервисе. ORM-модель локальная, чтобы не тащить
    зависимости api в parser. Миграциями владеет api."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


def save_skill(name: str, category: str, description: str) -> bool:
    """Сохраняет навык. Возвращает True если создан, False если уже существовал."""
    with Session(engine) as session:
        existing = session.query(Skill).filter(Skill.name == name).first()
        if existing:
            return False
        skill = Skill(
            name=name,
            category=category,
            description=(description or "")[:500],
        )
        session.add(skill)
        session.commit()
        return True
