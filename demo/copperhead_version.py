"""
Copperhead Implementation
Count up to N, sort into groups, track execution time.
Uses @cp.compile for Rust-level performance.
"""

import time
import random
import copperhead as cp


@cp.compile(target="rust")
def generate_numbers(n: cp.i64) -> list[cp.i64]:
    """Generate list of numbers from 0 to n-1."""
    numbers = cp.Vec()
    for i in range(n):
        numbers.push(i)
    return numbers


@cp.compile(target="rust")
def sort_group(group: list[cp.i64]) -> list[cp.i64]:
    """Sort a single group using insertion sort (fast for small arrays)."""
    result = cp.Vec(group)
    n = result.len()
    for i in range(1, n):
        key = result[i]
        j = i - 1
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = key
    return result


@cp.compile(target="rust")
def sort_groups(groups: list[list[cp.i64]]) -> list[list[cp.i64]]:
    """Sort each group."""
    sorted_groups = cp.Vec()
    for group in groups:
        sorted_groups.push(sort_group(group))
    return sorted_groups


@cp.compile(target="rust")
def merge_sorted(groups: list[list[cp.i64]]) -> list[cp.i64]:
    """Merge all sorted groups into one sorted list."""
    merged = cp.Vec()
    for group in groups:
        for num in group:
            merged.push(num)
    
    # Final sort (merge sort would be better, but this works)
    n = merged.len()
    for i in range(n):
        for j in range(0, n - i - 1):
            if merged[j] > merged[j + 1]:
                temp = merged[j]
                merged[j] = merged[j + 1]
                merged[j + 1] = temp
    
    return merged


@cp.compile(target="rust")
def calculate_sum(numbers: list[cp.i64]) -> cp.i64:
    """Calculate sum of all numbers."""
    total = 0
    for n in numbers:
        total += n
    return total


@cp.compile(target="rust")
def get_first_n(numbers: list[cp.i64], count: cp.i64) -> list[cp.i64]:
    """Get first N elements."""
    result = cp.Vec()
    for i in range(min(count, numbers.len())):
        result.push(numbers[i])
    return result


@cp.compile(target="rust")
def get_last_n(numbers: list[cp.i64], count: cp.i64) -> list[cp.i64]:
    """Get last N elements."""
    result = cp.Vec()
    start = max(0, numbers.len() - count)
    for i in range(start, numbers.len()):
        result.push(numbers[i])
    return result


def count_and_sort(n: int, group_size: int) -> dict:
    """
    Count up to N, sort numbers into groups, return statistics.
    Uses Copperhead for compiled functions.
    """
    start_time = time.perf_counter()
    
    # Step 1: Generate numbers
    numbers = generate_numbers(n)
    
    # Step 2: Shuffle for realism (Python random, then convert)
    random.seed(42)
    py_list = list(numbers)
    random.shuffle(py_list)
    numbers = cp.Vec(py_list)
    
    # Step 3: Split into groups
    groups = cp.Vec()
    for i in range(0, len(numbers), group_size):
        group = cp.Vec()
        for j in range(i, min(i + group_size, len(numbers))):
            group.push(numbers[j])
        groups.push(group)
    
    # Step 4: Sort each group
    sorted_groups = sort_groups(groups)
    
    # Step 5: Merge sorted groups
    merged = merge_sorted(sorted_groups)
    
    # Step 6: Calculate statistics
    total_sum = calculate_sum(merged)
    average = total_sum / len(merged) if len(merged) > 0 else 0
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    return {
        "n": n,
        "group_size": group_size,
        "num_groups": len(sorted_groups),
        "total_numbers": len(merged),
        "sum": total_sum,
        "average": average,
        "first_10": list(get_first_n(merged, 10)),
        "last_10": list(get_last_n(merged, 10)),
        "time_seconds": elapsed,
    }


def benchmark(iterations: int = 5, n: int = 1_000_000, group_size: int = 10_000) -> dict:
    """
    Run benchmark multiple iterations and return average time.
    """
    times = []
    
    for i in range(iterations):
        result = count_and_sort(n, group_size)
        times.push(result["time_seconds"])
        print(f"  Iteration {i + 1}: {result['time_seconds']:.4f}s")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return {
        "iterations": iterations,
        "n": n,
        "group_size": group_size,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "all_times": times,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Copperhead: Count, Sort, and Group")
    print("=" * 60)
    
    # Run single test
    print("\n[Single Run]")
    result = count_and_sort(1_000_000, 10_000)
    print(f"  Numbers: {result['total_numbers']:,}")
    print(f"  Groups: {result['num_groups']}")
    print(f"  Sum: {result['sum']:,}")
    print(f"  Average: {result['average']:.2f}")
    print(f"  First 10: {result['first_10']}")
    print(f"  Last 10: {result['last_10']}")
    print(f"  Time: {result['time_seconds']:.4f}s")
    
    # Run benchmark
    print("\n[Benchmark - 5 iterations]")
    bench = benchmark(iterations=5, n=1_000_000, group_size=10_000)
    print(f"\n  Average: {bench['avg_time']:.4f}s")
    print(f"  Min: {bench['min_time']:.4f}s")
    print(f"  Max: {bench['max_time']:.4f}s")
    
    # Save results for comparison
    import json
    with open("copperhead_results.json", "w") as f:
        json.dump(bench, f, indent=2)
    
    print("\nResults saved to copperhead_results.json")
