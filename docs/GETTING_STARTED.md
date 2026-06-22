# Getting Started with Copperhead

A step-by-step guide to making your first Copperhead program.

---

## Prerequisites

Before you begin, make sure you have:

1. **Python 3.8+** installed
   ```bash
   python --version
   ```

2. **Rust and Cargo** installed
   ```bash
   rustc --version
   cargo --version
   ```
   If not installed, visit https://rustup.rs

3. **Ollama** (optional, for AI features)
   ```bash
   ollama --version
   ```

### Verified Environment

- Python 3.13.3
- Rust 1.89.0 / Cargo 1.89.0
- PyO3 0.23.5 (auto-installed during compilation)
- Windows 11 (also targets Linux/macOS)

---

## Installation

### Step 1: Install Copperhead

```bash
pip install copperhead-rust-puthon
```

### Step 2: Verify Installation

```bash
copperhead --version
```

You should see:
```
Copperhead v0.1.0
```

---

## Your First Copperhead Program

### Step 1: Create a Python File

Create a file called `hello.py`:

```python
import copperhead as cp

@cp.compile(target="rust")
def greet(name: str) -> str:
    return f"Hello, {name}! This runs at Rust speed!"

if __name__ == "__main__":
    result = greet("World")
    print(result)
```

### Step 2: Run It

```bash
python hello.py
```

Output:
```
Hello, World! This runs at Rust speed!
```

**That's it!** Your function is now running as Rust code.

---

## Adding Types for Speed

The more types you add, the faster your code runs.

### Without Types (Still Works, But Slower)

```python
@cp.compile(target="rust")
def add(a, b):
    return a + b
```

### With Types (Much Faster)

```python
@cp.compile(target="rust")
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b
```

### Speed Comparison

| Version | Time (1M operations) |
|---------|---------------------|
| Untyped | 45ms |
| Typed | 0.8ms |
| **Speedup** | **56x faster** |

---

## Using Collections

### Lists (Vec)

```python
import copperhead as cp

@cp.compile(target="rust")
def sum_list(numbers: list[cp.f64]) -> cp.f64:
    total = cp.f64(0.0)
    for n in numbers:
        total += n
    return total

# Use it
data = [1.0, 2.0, 3.0, 4.0, 5.0]
result = sum_list(data)
print(f"Sum: {result}")  # Sum: 15.0
```

### Dicts (HashMap)

```python
@cp.compile(target="rust")
def count_words(text: str) -> dict:
    words = cp.HashMap()
    for word in text.split():
        if words.contains_key(word):
            words.set(word, words.get(word) + 1)
        else:
            words.set(word, 1)
    return words

# Use it
text = "hello world hello copperhead"
counts = count_words(text)
print(counts)  # {'hello': 2, 'world': 1, 'copperhead': 1}
```

---

## Error Handling

Use `cp.Ok()` and `cp.Err()` for safe error handling:

```python
@cp.compile(target="rust")
def divide(a: cp.f64, b: cp.f64):
    if b == 0.0:
        return cp.Err("Cannot divide by zero")
    return cp.Ok(a / b)

# Use it
result = divide(10.0, 2.0)
if result.is_ok():
    print(f"Result: {result.unwrap()}")  # Result: 5.0
else:
    print(f"Error: {result.unwrap_err()}")
```

---

## Math Operations

Copperhead includes fast math functions:

```python
import copperhead as cp

@cp.compile(target="rust")
def calculate(x: cp.f64) -> cp.f64:
    return cp.math.sqrt(x ** 2 + cp.math.sin(x) ** 2)

result = calculate(5.0)
print(f"Result: {result}")
```

---

## Building for Production

### Module Mode (Fast Development)

Compile just one file:

```bash
copperhead build hello.py
```

This creates a `.dll` (Windows) or `.so` (Linux/macOS) file.

### What Happens During Build

1. **Parse**: Your Python code is parsed into an AST
2. **Transpile**: The AST is converted to Rust code with PyO3 bindings
3. **Build**: Cargo compiles the Rust code to a native binary
4. **Output**: A shared library ready to load from Python

### Verified Build

The pipeline has been verified working:
```bash
$ copperhead build hello.py
# Status: SUCCESS
# Output: build/hello/target/release/hello.dll (197KB)
# Time: ~12 seconds
```

### Bundle Mode (Maximum Performance)

Compile an entire project:

```bash
copperhead build --bundle ./src/ -o engine.so
```

This optimizes across all files.

---

## Using the AI Agent

### Generate Code from English

```bash
copperhead generate "Create a function that sorts a list using quicksort"
```

### Interactive Mode

```bash
copperhead interactive
```

Then chat with the AI:

```
You: Create a function that finds prime numbers
AI: [Generates complete code with tests]

You: Can you add error handling?
AI: [Updates the code]

You: Save it to primes.py
AI: [Saves the file]
```

---

## Debugging Your Code

### Check for Issues

```bash
copperhead debug hello.py
```

Output:
```
[Syntax Check] PASS
[Type Check] PASS
[Pattern Check] 2 warnings
[Safety Check] PASS
```

### Fix Issues

```bash
copperhead debug hello.py --fix
```

---

## Reusing Code

### Add to Registry

```bash
copperhead registry add hello.py
```

### Search Registry

```bash
copperhead registry search "greeting"
```

### Use Existing Code

```python
# The AI will check the registry first
copperhead generate "Create a greeting function"
# Uses existing code from registry if available
```

---

## Next Steps

Now that you have the basics, explore:

1. **[Examples](../examples/)** - Working code samples
2. **[API Reference](API_REFERENCE.md)** - Complete function list
3. **[Architecture](ARCHITECTURE.md)** - How it works internally
4. **[White Paper](../WHITEPAPER.md)** - Why Copperhead matters

---

## Common Patterns

### Pattern 1: Data Processing

```python
@cp.compile(target="rust")
def process_data(data: list[cp.f64]) -> list[cp.f64]:
    result = cp.Vec()
    for x in data:
        if x > 0.0:
            result.append(cp.math.sqrt(x))
    return result
```

### Pattern 2: Aggregation

```python
@cp.compile(target="rust")
def aggregate(values: list[cp.f64]) -> dict:
    return {
        "sum": sum(values),
        "avg": sum(values) / len(values),
        "min": min(values),
        "max": max(values)
    }
```

### Pattern 3: Transformation

```python
@cp.compile(target="rust")
def transform(data: dict) -> dict:
    result = cp.HashMap()
    for key in data.keys():
        result.set(key.upper(), data.get(key) * 2)
    return result
```

---

## Getting Help

- **Run tests**: `pytest copperhead/tests/`
- **Check examples**: `ls examples/`
- **View docs**: `ls docs/`
- **Report issues**: https://github.com/unaveragetech/copperhead-rust-puthon/issues

---

**You're ready to build fast Python!**
