"""
Real Ollama Test - No Mock Data
Tests that Ollama can generate Copperhead code from descriptions.
"""

import subprocess
import json
import ast
import time


def run_ollama(prompt: str, model: str = "maryasov/qwen2.5-coder-cline:latest") -> str:
    """Run Ollama and get response."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='ignore'
        )
        # Clean up terminal escape sequences
        output = result.stdout
        # Remove ANSI escape codes
        import re
        output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
        output = re.sub(r'\[K', '', output)
        output = re.sub(r'\[\?25[hl]', '', output)
        output = re.sub(r'\[[0-9]+G', '', output)
        output = re.sub(r'\[2K', '', output)
        return output.strip()
    except Exception as e:
        return f"Error: {e}"


def test_basic_generation():
    """Test 1: Basic code generation from description."""
    print("=" * 70)
    print("TEST 1: Basic Copperhead Code Generation")
    print("=" * 70)
    
    prompt = """Write a Copperhead function that takes a list of numbers and returns the sum.
Use proper Copperhead types (cp.f64) and the @cp.compile decorator.
Only return the Python code, no explanation.

Example format:
import copperhead as cp

@cp.compile(target="rust")
def function_name(param: type) -> return_type:
    # code here
    return result
"""
    
    print("\nPrompt:")
    print(prompt)
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    print(f"\nResponse ({elapsed:.1f}s):")
    print("-" * 70)
    print(response)
    print("-" * 70)
    
    # Validate
    checks = {
        "Has import copperhead": "import copperhead" in response,
        "Has @cp.compile": "@cp.compile" in response,
        "Has def keyword": "def " in response,
        "Has return statement": "return " in response,
        "Syntax valid": False,
    }
    
    # Try to parse as Python
    try:
        # Extract code block if present
        code = response
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        ast.parse(code)
        checks["Syntax valid"] = True
    except:
        pass
    
    print("\nValidation:")
    for check, passed in checks.items():
        print(f"  {check}: {'PASS' if passed else 'FAIL'}")
    
    return all(checks.values())


def test_sort_function():
    """Test 2: Generate a sort function."""
    print("\n" + "=" * 70)
    print("TEST 2: Generate Sort Function")
    print("=" * 70)
    
    prompt = """Write a Copperhead function that sorts a list of integers.
Use @cp.compile(target="rust") decorator.
Use cp.i64 type for integers.
Use cp.Vec for the list.
Only return the Python code.
"""
    
    print("\nPrompt:")
    print(prompt)
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    print(f"\nResponse ({elapsed:.1f}s):")
    print("-" * 70)
    print(response)
    print("-" * 70)
    
    # Validate
    checks = {
        "Has import copperhead": "import copperhead" in response,
        "Has @cp.compile": "@cp.compile" in response,
        "Has cp.i64": "cp.i64" in response,
        "Has def keyword": "def " in response,
        "Syntax valid": False,
    }
    
    try:
        code = response
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        ast.parse(code)
        checks["Syntax valid"] = True
    except:
        pass
    
    print("\nValidation:")
    for check, passed in checks.items():
        print(f"  {check}: {'PASS' if passed else 'FAIL'}")
    
    return all(checks.values())


def test_error_handling():
    """Test 3: Generate code with error handling."""
    print("\n" + "=" * 70)
    print("TEST 3: Generate with Error Handling")
    print("=" * 70)
    
    prompt = """Write a Copperhead function that divides two numbers.
It should return cp.Err if dividing by zero, cp.Ok otherwise.
Use @cp.compile(target="rust") decorator.
Use cp.f64 type.
Only return the Python code.
"""
    
    print("\nPrompt:")
    print(prompt)
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    print(f"\nResponse ({elapsed:.1f}s):")
    print("-" * 70)
    print(response)
    print("-" * 70)
    
    # Validate
    checks = {
        "Has import copperhead": "import copperhead" in response,
        "Has @cp.compile": "@cp.compile" in response,
        "Has cp.f64": "cp.f64" in response,
        "Has cp.Err": "cp.Err" in response,
        "Has cp.Ok": "cp.Ok" in response,
        "Has def keyword": "def " in response,
        "Syntax valid": False,
    }
    
    try:
        code = response
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        ast.parse(code)
        checks["Syntax valid"] = True
    except:
        pass
    
    print("\nValidation:")
    for check, passed in checks.items():
        print(f"  {check}: {'PASS' if passed else 'FAIL'}")
    
    return all(checks.values())


def test_complex_function():
    """Test 4: Generate a complex function with multiple operations."""
    print("\n" + "=" * 70)
    print("TEST 4: Generate Complex Function")
    print("=" * 70)
    
    prompt = """Write a Copperhead function that:
1. Takes a list of numbers (cp.f64)
2. Calculates the mean and standard deviation
3. Returns a dictionary with both values
4. Uses @cp.compile(target="rust") decorator
5. Uses cp.math for calculations
6. Has proper error handling for empty lists
Only return the Python code.
"""
    
    print("\nPrompt:")
    print(prompt)
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    print(f"\nResponse ({elapsed:.1f}s):")
    print("-" * 70)
    print(response)
    print("-" * 70)
    
    # Validate
    checks = {
        "Has import copperhead": "import copperhead" in response,
        "Has @cp.compile": "@cp.compile" in response,
        "Has cp.f64": "cp.f64" in response,
        "Has cp.math": "cp.math" in response,
        "Has def keyword": "def " in response,
        "Has return dict": "return" in response and ("{" in response or "dict" in response.lower()),
        "Syntax valid": False,
    }
    
    try:
        code = response
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        ast.parse(code)
        checks["Syntax valid"] = True
    except:
        pass
    
    print("\nValidation:")
    for check, passed in checks.items():
        print(f"  {check}: {'PASS' if passed else 'FAIL'}")
    
    return all(checks.values())


if __name__ == "__main__":
    print("OLLAMA REAL TEST - NO MOCK DATA")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Basic Generation", test_basic_generation()))
    results.append(("Sort Function", test_sort_function()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Complex Function", test_complex_function()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, result in results:
        print(f"  {name}: {'PASS' if result else 'FAIL'}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\nALL TESTS PASSED!")
    else:
        print("\nSome tests failed.")
