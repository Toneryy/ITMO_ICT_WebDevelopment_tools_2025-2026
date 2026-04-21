"""
Общие утилиты для работы с базой данных Lr1 (skills table).
Каждый поток/процесс создаёт собственный движок SQLAlchemy,
чтобы избежать конфликтов соединений.
"""

import os
from sqlalchemy import Column, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:superuser@127.0.0.1:5432/teamfinder_db",
)


class Base(DeclarativeBase):
    pass


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


def make_engine():
    """Создаёт новый движок. Вызывать в каждом процессе/потоке отдельно."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def save_skill(engine, name: str, category: str, description: str) -> bool:
    """Сохраняет навык в БД. Возвращает True если запись создана, False если уже есть."""
    with Session(engine) as session:
        exists = session.query(Skill).filter(Skill.name == name).first()
        if exists:
            return False
        skill = Skill(name=name, category=category, description=description[:500] if description else "")
        session.add(skill)
        session.commit()
        return True
