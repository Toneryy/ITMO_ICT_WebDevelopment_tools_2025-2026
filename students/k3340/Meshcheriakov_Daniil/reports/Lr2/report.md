# Лабораторная работа 2. Потоки. Процессы. Асинхронность.

## Цель работы

Понять отличия между потоками и процессами, а также освоить асинхронное программирование в Python на практических задачах.

---

## Теоретическая часть

### GIL (Global Interpreter Lock)

CPython содержит глобальную блокировку интерпретатора (GIL), которая гарантирует, что в любой момент времени только один поток выполняет байт-код Python. Это упрощает управление памятью, но ограничивает параллелизм для CPU-bound задач.

| Тип задачи | Threading | Multiprocessing | AsyncIO |
|------------|-----------|-----------------|---------|
| CPU-bound  | Нет ускорения (GIL) | Реальный параллелизм | Нет ускорения |
| I/O-bound  | Ускорение есть | Ускорение есть (с оверхедом) | Лучший вариант |

### threading

- Потоки существуют в рамках одного процесса и разделяют память.
- GIL не позволяет двум потокам одновременно исполнять Python-код.
- При блокирующих I/O операциях GIL **освобождается**, поэтому для сетевых запросов потоки эффективны.
- Синхронизация через `threading.Lock`, `Queue`, `Event`.

### multiprocessing

- Каждый процесс — отдельный интерпретатор Python с независимой памятью.
- GIL не является проблемой: каждый процесс имеет свой GIL.
- Данные между процессами передаются через IPC (pickle-сериализация).
- Overhead на создание процессов выше, чем для потоков.
- Подходит для CPU-bound задач: числодробилки, обработка изображений и т. д.

### asyncio

- Однопоточная модель параллелизма на основе кооперативной многозадачности.
- `async/await` — синтаксический сахар над корутинами.
- `asyncio.gather()` запускает несколько корутин «одновременно» — event loop переключается при каждом `await`.
- Для CPU-bound задач нужен `asyncio.to_thread()` (ThreadPoolExecutor) или `loop.run_in_executor()` с ProcessPoolExecutor.
- Лучший выбор для высоконагруженных I/O-bound приложений (web-серверы, чаты, парсеры).

---

## Задача 1. Сумма чисел от 1 до 10 000 000 000 000

### Описание

Каждая программа разбивает диапазон `[1, N]` на `NUM_TASKS = 8` равных частей.

**Формула арифметической прогрессии** для чанка `[start, end]`:

```
sum = (end - start + 1) * (start + end) // 2
```

Это позволяет мгновенно получить точный ответ для N = 10¹³. Для реального замера времени также используется `N_BENCH = 100_000_000` с итерацией через `range()`.

### Результаты (пример замеров, 8 ядер)

#### Формула (N = 10 000 000 000 000)

| Подход | Время (сек) | Ускорение |
|--------|------------|-----------|
| Threading | ~0.0002 | — |
| Multiprocessing | ~0.05 | — |
| AsyncIO | ~0.0002 | — |

> Формула работает за O(1) в каждом чанке, поэтому все варианты мгновенны. Overhead multiprocessing на создание процессов заметен.

#### Реальная итерация (N = 100 000 000)

| Подход | Время (сек) | Ускорение |
|--------|------------|-----------|
| Sequential | ~8.0 | 1x |
| Threading (8 потоков) | ~8.2 | ~1x (GIL) |
| Multiprocessing (8 процессов) | ~1.3 | ~6x |
| AsyncIO + to_thread (8 потоков) | ~8.1 | ~1x (GIL) |
| AsyncIO + ProcessPoolExecutor | ~1.4 | ~5.7x |

### Выводы по Задаче 1

- **Threading** при CPU-bound задачах не даёт ускорения из-за GIL. Потоки работают последовательно по байт-коду.
- **Multiprocessing** обходит GIL и даёт линейное ускорение до числа физических ядер.
- **AsyncIO** без executor — полностью последовательный для CPU-bound. С ProcessPoolExecutor показывает результат, аналогичный multiprocessing.
- Формула `n*(n+1)//2` по чанкам — правильный способ «параллельного» вычисления суммы: каждый worker делает O(1) работы.

---

## Задача 2. Параллельный парсинг веб-страниц

### Описание

Программы парсят 12 страниц Wikipedia о технологиях (Python, JavaScript, Docker, PostgreSQL и др.) и сохраняют данные в таблицу `skills` базы данных из Лабораторной работы 1.

**Структура данных:**
- `name` — заголовок страницы (H1)
- `category` — категория: `programming`, `devops`, `databases`
- `description` — первый информативный абзац страницы

**URL-список:**

| URL | Категория |
|-----|-----------|
| Python (programming language) | programming |
| JavaScript | programming |
| TypeScript | programming |
| Go (programming language) | programming |
| Rust (programming language) | programming |
| Docker (software) | devops |
| Kubernetes | devops |
| PostgreSQL | databases |
| Redis | databases |
| React (JavaScript library) | programming |
| Vue.js | programming |
| Django (web framework) | programming |

### Реализация Threading

```python
def parse_and_save(url, category, engine):
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("h1").get_text(strip=True)
    # ... извлечение описания ...
    save_skill(engine, title, category, description)
```

- Один shared engine на все потоки (SQLAlchemy thread-safe по умолчанию).
- `threading.Lock` для синхронизации вывода в консоль.
- Все потоки запускаются сразу, затем `join()`.

### Реализация Multiprocessing

```python
def parse_and_save(args):
    url, category = args
    engine = make_engine()  # создаём ВНУТРИ процесса!
    # ... парсинг ...
    save_skill(engine, title, category, description)
    engine.dispose()
```

- Ключевая особенность: **engine создаётся внутри каждого процесса**, т.к. SQLAlchemy connection pool нельзя передавать между процессами через pickle.
- `mp.Pool.map()` автоматически распределяет задачи.

### Реализация AsyncIO

```python
async def parse_and_save(session, pool, url, category):
    async with session.get(url) as resp:
        html = await resp.text()
    # ... парсинг (синхронный BeautifulSoup) ...
    await save_skill_async(pool, title, category, description)
```

- `aiohttp.ClientSession` для асинхронных HTTP-запросов.
- `asyncpg.Pool` для асинхронной записи в PostgreSQL.
- `asyncio.gather()` запускает все 12 корутин конкурентно.
- BeautifulSoup работает синхронно, но его время незначительно по сравнению с I/O.

### Результаты замеров (пример, 12 URL, ~150 мс на запрос)

| Подход | Время (сек) | Параллельных задач |
|--------|------------|-------------------|
| Sequential | ~1.8 | 1 |
| Threading | ~0.25 | 12 |
| Multiprocessing | ~0.55 | 8–12 |
| AsyncIO | ~0.20 | 12 |

### Выводы по Задаче 2

- **Threading** хорошо подходит для I/O-bound задач: GIL освобождается во время ожидания HTTP-ответа, поэтому потоки реально выполняются параллельно.
- **Multiprocessing** работает, но медленнее для I/O-bound из-за overhead создания процессов и сериализации данных.
- **AsyncIO** — оптимальный подход для парсинга: минимальный overhead, масштабируется до сотен одновременных запросов без создания потоков/процессов.

---

## Общие выводы

| Характеристика | Threading | Multiprocessing | AsyncIO |
|----------------|-----------|-----------------|---------|
| CPU-bound задачи | Плохо (GIL) | Отлично | Плохо (нужен executor) |
| I/O-bound задачи | Хорошо | Средне | Отлично |
| Разделяемая память | Да | Нет (IPC) | Да (одиночный поток) |
| Overhead | Низкий | Высокий | Минимальный |
| Сложность кода | Средняя | Средняя | Высокая (asyncio) |
| Масштабируемость | Ограничена GIL | По числу ядер | Очень высокая |

**Практические рекомендации:**
- Парсинг, API-запросы, работа с файлами → **AsyncIO** (при большом масштабе) или **Threading** (при простом коде).
- Числодробилки, ML-обработка, тяжёлые вычисления → **Multiprocessing**.
- Смешанные задачи → **AsyncIO + ProcessPoolExecutor** для CPU частей.
