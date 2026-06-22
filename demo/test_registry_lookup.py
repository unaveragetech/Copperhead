"""Test AI registry lookup: can the AI find and reuse saved functions?"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copperhead.registry import ModuleRegistry


def test_registry_search():
    """Test that registry search returns relevant results."""
    db_path = os.path.join(tempfile.gettempdir(), "test_ai_registry.db")
    registry = ModuleRegistry(db_path=db_path)

    # Populate with basic examples
    from copperhead.registry import ModuleMetadata, FunctionSignature, ModuleStatus

    registry.register_module(ModuleMetadata(
        id="basic_sum",
        name="basic_sum",
        description="Sum a list of numbers using Copperhead",
        functions=[
            FunctionSignature(
                name="sum_list",
                args=[("numbers", "list[f64]")],
                return_type="f64",
                description="Sum all numbers in a list",
                examples=[
                    "sum_list([1.0, 2.0, 3.0]) == 6.0",
                    "sum_list([]) == 0.0"
                ]
            )
        ],
        tags=["math", "list", "sum"],
        status=ModuleStatus.COMPILED,
        usage_count=0
    ))

    registry.register_module(ModuleMetadata(
        id="sort_numbers",
        name="sort_numbers",
        description="Sort a list of numbers using quicksort",
        functions=[
            FunctionSignature(
                name="sort_numbers",
                args=[("numbers", "list[i64]")],
                return_type="list[i64]",
                description="Sort a list of integers in ascending order",
                examples=[
                    "sort_numbers([3, 1, 2]) == [1, 2, 3]"
                ]
            )
        ],
        tags=["sort", "list", "algorithm"],
        status=ModuleStatus.COMPILED,
        usage_count=0
    ))

    registry.register_module(ModuleMetadata(
        id="safe_divide",
        name="safe_divide",
        description="Safe division with error handling using Result type",
        functions=[
            FunctionSignature(
                name="divide",
                args=[("a", "f64"), ("b", "f64")],
                return_type="Result<f64, str>",
                description="Divide two numbers, returning Err if divisor is zero",
                examples=[
                    "divide(10.0, 2.0) == Ok(5.0)",
                    "divide(1.0, 0.0) == Err('Division by zero')"
                ]
            )
        ],
        tags=["math", "error", "result"],
        status=ModuleStatus.COMPILED,
        usage_count=0
    ))

    # Test search
    results = registry.search_modules("sort")
    assert len(results) >= 1, f"Expected at least 1 result for 'sort', got {len(results)}"
    assert results[0].name == "sort_numbers"
    print(f"[PASS] Search 'sort': found {len(results)} results")

    # Test function search
    func_results = registry.search_functions("divide")
    assert len(func_results) >= 1, f"Expected divide function, got {len(func_results)}"
    func = func_results[0][1]
    assert func.name == "divide"
    assert func.return_type == "Result<f64, str>"
    print(f"[PASS] Function search 'divide': found with correct return type")

    # Test stats
    stats = registry.get_stats()
    assert stats["total_modules"] == 3
    assert stats["total_functions"] == 3
    print(f"[PASS] Stats: {stats['total_modules']} modules, {stats['total_functions']} functions")

    # Test that examples are stored correctly
    module = registry.get_module("basic_sum")
    assert module is not None
    func = module.functions[0]
    assert func.examples[0] == "sum_list([1.0, 2.0, 3.0]) == 6.0"
    print(f"[PASS] Examples stored correctly")

    # Cleanup (ignore Windows lock)
    try:
        os.remove(db_path)
    except PermissionError:
        pass


if __name__ == "__main__":
    test_registry_search()
    print("\nAll registry tests passed!")
