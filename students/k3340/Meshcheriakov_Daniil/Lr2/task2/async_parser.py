"""
Задача 2 — AsyncIO
Параллельный парсинг Wikipedia-страниц о технологиях
и сохранение в таблицу skills базы данных Lr1.

aiohttp делает асинхронные HTTP-запросы без блокировки event loop.
asyncpg используется для асинхронной записи в PostgreSQL.
asyncio.gather() запускает все корутины «одновременно»:
event loop переключается между ними при каждом await.
"""

import asyncio
import os
import time

import aiohttp
import asyncpg
from bs4 import BeautifulSoup

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:superuser@127.0.0.1:5432/teamfinder_db",
)

# asyncpg использует другой формат DSN (без драйвера)
def _asyncpg_dsn() -> str:
    return DATABASE_URL.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+asyncpg://", "postgresql://"
    )


URLS: list[tuple[str, str]] = [
    ("https://en.wikipedia.org/wiki/Python_(programming_language)", "programming"),
    ("https://en.wikipedia.org/wiki/JavaScript", "programming"),
    ("https://en.wikipedia.org/wiki/TypeScript", "programming"),
    ("https://en.wikipedia.org/wiki/Go_(programming_language)", "programming"),
    ("https://en.wikipedia.org/wiki/Rust_(programming_language)", "programming"),
    ("https://en.wikipedia.org/wiki/Docker_(software)", "devops"),
    ("https://en.wikipedia.org/wiki/Kubernetes", "devops"),
    ("https://en.wikipedia.org/wiki/PostgreSQL", "databases"),
    ("https://en.wikipedia.org/wiki/Redis", "databases"),
    ("https://en.wikipedia.org/wiki/React_(JavaScript_library)", "programming"),
    ("https://en.wikipedia.org/wiki/Vue.js", "programming"),
    ("https://en.wikipedia.org/wiki/Django_(web_framework)", "programming"),
]


async def save_skill_async(pool: asyncpg.Pool, name: str, category: str, description: str) -> bool:
    """Асинхронно сохраняет навык через asyncpg. Возвращает True если создан."""
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM skills WHERE name = $1", name)
        if existing:
            return False
        await conn.execute(
            "INSERT INTO skills (name, category, description) VALUES ($1, $2, $3)",
            name,
            category,
            description[:500] if description else "",
        )
        return True


async def parse_and_save(
    session: aiohttp.ClientSession,
    pool: asyncpg.Pool,
    url: str,
    category: str,
) -> None:
    """Асинхронно загружает страницу, парсит и сохраняет в БД."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1").get_text(strip=True)

        content_div = soup.find("div", class_="mw-parser-output")
        description = ""
        if content_div:
            for p in content_div.find_all("p", recursive=False):
                text = p.get_text(strip=True)
                if len(text) > 50:
                    description = text
                    break

        created = await save_skill_async(pool, title, category, description)
        status = "создан" if created else "уже существует"
        print(f"[async] {title!r:40s} → {status}")

    except Exception as exc:
        print(f"[ОШИБКА] {url}: {exc}")


async def main() -> None:
    print("=" * 60)
    print("AsyncIO — парсинг веб-страниц")
    print("=" * 60)

    pool = await asyncpg.create_pool(dsn=_asyncpg_dsn(), min_size=2, max_size=10)
    headers = {"User-Agent": "Mozilla/5.0"}

    t0 = time.perf_counter()

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [
            parse_and_save(session, pool, url, category)
            for url, category in URLS
        ]
        await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - t0
    await pool.close()

    print(f"\nКорутин: {len(URLS)}")
    print(f"Время:   {elapsed:.3f} сек")


if __name__ == "__main__":
    asyncio.run(main())
