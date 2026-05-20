from fastapi import FastAPI

from app.routers import auth, parser, projects, skills, teams, users

app = FastAPI(
    title="TeamFinder API",
    description="Платформа для поиска людей в команду. Lr3: + парсинг через отдельный сервис и Celery.",
    version="3.0.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(skills.router)
app.include_router(projects.router)
app.include_router(teams.router)
app.include_router(parser.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {"message": "Welcome to TeamFinder API", "docs": "/docs", "redoc": "/redoc"}
