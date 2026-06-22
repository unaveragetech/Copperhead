"""Test AI registry integration: verify the AI receives registry context."""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copperhead.registry import (
    ModuleRegistry, ModuleMetadata, FunctionSignature, ModuleStatus
)


def setup_registry():
    """Create a registry with known functions."""
    db_path = os.path.join(tempfile.gettempdir(), "test_ai_integration.db")
    registry = ModuleRegistry(db_path=db_path)

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
                examples=["sum_list([1.0, 2.0, 3.0]) == 6.0"]
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
                examples=["sort_numbers([3, 1, 2]) == [1, 2, 3]"]
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
                examples=["divide(10.0, 2.0) == Ok(5.0)"]
            )
        ],
        tags=["math", "error", "result"],
        status=ModuleStatus.COMPILED,
        usage_count=0
    ))

    return registry, db_path


def test_search_finds_sort():
    """Registry search finds sort function for 'sort a list' query."""
    registry, db_path = setup_registry()
    results = registry.search_functions("sort")
    assert len(results) >= 1, f"Expected sort function, got {len(results)}"
    func = results[0][1]
    assert func.name == "sort_numbers"
    print(f"[PASS] Search 'sort': found {func.name}({func.args}) -> {func.return_type}")
    try:
        os.remove(db_path)
    except PermissionError:
        pass


def test_search_finds_sum():
    """Registry search finds sum function for 'sum numbers' query."""
    registry, db_path = setup_registry()
    results = registry.search_functions("sum")
    assert len(results) >= 1
    func = results[0][1]
    assert func.name == "sum_list"
    print(f"[PASS] Search 'sum': found {func.name}")
    try:
        os.remove(db_path)
    except PermissionError:
        pass


def test_search_finds_divide():
    """Registry search finds divide function for 'division' query."""
    registry, db_path = setup_registry()
    results = registry.search_functions("divide")
    assert len(results) >= 1
    func = results[0][1]
    assert func.name == "divide"
    assert "Result" in func.return_type
    print(f"[PASS] Search 'divide': found {func.name} -> {func.return_type}")
    try:
        os.remove(db_path)
    except PermissionError:
        pass


def test_prompt_includes_registry():
    """Verify the AI prompt includes registry function context."""
    # Simulate what the AI does: search registry and build prompt
    registry, db_path = setup_registry()

    # Search for "sort" functions
    keywords = "sort a list of numbers".lower().split()
    results = []
    for kw in keywords:
        if len(kw) > 3:
            matches = registry.search_functions(kw, limit=5)
            results.extend(matches)

    # Deduplicate
    seen = set()
    unique = []
    for module, func in results:
        key = f"{module.id}:{func.name}"
        if key not in seen:
            seen.add(key)
            unique.append((module, func))

    assert len(unique) >= 1, "Expected at least 1 unique match"

    # Build prompt section like the AI does
    prompt_parts = ["User description: Create a function that sorts a list"]
    prompt_parts.append("\n## EXISTING FUNCTIONS IN REGISTRY")
    prompt_parts.append("Consider reusing these functions instead of rewriting:")
    for module, func in unique[:5]:
        args_str = ", ".join([f"{name}: {type_}" for name, type_ in func.args])
        prompt_parts.append(f"- {module.name}.{func.name}({args_str}) -> {func.return_type}")

    prompt = "\n".join(prompt_parts)

    # Verify prompt contains registry info
    assert "sort_numbers" in prompt
    assert "list[i64]" in prompt
    assert "EXISTING FUNCTIONS IN REGISTRY" in prompt
    print(f"[PASS] Prompt includes registry context ({len(unique)} functions)")
    print(f"  Sample prompt section:\n{chr(10).join(prompt_parts[2:5])}")
    try:
        os.remove(db_path)
    except PermissionError:
        pass


def test_copperhead_coder_uses_registry():
    """Verify CopperheadCoder._search_registry returns results."""
    from copperhead.llm import CopperheadCoder

    # Create coder with temp registry
    registry, db_path = setup_registry()
    coder = CopperheadCoder.__new__(CopperheadCoder)
    coder.registry = registry

    # Test search
    results = coder._search_registry("sort a list of numbers")
    assert len(results) >= 1, f"Expected results, got {len(results)}"
    module, func = results[0]
    assert func.name == "sort_numbers"
    print(f"[PASS] CopperheadCoder._search_registry found {func.name}")

    # Test prompt building
    prompt = coder._build_prompt(
        "Create a function that sorts a list",
        existing_code=None,
        last_code=None,
        iteration=1,
        existing_functions=results,
        used_modules=[]
    )
    assert "sort_numbers" in prompt
    assert "EXISTING FUNCTIONS IN REGISTRY" in prompt
    print(f"[PASS] Prompt builder includes registry functions")
    try:
        os.remove(db_path)
    except PermissionError:
        pass


if __name__ == "__main__":
    test_search_finds_sort()
    test_search_finds_sum()
    test_search_finds_divide()
    test_prompt_includes_registry()
    test_copperhead_coder_uses_registry()
    print("\nAll AI registry integration tests passed!")
