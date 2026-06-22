"""
Standard Python Implementation
Count up to N, sort into groups, track execution time.
"""

import time
import random


def count_and_sort(n: int, group_size: int) -> dict:
    """
    Count up to N, sort numbers into groups, return statistics.
    
    Args:
        n: The high number to count up to
        group_size: Size of each group for sorting
        
    Returns:
        Dictionary with results and timing info
    """
    start_time = time.perf_counter()
    
    # Step 1: Generate numbers
    numbers = list(range(n))
    
    # Step 2: Shuffle for realism
    random.seed(42)
    random.shuffle(numbers)
    
    # Step 3: Sort into groups
    groups = []
    for i in range(0, len(numbers), group_size):
        group = numbers[i:i + group_size]
        group.sort()
        groups.append(group)
    
    # Step 4: Merge sorted groups
    merged = []
    for group in groups:
        merged.extend(group)
    merged.sort()
    
    # Step 5: Calculate statistics
    total_sum = sum(merged)
    average = total_sum / len(merged) if merged else 0
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    return {
        "n": n,
        "group_size": group_size,
        "num_groups": len(groups),
        "total_numbers": len(merged),
        "sum": total_sum,
        "average": average,
        "first_10": merged[:10],
        "last_10": merged[-10:],
        "time_seconds": elapsed,
    }


def benchmark(iterations: int = 5, n: int = 1_000_000, group_size: int = 10_000) -> dict:
    """
    Run benchmark multiple iterations and return average time.
    """
    times = []
    
    for i in range(iterations):
        result = count_and_sort(n, group_size)
        times.append(result["time_seconds"])
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
    print("Standard Python: Count, Sort, and Group")
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
    with open("standard_python_results.json", "w") as f:
        json.dump(bench, f, indent=2)
    
    print("\nResults saved to standard_python_results.json")
