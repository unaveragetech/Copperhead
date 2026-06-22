"""
Speed Comparison: Standard Python vs Copperhead
Runs both implementations and shows the performance difference.
"""

import time
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_standard_python(n: int = 1_000_000, group_size: int = 10_000, iterations: int = 3):
    """Run standard Python benchmark."""
    from standard_python import count_and_sort
    
    times = []
    for i in range(iterations):
        result = count_and_sort(n, group_size)
        times.append(result["time_seconds"])
    
    return {
        "implementation": "Standard Python",
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "times": times,
    }


def run_copperhead(n: int = 1_000_000, group_size: int = 10_000, iterations: int = 3):
    """Run Copperhead benchmark."""
    from copperhead_version import count_and_sort
    
    times = []
    for i in range(iterations):
        result = count_and_sort(n, group_size)
        times.append(result["time_seconds"])
    
    return {
        "implementation": "Copperhead",
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "times": times,
    }


def compare(n: int = 1_000_000, group_size: int = 10_000, iterations: int = 3):
    """Run comparison and display results."""
    print("=" * 70)
    print("SPEED COMPARISON: Standard Python vs Copperhead")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Numbers: {n:,}")
    print(f"  Group size: {group_size:,}")
    print(f"  Iterations: {iterations}")
    
    # Run Standard Python
    print("\n" + "-" * 70)
    print("Running Standard Python...")
    print("-" * 70)
    py_results = run_standard_python(n, group_size, iterations)
    for i, t in enumerate(py_results["times"]):
        print(f"  Iteration {i + 1}: {t:.4f}s")
    print(f"  Average: {py_results['avg_time']:.4f}s")
    
    # Run Copperhead
    print("\n" + "-" * 70)
    print("Running Copperhead...")
    print("-" * 70)
    cp_results = run_copperhead(n, group_size, iterations)
    for i, t in enumerate(cp_results["times"]):
        print(f"  Iteration {i + 1}: {t:.4f}s")
    print(f"  Average: {cp_results['avg_time']:.4f}s")
    
    # Calculate speedup
    speedup = py_results["avg_time"] / cp_results["avg_time"] if cp_results["avg_time"] > 0 else 0
    
    # Display comparison
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\n{'Metric':<25} {'Standard Python':<20} {'Copperhead':<20} {'Speedup':<10}")
    print("-" * 75)
    print(f"{'Average Time':<25} {py_results['avg_time']:<20.4f} {cp_results['avg_time']:<20.4f} {speedup:<10.2f}x")
    print(f"{'Min Time':<25} {py_results['min_time']:<20.4f} {cp_results['min_time']:<20.4f}")
    print(f"{'Max Time':<25} {py_results['max_time']:<20.4f} {cp_results['max_time']:<20.4f}")
    
    # Visual bar chart
    print("\n" + "=" * 70)
    print("VISUAL COMPARISON")
    print("=" * 70)
    
    max_time = max(py_results["avg_time"], cp_results["avg_time"])
    py_bar_len = int((py_results["avg_time"] / max_time) * 50)
    cp_bar_len = int((cp_results["avg_time"] / max_time) * 50)
    
    print(f"\nStandard Python: {'█' * py_bar_len} {py_results['avg_time']:.4f}s")
    print(f"Copperhead:      {'█' * cp_bar_len} {cp_results['avg_time']:.4f}s")
    
    print("\n" + "=" * 70)
    print(f"CONCLUSION: Copperhead is {speedup:.2f}x FASTER than Standard Python")
    print("=" * 70)
    
    # Save results
    results = {
        "config": {
            "n": n,
            "group_size": group_size,
            "iterations": iterations,
        },
        "standard_python": py_results,
        "copperhead": cp_results,
        "speedup": speedup,
    }
    
    with open("comparison_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to comparison_results.json")
    
    return results


if __name__ == "__main__":
    # Run with smaller size first for quick test
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        compare(n=100_000, group_size=1_000, iterations=2)
    else:
        compare(n=1_000_000, group_size=10_000, iterations=3)
