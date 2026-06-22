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

prompt = """Write a Copperhead function that calculates statistics for a list of numbers.

Requirements:
1. Import copperhead as cp (NOT cupy, NOT numpy)
2. Use @cp.compile(target="rust") decorator
3. Use cp.f64 for the numbers
4. Use cp.Vec for the list
5. Calculate mean and standard deviation manually (no cp.mean)
6. Return both values as a dict
7. Handle empty list case

Only return the Python code, no explanation."""

print("Generating...")
response = run_ollama(prompt)
print("Response:")
print(response)

# Validate
code = response
if "```python" in code:
    code = code.split("```python")[1].split("```")[0]

print("\nValidation:")
print(f"  Has import copperhead: {'import copperhead' in code}")
print(f"  Has @cp.compile: {'@cp.compile' in code}")
print(f"  Has cp.f64: {'cp.f64' in code}")
print(f"  Has cp.Vec: {'cp.Vec' in code}")

try:
    ast.parse(code)
    print("  Syntax valid: PASS")
except SyntaxError as e:
    print(f"  Syntax valid: FAIL ({e})")
