"""
Test AI with clear rules about what works in Copperhead.
"""

import subprocess
import re


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


print("=" * 70)
print("TEST: AI with Clear Copperhead Rules")
print("=" * 70)

prompt = """Write a Copperhead function that calculates mean and standard deviation.

IMPORTANT RULES:
1. Use "import copperhead as cp"
2. Use "@cp.compile(target='rust')" decorator
3. Do NOT use Vec[f64] type hints - they don't work at runtime
4. Do NOT use cp.sqrt, cp.sum, cp.mean - they don't exist
5. Calculate everything manually with loops
6. Use cp.Vec() to create lists
7. Use cp.f64() to create floats

Here is correct code that works:

```python
import copperhead as cp

@cp.compile(target="rust")
def sum_list(numbers):
    total = cp.f64(0)
    for num in numbers:
        total += num
    return total
```

Now write a function that:
1. Takes a list of numbers
2. Calculates the mean (average)
3. Calculates the standard deviation
4. Returns both values

Only return the Python code, no explanation."""

response = run_ollama(prompt)
code = extract_code(response)

print("\nGenerated code:")
print("-" * 70)
print(code)
print("-" * 70)

# Try to execute
import copperhead as cp

try:
    namespace = {'cp': cp, '__builtins__': __builtins__}
    exec(code, namespace)
    
    # Test the function
    test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    if 'calculate_mean_std' in namespace:
        result = namespace['calculate_mean_std'](test_data)
        print(f"\nTest with {test_data}:")
        print(f"Result: {result}")
        print("\n[PASS] Code works!")
    elif 'mean_std_dev' in namespace:
        result = namespace['mean_std_dev'](test_data)
        print(f"\nTest with {test_data}:")
        print(f"Result: {result}")
        print("\n[PASS] Code works!")
    else:
        print("\n[INFO] Function defined but not tested")
except Exception as e:
    print(f"\n[FAIL] Error: {e}")
