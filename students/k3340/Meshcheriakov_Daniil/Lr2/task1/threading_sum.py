"""
Задача 1 — Threading
Вычисление суммы чисел от 1 до N с разбиением на NUM_THREADS потоков.

Ограничение GIL: потоки в Python не дают прироста производительности
для CPU-bound задач, так как только один поток выполняет байт-код
одновременно. Для 10^13 используется формула арифметической прогрессии,
а для честного бенчмарка — N_BENCH с реальной итерацией через range().
"""

import threading
import time

N = 10_000_000_000_000   # Целевое значение (формула)
N_BENCH = 100_000_000    # Реальная итерация для замера времени
NUM_THREADS = 8


def calculate_sum(start: int, end: int, results: list, index: int) -> None:
    """Сумма целых чисел [start, end] через формулу арифметической прогрессии."""
    count = end - start + 1
    results[index] = count * (start + end) // 2


def calculate_sum_iter(start: int, end: int, results: list, index: int) -> None:
    """Сумма целых чисел [start, end] через реальную итерацию (для бенчмарка)."""
    results[index] = sum(range(start, end + 1))


def run_parallel(n: int, use_iter: bool = False) -> tuple[int, float]:
    chunk = n // NUM_THREADS
    threads: list[threading.Thread] = []
    results = [0] * NUM_THREADS

    t0 = time.perf_counter()

    for i in range(NUM_THREADS):
        start = i * chunk + 1
        end = (i + 1) * chunk if i < NUM_THREADS - 1 else n
        fn = calculate_sum_iter if use_iter else calculate_sum
        t = threading.Thread(target=fn, args=(start, end, results, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - t0
    return sum(results), elapsed


def main() -> None:
    print("=" * 55)
    print("Threading — сумма от 1 до N")
    print("=" * 55)

    # 1. Формула для N = 10^13 (результат мгновенный)
    total, elapsed = run_parallel(N, use_iter=False)
    expected = N * (N + 1) // 2
    print(f"\n[Формула] N = {N:,}")
    print(f"  Сумма:    {total:,}")
    print(f"  Ожидается:{expected:,}")
    print(f"  Верно:    {total == expected}")
    print(f"  Время:    {elapsed:.6f} сек")

    # 2. Реальная итерация для N_BENCH
    total_b, elapsed_b = run_parallel(N_BENCH, use_iter=True)
    expected_b = N_BENCH * (N_BENCH + 1) // 2
    print(f"\n[Итерация] N = {N_BENCH:,}  (бенчмарк)")
    print(f"  Потоков:  {NUM_THREADS}")
    print(f"  Сумма:    {total_b:,}")
    print(f"  Верно:    {total_b == expected_b}")
    print(f"  Время:    {elapsed_b:.4f} сек")


if __name__ == "__main__":
    main()
