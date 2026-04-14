from fastapi import FastAPI

from app.routers import auth, projects, skills, teams, users

app = FastAPI(
    title="TeamFinder API",
    description="Платформа для поиска людей в команду. Регистрация, профили, навыки, проекты и команды.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(skills.router)
app.include_router(projects.router)
app.include_router(teams.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {"message": "Welcome to TeamFinder API", "docs": "/docs", "redoc": "/redoc"}
