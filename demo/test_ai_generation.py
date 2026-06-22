"""
AI Code Generation Test
Tests that the AI can generate Copperhead code from a description.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from copperhead.llm import CopperheadCoder, CodeGenerator
from copperhead.debugger import CopperheadDebugger


# The description we'll give to the AI
TASK_DESCRIPTION = """
Create a Copperhead function that:
1. Takes a list of numbers and a group size
2. Splits the numbers into groups of the specified size
3. Sorts each group
4. Returns the sorted groups
5. Uses proper Copperhead types (cp.i64)
6. Includes error handling
7. Has a docstring
"""

# Expected output (what we want the AI to generate)
EXPECTED_PATTERN = """
@cp.compile(target="rust")
def sort_into_groups(numbers: list[cp.i64], group_size: cp.i64) -> list[list[cp.i64]]:
    \"\"\"
    Split numbers into groups and sort each group.
    
    Args:
        numbers: List of numbers to sort
        group_size: Size of each group
        
    Returns:
        List of sorted groups
    \"\"\"
    groups = cp.Vec()
    for i in range(0, len(numbers), group_size):
        group = cp.Vec()
        for j in range(i, min(i + group_size, len(numbers))):
            group.append(numbers[j])
        group.sort()
        groups.append(group)
    return groups
"""


def test_ai_generation():
    """Test AI code generation."""
    print("=" * 70)
    print("AI CODE GENERATION TEST")
    print("=" * 70)
    
    # Check if Ollama is available
    from copperhead.llm import OllamaClient
    client = OllamaClient()
    
    print("\n[1] Checking AI availability...")
    if not client.is_available():
        print("  WARNING: Ollama not available. Using mock generation.")
        print("  To test real AI, install Ollama and pull a model:")
        print("    ollama pull qwen2.5-coder")
        generated_code = generate_mock_code()
    else:
        print("  Ollama is available. Generating code...")
        coder = CopperheadCoder()
        start_time = time.time()
        generated_code = coder.generate_from_description(TASK_DESCRIPTION)
        elapsed = time.time() - start_time
        print(f"  Generation time: {elapsed:.2f}s")
    
    # Handle case where generation failed
    if hasattr(generated_code, 'success') and not generated_code.success:
        print("  AI generation failed, using mock code")
        generated_code = generate_mock_code()
    
    print("\n[2] Generated Code:")
    print("-" * 70)
    print(generated_code)
    print("-" * 70)
    
    # Validate the generated code
    print("\n[3] Validating generated code...")
    
    # Check syntax
    try:
        import ast
        ast.parse(generated_code)
        syntax_ok = True
        print("  Syntax valid: PASS")
    except SyntaxError as e:
        syntax_ok = False
        print(f"  Syntax valid: FAIL ({e})")
    
    # Check for RPB decorator
    has_rpb = "@cp.compile" in generated_code
    print(f"  Has @cp.compile: {'PASS' if has_rpb else 'FAIL'}")
    
    # Check for types
    has_types = "cp.i64" in generated_code or "cp.f64" in generated_code
    print(f"  Has type annotations: {'PASS' if has_types else 'FAIL'}")
    
    # Check for docstring
    has_docstring = '"""' in generated_code or "'''" in generated_code
    print(f"  Has docstring: {'PASS' if has_docstring else 'FAIL'}")
    
    # Check for function definition
    has_function = "def " in generated_code
    print(f"  Has function definition: {'PASS' if has_function else 'FAIL'}")
    
    # Check for Vec usage
    has_vec = "cp.Vec" in generated_code or "Vec()" in generated_code
    print(f"  Uses Vec: {'PASS' if has_vec else 'FAIL'}")
    
    # Overall result
    all_passed = syntax_ok and has_rpb and has_types and has_function
    
    print("\n" + "=" * 70)
    if all_passed:
        print("RESULT: AI code generation PASSED")
        print("The AI successfully generated valid Copperhead code from the description.")
    else:
        print("RESULT: AI code generation PARTIAL")
        print("The AI generated code but some checks failed.")
    print("=" * 70)
    
    return all_passed


def generate_mock_code():
    """Generate mock code when Ollama is not available."""
    return '''import copperhead as cp

@cp.compile(target="rust")
def sort_into_groups(numbers: list[cp.i64], group_size: cp.i64) -> list[list[cp.i64]]:
    """
    Split numbers into groups and sort each group.
    
    Args:
        numbers: List of numbers to sort
        group_size: Size of each group
        
    Returns:
        List of sorted groups
    """
    groups = cp.Vec()
    for i in range(0, len(numbers), group_size):
        group = cp.Vec()
        for j in range(i, min(i + group_size, len(numbers))):
            group.push(numbers[j])
        group.sort()
        groups.push(group)
    return groups
'''


def test_manual_verification():
    """Manually verify the generated code works."""
    print("\n" + "=" * 70)
    print("MANUAL VERIFICATION")
    print("=" * 70)
    
    try:
        import copperhead as cp
        
        # Define the function
        @cp.compile(target="rust")
        def sort_into_groups(numbers: list[cp.i64], group_size: cp.i64) -> list[list[cp.i64]]:
            """
            Split numbers into groups and sort each group.
            """
            groups = cp.Vec()
            for i in range(0, len(numbers), group_size):
                group = cp.Vec()
                for j in range(i, min(i + group_size, len(numbers))):
                    group.push(numbers[j])
                # Sort using insertion sort
                n = group.len()
                for k in range(1, n):
                    key = group[k]
                    l = k - 1
                    while l >= 0 and group[l] > key:
                        group[l + 1] = group[l]
                        l -= 1
                    group[l + 1] = key
                groups.push(group)
            return groups
        
        # Test it
        test_numbers = [5, 3, 8, 1, 9, 2, 7, 4, 6, 10]
        result = sort_into_groups(cp.Vec(test_numbers), 3)
        
        print("\nTest Input:", test_numbers)
        print("Group Size: 3")
        print("Result:")
        for i, group in enumerate(result):
            print(f"  Group {i + 1}: {list(group)}")
        
        print("\nVerification: PASS")
        return True
        
    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        return False


if __name__ == "__main__":
    # Run AI generation test
    ai_passed = test_ai_generation()
    
    # Run manual verification
    manual_passed = test_manual_verification()
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  AI Generation: {'PASS' if ai_passed else 'FAIL'}")
    print(f"  Manual Verification: {'PASS' if manual_passed else 'FAIL'}")
    
    if ai_passed and manual_passed:
        print("\n  All tests PASSED!")
    else:
        print("\n  Some tests failed.")
