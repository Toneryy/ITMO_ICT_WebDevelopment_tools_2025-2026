"""
Задача 2 — Threading
Параллельный парсинг Wikipedia-страниц о технологиях
и сохранение в таблицу skills базы данных Lr1.

Threading подходит для I/O-bound задач (сетевые запросы):
GIL освобождается во время ожидания ответа от сервера,
поэтому потоки реально выполняются параллельно.
"""

import threading
import time

import requests
from bs4 import BeautifulSoup

from db import make_engine, save_skill

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

_lock = threading.Lock()


def parse_and_save(url: str, category: str, engine) -> None:
    """Загружает страницу, парсит заголовок и первый абзац, сохраняет в БД."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.find("h1").get_text(strip=True)

        # Первый непустой абзац основного контента
        content_div = soup.find("div", class_="mw-parser-output")
        description = ""
        if content_div:
            for p in content_div.find_all("p", recursive=False):
                text = p.get_text(strip=True)
                if len(text) > 50:
                    description = text
                    break

        created = save_skill(engine, title, category, description)
        status = "создан" if created else "уже существует"

        with _lock:
            thread = threading.current_thread().name
            print(f"[{thread}] {title!r:40s} → {status}")

    except Exception as exc:
        with _lock:
            print(f"[ОШИБКА] {url}: {exc}")


def main() -> None:
    print("=" * 60)
    print("Threading — парсинг веб-страниц")
    print("=" * 60)

    engine = make_engine()
    threads: list[threading.Thread] = []

    t0 = time.perf_counter()

    for url, category in URLS:
        t = threading.Thread(
            target=parse_and_save,
            args=(url, category, engine),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - t0
    print(f"\nПотоков: {len(URLS)}")
    print(f"Время:   {elapsed:.3f} сек")


if __name__ == "__main__":
    main()
