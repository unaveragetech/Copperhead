"""
Test Interpreter: AI iterates and fixes errors until code works.
"""

import subprocess
import re
import ast
import time


def run_ollama(prompt):
    result = subprocess.run(
        ['ollama', 'run', 'maryasov/qwen2.5-coder-cline:latest'],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
        encoding='utf-8',
        errors='ignore'
    )
    output = result.stdout
    output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
    output = re.sub(r'\[K', '', output)
    output = re.sub(r'\[\?25[hl]', '', output)
    return output.strip()


def extract_code(response):
    """Extract code from markdown code blocks."""
    code = response
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0]
    elif "```" in code:
        code = code.split("```")[1].split("```")[0]
    return code.strip()


def validate_code(code):
    """Validate code and return issues."""
    issues = []
    
    # Check syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"Syntax error: {e}")
    
    # Check imports
    if "import copperhead" not in code:
        issues.append("Missing 'import copperhead'")
    
    # Check decorator
    if "@cp.compile" not in code:
        issues.append("Missing @cp.compile decorator")
    
    # Check types
    if "cp.f64" not in code and "cp.i64" not in code and "cp.i32" not in code:
        issues.append("Missing Copperhead types")
    
    # Check function definition
    if "def " not in code:
        issues.append("No function defined")
    
    # Check for common mistakes
    if "cp.sqrt" in code:
        issues.append("Should use cp.math.sqrt, not cp.sqrt")
    if "import cupy" in code:
        issues.append("Wrong import: should be copperhead, not cupy")
    
    return issues


def test_with_iteration():
    """Test AI generating code with iteration until it works."""
    print("=" * 70)
    print("INTERPRETER TEST: AI Iterates Until Code Works")
    print("=" * 70)
    
    description = """Write a Copperhead function that:
1. Takes a list of numbers
2. Calculates the mean
3. Returns the mean
4. Uses cp.f64 type
5. Handles empty list"""
    
    print("\nDescription:")
    print(description)
    
    max_iterations = 5
    code = None
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")
        
        # Build prompt with error feedback
        if iteration == 1:
            prompt = f"""{description}

Use import copperhead as cp.
Use @cp.compile(target="rust") decorator.
Use cp.f64 for numbers.
Use cp.Vec for lists.
Only return the Python code, no explanation."""
        else:
            prompt = f"""The previous code had errors:

Previous code:
```python
{code}
```

Errors found:
{chr(10).join(previous_issues)}

Fix these errors and return corrected code. Use import copperhead as cp, @cp.compile(target="rust"), cp.f64, and cp.Vec."""
        
        # Generate code
        print("Generating...")
        response = run_ollama(prompt)
        code = extract_code(response)
        
        print(f"\nGenerated code:")
        print(code)
        
        # Validate
        issues = validate_code(code)
        previous_issues = issues
        
        if not issues:
            print(f"\n[PASS] Code is valid after {iteration} iteration(s)!")
            return True, code, iteration
        else:
            print(f"\n[FAIL] Issues found:")
            for issue in issues:
                print(f"  - {issue}")
    
    print(f"\n[FAIL] Could not generate valid code after {max_iterations} iterations")
    return False, code, max_iterations


def test_error_fixing():
    """Test AI fixing specific errors."""
    print("\n" + "=" * 70)
    print("TEST: AI Fixes Specific Errors")
    print("=" * 70)
    
    # Start with intentionally broken code
    broken_code = """import copperhead as cp

@cp.compile(target="rust")
def calculate_mean(numbers):
    mean = cp.mean(numbers)
    return mean"""
    
    print("\nStarting with broken code:")
    print(broken_code)
    
    issues = [
        "cp.mean() does not exist - should use manual calculation",
        "Missing type annotations (should use cp.f64, cp.Vec)",
    ]
    
    print("\nKnown issues:")
    for issue in issues:
        print(f"  - {issue}")
    
    prompt = f"""The following Copperhead code has errors:

```python
{broken_code}
```

Errors:
1. cp.mean() does not exist - calculate mean manually
2. Missing type annotations - use cp.f64 and cp.Vec

Fix these errors and return corrected code. Use import copperhead as cp, @cp.compile(target="rust"), cp.f64, and cp.Vec."""
    
    print("\nAsking AI to fix...")
    response = run_ollama(prompt)
    code = extract_code(response)
    
    print("\nFixed code:")
    print(code)
    
    # Validate
    issues = validate_code(code)
    
    if not issues:
        print("\n[PASS] AI successfully fixed the code!")
        return True
    else:
        print("\n[FAIL] Issues remain:")
        for issue in issues:
            print(f"  - {issue}")
        return False


if __name__ == "__main__":
    print("INTERPRETER ITERATION TEST")
    print("=" * 70)
    
    # Test 1: Iterative generation
    success1, final_code, iterations = test_with_iteration()
    
    # Test 2: Error fixing
    success2 = test_error_fixing()
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Iterative Generation: {'PASS' if success1 else 'FAIL'} ({iterations} iterations)")
    print(f"  Error Fixing: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests failed.")
