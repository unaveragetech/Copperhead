"""
Copperhead Benchmark Runner

Benchmarks every module in the registry against its pure Python equivalent.
Compiles all Copperhead functions into a single Rust .dll, loads it,
and runs true head-to-head timing comparisons.

Output: benchmarks/results/benchmark_results.csv
"""

import sys
import os
import time
import csv
import json
import math
import random
import statistics as py_stats
import tempfile
import subprocess
import importlib.util
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copperhead.transpiler import transpile_source, generate_cargo_toml
from copperhead.registry import ModuleRegistry

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BENCHMARK_DIR, "results")
BUILD_DIR = os.path.join(BENCHMARK_DIR, "build")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)

ITERATIONS = 1000
WARMUP = 50

random.seed(42)

MODULE_NAME = "copperhead_bench"


def generate_test_data():
    """Generate test data for each module benchmark."""
    data_small = [random.uniform(-100, 100) for _ in range(100)]
    data_medium = [random.uniform(-100, 100) for _ in range(1000)]
    data_large = [random.uniform(-100, 100) for _ in range(10000)]
    int_small = [random.randint(0, 1000) for _ in range(100)]
    int_medium = [random.randint(0, 1000) for _ in range(1000)]
    int_sorted = sorted(int_medium)
    matrix_a = [[random.uniform(-10, 10) for _ in range(8)] for _ in range(8)]
    matrix_b = [[random.uniform(-10, 10) for _ in range(8)] for _ in range(8)]
    str_short = "hello world"
    str_med = "The quick brown fox jumps over the lazy dog" * 10
    str_palindrome = "racecar"
    str_kitten = "kitten"
    str_sitting = "sitting"

    return {
        "basic_sum": ([data_large, ], data_large),
        "basic_max": ([data_large, ], max(data_large)),
        "basic_clamp": ([42.5, 0.0, 10.0, ], 10.0),
        "basic_average": ([data_large, ], sum(data_large) / len(data_large)),
        "basic_count": ([int_medium, 500, ], int_medium.count(500)),
        "adv_fibonacci": ([30, ], 832040),
        "adv_prime_check": ([999983, ], True),
        "adv_gcd": ([1071, 462, ], 21),
        "adv_factorial": ([20, ], 2432902008176640000),
        "adv_prime_sieve": ([1000, ], None),
        "adv_bubblesort": ([data_small[:], ], sorted(data_small)),
        "adv_quicksort": ([data_medium[:], ], sorted(data_medium)),
        "adv_mergesort": ([data_medium[:], ], sorted(data_medium)),
        "adv_insertion_sort": ([data_small[:], ], sorted(data_small)),
        "adv_linear_search": ([int_medium, int_medium[500], ], 500),
        "adv_binary_search": ([int_sorted, int_sorted[500], ], None),
        "stat_variance": ([data_medium, ], py_stats.pvariance(data_medium)),
        "stat_stddev": ([data_medium, ], py_stats.pstdev(data_medium)),
        "stat_median": ([data_medium, ], py_stats.median(data_medium)),
        "stat_moving_avg": ([data_medium, 10, ], None),
        "stat_pearson": ([data_medium, [x * 2 + 1 for x in data_medium], ], None),
        "stat_linreg": ([data_medium, [x * 2 + 1 for x in data_medium], ], None),
        "la_dot_product": ([data_medium, data_medium, ], sum(a * b for a, b in zip(data_medium, data_medium))),
        "la_vec_add": ([data_medium, data_medium, ], [a + b for a, b in zip(data_medium, data_medium)]),
        "la_vec_scale": ([data_medium, 3.14, ], [x * 3.14 for x in data_medium]),
        "la_matrix_mul": ([matrix_a, matrix_b, ], None),
        "la_matrix_transpose": ([matrix_a, ], None),
        "dist_euclidean": ([data_medium, data_medium, ], 0.0),
        "dist_manhattan": ([data_medium, data_medium, ], 0.0),
        "dist_cosine": ([data_medium, data_medium, ], 1.0),
        "dist_levenshtein": ([str_kitten, str_sitting, ], 3),
        "str_reverse": ([str_med, ], str_med[::-1]),
        "str_count_words": ([str_med, ], str_med.count(' ') + 1),
        "str_palindrome": ([str_palindrome, ], True),
        "dp_histogram": ([data_medium, 10, ], None),
        "dp_normalize": ([data_medium, ], None),
        "dp_convolve": ([data_medium, [1.0, 0.0], ], None),
        "dp_zscore": ([data_medium, ], None),
        "misc_sqrt_newton": ([1234567.89, ], math.sqrt(1234567.89)),
        "misc_mandelbrot": ([-0.5, 0.0, 1000, ], None),
    }


# ═══════════════════════════════════════════════════════════════════════
# PURE PYTHON EQUIVALENT IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════

def py_sum_list(numbers):
    total = 0.0
    for num in numbers:
        total += num
    return total

def py_find_max(numbers):
    if not numbers:
        return 0.0
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val

def py_clamp(value, min_val, max_val):
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value

def py_average(numbers):
    if not numbers:
        return 0.0
    total = 0.0
    for num in numbers:
        total += num
    return total / len(numbers)

def py_count_occurrences(items, target):
    count = 0
    for item in items:
        if item == target:
            count += 1
    return count

def py_fibonacci(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def py_is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def py_gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def py_factorial(n):
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def py_prime_sieve(n):
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    i = 2
    while i * i <= n:
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
        i += 1
    return [i for i in range(2, n + 1) if sieve[i]]

def py_bubble_sort(arr):
    result = list(arr)
    n = len(result)
    for i in range(n):
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result

def py_quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return py_quick_sort(left) + middle + py_quick_sort(right)

def py_merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = py_merge_sort(arr[:mid])
    right = py_merge_sort(arr[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def py_insertion_sort(arr):
    result = list(arr)
    for i in range(1, len(result)):
        key = result[i]
        j = i - 1
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = key
    return result

def py_linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

def py_binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

def py_variance(data):
    n = len(data)
    if n == 0:
        return 0.0
    mean = sum(data) / n
    return sum((x - mean) ** 2 for x in data) / n

def py_stddev(data):
    return math.sqrt(py_variance(data))

def py_median(data):
    n = len(data)
    if n == 0:
        return 0.0
    s = sorted(data)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2.0
    return s[mid]

def py_moving_average(data, window):
    result = []
    for i in range(len(data) - window + 1):
        s = sum(data[i:i + window])
        result.append(s / window)
    return result

def py_pearson(x, y):
    n = len(x)
    if n == 0 or n != len(y):
        return 0.0
    sx = sum(x); sy = sum(y)
    sxy = sum(a * b for a, b in zip(x, y))
    sx2 = sum(a * a for a in x); sy2 = sum(b * b for b in y)
    num = n * sxy - sx * sy
    den = math.sqrt((n * sx2 - sx ** 2) * (n * sy2 - sy ** 2))
    return num / den if den != 0 else 0.0

def py_linear_regression(x, y):
    n = len(x)
    if n == 0 or n != len(y):
        return [0.0, 0.0]
    sx = sum(x); sy = sum(y)
    sxy = sum(a * b for a, b in zip(x, y))
    sx2 = sum(a * a for a in x)
    denom = n * sx2 - sx ** 2
    if denom == 0:
        return [0.0, sy / n]
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    return [slope, intercept]

def py_dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))

def py_vector_add(a, b):
    return [a + b for a, b in zip(a, b)]

def py_vector_scale(v, scalar):
    return [x * scalar for x in v]

def py_matrix_multiply(a, b):
    rows_a = len(a); cols_a = len(a[0]); cols_b = len(b[0])
    result = [[0.0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result

def py_matrix_transpose(m):
    rows = len(m); cols = len(m[0])
    return [[m[i][j] for i in range(rows)] for j in range(cols)]

def py_euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def py_manhattan(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))

def py_cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0

def py_levenshtein(s1, s2):
    m, n = len(s1), len(s2)
    if m == 0: return n
    if n == 0: return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[n]

def py_reverse_string(s):
    return s[::-1]

def py_count_words(s):
    return len(s.split())

def py_is_palindrome(s):
    return s == s[::-1]

def py_build_histogram(data, bins):
    if not data or bins <= 0:
        return []
    lo, hi = min(data), max(data)
    if hi == lo:
        return [len(data)]
    width = (hi - lo) / bins
    counts = [0] * bins
    for x in data:
        idx = int((x - lo) / width)
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1
    return counts

def py_normalize(data):
    if not data:
        return []
    lo, hi = min(data), max(data)
    if hi == lo:
        return [0.0] * len(data)
    rng = hi - lo
    return [(x - lo) / rng for x in data]

def py_convolve_1d(signal, kernel):
    n, k = len(signal), len(kernel)
    result = []
    for i in range(n - k + 1):
        s = sum(signal[i + j] * kernel[j] for j in range(k))
        result.append(s)
    return result

def py_zscore(data):
    n = len(data)
    if n == 0:
        return []
    mean = sum(data) / n
    sd = py_stddev(data)
    if sd == 0:
        return [0.0] * n
    return [(x - mean) / sd for x in data]

def py_sqrt_newton(x):
    if x < 0 or x == 0:
        return 0.0
    guess = x
    for _ in range(100):
        new_guess = (guess + x / guess) / 2.0
        if abs(new_guess - guess) < 1e-10:
            return new_guess
        guess = new_guess
    return guess

def py_mandelbrot(cx, cy, max_iter):
    x, y = 0.0, 0.0
    for i in range(max_iter):
        x2, y2 = x * x, y * y
        if x2 + y2 > 4.0:
            return i
        x_new = x2 - y2 + cx
        y = 2.0 * x * y + cy
        x = x_new
    return max_iter


# Map module IDs to (python_func, func_name_in_rust)
PYTHON_EQUIVALENTS = {
    "basic_sum": (py_sum_list, "sum_list"),
    "basic_max": (py_find_max, "find_max"),
    "basic_clamp": (py_clamp, "clamp"),
    "basic_average": (py_average, "average"),
    "basic_count": (py_count_occurrences, "count_occurrences"),
    "adv_fibonacci": (py_fibonacci, "fibonacci"),
    "adv_prime_check": (py_is_prime, "is_prime"),
    "adv_gcd": (py_gcd, "gcd"),
    "adv_factorial": (py_factorial, "factorial"),
    "adv_prime_sieve": (py_prime_sieve, "prime_sieve"),
    "adv_bubblesort": (py_bubble_sort, "bubble_sort"),
    "adv_quicksort": (py_quick_sort, "quick_sort"),
    "adv_mergesort": (py_merge_sort, "merge_sort"),
    "adv_insertion_sort": (py_insertion_sort, "insertion_sort"),
    "adv_linear_search": (py_linear_search, "linear_search"),
    "adv_binary_search": (py_binary_search, "binary_search"),
    "stat_variance": (py_variance, "variance"),
    "stat_stddev": (py_stddev, "stddev"),
    "stat_median": (py_median, "median"),
    "stat_moving_avg": (py_moving_average, "moving_average"),
    "stat_pearson": (py_pearson, "pearson_correlation"),
    "stat_linreg": (py_linear_regression, "linear_regression"),
    "la_dot_product": (py_dot_product, "dot_product"),
    "la_vec_add": (py_vector_add, "vector_add"),
    "la_vec_scale": (py_vector_scale, "vector_scale"),
    "la_matrix_mul": (py_matrix_multiply, "matrix_multiply"),
    "la_matrix_transpose": (py_matrix_transpose, "matrix_transpose"),
    "dist_euclidean": (py_euclidean, "euclidean_distance"),
    "dist_manhattan": (py_manhattan, "manhattan_distance"),
    "dist_cosine": (py_cosine_similarity, "cosine_similarity"),
    "dist_levenshtein": (py_levenshtein, "levenshtein"),
    "str_reverse": (py_reverse_string, "reverse_string"),
    "str_count_words": (py_count_words, "count_words"),
    "str_palindrome": (py_is_palindrome, "is_palindrome"),
    "dp_histogram": (py_build_histogram, "build_histogram"),
    "dp_normalize": (py_normalize, "normalize"),
    "dp_convolve": (py_convolve_1d, "convolve_1d"),
    "dp_zscore": (py_zscore, "zscore"),
    "misc_sqrt_newton": (py_sqrt_newton, "sqrt_newton"),
    "misc_mandelbrot": (py_mandelbrot, "mandelbrot"),
}


def benchmark_func(func, args, iterations=ITERATIONS, warmup=WARMUP):
    """Benchmark a function with given args. Returns avg time in seconds."""
    for _ in range(warmup):
        func(*args)
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args)
    elapsed = time.perf_counter() - start
    return elapsed / iterations


def build_rust_module(registry):
    """Build all Copperhead functions into a single Rust .dll."""
    modules = registry.get_all_modules()

    # Combine all source code into one file
    combined_source = "import copperhead as cp\n\n"
    for m in modules:
        if m.rust_code:
            lines = m.rust_code.split('\n')
            func_lines = [l for l in lines if not l.startswith("import copperhead")]
            combined_source += '\n'.join(func_lines) + "\n\n"

    # Transpile to Rust
    print("Transpiling all modules to Rust...")
    rust_code = transpile_source(combined_source)

    # Fix the module init function name to match the crate name
    # PyO3 #[pymodule] generates PyInit_<func_name>, so we need the func name to match
    rust_code = rust_code.replace(
        "fn _copperhead_module(m:",
        f"fn {MODULE_NAME}(m:"
    )

    # Write build files
    build_path = os.path.join(BUILD_DIR, MODULE_NAME)
    src_path = os.path.join(build_path, "src")
    os.makedirs(src_path, exist_ok=True)

    with open(os.path.join(src_path, "lib.rs"), 'w', encoding='utf-8') as f:
        f.write(rust_code)

    with open(os.path.join(build_path, "Cargo.toml"), 'w', encoding='utf-8') as f:
        f.write(generate_cargo_toml(MODULE_NAME))

    # Compile with cargo
    print("Compiling Rust module with cargo (this may take a minute)...")
    result = subprocess.run(
        ["cargo", "build", "--release"],
        cwd=build_path,
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode != 0:
        print("Cargo build failed!")
        print(result.stderr[-2000:])
        return None, result.stderr

    # Find the compiled .dll
    if sys.platform == "win32":
        lib_name = f"{MODULE_NAME}.dll"
    elif sys.platform == "darwin":
        lib_name = f"lib{MODULE_NAME}.dylib"
    else:
        lib_name = f"lib{MODULE_NAME}.so"

    lib_path = os.path.join(build_path, "target", "release", lib_name)

    if not os.path.exists(lib_path):
        print(f"Compiled library not found at {lib_path}")
        return None, "Library not found"

    print(f"Rust module compiled: {lib_path}")
    return lib_path, None


def load_rust_module(lib_path):
    """Load a compiled Rust .dll as a Python module."""
    tmp_dir = os.path.join(BUILD_DIR, "loaded")
    os.makedirs(tmp_dir, exist_ok=True)

    if sys.platform == "win32":
        ext = ".pyd"
    else:
        ext = ".so"

    dest = os.path.join(tmp_dir, f"{MODULE_NAME}{ext}")
    shutil.copy2(lib_path, dest)

    # Add to sys.path and import
    if tmp_dir not in sys.path:
        sys.path.insert(0, tmp_dir)

    import importlib
    mod = importlib.import_module(MODULE_NAME)
    return mod


def main():
    print("=" * 70)
    print("Copperhead Benchmark Runner")
    print("=" * 70)

    # Get registry
    registry = ModuleRegistry()
    modules = registry.get_all_modules()
    print(f"Found {len(modules)} modules in registry")

    # Generate test data
    test_data = generate_test_data()

    # Run Python benchmarks
    print(f"\nRunning Python benchmarks ({ITERATIONS} iterations each)...")
    py_results = {}
    for mod in modules:
        mod_id = mod.id
        if mod_id not in PYTHON_EQUIVALENTS:
            print(f"  SKIP {mod_id} (no Python equivalent)")
            continue

        py_func, rust_func_name = PYTHON_EQUIVALENTS[mod_id]
        if mod_id not in test_data:
            print(f"  SKIP {mod_id} (no test data)")
            continue

        args, expected = test_data[mod_id]

        try:
            avg_time = benchmark_func(py_func, args)
            py_results[mod_id] = {
                "func": py_func,
                "rust_name": rust_func_name,
                "args": args,
                "expected": expected,
                "python_time": avg_time,
            }
            print(f"  {mod_id:30s} Python: {avg_time*1e6:>10.2f} us")
        except Exception as e:
            print(f"  ERROR {mod_id}: {e}")

    # Build and load Rust module
    print(f"\n{'=' * 70}")
    lib_path, error = build_rust_module(registry)

    rust_module = None
    if lib_path:
        try:
            rust_module = load_rust_module(lib_path)
            print("Rust module loaded successfully!")
        except Exception as e:
            print(f"Failed to load Rust module: {e}")

    # Run Rust benchmarks
    if rust_module:
        print(f"\nRunning Rust benchmarks ({ITERATIONS} iterations each)...")
        for mod_id, info in py_results.items():
            rust_func = getattr(rust_module, info["rust_name"], None)
            if rust_func is None:
                print(f"  SKIP {mod_id} (Rust function not found)")
                info["rust_time"] = None
                info["speedup"] = None
                continue

            try:
                rust_args = info["args"]
                avg_time = benchmark_func(rust_func, rust_args, iterations=ITERATIONS, warmup=WARMUP)
                info["rust_time"] = avg_time
                if avg_time > 0:
                    info["speedup"] = info["python_time"] / avg_time
                else:
                    info["speedup"] = float('inf')
                print(f"  {mod_id:30s} Rust: {avg_time*1e6:>10.2f} us  Speedup: {info['speedup']:>7.1f}x")
            except Exception as e:
                info["rust_time"] = None
                info["speedup"] = None
                print(f"  ERROR {mod_id}: {e}")
    else:
        print("\nRust compilation failed - skipping Rust benchmarks")
        for mod_id, info in py_results.items():
            info["rust_time"] = None
            info["speedup"] = None

    # Generate CSV
    print(f"\n{'=' * 70}")
    print("Generating CSV report...")
    csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "module_id", "module_name", "function", "category", "difficulty",
            "description", "tags",
            "python_time_us", "rust_time_us", "speedup",
            "iterations", "input_size",
        ])

        for mod in modules:
            mod_id = mod.id
            if mod_id not in py_results:
                continue

            info = py_results[mod_id]
            py_us = info["python_time"] * 1e6
            rs_us = info["rust_time"] * 1e6 if info["rust_time"] else "N/A"
            speedup = info["speedup"] if info["speedup"] else "N/A"

            args = info["args"]
            input_size = 1
            if args and hasattr(args[0], '__len__'):
                input_size = len(args[0])

            category = "unknown"
            difficulty = "unknown"
            for tag in mod.tags:
                if tag in ("math", "statistics", "sort", "search", "string",
                           "linear-algebra", "distance", "data-processing",
                           "number-theory"):
                    category = tag
                if tag in ("basic", "intermediate", "advanced"):
                    difficulty = tag

            writer.writerow([
                mod_id,
                mod.name,
                info["rust_name"],
                category,
                difficulty,
                mod.description,
                ";".join(mod.tags),
                f"{py_us:.2f}",
                f"{rs_us:.2f}" if isinstance(rs_us, float) else rs_us,
                f"{speedup:.1f}" if isinstance(speedup, float) else speedup,
                ITERATIONS,
                input_size,
            ])

    print(f"CSV saved to: {csv_path}")

    # Print summary
    print(f"\n{'=' * 70}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Module':<30s} {'Python (us)':>12s} {'Rust (us)':>12s} {'Speedup':>10s}")
    print("-" * 70)

    speedups = []
    for mod in modules:
        mod_id = mod.id
        if mod_id not in py_results:
            continue
        info = py_results[mod_id]
        py_us = info["python_time"] * 1e6
        if info["rust_time"]:
            rs_us = info["rust_time"] * 1e6
            su = info["speedup"]
            speedups.append(su)
            print(f"{mod_id:<30s} {py_us:>10.2f}us {rs_us:>10.2f}us {su:>8.1f}x")
        else:
            print(f"{mod_id:<30s} {py_us:>10.2f}us {'N/A':>12s} {'N/A':>10s}")

    if speedups:
        print("-" * 70)
        print(f"{'Average speedup:':<30s} {'':>12s} {'':>12s} {sum(speedups)/len(speedups):>8.1f}x")
        print(f"{'Max speedup:':<30s} {'':>12s} {'':>12s} {max(speedups):>8.1f}x")
        print(f"{'Min speedup:':<30s} {'':>12s} {'':>12s} {min(speedups):>8.1f}x")

    print(f"\nResults saved to: {csv_path}")
    return csv_path


if __name__ == "__main__":
    main()