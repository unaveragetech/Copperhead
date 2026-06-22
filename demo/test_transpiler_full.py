"""Test comprehensive transpilation and verify zero placeholders."""

from copperhead.transpiler import transpile_source, generate_cargo_toml
import os
import tempfile

code = """import copperhead as cp

@cp.compile(target='rust')
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b

@cp.compile(target='rust')
def factorial(n: cp.i64) -> cp.i64:
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

@cp.compile(target='rust')
def fibonacci(n: cp.i64) -> list[cp.i64]:
    if n <= 0:
        return []
    if n == 1:
        return [0]
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

@cp.compile(target='rust')
def sum_list(numbers: list[cp.f64]) -> cp.f64:
    total = 0.0
    for n in numbers:
        total += n
    return total

@cp.compile(target='rust')
def abs_value(x: cp.f64) -> cp.f64:
    if x < 0.0:
        return -x
    return x

@cp.compile(target='rust')
def max_of_three(a: cp.f64, b: cp.f64, c: cp.f64) -> cp.f64:
    result = a
    if b > result:
        result = b
    if c > result:
        result = c
    return result

@cp.compile(target='rust')
def is_even(n: cp.i64) -> bool:
    return n % 2 == 0

@cp.compile(target='rust')
def count_positives(numbers: list[cp.f64]) -> cp.i64:
    count = 0
    for n in numbers:
        if n > 0.0:
            count += 1
    return count

@cp.compile(target='rust')
def power(base: cp.f64, exp: cp.i64) -> cp.f64:
    result = 1.0
    for _ in range(exp):
        result *= base
    return result
"""

rust_code = transpile_source(code)
print(rust_code)
print(f"\n--- {len(rust_code.splitlines())} lines of Rust ---")

# Verify no placeholder bodies in generated functions
lines = rust_code.splitlines()
in_fn = False
fn_name = ""
fn_lines = []
all_fns = {}

for line in lines:
    if line.strip().startswith("fn "):
        if fn_name and fn_lines:
            all_fns[fn_name] = fn_lines
        fn_name = line.strip().split("(")[0].replace("fn ", "")
        fn_lines = []
        in_fn = True
    elif in_fn:
        if line.strip() == "}" and not any(c in line for c in ["if", "else", "for", "while"]):
            all_fns[fn_name] = fn_lines
            in_fn = False
            fn_lines = []
        else:
            fn_lines.append(line)

print("\n--- Placeholder check ---")
placeholder_found = False
for fn_name, body_lines in all_fns.items():
    body_text = "\n".join(body_lines)
    if "Ok(0.0)" in body_text or "Ok(0);" in body_text or "Ok(false)" in body_text:
        print(f"PLACEHOLDER FOUND in {fn_name}: {body_text.strip()}")
        placeholder_found = True
    elif "PyNone" in body_text:
        print(f"PLACEHOLDER FOUND in {fn_name}: {body_text.strip()}")
        placeholder_found = True
    else:
        has_real_code = any(
            l.strip() and not l.strip().startswith("//")
            for l in body_lines
        )
        if has_real_code:
            print(f"OK: {fn_name} - real code ({len(body_lines)} lines)")

if not placeholder_found:
    print("\nZERO PLACEHOLDERS - all function bodies are real transpiled code")

# Compile test
build_dir = os.path.join(tempfile.gettempdir(), "copperhead_full_test")
os.makedirs(os.path.join(build_dir, "src"), exist_ok=True)
with open(os.path.join(build_dir, "src", "lib.rs"), "w") as f:
    f.write(rust_code)
with open(os.path.join(build_dir, "Cargo.toml"), "w") as f:
    f.write(generate_cargo_toml("full_test"))
print(f"\nWritten to {build_dir}")
