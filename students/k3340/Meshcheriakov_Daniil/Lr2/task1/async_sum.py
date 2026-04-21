"""
Задача 1 — AsyncIO
Вычисление суммы чисел от 1 до N с использованием asyncio.

AsyncIO предназначен для I/O-bound задач, а не CPU-bound.
Для CPU-bound работы используется asyncio.to_thread() — каждая
«корутина» запускает вычисление в отдельном потоке через
ThreadPoolExecutor. Из-за GIL параллелизма это не даёт, но
демонстрирует паттерн async/await для CPU-задач.

Для честного CPU-параллелизма с asyncio нужно использовать
loop.run_in_executor с ProcessPoolExecutor.
"""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor

N = 10_000_000_000_000
N_BENCH = 100_000_000
NUM_TASKS = 8


def calculate_sum(start: int, end: int) -> int:
    """Формула арифметической прогрессии (запускается вне event loop)."""
    count = end - start + 1
    return count * (start + end) // 2


def calculate_sum_iter(start: int, end: int) -> int:
    """Реальная итерация (запускается вне event loop)."""
    return sum(range(start, end + 1))


def build_chunks(n: int, num_tasks: int) -> list[tuple[int, int]]:
    chunk = n // num_tasks
    chunks = []
    for i in range(num_tasks):
        start = i * chunk + 1
        end = (i + 1) * chunk if i < num_tasks - 1 else n
        chunks.append((start, end))
    return chunks


async def async_calculate(start: int, end: int, use_iter: bool = False) -> int:
    """Запускает CPU-bound функцию в thread pool, не блокируя event loop."""
    fn = calculate_sum_iter if use_iter else calculate_sum
    return await asyncio.to_thread(fn, start, end)


async def run_with_threads(n: int, use_iter: bool = False) -> tuple[int, float]:
    """asyncio + ThreadPoolExecutor (демонстрационный, GIL ограничивает)."""
    chunks = build_chunks(n, NUM_TASKS)
    t0 = time.perf_counter()
    tasks = [async_calculate(s, e, use_iter) for s, e in chunks]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - t0
    return sum(results), elapsed


async def run_with_processes(n: int) -> tuple[int, float]:
    """asyncio + ProcessPoolExecutor — реальный параллелизм для CPU-задач."""
    chunks = build_chunks(n, NUM_TASKS)
    loop = asyncio.get_running_loop()

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=NUM_TASKS) as pool:
        futures = [
            loop.run_in_executor(pool, calculate_sum_iter, s, e)
            for s, e in chunks
        ]
        results = await asyncio.gather(*futures)
    elapsed = time.perf_counter() - t0
    return sum(results), elapsed


async def main() -> None:
    print("=" * 55)
    print("AsyncIO — сумма от 1 до N")
    print("=" * 55)

    # 1. Формула для N = 10^13 (через to_thread)
    total, elapsed = await run_with_threads(N, use_iter=False)
    expected = N * (N + 1) // 2
    print(f"\n[Формула + to_thread] N = {N:,}")
    print(f"  Корутин:  {NUM_TASKS}")
    print(f"  Сумма:    {total:,}")
    print(f"  Верно:    {total == expected}")
    print(f"  Время:    {elapsed:.6f} сек")

    # 2. Итерация — asyncio + threads (GIL ограничивает)
    total_t, elapsed_t = await run_with_threads(N_BENCH, use_iter=True)
    expected_b = N_BENCH * (N_BENCH + 1) // 2
    print(f"\n[Итерация + to_thread] N = {N_BENCH:,}")
    print(f"  Верно:    {total_t == expected_b}")
    print(f"  Время:    {elapsed_t:.4f} сек  (GIL: почти последовательно)")

    # 3. Итерация — asyncio + ProcessPoolExecutor (истинный параллелизм)
    total_p, elapsed_p = await run_with_processes(N_BENCH)
    print(f"\n[Итерация + ProcessPoolExecutor] N = {N_BENCH:,}")
    print(f"  Верно:    {total_p == expected_b}")
    print(f"  Время:    {elapsed_p:.4f} сек  (реальный параллелизм)")

    print()
    print("Вывод: для CPU-bound нужен ProcessPoolExecutor, а не to_thread.")
    print("Чистый async/await без executor = последовательное выполнение.")


if __name__ == "__main__":
    asyncio.run(main())
