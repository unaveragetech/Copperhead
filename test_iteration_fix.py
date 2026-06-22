"""
Test AI iterating and fixing code based on execution feedback.
"""

import subprocess
import re
import ast


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


def try_execute(code):
    """Try to execute the code and return any errors."""
    try:
        # Import real copperhead module
        import copperhead as cp
        
        # Remove type hints that don't work at runtime
        # Replace Vec[f64] with just list, etc.
        import re
        clean_code = code
        clean_code = re.sub(r'cp\.Vec\[.*?\]', 'list', clean_code)
        clean_code = re.sub(r'cp\.f64', 'float', clean_code)
        clean_code = re.sub(r'cp\.i64', 'int', clean_code)
        clean_code = re.sub(r'cp\.i32', 'int', clean_code)
        clean_code = re.sub(r'cp\.f32', 'float', clean_code)
        clean_code = re.sub(r'cp\.bool', 'bool', clean_code)
        clean_code = re.sub(r'cp\.str', 'str', clean_code)
        clean_code = re.sub(r'-> cp\.f64', '-> float', clean_code)
        clean_code = re.sub(r'-> cp\.i64', '-> int', clean_code)
        clean_code = re.sub(r'-> list\[.*?\]', '-> list', clean_code)
        
        namespace = {
            'cp': cp,
            '__builtins__': __builtins__,
        }
        
        exec(clean_code, namespace)
        return None, namespace
    except Exception as e:
        return str(e), namespace


def test_iteration_fix():
    """Test AI fixing code based on execution errors."""
    print("=" * 70)
    print("ITERATION FIX TEST")
    print("=" * 70)
    
    # Start with ambiguous description
    description = "Write a function that calculates the average and standard deviation of a list of numbers"
    
    print(f"\nOriginal request: {description}")
    
    # Iteration 1: Initial generation
    print("\n--- Iteration 1: Initial Generation ---")
    prompt = f"""{description}

Use import copperhead as cp.
Use @cp.compile(target="rust") decorator.
Use cp.f64 for numbers.
Use cp.Vec for lists.
Only return the Python code."""
    
    response = run_ollama(prompt)
    code = extract_code(response)
    print(code)
    
    # Try to execute
    error, namespace = try_execute(code)
    
    if error:
        print(f"\nExecution error: {error}")
        
        # Iteration 2: Fix based on error
        print("\n--- Iteration 2: Fix Based on Error ---")
        prompt2 = f"""The previous code had an error:

```python
{code}
```

Error: {error}

The issue is that Copperhead doesn't have cp.mean() or cp.std() functions.
You must calculate mean and standard deviation manually using loops.

Fix the code. Use import copperhead as cp, @cp.compile(target="rust"), cp.f64, cp.Vec.
Only return the Python code."""
        
        response2 = run_ollama(prompt2)
        code2 = extract_code(response2)
        print(code2)
        
        # Try again
        error2, namespace2 = try_execute(code2)
        
        if error2:
            print(f"\nExecution error: {error2}")
            
            # Iteration 3: More specific fix
            print("\n--- Iteration 3: More Specific Fix ---")
            prompt3 = f"""The code still has errors:

```python
{code2}
```

Error: {error2}

Copperhead API:
- cp.Vec() creates a list
- cp.f64() converts to float
- No cp.mean(), cp.std(), cp.sum() functions exist
- You must use manual loops and calculations

Fix the code to work with the real Copperhead API.
Only return the Python code."""
            
            response3 = run_ollama(prompt3)
            code3 = extract_code(response3)
            print(code3)
            
            error3, namespace3 = try_execute(code3)
            if error3:
                print(f"\nExecution error: {error3}")
            else:
                print("\n[PASS] Code works after 3 iterations!")
                return True
        else:
            print("\n[PASS] Code works after 2 iterations!")
            return True
    else:
        print("\n[PASS] Code works on first try!")
        return True
    
    return False


def test_api_learning():
    """Test if AI can learn the Copperhead API from examples."""
    print("\n" + "=" * 70)
    print("API LEARNING TEST")
    print("=" * 70)
    
    # Provide example of correct Copperhead code
    example = """Here is correct Copperhead code:

```python
import copperhead as cp

@cp.compile(target="rust")
def sum_list(numbers: cp.Vec[cp.f64]) -> cp.f64:
    total = cp.f64(0)
    for num in numbers:
        total += num
    return total
```

Notice:
- cp.Vec is used for lists
- cp.f64 is used for floats
- Manual loops are used (no cp.sum)
"""
    
    print("\nProviding API example to AI...")
    
    prompt = f"""{example}

Now write a function that:
1. Takes a list of numbers
2. Calculates the mean (average)
3. Returns the mean

Use the same style as the example above.
Only return the Python code."""
    
    response = run_ollama(prompt)
    code = extract_code(response)
    
    print("\nAI's response after seeing example:")
    print("-" * 70)
    print(code)
    print("-" * 70)
    
    # Validate
    error, namespace = try_execute(code)
    
    if error:
        print(f"\nExecution error: {error}")
        return False
    else:
        print("\n[PASS] AI learned from the example!")
        return True


if __name__ == "__main__":
    print("ITERATION AND API LEARNING TEST")
    print("=" * 70)
    
    result1 = test_iteration_fix()
    result2 = test_api_learning()
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Iteration Fix: {'PASS' if result1 else 'FAIL'}")
    print(f"  API Learning: {'PASS' if result2 else 'FAIL'}")
    
    if result1 and result2:
        print("\nAI can iterate, fix errors, and learn from examples!")
    else:
        print("\nSome tests failed.")
