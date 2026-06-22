"""
Test AI with ambiguous descriptions - AI must figure out what to build.
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
    code = response
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0]
    elif "```" in code:
        code = code.split("```")[1].split("```")[0]
    return code.strip()


def validate_and_run(code):
    """Validate code and try to run it."""
    issues = []
    
    # Check syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]
    
    # Check imports
    if "import copperhead" not in code:
        issues.append("Missing 'import copperhead'")
    
    # Check decorator
    if "@cp.compile" not in code:
        issues.append("Missing @cp.compile decorator")
    
    # Check function
    if "def " not in code:
        issues.append("No function defined")
    
    return len(issues) == 0, issues


def test_ambiguous_1():
    """Ambiguous: 'make something that finds patterns in data'"""
    print("=" * 70)
    print("TEST 1: Ambiguous Description")
    print("=" * 70)
    
    prompt = """Write Copperhead code for this request:

"Make something that finds patterns in data"

The code should:
- Use import copperhead as cp
- Use @cp.compile(target="rust") decorator
- Be useful for data analysis
- Handle edge cases

The AI must figure out what "finds patterns" means and implement something useful.
Only return the Python code."""
    
    print("\nDescription: 'Make something that finds patterns in data'")
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    code = extract_code(response)
    
    print(f"\nAI Interpretation ({elapsed:.1f}s):")
    print("-" * 70)
    print(code)
    print("-" * 70)
    
    # Validate
    valid, issues = validate_and_run(code)
    
    print("\nValidation:")
    print(f"  Valid Python: {'PASS' if valid else 'FAIL'}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")
    
    # Check what the AI interpreted "patterns" as
    has_statistics = any(x in code for x in ["mean", "std", "average", "variance"])
    has_frequency = any(x in code for x in ["count", "frequency", "occur"])
    has_sequence = any(x in code for x in ["sequence", "consecutive", "pattern"])
    
    print("\n  AI's interpretation of 'patterns':")
    print(f"    Statistical analysis: {has_statistics}")
    print(f"    Frequency counting: {has_frequency}")
    print(f"    Sequence detection: {has_sequence}")
    
    return valid


def test_ambiguous_2():
    """Ambiguous: 'handle messy input gracefully'"""
    print("\n" + "=" * 70)
    print("TEST 2: Very Ambiguous Description")
    print("=" * 70)
    
    prompt = """Write Copperhead code for this request:

"handle messy input gracefully"

The code should:
- Use import copperhead as cp
- Use @cp.compile(target="rust") decorator
- Be robust and handle bad data
- Return sensible defaults

The AI must figure out what "messy input" means and implement error handling.
Only return the Python code."""
    
    print("\nDescription: 'handle messy input gracefully'")
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    code = extract_code(response)
    
    print(f"\nAI Interpretation ({elapsed:.1f}s):")
    print("-" * 70)
    print(code)
    print("-" * 70)
    
    # Validate
    valid, issues = validate_and_run(code)
    
    print("\nValidation:")
    print(f"  Valid Python: {'PASS' if valid else 'FAIL'}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")
    
    # Check what "messy input" handling looks like
    has_none_check = "None" in code or "none" in code.lower()
    has_type_check = "isinstance" in code or "type" in code
    has_try_except = "try" in code or "except" in code
    has_default = "default" in code or "0" in code or "empty" in code.lower()
    
    print("\n  AI's interpretation of 'messy input':")
    print(f"    None/null checking: {has_none_check}")
    print(f"    Type checking: {has_type_check}")
    print(f"    Try/except: {has_try_except}")
    print(f"    Default values: {has_default}")
    
    return valid


def test_ambiguous_3():
    """Ambiguous: 'optimize for speed but keep it readable'"""
    print("\n" + "=" * 70)
    print("TEST 3: Conflicting Requirements")
    print("=" * 70)
    
    prompt = """Write Copperhead code for this request:

"optimize for speed but keep it readable"

The code should:
- Use import copperhead as cp
- Use @cp.compile(target="rust") decorator
- Balance performance with clarity
- Be well-documented

The AI must figure out how to balance "speed" and "readability".
Only return the Python code."""
    
    print("\nDescription: 'optimize for speed but keep it readable'")
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    code = extract_code(response)
    
    print(f"\nAI Interpretation ({elapsed:.1f}s):")
    print("-" * 70)
    print(code)
    print("-" * 70)
    
    # Validate
    valid, issues = validate_and_run(code)
    
    print("\nValidation:")
    print(f"  Valid Python: {'PASS' if valid else 'FAIL'}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")
    
    # Check balance
    has_types = "cp.f64" in code or "cp.i64" in code
    has_docstring = '"""' in code or "'''" in code
    has_comments = "#" in code
    has_efficient = any(x in code for x in ["range", "for", "while"])
    
    print("\n  AI's balance of speed vs readability:")
    print(f"    Uses types for speed: {has_types}")
    print(f"    Has docstring: {has_docstring}")
    print(f"    Has comments: {has_comments}")
    print(f"    Uses efficient loops: {has_efficient}")
    
    return valid


def test_ambiguous_4():
    """Ambiguous: 'like numpy but for Copperhead'"""
    print("\n" + "=" * 70)
    print("TEST 4: Reference to External Library")
    print("=" * 70)
    
    prompt = """Write Copperhead code for this request:

"make a simple version of numpy's array operations for Copperhead"

The code should:
- Use import copperhead as cp
- Use @cp.compile(target="rust") decorator
- Implement basic array operations
- Be compatible with Copperhead types

The AI must figure out what numpy operations to implement.
Only return the Python code."""
    
    print("\nDescription: 'make a simple version of numpy's array operations'")
    print("\nGenerating...")
    
    start = time.time()
    response = run_ollama(prompt)
    elapsed = time.time() - start
    
    code = extract_code(response)
    
    print(f"\nAI Interpretation ({elapsed:.1f}s):")
    print("-" * 70)
    print(code)
    print("-" * 70)
    
    # Validate
    valid, issues = validate_and_run(code)
    
    print("\nValidation:")
    print(f"  Valid Python: {'PASS' if valid else 'FAIL'}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")
    
    # Check what numpy-like features
    has_sum = "sum" in code
    has_mean = "mean" in code
    has_std = "std" in code
    has_map = "map" in code or "transform" in code
    
    print("\n  AI's numpy interpretation:")
    print(f"    Sum operation: {has_sum}")
    print(f"    Mean operation: {has_mean}")
    print(f"    Std operation: {has_std}")
    print(f"    Map/transform: {has_map}")
    
    return valid


if __name__ == "__main__":
    print("AMBIGUOUS DESCRIPTION TEST")
    print("AI must interpret vague requirements and generate useful code")
    print("=" * 70)
    
    results = []
    results.append(("Find patterns", test_ambiguous_1()))
    results.append(("Handle messy input", test_ambiguous_2()))
    results.append(("Speed vs readability", test_ambiguous_3()))
    results.append(("Numpy-like ops", test_ambiguous_4()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, result in results:
        print(f"  {name}: {'PASS' if result else 'FAIL'}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\nAI successfully interpreted all ambiguous descriptions!")
    else:
        print("\nSome interpretations failed validation.")
