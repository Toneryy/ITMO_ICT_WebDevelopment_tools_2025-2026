"""
Задача 2 — Multiprocessing
Параллельный парсинг Wikipedia-страниц о технологиях
и сохранение в таблицу skills базы данных Lr1.

Каждый процесс создаёт собственное соединение с БД —
SQLAlchemy engine нельзя передавать между процессами.
Для I/O-bound задач overhead на создание процессов заметен,
поэтому multiprocessing чаще всего медленнее threading/async
при парсинге, но зато без GIL для любой CPU-обработки данных.
"""

import multiprocessing as mp
import time

import requests
from bs4 import BeautifulSoup

from db import DATABASE_URL, make_engine, save_skill

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


def parse_and_save(args: tuple[str, str]) -> str:
    """
    Точка входа для каждого рабочего процесса.
    Возвращает строку-результат для вывода в главном процессе.
    """
    url, category = args
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.find("h1").get_text(strip=True)

        content_div = soup.find("div", class_="mw-parser-output")
        description = ""
        if content_div:
            for p in content_div.find_all("p", recursive=False):
                text = p.get_text(strip=True)
                if len(text) > 50:
                    description = text
                    break

        # Создаём движок внутри процесса (нельзя передавать между процессами)
        engine = make_engine()
        created = save_skill(engine, title, category, description)
        engine.dispose()

        pid = mp.current_process().pid
        status = "создан" if created else "уже существует"
        return f"[PID {pid}] {title!r:40s} → {status}"

    except Exception as exc:
        return f"[ОШИБКА] {url}: {exc}"


def main() -> None:
    print("=" * 60)
    print("Multiprocessing — парсинг веб-страниц")
    print("=" * 60)

    t0 = time.perf_counter()

    with mp.Pool(processes=min(len(URLS), mp.cpu_count())) as pool:
        results = pool.map(parse_and_save, URLS)

    elapsed = time.perf_counter() - t0

    for line in results:
        print(line)

    print(f"\nПроцессов: {min(len(URLS), mp.cpu_count())}")
    print(f"Время:     {elapsed:.3f} сек")


if __name__ == "__main__":
    main()
