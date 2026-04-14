@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === TeamFinder: установка зависимостей (если нужно) ===
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
  echo Не удалось вызвать "py -3". Поставь Python 3.10+ с python.org и отметь "Add to PATH", либо замени в этом файле py -3 на полный путь к python.exe
  pause
  exit /b 1
)

echo.
echo === Запуск API: http://127.0.0.1:8000/docs ===
echo Убедись, что PostgreSQL запущен и база teamfinder_db создана, миграции применены: alembic upgrade head
echo.

py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause
