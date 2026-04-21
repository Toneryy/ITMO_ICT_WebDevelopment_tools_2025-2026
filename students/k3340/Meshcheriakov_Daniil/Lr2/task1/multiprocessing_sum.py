"""
Задача 1 — Multiprocessing
Вычисление суммы чисел от 1 до N с разбиением на NUM_WORKERS процессов.

Процессы обходят ограничение GIL: каждый процесс — отдельный
интерпретатор Python с независимой памятью. CPU-bound задачи
реально ускоряются пропорционально числу ядер.
"""

import multiprocessing as mp
import time

N = 10_000_000_000_000
N_BENCH = 100_000_000
NUM_WORKERS = 8


def calculate_sum(start: int, end: int) -> int:
    """Сумма через формулу арифметической прогрессии."""
    count = end - start + 1
    return count * (start + end) // 2


def calculate_sum_iter(start: int, end: int) -> int:
    """Сумма через реальную итерацию (для бенчмарка)."""
    return sum(range(start, end + 1))


def build_chunks(n: int, num_workers: int) -> list[tuple[int, int]]:
    chunk = n // num_workers
    chunks = []
    for i in range(num_workers):
        start = i * chunk + 1
        end = (i + 1) * chunk if i < num_workers - 1 else n
        chunks.append((start, end))
    return chunks


def run_parallel(n: int, use_iter: bool = False) -> tuple[int, float]:
    chunks = build_chunks(n, NUM_WORKERS)
    fn = calculate_sum_iter if use_iter else calculate_sum

    t0 = time.perf_counter()
    with mp.Pool(processes=NUM_WORKERS) as pool:
        results = pool.starmap(fn, chunks)
    elapsed = time.perf_counter() - t0

    return sum(results), elapsed


def run_sequential(n: int) -> tuple[int, float]:
    """Последовательное вычисление для сравнения."""
    t0 = time.perf_counter()
    total = sum(range(1, n + 1))
    elapsed = time.perf_counter() - t0
    return total, elapsed


def main() -> None:
    print("=" * 55)
    print("Multiprocessing — сумма от 1 до N")
    print("=" * 55)

    # 1. Формула для N = 10^13
    total, elapsed = run_parallel(N, use_iter=False)
    expected = N * (N + 1) // 2
    print(f"\n[Формула] N = {N:,}")
    print(f"  Сумма:    {total:,}")
    print(f"  Верно:    {total == expected}")
    print(f"  Время:    {elapsed:.6f} сек")

    # 2. Параллельная итерация vs последовательная для N_BENCH
    total_p, elapsed_p = run_parallel(N_BENCH, use_iter=True)
    total_s, elapsed_s = run_sequential(N_BENCH)
    expected_b = N_BENCH * (N_BENCH + 1) // 2

    print(f"\n[Итерация] N = {N_BENCH:,}  (бенчмарк)")
    print(f"  Процессов: {NUM_WORKERS}")
    print(f"  Верно:     {total_p == expected_b}")
    print(f"  Параллельно:     {elapsed_p:.4f} сек")
    print(f"  Последовательно: {elapsed_s:.4f} сек")
    if elapsed_p > 0:
        print(f"  Ускорение:       {elapsed_s / elapsed_p:.2f}x")
    print()
    print("Multiprocessing обходит GIL и даёт реальное ускорение.")


if __name__ == "__main__":
    main()
