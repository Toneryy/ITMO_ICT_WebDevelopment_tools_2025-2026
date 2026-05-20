from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from app.db import save_skill
from app.parser import fetch_and_extract

app = FastAPI(
    title="TeamFinder Parser",
    description="Отдельный сервис парсинга. Загружает страницу, извлекает заголовок и описание, пишет в таблицу `skills`.",
    version="1.0.0",
)


class ParseRequest(BaseModel):
    url: HttpUrl
    category: str = "programming"


class ParseResponse(BaseModel):
    title: str
    category: str
    created: bool


@app.get("/", tags=["root"])
def root() -> dict:
    return {"service": "parser", "docs": "/docs"}


@app.get("/health", tags=["root"])
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse, tags=["parser"])
def parse(payload: ParseRequest) -> ParseResponse:
    try:
        title, description = fetch_and_extract(str(payload.url))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch/parse: {exc}")

    try:
        created = save_skill(title, payload.category, description)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB error: {exc}")

    return ParseResponse(title=title, category=payload.category, created=created)
