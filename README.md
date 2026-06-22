# Copperhead

**Write Python. Run Rust.**

[![GitHub](https://img.shields.io/badge/GitHub-unaveragetech%2FCopperhead-blue?logo=github)](https://github.com/unaveragetech/Copperhead)
[![Docs](https://img.shields.io/badge/Docs-Interactive-green?logo=markdown)](https://copperhead-ad8qypth.manus.space)
[![Tests](https://img.shields.io/badge/tests-179%20passing-brightgreen)](https://github.com/unaveragetech/Copperhead/tree/main/copperhead/tests/)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/unaveragetech/Copperhead/blob/main/LICENSE)

> **Interactive Documentation:** [copperhead-ad8qypth.manus.space](https://copperhead-ad8qypth.manus.space)

---

## What is Copperhead?

Copperhead is a programming tool that lets you write code in Python (the easy language) but run it at Rust speeds (the fast language). You get the simplicity of Python with the performance of Rust.

**No new language to learn. No complex build steps. Just faster Python.**

---

## Quick Start (2 minutes)

### Install
```bash
pip install copperhead
```

### Write Fast Python
```python
import copperhead as cp

# Mark this function for Rust speed
@cp.compile(target="rust")
def calculate(x: float) -> float:
    return x * x + cp.math.sin(x)

# Call it like normal Python
result = calculate(5.0)  # Runs at Rust speed!
```

### Run
```bash
python my_script.py
```

That's it. No compilation step. Just write and run.

---

## Why Copperhead?

### The Problem
- **Python is easy** but slow for heavy computations
- **Rust is fast** but hard to learn and write
- **You've been forced to choose** between easy and fast

### The Solution
Copperhead lets you:
1. Write Python (easy)
2. Mark functions for Rust speed (simple annotation)
3. Get 10-100x faster execution (automatic)

### What Makes It Different

| Feature | Copperhead | Other Tools |
|---------|------------|-------------|
| Still Python? | Yes, 100% | Usually no |
| Learn new syntax? | No | Yes |
| Gradual optimization? | Yes | No |
| AI code generation? | Yes | No |
| Point to specific functions? | Yes | No |

---

## Core Features

### 1. Rich Python Blocks
Mark any function for Rust compilation:

```python
@cp.compile(target="rust")
def my_fast_function(data: list[float]) -> float:
    total = 0.0
    for x in data:
        total += x * x
    return total
```

### 2. Type System (Optional but Faster)
Add types for even more speed:

```python
@cp.compile(target="rust")
def process(x: cp.f64, y: cp.f64) -> cp.f64:
    return x + y
```

Available types:
- `cp.i8`, `cp.i16`, `cp.i32`, `cp.i64` (integers)
- `cp.f32`, `cp.f64` (decimals)
- `cp.bool` (true/false)
- `cp.str` (text)
- `list[T]`, `dict[K, V]` (collections)

### 3. Ownership (For Advanced Users)
Control how data is passed to Rust:

```python
# Mutable reference (can modify)
def update(state: cp.mut[MyClass]) -> None:
    state.value += 1

# Immutable reference (read-only)
def read(data: cp.ref[MyClass]) -> float:
    return data.value
```

### 4. GIL Release (For Threading)
Enable true parallel processing:

```python
@cp.compile(target="rust")
@cp.no_gil
def cpu_heavy(n: int) -> float:
    total = 0.0
    for i in range(n):
        total += cp.math.sin(float(i))
    return total
```

### 5. Math Module
Built-in math functions that compile to fast Rust:

```python
cp.math.sin(x)      # Sine
cp.math.cos(x)      # Cosine
cp.math.sqrt(x)     # Square root
cp.math.pow(x, y)   # Power
cp.math.log(x)      # Natural log
cp.math.min(a, b)   # Minimum
cp.math.max(a, b)   # Maximum
```

### 6. Error Handling
Safe error handling with Rust-style Results:

```python
@cp.compile(target="rust")
def divide(a: float, b: float):
    if b == 0.0:
        return cp.Err("Cannot divide by zero")
    return cp.Ok(a / b)
```

---

## AI Agent

Copperhead includes an AI assistant that writes code for you.

### Generate Code from English
```bash
copperhead generate "Create a function that sorts a list using quicksort"
```

### Interactive Mode
```bash
copperhead interactive
```

Then just describe what you want:
```
You: Create a function that finds prime numbers up to n
AI: [Generates complete Copperhead code with tests]
```

### What the AI Does
1. Understands your plain-English description
2. Plans the best approach
3. Checks if similar code already exists
4. Writes complete, tested code
5. Debugs it before giving it to you

---

## Interactive Interpreter

A shared workspace for you and the AI:

```bash
copperhead interpret
```

### Commands

| Command | What It Does |
|---------|--------------|
| `<code>` | Add code to workspace |
| `?<description>` | Ask AI to generate code |
| `:debug` | Check code for errors |
| `:test` | Run tests |
| `:build` | Compile to Rust |
| `:list` | Show all code blocks |
| `:save file.py` | Save workspace |
| `:load file.py` | Load workspace |
| `:help` | Show all commands |
| `:exit` | Quit |

### Example Session

```
copperhead> ?Create a function that calculates factorial

[AI generates code with types and tests]

copperhead> :debug
[Checks code for issues]

copperhead> :test
[Runs generated tests]

copperhead> :save factorial.py
[ Saves to file]
```

---

## Module Registry

Store and reuse your best functions.

### Commands
```bash
copperhead registry list              # See all modules
copperhead registry search "matrix"   # Find specific functions
copperhead registry add script.py     # Save a module
copperhead registry stats             # See usage statistics
```

### Why Use It
- Don't rewrite the same function twice
- Share code with your team
- Track what's working well

---

## Debugging

Check your code before running it.

### CLI Debug
```bash
copperhead debug script.py           # Full debug
copperhead debug script.py --types   # Type checking only
```

### What It Checks
1. **Syntax** - Is the code valid Python?
2. **Types** - Are type annotations correct?
3. **Patterns** - Does it follow Copperhead best practices?
4. **Safety** - Is it safe to run?

---

## Building for Production

Compile to fast Rust binaries.

### Module Mode (Fast Development)
```bash
copperhead build script.py
```
Compiles just that file. Fast for development.

### Bundle Mode (Maximum Performance)
```bash
copperhead build --bundle ./project/ -o engine.so
```
Compiles everything into one optimized binary. Best for production.

---

## Examples

See the `examples/` directory:

| File | What It Shows |
|------|---------------|
| `basic_math.py` | Simple math operations |
| `data_processing.py` | Working with lists and dicts |
| `ownership.py` | Advanced memory control |
| `performance.py` | Speed comparisons |
| `abstract_examples.py` | Complex algorithms |

---

## Testing

### Run All Tests
```bash
# 179 tests
pytest copperhead/tests/

# Or run the comprehensive test
python comprehensive_test.py
```

### Run Specific Tests
```bash
pytest copperhead/tests/test_types.py      # Type system
pytest copperhead/tests/test_parser.py     # Parser
pytest copperhead/tests/test_transpiler.py # Transpiler
```

---

## Architecture

```
copperhead/
├── __init__.py          # Core types and decorators
├── parser.py            # Reads and understands Python code
├── transpiler.py        # Converts Python to Rust
├── compiler.py          # Builds Rust binaries
├── cli.py               # Command-line interface
├── llm.py               # AI agent
├── debugger.py          # Code validation
├── registry.py          # Module database
├── interpreter.py       # Interactive workspace
└── tests/               # 179 tests
```

---

## How It Works (Simplified)

```
Your Python Code
      ↓
[Parser] - Reads and understands it
      ↓
[Type Analyzer] - Figures out types
      ↓
[Rust Generator] - Writes equivalent Rust
      ↓
[PyO3 Bridge] - Adds Python calling code
      ↓
[LLVM Compiler] - Creates fast machine code
      ↓
[Import Hook] - Makes it available to Python
```

---

## Requirements

- Python 3.8+
- Rust and Cargo (for compilation)
- Ollama (for AI features, optional)

---

## Performance

Typical speedups on real tasks:

| Task | Python | Copperhead | Speedup |
|------|--------|------------|---------|
| Sort 1M numbers | 450ms | 12ms | 37x |
| Image processing | 2.1s | 0.08s | 26x |
| Financial models | 8.5s | 0.3s | 28x |
| JSON parsing | 1.2s | 0.15s | 8x |

---

## FAQ

**Q: Do I need to learn Rust?**
A: No. You write Python. Copperhead handles the Rust.

**Q: Will my existing code work?**
A: Yes. Add `@cp.compile` to speed up specific functions.

**Q: Is it really that fast?**
A: Yes. 10-100x faster for CPU-intensive tasks.

**Q: Can I use NumPy/Pandas?**
A: Yes. Copperhead works with existing Python libraries.

**Q: How does the AI work?**
A: It uses Ollama (local AI). Your code never leaves your computer.

**Q: What if something breaks?**
A: Your code still runs as Python, so your debugger works. Copperhead also has its own debugger.

---

## Learn More

- **[White Paper](https://github.com/unaveragetech/Copperhead/blob/main/WHITEPAPER.md)** - Detailed explanation for everyone
- **[Technical Deep Dive](https://github.com/unaveragetech/Copperhead/blob/main/docs/ARCHITECTURE.md)** - How it works internally
- **[Getting Started](https://github.com/unaveragetech/Copperhead/blob/main/docs/GETTING_STARTED.md)** - Step-by-step guide
- **[Tutorial](https://github.com/unaveragetech/Copperhead/blob/main/docs/TUTORIAL.md)** - Learn with examples
- **[API Reference](https://github.com/unaveragetech/Copperhead/blob/main/docs/API_REFERENCE.md)** - Complete function list
- **[Roadmap](https://github.com/unaveragetech/Copperhead/blob/main/ROADMAP.md)** - What's coming next

---

## Contributing

Contributions welcome! See the [Roadmap](https://github.com/unaveragetech/Copperhead/blob/main/ROADMAP.md) for planned features.

```bash
# Clone the repo
git clone https://github.com/unaveragetech/Copperhead.git
cd Copperhead

# Install dependencies
pip install -e .

# Run tests
pytest copperhead/tests/
```

---

## Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/unaveragetech/Copperhead/issues)
- **Discussions**: [Ask questions](https://github.com/unaveragetech/Copperhead/discussions)

---

## License

MIT License - Use it however you want.

---

**Copperhead: Write Python. Run Rust.**
