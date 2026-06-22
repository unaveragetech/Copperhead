"""
Populate the registry with basic and advanced Copperhead examples.
This allows the AI to look up existing functions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copperhead.registry import ModuleRegistry, ModuleMetadata, FunctionSignature, ModuleStatus


def create_registry():
    """Create a fresh registry."""
    from copperhead.registry import ModuleRegistry
    import tempfile
    # Use default path inside package
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(pkg_dir, "copperhead", ".copperhead", "registry.db")
    # Remove old DB if exists (handle Windows locks gracefully)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass  # Will be overwritten by new connection
    return ModuleRegistry(db_path=db_path)


def populate_basic_examples(registry: ModuleRegistry):
    """Add basic Copperhead examples."""
    
    # 1. Sum function
    registry.register_module(ModuleMetadata(
        id="basic_sum",
        name="basic_sum",
        description="Sum a list of numbers using Copperhead",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "basic", "sum", "aggregate"],
        functions=[
            FunctionSignature(
                name="sum_list",
                args=[("numbers", "list[cp.f64]")],
                return_type="cp.f64",
                description="Calculate the sum of a list of floating point numbers",
                is_rpb=True,
                examples=["sum_list([1.0, 2.0, 3.0]) -> 6.0"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def sum_list(numbers: list[cp.f64]) -> cp.f64:
    \"\"\"Calculate the sum of a list of numbers.\"\"\"
    total = cp.f64(0)
    for num in numbers:
        total += num
    return total"""
    ))
    
    # 2. Find max
    registry.register_module(ModuleMetadata(
        id="basic_max",
        name="basic_max",
        description="Find maximum value in a list",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "basic", "max", "search"],
        functions=[
            FunctionSignature(
                name="find_max",
                args=[("numbers", "list[cp.f64]")],
                return_type="cp.f64",
                description="Find the maximum value in a list of numbers",
                is_rpb=True,
                examples=["find_max([3.0, 1.0, 4.0, 1.0, 5.0]) -> 5.0"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def find_max(numbers: list[cp.f64]) -> cp.f64:
    \"\"\"Find the maximum value in a list.\"\"\"
    if len(numbers) == 0:
        return cp.f64(0)
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val"""
    ))
    
    # 3. Count occurrences
    registry.register_module(ModuleMetadata(
        id="basic_count",
        name="basic_count",
        description="Count occurrences of a value in a list",
        version="1.0.0",
        author="Copperhead",
        tags=["search", "basic", "count", "frequency"],
        functions=[
            FunctionSignature(
                name="count_occurrences",
                args=[("items", "list"), ("target", "object")],
                return_type="cp.i64",
                description="Count how many times target appears in items",
                is_rpb=True,
                examples=["count_occurrences([1, 2, 2, 3, 2], 2) -> 3"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def count_occurrences(items: list, target) -> cp.i64:
    \"\"\"Count how many times target appears in items.\"\"\"
    count = 0
    for item in items:
        if item == target:
            count += 1
    return count"""
    ))
    
    # 4. Clamp value
    registry.register_module(ModuleMetadata(
        id="basic_clamp",
        name="basic_clamp",
        description="Clamp a value between min and max",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "basic", "clamp", "bounds"],
        functions=[
            FunctionSignature(
                name="clamp",
                args=[("value", "cp.f64"), ("min_val", "cp.f64"), ("max_val", "cp.f64")],
                return_type="cp.f64",
                description="Clamp a value between min and max bounds",
                is_rpb=True,
                examples=["clamp(5.0, 0.0, 10.0) -> 5.0", "clamp(-5.0, 0.0, 10.0) -> 0.0"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def clamp(value: cp.f64, min_val: cp.f64, max_val: cp.f64) -> cp.f64:
    \"\"\"Clamp a value between min and max bounds.\"\"\"
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value"""
    ))
    
    # 5. Average
    registry.register_module(ModuleMetadata(
        id="basic_average",
        name="basic_average",
        description="Calculate the average of a list of numbers",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "basic", "average", "mean", "statistics"],
        functions=[
            FunctionSignature(
                name="average",
                args=[("numbers", "list[cp.f64]")],
                return_type="cp.f64",
                description="Calculate the arithmetic mean of a list of numbers",
                is_rpb=True,
                examples=["average([1.0, 2.0, 3.0, 4.0, 5.0]) -> 3.0"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def average(numbers: list[cp.f64]) -> cp.f64:
    \"\"\"Calculate the arithmetic mean of a list.\"\"\"
    if len(numbers) == 0:
        return cp.f64(0)
    total = cp.f64(0)
    for num in numbers:
        total += num
    return total / len(numbers)"""
    ))
    
    print("Added 5 basic examples")


def populate_advanced_examples(registry: ModuleRegistry):
    """Add advanced Copperhead examples."""
    
    # 1. Fibonacci
    registry.register_module(ModuleMetadata(
        id="adv_fibonacci",
        name="adv_fibonacci",
        description="Calculate Fibonacci numbers iteratively",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "advanced", "fibonacci", "sequence", "recursion"],
        functions=[
            FunctionSignature(
                name="fibonacci",
                args=[("n", "cp.i64")],
                return_type="cp.i64",
                description="Calculate the nth Fibonacci number iteratively",
                is_rpb=True,
                examples=["fibonacci(10) -> 55", "fibonacci(0) -> 0"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def fibonacci(n: cp.i64) -> cp.i64:
    \"\"\"Calculate the nth Fibonacci number iteratively.\"\"\"
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b"""
    ))
    
    # 2. Bubble sort
    registry.register_module(ModuleMetadata(
        id="adv_bubblesort",
        name="adv_bubblesort",
        description="Sort a list using bubble sort algorithm",
        version="1.0.0",
        author="Copperhead",
        tags=["sort", "advanced", "algorithm", "bubble"],
        functions=[
            FunctionSignature(
                name="bubble_sort",
                args=[("arr", "list[cp.f64]")],
                return_type="list[cp.f64]",
                description="Sort a list of numbers using bubble sort",
                is_rpb=True,
                examples=["bubble_sort([3.0, 1.0, 4.0, 1.0, 5.0]) -> [1.0, 1.0, 3.0, 4.0, 5.0]"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def bubble_sort(arr: list[cp.f64]) -> list[cp.f64]:
    \"\"\"Sort a list using bubble sort algorithm.\"\"\"
    n = len(arr)
    result = list(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result"""
    ))
    
    # 3. Matrix multiply
    registry.register_module(ModuleMetadata(
        id="adv_matrix_mul",
        name="adv_matrix_mul",
        description="Multiply two matrices",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "advanced", "matrix", "linear-algebra", "multiply"],
        functions=[
            FunctionSignature(
                name="matrix_multiply",
                args=[("a", "list[list[cp.f64]]"), ("b", "list[list[cp.f64]]")],
                return_type="list[list[cp.f64]]",
                description="Multiply two matrices and return the result",
                is_rpb=True,
                examples=["matrix_multiply([[1,2],[3,4]], [[5,6],[7,8]]) -> [[19,22],[43,50]]"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def matrix_multiply(a: list[list[cp.f64]], b: list[list[cp.f64]]) -> list[list[cp.f64]]:
    \"\"\"Multiply two matrices.\"\"\"
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    
    result = [[cp.f64(0) for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result"""
    ))
    
    # 4. Prime check
    registry.register_module(ModuleMetadata(
        id="adv_prime_check",
        name="adv_prime_check",
        description="Check if a number is prime",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "advanced", "prime", "number-theory"],
        functions=[
            FunctionSignature(
                name="is_prime",
                args=[("n", "cp.i64")],
                return_type="cp.bool",
                description="Check if a number is prime",
                is_rpb=True,
                examples=["is_prime(7) -> True", "is_prime(4) -> False"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def is_prime(n: cp.i64) -> cp.bool:
    \"\"\"Check if a number is prime.\"\"\"
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
    return True"""
    ))
    
    # 5. GCD
    registry.register_module(ModuleMetadata(
        id="adv_gcd",
        name="adv_gcd",
        description="Calculate Greatest Common Divisor using Euclidean algorithm",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "advanced", "gcd", "number-theory", "euclidean"],
        functions=[
            FunctionSignature(
                name="gcd",
                args=[("a", "cp.i64"), ("b", "cp.i64")],
                return_type="cp.i64",
                description="Calculate the Greatest Common Divisor of two numbers",
                is_rpb=True,
                examples=["gcd(12, 8) -> 4", "gcd(54, 24) -> 6"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def gcd(a: cp.i64, b: cp.i64) -> cp.i64:
    \"\"\"Calculate GCD using Euclidean algorithm.\"\"\"
    while b:
        a, b = b, a % b
    return a"""
    ))
    
    # 6. String reverse
    registry.register_module(ModuleMetadata(
        id="adv_string_reverse",
        name="adv_string_reverse",
        description="Reverse a string",
        version="1.0.0",
        author="Copperhead",
        tags=["string", "advanced", "reverse", "manipulation"],
        functions=[
            FunctionSignature(
                name="reverse_string",
                args=[("s", "str")],
                return_type="str",
                description="Reverse a string",
                is_rpb=True,
                examples=["reverse_string('hello') -> 'olleh'"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def reverse_string(s: str) -> str:
    \"\"\"Reverse a string.\"\"\"
    return s[::-1]"""
    ))
    
    # 7. Linear search
    registry.register_module(ModuleMetadata(
        id="adv_linear_search",
        name="adv_linear_search",
        description="Search for a value in a list",
        version="1.0.0",
        author="Copperhead",
        tags=["search", "advanced", "linear", "algorithm"],
        functions=[
            FunctionSignature(
                name="linear_search",
                args=[("arr", "list"), ("target", "object")],
                return_type="cp.i64",
                description="Search for target in arr, return index or -1 if not found",
                is_rpb=True,
                examples=["linear_search([1,2,3,4,5], 3) -> 2", "linear_search([1,2,3], 6) -> -1"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def linear_search(arr: list, target) -> cp.i64:
    \"\"\"Search for target in arr, return index or -1.\"\"\"
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1"""
    ))
    
    # 8. Error handling example
    registry.register_module(ModuleMetadata(
        id="adv_safe_divide",
        name="adv_safe_divide",
        description="Safe division with error handling using Result type",
        version="1.0.0",
        author="Copperhead",
        tags=["math", "advanced", "error-handling", "result", "division"],
        functions=[
            FunctionSignature(
                name="safe_divide",
                args=[("a", "cp.f64"), ("b", "cp.f64")],
                return_type="cp.Result[cp.f64]",
                description="Divide two numbers safely, returning Result type",
                is_rpb=True,
                examples=["safe_divide(10.0, 2.0) -> Ok(5.0)", "safe_divide(10.0, 0.0) -> Err('Division by zero')"]
            )
        ],
        status=ModuleStatus.COMPILED,
        rust_code="""import copperhead as cp

@cp.compile(target="rust")
def safe_divide(a: cp.f64, b: cp.f64):
    \"\"\"Divide two numbers safely.\"\"\"
    if b == 0.0:
        return cp.Err("Division by zero")
    return cp.Ok(a / b)"""
    ))
    
    print("Added 8 advanced examples")


def main():
    """Populate the registry."""
    print("Creating registry...")
    registry = create_registry()
    
    print("Populating basic examples...")
    populate_basic_examples(registry)
    
    print("Populating advanced examples...")
    populate_advanced_examples(registry)
    
    # Print stats
    stats = registry.get_stats()
    print(f"\nRegistry populated:")
    print(f"  Modules: {stats['total_modules']}")
    print(f"  Functions: {stats['total_functions']}")
    
    # Test search
    print("\nTesting search...")
    results = registry.search_modules("sort")
    print(f"  Search 'sort': {len(results)} results")
    
    results = registry.search_modules("math")
    print(f"  Search 'math': {len(results)} results")
    
    results = registry.search_functions("divide")
    print(f"  Search functions 'divide': {len(results)} results")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
