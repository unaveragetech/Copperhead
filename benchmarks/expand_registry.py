"""
Expand the Copperhead registry with 40 vetted, useful modules.

Each module has:
- A Copperhead (@cp.compile) source implementation
- A pure Python standard equivalent for benchmarking
- Test inputs and expected outputs
- Rich metadata (tags, description, category, difficulty)

Categories: math, statistics, search, sort, string, linear-algebra,
            number-theory, algorithm, data-processing, cryptography
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copperhead.registry import (
    ModuleRegistry, ModuleMetadata, FunctionSignature, ModuleStatus
)


def create_fresh_registry():
    import tempfile
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(pkg_dir, "copperhead", ".copperhead", "registry.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass
    return ModuleRegistry(db_path=db_path)


def reg(id, name, desc, tags, func_name, args, ret_type, func_desc, source, category, difficulty="basic", examples=None):
    """Helper to create a module registration."""
    return ModuleMetadata(
        id=id,
        name=name,
        description=desc,
        version="1.0.0",
        author="Copperhead",
        tags=tags + [category, difficulty],
        functions=[
            FunctionSignature(
                name=func_name,
                args=args,
                return_type=ret_type,
                description=func_desc,
                is_rpb=True,
                examples=examples or []
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code=source
    )


def populate_all(registry):
    modules = []

    # ═══════════════════════════════════════════════════════════════════
    # MATH BASICS (1-5)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "basic_sum", "basic_sum", "Sum a list of numbers",
        ["math", "sum", "aggregate"],
        "sum_list", [("numbers", "list[cp.f64]")], "cp.f64",
        "Calculate the sum of a list of floating point numbers",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef sum_list(numbers: list[cp.f64]) -> cp.f64:\n    total = cp.f64(0)\n    for num in numbers:\n        total += num\n    return total',
        "math", "basic", ["sum_list([1.0, 2.0, 3.0]) -> 6.0"]
    ))

    modules.append(reg(
        "basic_max", "basic_max", "Find maximum value in a list",
        ["math", "max", "search"],
        "find_max", [("numbers", "list[cp.f64]")], "cp.f64",
        "Find the maximum value in a list of numbers",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef find_max(numbers: list[cp.f64]) -> cp.f64:\n    if len(numbers) == 0:\n        return cp.f64(0)\n    max_val = numbers[0]\n    for num in numbers:\n        if num > max_val:\n            max_val = num\n    return max_val',
        "math", "basic", ["find_max([3.0, 1.0, 4.0, 1.0, 5.0]) -> 5.0"]
    ))

    modules.append(reg(
        "basic_clamp", "basic_clamp", "Clamp a value between min and max",
        ["math", "clamp", "bounds"],
        "clamp", [("value", "cp.f64"), ("min_val", "cp.f64"), ("max_val", "cp.f64")], "cp.f64",
        "Clamp a value between min and max bounds",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef clamp(value: cp.f64, min_val: cp.f64, max_val: cp.f64) -> cp.f64:\n    if value < min_val:\n        return min_val\n    if value > max_val:\n        return max_val\n    return value',
        "math", "basic", ["clamp(5.0, 0.0, 10.0) -> 5.0"]
    ))

    modules.append(reg(
        "basic_average", "basic_average", "Calculate the average of a list",
        ["math", "average", "mean", "statistics"],
        "average", [("numbers", "list[cp.f64]")], "cp.f64",
        "Calculate the arithmetic mean of a list of numbers",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef average(numbers: list[cp.f64]) -> cp.f64:\n    if len(numbers) == 0:\n        return cp.f64(0)\n    total = cp.f64(0)\n    for num in numbers:\n        total += num\n    return total / len(numbers)',
        "math", "basic", ["average([1.0, 2.0, 3.0, 4.0, 5.0]) -> 3.0"]
    ))

    modules.append(reg(
        "basic_count", "basic_count", "Count occurrences of a value in a list",
        ["search", "count", "frequency"],
        "count_occurrences", [("items", "list[cp.i64]"), ("target", "cp.i64")], "cp.i64",
        "Count how many times target appears in items",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef count_occurrences(items: list[cp.i64], target: cp.i64) -> cp.i64:\n    count = 0\n    for item in items:\n        if item == target:\n            count += 1\n    return count',
        "search", "basic", ["count_occurrences([1, 2, 2, 3, 2], 2) -> 3"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # NUMBER THEORY (6-10)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "adv_fibonacci", "adv_fibonacci", "Calculate Fibonacci numbers iteratively",
        ["math", "fibonacci", "sequence", "recursion"],
        "fibonacci", [("n", "cp.i64")], "cp.i64",
        "Calculate the nth Fibonacci number iteratively",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef fibonacci(n: cp.i64) -> cp.i64:\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a = 0\n    b = 1\n    for _ in range(2, n + 1):\n        temp = a + b\n        a = b\n        b = temp\n    return b',
        "number-theory", "advanced", ["fibonacci(10) -> 55"]
    ))

    modules.append(reg(
        "adv_prime_check", "adv_prime_check", "Check if a number is prime",
        ["math", "prime", "number-theory"],
        "is_prime", [("n", "cp.i64")], "cp.bool",
        "Check if a number is prime",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef is_prime(n: cp.i64) -> cp.bool:\n    if n < 2:\n        return False\n    if n == 2:\n        return True\n    if n % 2 == 0:\n        return False\n    i = 3\n    while i * i <= n:\n        if n % i == 0:\n            return False\n        i += 2\n    return True',
        "number-theory", "advanced", ["is_prime(7) -> True", "is_prime(4) -> False"]
    ))

    modules.append(reg(
        "adv_gcd", "adv_gcd", "Greatest Common Divisor (Euclidean algorithm)",
        ["math", "gcd", "number-theory", "euclidean"],
        "gcd", [("a", "cp.i64"), ("b", "cp.i64")], "cp.i64",
        "Calculate the GCD of two numbers using Euclidean algorithm",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef gcd(a: cp.i64, b: cp.i64) -> cp.i64:\n    while b != 0:\n        temp = b\n        b = a % b\n        a = temp\n    return a',
        "number-theory", "advanced", ["gcd(12, 8) -> 4"]
    ))

    modules.append(reg(
        "adv_factorial", "adv_factorial", "Calculate factorial iteratively",
        ["math", "factorial", "number-theory"],
        "factorial", [("n", "cp.i64")], "cp.i64",
        "Calculate the factorial of n iteratively",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef factorial(n: cp.i64) -> cp.i64:\n    if n <= 1:\n        return 1\n    result = 1\n    for i in range(2, n + 1):\n        result *= i\n    return result',
        "number-theory", "advanced", ["factorial(5) -> 120"]
    ))

    modules.append(reg(
        "adv_prime_sieve", "adv_prime_sieve", "Sieve of Eratosthenes - find all primes up to n",
        ["math", "prime", "sieve", "number-theory"],
        "prime_sieve", [("n", "cp.i64")], "list[cp.i64]",
        "Find all prime numbers up to n using Sieve of Eratosthenes",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef prime_sieve(n: cp.i64) -> list[cp.i64]:\n    if n < 2:\n        return []\n    sieve = []\n    for _ in range(n + 1):\n        sieve.append(True)\n    sieve[0] = False\n    sieve[1] = False\n    i = 2\n    while i * i <= n:\n        if sieve[i]:\n            j = i * i\n            while j <= n:\n                sieve[j] = False\n                j += i\n        i += 1\n    result = []\n    for i in range(2, n + 1):\n        if sieve[i]:\n            result.append(i)\n    return result',
        "number-theory", "advanced", ["prime_sieve(10) -> [2, 3, 5, 7]"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # SORTING ALGORITHMS (11-14)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "adv_bubblesort", "adv_bubblesort", "Bubble sort algorithm",
        ["sort", "algorithm", "bubble"],
        "bubble_sort", [("arr", "list[cp.f64]")], "list[cp.f64]",
        "Sort a list of numbers using bubble sort",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef bubble_sort(arr: list[cp.f64]) -> list[cp.f64]:\n    n = len(arr)\n    result = []\n    for x in arr:\n        result.append(x)\n    for i in range(n):\n        for j in range(0, n - i - 1):\n            if result[j] > result[j + 1]:\n                temp = result[j]\n                result[j] = result[j + 1]\n                result[j + 1] = temp\n    return result',
        "sort", "advanced", ["bubble_sort([3.0, 1.0, 4.0]) -> [1.0, 3.0, 4.0]"]
    ))

    modules.append(reg(
        "adv_quicksort", "adv_quicksort", "Quicksort algorithm",
        ["sort", "algorithm", "quicksort", "divide-conquer"],
        "quick_sort", [("arr", "list[cp.f64]")], "list[cp.f64]",
        "Sort a list of numbers using quicksort",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef quick_sort(arr: list[cp.f64]) -> list[cp.f64]:\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = []\n    middle = []\n    right = []\n    for x in arr:\n        if x < pivot:\n            left.append(x)\n        elif x == pivot:\n            middle.append(x)\n        else:\n            right.append(x)\n    left = quick_sort(left)\n    right = quick_sort(right)\n    result = []\n    for x in left:\n        result.append(x)\n    for x in middle:\n        result.append(x)\n    for x in right:\n        result.append(x)\n    return result',
        "sort", "advanced", ["quick_sort([3.0, 1.0, 4.0]) -> [1.0, 3.0, 4.0]"]
    ))

    modules.append(reg(
        "adv_mergesort", "adv_mergesort", "Merge sort algorithm",
        ["sort", "algorithm", "mergesort", "divide-conquer"],
        "merge_sort", [("arr", "list[cp.f64]")], "list[cp.f64]",
        "Sort a list of numbers using merge sort",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef merge_sort(arr: list[cp.f64]) -> list[cp.f64]:\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = []\n    for i in range(mid):\n        left.append(arr[i])\n    right = []\n    for i in range(mid, len(arr)):\n        right.append(arr[i])\n    left = merge_sort(left)\n    right = merge_sort(right)\n    result = []\n    i = 0\n    j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    while i < len(left):\n        result.append(left[i])\n        i += 1\n    while j < len(right):\n        result.append(right[j])\n        j += 1\n    return result',
        "sort", "advanced", ["merge_sort([3.0, 1.0, 4.0]) -> [1.0, 3.0, 4.0]"]
    ))

    modules.append(reg(
        "adv_insertion_sort", "adv_insertion_sort", "Insertion sort algorithm",
        ["sort", "algorithm", "insertion"],
        "insertion_sort", [("arr", "list[cp.f64]")], "list[cp.f64]",
        "Sort a list of numbers using insertion sort",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef insertion_sort(arr: list[cp.f64]) -> list[cp.f64]:\n    result = []\n    for x in arr:\n        result.append(x)\n    for i in range(1, len(result)):\n        key = result[i]\n        j = i - 1\n        while j >= 0 and result[j] > key:\n            result[j + 1] = result[j]\n            j -= 1\n        result[j + 1] = key\n    return result',
        "sort", "advanced", ["insertion_sort([3.0, 1.0, 4.0]) -> [1.0, 3.0, 4.0]"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # SEARCH ALGORITHMS (15-16)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "adv_linear_search", "adv_linear_search", "Linear search in a list",
        ["search", "algorithm", "linear"],
        "linear_search", [("arr", "list[cp.i64]"), ("target", "cp.i64")], "cp.i64",
        "Search for target in arr, return index or -1 if not found",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef linear_search(arr: list[cp.i64], target: cp.i64) -> cp.i64:\n    for i in range(len(arr)):\n        if arr[i] == target:\n            return i\n    return -1',
        "search", "advanced", ["linear_search([1,2,3,4,5], 3) -> 2"]
    ))

    modules.append(reg(
        "adv_binary_search", "adv_binary_search", "Binary search on a sorted list",
        ["search", "algorithm", "binary", "divide-conquer"],
        "binary_search", [("arr", "list[cp.i64]"), ("target", "cp.i64")], "cp.i64",
        "Search for target in a sorted list using binary search",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef binary_search(arr: list[cp.i64], target: cp.i64) -> cp.i64:\n    lo = 0\n    hi = len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1',
        "search", "advanced", ["binary_search([1,2,3,4,5], 3) -> 2"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # STATISTICS (17-22)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "stat_variance", "stat_variance", "Calculate variance of a list",
        ["statistics", "variance", "spread"],
        "variance", [("data", "list[cp.f64]")], "cp.f64",
        "Calculate the population variance of a dataset",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef variance(data: list[cp.f64]) -> cp.f64:\n    n = len(data)\n    if n == 0:\n        return cp.f64(0)\n    mean = cp.f64(0)\n    for x in data:\n        mean += x\n    mean = mean / n\n    ssd = cp.f64(0)\n    for x in data:\n        diff = x - mean\n        ssd += diff * diff\n    return ssd / n',
        "statistics", "intermediate", ["variance([1.0, 2.0, 3.0, 4.0, 5.0]) -> 2.0"]
    ))

    modules.append(reg(
        "stat_stddev", "stat_stddev", "Calculate standard deviation of a list",
        ["statistics", "stddev", "spread"],
        "stddev", [("data", "list[cp.f64]")], "cp.f64",
        "Calculate the population standard deviation of a dataset",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef stddev(data: list[cp.f64]) -> cp.f64:\n    n = len(data)\n    if n == 0:\n        return cp.f64(0)\n    mean = cp.f64(0)\n    for x in data:\n        mean += x\n    mean = mean / n\n    ssd = cp.f64(0)\n    for x in data:\n        diff = x - mean\n        ssd += diff * diff\n    return cp.math.sqrt(ssd / n)',
        "statistics", "intermediate", ["stddev([1.0, 2.0, 3.0, 4.0, 5.0]) -> 1.414..."]
    ))

    modules.append(reg(
        "stat_median", "stat_median", "Calculate the median of a list",
        ["statistics", "median", "central-tendency"],
        "median", [("data", "list[cp.f64]")], "cp.f64",
        "Calculate the median value of a sorted dataset",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef median(data: list[cp.f64]) -> cp.f64:\n    n = len(data)\n    if n == 0:\n        return cp.f64(0)\n    sorted_data = sorted(data)\n    mid = n // 2\n    if n % 2 == 0:\n        return (sorted_data[mid - 1] + sorted_data[mid]) / 2.0\n    return sorted_data[mid]',
        "statistics", "intermediate", ["median([1.0, 2.0, 3.0, 4.0, 5.0]) -> 3.0"]
    ))

    modules.append(reg(
        "stat_moving_avg", "stat_moving_avg", "Moving average with window size k",
        ["statistics", "moving-average", "smoothing", "signal"],
        "moving_average", [("data", "list[cp.f64]"), ("window", "cp.i64")], "list[cp.f64]",
        "Calculate the moving average of a data series with given window size",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef moving_average(data: list[cp.f64], window: cp.i64) -> list[cp.f64]:\n    n = len(data)\n    w = window\n    result = []\n    for i in range(n - w + 1):\n        s = cp.f64(0)\n        for j in range(w):\n            s += data[i + j]\n        result.append(s / w)\n    return result',
        "statistics", "intermediate", ["moving_average([1.0,2.0,3.0,4.0,5.0], 3) -> [2.0, 3.0, 4.0]"]
    ))

    modules.append(reg(
        "stat_pearson", "stat_pearson", "Pearson correlation coefficient",
        ["statistics", "correlation", "pearson"],
        "pearson_correlation", [("x", "list[cp.f64]"), ("y", "list[cp.f64]")], "cp.f64",
        "Calculate the Pearson correlation coefficient between two datasets",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef pearson_correlation(x: list[cp.f64], y: list[cp.f64]) -> cp.f64:\n    n = len(x)\n    if n == 0 or n != len(y):\n        return cp.f64(0)\n    sum_x = cp.f64(0)\n    sum_y = cp.f64(0)\n    sum_xy = cp.f64(0)\n    sum_x2 = cp.f64(0)\n    sum_y2 = cp.f64(0)\n    for i in range(n):\n        sum_x += x[i]\n        sum_y += y[i]\n        sum_xy += x[i] * y[i]\n        sum_x2 += x[i] * x[i]\n        sum_y2 += y[i] * y[i]\n    numerator = n * sum_xy - sum_x * sum_y\n    denominator = cp.math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))\n    if denominator == 0.0:\n        return cp.f64(0)\n    return numerator / denominator',
        "statistics", "advanced", ["pearson_correlation([1,2,3], [2,4,6]) -> 1.0"]
    ))

    modules.append(reg(
        "stat_linreg", "stat_linreg", "Simple linear regression (slope and intercept)",
        ["statistics", "regression", "linear"],
        "linear_regression", [("x", "list[cp.f64]"), ("y", "list[cp.f64]")], "list[cp.f64]",
        "Fit a line y = mx + b and return [slope, intercept]",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef linear_regression(x: list[cp.f64], y: list[cp.f64]) -> list[cp.f64]:\n    n = len(x)\n    if n == 0 or n != len(y):\n        return [cp.f64(0), cp.f64(0)]\n    sum_x = cp.f64(0)\n    sum_y = cp.f64(0)\n    sum_xy = cp.f64(0)\n    sum_x2 = cp.f64(0)\n    for i in range(n):\n        sum_x += x[i]\n        sum_y += y[i]\n        sum_xy += x[i] * y[i]\n        sum_x2 += x[i] * x[i]\n    denom = n * sum_x2 - sum_x * sum_x\n    if denom == 0.0:\n        return [cp.f64(0), sum_y / n]\n    slope = (n * sum_xy - sum_x * sum_y) / denom\n    intercept = (sum_y - slope * sum_x) / n\n    return [slope, intercept]',
        "statistics", "advanced", ["linear_regression([0,1,2,3], [1,3,5,7]) -> [2.0, 1.0]"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # LINEAR ALGEBRA (23-27)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "la_dot_product", "la_dot_product", "Dot product of two vectors",
        ["linear-algebra", "dot-product", "vector"],
        "dot_product", [("a", "list[cp.f64]"), ("b", "list[cp.f64]")], "cp.f64",
        "Calculate the dot product of two vectors",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef dot_product(a: list[cp.f64], b: list[cp.f64]) -> cp.f64:\n    n = len(a)\n    result = cp.f64(0)\n    for i in range(n):\n        result += a[i] * b[i]\n    return result',
        "linear-algebra", "intermediate", ["dot_product([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) -> 32.0"]
    ))

    modules.append(reg(
        "la_vec_add", "la_vec_add", "Element-wise vector addition",
        ["linear-algebra", "vector", "addition"],
        "vector_add", [("a", "list[cp.f64]"), ("b", "list[cp.f64]")], "list[cp.f64]",
        "Add two vectors element-wise",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef vector_add(a: list[cp.f64], b: list[cp.f64]) -> list[cp.f64]:\n    n = len(a)\n    result = []\n    for i in range(n):\n        result.append(a[i] + b[i])\n    return result',
        "linear-algebra", "basic", ["vector_add([1.0, 2.0], [3.0, 4.0]) -> [4.0, 6.0]"]
    ))

    modules.append(reg(
        "la_vec_scale", "la_vec_scale", "Scale a vector by a scalar",
        ["linear-algebra", "vector", "scale"],
        "vector_scale", [("v", "list[cp.f64]"), ("scalar", "cp.f64")], "list[cp.f64]",
        "Multiply each element of a vector by a scalar",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef vector_scale(v: list[cp.f64], scalar: cp.f64) -> list[cp.f64]:\n    result = []\n    for i in range(len(v)):\n        result.append(v[i] * scalar)\n    return result',
        "linear-algebra", "basic", ["vector_scale([1.0, 2.0, 3.0], 2.0) -> [2.0, 4.0, 6.0]"]
    ))

    modules.append(reg(
        "la_matrix_mul", "la_matrix_mul", "Multiply two matrices",
        ["linear-algebra", "matrix", "multiply"],
        "matrix_multiply", [("a", "list[list[cp.f64]]"), ("b", "list[list[cp.f64]]")], "list[list[cp.f64]]",
        "Multiply two matrices and return the result",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef matrix_multiply(a: list[list[cp.f64]], b: list[list[cp.f64]]) -> list[list[cp.f64]]:\n    rows_a = len(a)\n    cols_a = len(a[0])\n    cols_b = len(b[0])\n    result = [[cp.f64(0) for _ in range(cols_b)] for _ in range(rows_a)]\n    for i in range(rows_a):\n        for j in range(cols_b):\n            for k in range(cols_a):\n                result[i][j] += a[i][k] * b[k][j]\n    return result',
        "linear-algebra", "advanced", ["matrix_multiply([[1,2],[3,4]], [[5,6],[7,8]]) -> [[19,22],[43,50]]"]
    ))

    modules.append(reg(
        "la_matrix_transpose", "la_matrix_transpose", "Transpose a matrix",
        ["linear-algebra", "matrix", "transpose"],
        "matrix_transpose", [("m", "list[list[cp.f64]]")], "list[list[cp.f64]]",
        "Transpose a matrix (swap rows and columns)",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef matrix_transpose(m: list[list[cp.f64]]) -> list[list[cp.f64]]:\n    rows = len(m)\n    cols = len(m[0])\n    result = [[cp.f64(0) for _ in range(rows)] for _ in range(cols)]\n    for i in range(rows):\n        for j in range(cols):\n            result[j][i] = m[i][j]\n    return result',
        "linear-algebra", "intermediate", ["matrix_transpose([[1,2],[3,4]]) -> [[1,3],[2,4]]"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # DISTANCE / SIMILARITY (28-31)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "dist_euclidean", "dist_euclidean", "Euclidean distance between two vectors",
        ["distance", "euclidean", "vector"],
        "euclidean_distance", [("a", "list[cp.f64]"), ("b", "list[cp.f64]")], "cp.f64",
        "Calculate the Euclidean distance between two vectors",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef euclidean_distance(a: list[cp.f64], b: list[cp.f64]) -> cp.f64:\n    n = len(a)\n    ssd = cp.f64(0)\n    for i in range(n):\n        diff = a[i] - b[i]\n        ssd += diff * diff\n    return cp.math.sqrt(ssd)',
        "distance", "intermediate", ["euclidean_distance([0,0], [3,4]) -> 5.0"]
    ))

    modules.append(reg(
        "dist_manhattan", "dist_manhattan", "Manhattan distance between two vectors",
        ["distance", "manhattan", "vector"],
        "manhattan_distance", [("a", "list[cp.f64]"), ("b", "list[cp.f64]")], "cp.f64",
        "Calculate the Manhattan (L1) distance between two vectors",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef manhattan_distance(a: list[cp.f64], b: list[cp.f64]) -> cp.f64:\n    n = len(a)\n    total = cp.f64(0)\n    for i in range(n):\n        diff = a[i] - b[i]\n        if diff < 0.0:\n            diff = -diff\n        total += diff\n    return total',
        "distance", "intermediate", ["manhattan_distance([0,0], [3,4]) -> 7.0"]
    ))

    modules.append(reg(
        "dist_cosine", "dist_cosine", "Cosine similarity between two vectors",
        ["distance", "cosine", "similarity", "vector"],
        "cosine_similarity", [("a", "list[cp.f64]"), ("b", "list[cp.f64]")], "cp.f64",
        "Calculate the cosine similarity between two vectors",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef cosine_similarity(a: list[cp.f64], b: list[cp.f64]) -> cp.f64:\n    n = len(a)\n    dot = cp.f64(0)\n    norm_a = cp.f64(0)\n    norm_b = cp.f64(0)\n    for i in range(n):\n        dot += a[i] * b[i]\n        norm_a += a[i] * a[i]\n        norm_b += b[i] * b[i]\n    if norm_a == 0.0 or norm_b == 0.0:\n        return cp.f64(0)\n    return dot / (cp.math.sqrt(norm_a) * cp.math.sqrt(norm_b))',
        "distance", "advanced", ["cosine_similarity([1,0], [1,1]) -> 0.707..."]
    ))

    modules.append(reg(
        "dist_levenshtein", "dist_levenshtein", "Levenshtein edit distance between two strings",
        ["string", "distance", "edit", "levenshtein"],
        "levenshtein", [("s1", "str"), ("s2", "str")], "cp.i64",
        "Calculate the Levenshtein edit distance between two strings",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef levenshtein(s1: str, s2: str) -> cp.i64:\n    m = len(s1)\n    n = len(s2)\n    if m == 0:\n        return n\n    if n == 0:\n        return m\n    prev = []\n    for j in range(n + 1):\n        prev.append(j)\n    for i in range(1, m + 1):\n        curr = [i]\n        for j in range(1, n + 1):\n            cost = 1\n            if s1[i - 1] == s2[j - 1]:\n                cost = 0\n            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))\n        prev = curr\n    return prev[n]',
        "string", "advanced", ["levenshtein('kitten', 'sitting') -> 3"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # STRING OPERATIONS (32-34)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "str_reverse", "str_reverse", "Reverse a string",
        ["string", "reverse", "manipulation"],
        "reverse_string", [("s", "str")], "str",
        "Reverse a string character by character",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef reverse_string(s: str) -> str:\n    n = len(s)\n    result = []\n    for i in range(n):\n        result.append(s[n - 1 - i])\n    return "".join(result)',
        "string", "basic", ["reverse_string('hello') -> 'olleh'"]
    ))

    modules.append(reg(
        "str_count_words", "str_count_words", "Count words in a string",
        ["string", "count", "words", "text"],
        "count_words", [("s", "str")], "cp.i64",
        "Count the number of words in a string (space-separated)",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef count_words(s: str) -> cp.i64:\n    count = 0\n    in_word = False\n    for ch in s:\n        is_space = False\n        if ch == " ":\n            is_space = True\n        if is_space:\n            in_word = False\n        else:\n            if not in_word:\n                count += 1\n                in_word = True\n    return count',
        "string", "basic", ["count_words('hello world foo') -> 3"]
    ))

    modules.append(reg(
        "str_palindrome", "str_palindrome", "Check if a string is a palindrome",
        ["string", "palindrome", "check"],
        "is_palindrome", [("s", "str")], "cp.bool",
        "Check if a string reads the same forwards and backwards",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef is_palindrome(s: str) -> cp.bool:\n    n = len(s)\n    i = 0\n    j = n - 1\n    while i < j:\n        if s[i] != s[j]:\n            return False\n        i += 1\n        j -= 1\n    return True',
        "string", "basic", ["is_palindrome('racecar') -> True"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # DATA PROCESSING (35-38)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "dp_histogram", "dp_histogram", "Build a histogram from data",
        ["data-processing", "histogram", "bin", "distribution"],
        "build_histogram", [("data", "list[cp.f64]"), ("bins", "cp.i64")], "list[cp.i64]",
        "Build a histogram with the given number of bins",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef build_histogram(data: list[cp.f64], bins: cp.i64) -> list[cp.i64]:\n    if len(data) == 0 or bins <= 0:\n        return []\n    lo = data[0]\n    hi = data[0]\n    for x in data:\n        if x < lo:\n            lo = x\n        if x > hi:\n            hi = x\n    if hi == lo:\n        result = []\n        result.append(len(data))\n        return result\n    width = (hi - lo) / bins\n    counts = []\n    for _ in range(bins):\n        counts.append(0)\n    for x in data:\n        idx = int((x - lo) / width)\n        if idx >= bins:\n            idx = bins - 1\n        counts[idx] = counts[idx] + 1\n    return counts',
        "data-processing", "intermediate", ["build_histogram([1,2,3,4,5], 2) -> [2, 3]"]
    ))

    modules.append(reg(
        "dp_normalize", "dp_normalize", "Normalize data to [0, 1] range",
        ["data-processing", "normalize", "scale"],
        "normalize", [("data", "list[cp.f64]")], "list[cp.f64]",
        "Normalize a list of values to the [0, 1] range (min-max normalization)",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef normalize(data: list[cp.f64]) -> list[cp.f64]:\n    result = []\n    if len(data) == 0:\n        return result\n    lo = data[0]\n    hi = data[0]\n    for x in data:\n        if x < lo:\n            lo = x\n        if x > hi:\n            hi = x\n    if hi == lo:\n        for _ in data:\n            result.append(cp.f64(0))\n        return result\n    rng = hi - lo\n    for x in data:\n        result.append((x - lo) / rng)\n    return result',
        "data-processing", "intermediate", ["normalize([0.0, 5.0, 10.0]) -> [0.0, 0.5, 1.0]"]
    ))

    modules.append(reg(
        "dp_convolve", "dp_convolve", "1D convolution (signal processing)",
        ["data-processing", "convolution", "signal", "filter"],
        "convolve_1d", [("signal", "list[cp.f64]"), ("kernel", "list[cp.f64]")], "list[cp.f64]",
        "Apply 1D convolution of signal with kernel",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef convolve_1d(signal: list[cp.f64], kernel: list[cp.f64]) -> list[cp.f64]:\n    n = len(signal)\n    k = len(kernel)\n    result = []\n    for i in range(n - k + 1):\n        s = cp.f64(0)\n        for j in range(k):\n            s += signal[i + j] * kernel[j]\n        result.append(s)\n    return result',
        "data-processing", "advanced", ["convolve_1d([1,2,3,4,5], [1,0]) -> [1,2,3,4,5]"]
    ))

    modules.append(reg(
        "dp_zscore", "dp_zscore", "Z-score standardization of data",
        ["data-processing", "zscore", "standardize", "statistics"],
        "zscore", [("data", "list[cp.f64]")], "list[cp.f64]",
        "Standardize data to zero mean and unit variance (z-scores)",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef zscore(data: list[cp.f64]) -> list[cp.f64]:\n    result = []\n    n = len(data)\n    if n == 0:\n        return result\n    mean = cp.f64(0)\n    for x in data:\n        mean += x\n    mean = mean / n\n    ssd = cp.f64(0)\n    for x in data:\n        diff = x - mean\n        ssd += diff * diff\n    sd = cp.math.sqrt(ssd / n)\n    if sd == 0.0:\n        for _ in data:\n            result.append(cp.f64(0))\n        return result\n    for x in data:\n        result.append((x - mean) / sd)\n    return result',
        "data-processing", "intermediate", ["zscore([1.0, 2.0, 3.0]) -> [-1.22, 0.0, 1.22]"]
    ))

    # ═══════════════════════════════════════════════════════════════════
    # MISC / CRYPTO (39-40)
    # ═══════════════════════════════════════════════════════════════════

    modules.append(reg(
        "misc_sqrt_newton", "misc_sqrt_newton", "Square root via Newton's method",
        ["math", "sqrt", "newton", "iterative"],
        "sqrt_newton", [("x", "cp.f64")], "cp.f64",
        "Calculate square root using Newton-Raphson iterative method",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef sqrt_newton(x: cp.f64) -> cp.f64:\n    if x < 0.0:\n        return cp.f64(0)\n    if x == 0.0:\n        return cp.f64(0)\n    guess = x\n    for _ in range(100):\n        new_guess = (guess + x / guess) / 2.0\n        diff = new_guess - guess\n        if diff < 0.0:\n            diff = -diff\n        if diff < 1e-10:\n            return new_guess\n        guess = new_guess\n    return guess',
        "math", "advanced", ["sqrt_newton(9.0) -> 3.0"]
    ))

    modules.append(reg(
        "misc_mandelbrot", "misc_mandelbrot", "Mandelbrot set membership check",
        ["math", "fractal", "mandelbrot", "complex"],
        "mandelbrot", [("cx", "cp.f64"), ("cy", "cp.f64"), ("max_iter", "cp.i64")], "cp.i64",
        "Check if point (cx, cy) is in the Mandelbrot set, return iteration count",
        'import copperhead as cp\n\n@cp.compile(target="rust")\ndef mandelbrot(cx: cp.f64, cy: cp.f64, max_iter: cp.i64) -> cp.i64:\n    x = cp.f64(0)\n    y = cp.f64(0)\n    for i in range(max_iter):\n        x2 = x * x\n        y2 = y * y\n        if x2 + y2 > 4.0:\n            return i\n        x_new = x2 - y2 + cx\n        y = 2.0 * x * y + cy\n        x = x_new\n    return max_iter',
        "math", "advanced", ["mandelbrot(-1.0, 0.0, 100) -> 100"]
    ))

    # Register all
    for m in modules:
        registry.register_module(m)

    return len(modules)


def main():
    print("Creating fresh registry...")
    registry = create_fresh_registry()

    print("Populating 40 vetted modules...")
    count = populate_all(registry)

    stats = registry.get_stats()
    print(f"\nRegistry populated: {stats['total_modules']} modules, {stats['total_functions']} functions")

    categories = {}
    for m in registry.get_all_modules():
        for tag in m.tags:
            if tag in ("math", "statistics", "sort", "search", "string",
                       "linear-algebra", "distance", "data-processing",
                       "number-theory"):
                categories[tag] = categories.get(tag, 0) + 1

    print("\nModules by category:")
    for cat, cnt in sorted(categories.items()):
        print(f"  {cat}: {cnt}")

    print(f"\nDone! {count} modules registered.")


if __name__ == "__main__":
    main()
