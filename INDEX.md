# Copperhead Documentation Index

**Complete reference for building the Manus documentation site.**

> This file contains all insights from every documentation file.
> Use this to build a comprehensive, interactive documentation site.

---

## Project Overview

**Copperhead** is a Python-to-Rust transpilation framework that lets developers write Python code and run it at Rust speeds. It includes an AI agent that generates, debugs, and tests code from natural language descriptions.

- **GitHub:** https://github.com/unaveragetech/Copperhead
- **Docs Site:** https://copperhead-ad8qypth.manus.space
- **Version:** 0.1.0
- **License:** MIT
- **Python:** 3.8+
- **Tests:** 179 passing + 52 comprehensive integration tests

---

## Key Selling Points

1. **Write Python, Run Rust** - No new language to learn
2. **10-100x Speedup** - For CPU-intensive tasks
3. **AI Code Generation** - Describe in English, get code
4. **Module Registry** - Reuse proven functions
5. **Interactive Interpreter** - Shared workspace for user+AI
6. **Production Ready** - Debug, test, compile pipeline

---

## Installation

```bash
pip install copperhead
```

### Prerequisites

| Requirement | Purpose | Required? |
|-------------|---------|-----------|
| Python 3.8+ | Runtime | Yes |
| Rust + Cargo | Compilation | Yes |
| Ollama | AI features | No |

---

## Core Concept: Rich Python Blocks (RPB)

An RPB is a Python function marked for Rust compilation:

```python
import copperhead as cp

@cp.compile(target="rust")
def calculate(x: cp.f64) -> cp.f64:
    return x * x + cp.math.sin(x)
```

**Key insight:** The code still runs as Python. Only marked functions compile to Rust.

---

## Type System

### Primitive Types (16 total)

| Category | Copperhead | Rust | Size |
|----------|------------|------|------|
| Signed Int | `cp.i8` | `i8` | 1 byte |
| Signed Int | `cp.i16` | `i16` | 2 bytes |
| Signed Int | `cp.i32` | `i32` | 4 bytes |
| Signed Int | `cp.i64` | `i64` | 8 bytes |
| Unsigned Int | `cp.u8` | `u8` | 1 byte |
| Unsigned Int | `cp.u16` | `u16` | 2 bytes |
| Unsigned Int | `cp.u32` | `u32` | 4 bytes |
| Unsigned Int | `cp.u64` | `u64` | 8 bytes |
| Platform | `cp.usize` | `usize` | Platform |
| Platform | `cp.isize` | `isize` | Platform |
| Float | `cp.f32` | `f32` | 4 bytes |
| Float | `cp.f64` | `f64` | 8 bytes |
| Boolean | `cp.bool` | `bool` | 1 byte |
| String | `cp.str` | `String` | Heap |
| Bytes | `cp.bytes` | `Vec<u8>` | Heap |
| Char | `cp.char` | `char` | 4 bytes |

### Collection Types

| Copperhead | Python | Rust |
|------------|--------|------|
| `Vec[T]` | `list[T]` | `Vec<T>` |
| `HashMap[K,V]` | `dict[K,V]` | `HashMap<K,V>` |
| `Option[T]` | `Optional[T]` | `Option<T>` |
| `Result[T,E]` | `Union[T, E]` | `Result<T,E>` |

### Ownership Types

| Type | Purpose | Example |
|------|---------|---------|
| `cp.mut[T]` | Mutable reference | `state: cp.mut[MyClass]` |
| `cp.ref[T]` | Immutable reference | `data: cp.ref[MyClass]` |

### Speed by Type Coverage

| Type Coverage | Speed (1M ops) | Relative |
|---------------|----------------|----------|
| Untyped | 45ms | 1x |
| Python types | 12ms | 4x |
| Copperhead types | 0.8ms | 56x |

---

## Decorators

### `@cp.compile(target="rust")`

Marks a function for Rust compilation.

```python
@cp.compile(target="rust")
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b
```

### `@cp.no_gil`

Releases the GIL for true parallel execution.

```python
@cp.compile(target="rust")
@cp.no_gil
def cpu_heavy(n: int) -> float:
    total = 0.0
    for i in range(n):
        total += cp.math.sin(float(i))
    return total
```

---

## Collections API

### Vec[T] (Dynamic Array)

```python
# Create
numbers = cp.Vec([1, 2, 3, 4, 5])
empty = cp.Vec()

# Methods
numbers.append(6)           # Add element
numbers.extend([7, 8])     # Add multiple
numbers.pop()               # Remove last
numbers.remove(3)           # Remove by value
numbers.contains(4)         # Check existence
numbers.len()               # Get length
numbers.is_empty()          # Check if empty
numbers.clear()             # Remove all
numbers[index]              # Access by index
numbers[1:3]                # Slice
```

### HashMap[K,V]

```python
# Create
data = cp.HashMap({"name": "Alice", "age": "30"})

# Methods
data.set("city", "NYC")     # Add/update
data.get("name")            # Get value
data.remove("age")          # Remove key
data.contains_key("name")   # Check key
data.keys()                 # Get all keys
data.values()               # Get all values
data.items()                # Get all pairs
data.len()                  # Get length
data.is_empty()             # Check if empty
data.clear()                # Remove all
```

### Option[T]

```python
some_value = cp.Some(42)
no_value = cp.None_

some_value.is_some()        # Check if has value
some_value.is_none()        # Check if empty
some_value.unwrap()         # Get value (panics if None)
some_value.unwrap_or(0)     # Get value or default
some_value.map(lambda x: x * 2)  # Transform
```

### Result[T,E]

```python
success = cp.Ok(42)
failure = cp.Err("Something went wrong")

success.is_ok()             # Check if success
success.is_err()            # Check if error
success.unwrap()            # Get value (panics if Err)
success.unwrap_or(0)        # Get value or default
success.map(lambda x: x * 2)  # Transform success
```

---

## Math Module

### Trigonometry

```python
cp.math.sin(x)          # Sine
cp.math.cos(x)          # Cosine
cp.math.tan(x)          # Tangent
cp.math.asin(x)         # Arc sine
cp.math.acos(x)         # Arc cosine
cp.math.atan(x)         # Arc tangent
```

### Power and Root

```python
cp.math.sqrt(x)         # Square root
cp.math.cbrt(x)         # Cube root
cp.math.pow(x, y)       # Power (x^y)
cp.math.exp(x)          # e^x
cp.math.log(x)          # Natural log
cp.math.log2(x)         # Log base 2
cp.math.log10(x)        # Log base 10
```

### Rounding

```python
cp.math.floor(x)        # Round down
cp.math.ceil(x)         # Round up
cp.math.round(x)        # Round to nearest
```

### Comparison

```python
cp.math.abs(x)          # Absolute value
cp.math.min(a, b)       # Minimum
cp.math.max(a, b)       # Maximum
```

### Constants

```python
cp.math.PI              # 3.14159...
cp.math.E               # 2.71828...
cp.math.TAU             # 6.28318...
cp.math.INFINITY        # Infinity
cp.math.NAN             # Not a Number
```

---

## Error Handling

### CopperheadError

```python
try:
    result = process(data)
except cp.CopperheadError as e:
    print(f"Error: {e}")
```

### CompilationError

```python
try:
    cp.compile_module("bad_code.py")
except cp.CompilationError as e:
    print(f"Compilation failed: {e}")
```

### TranspilationError

```python
try:
    cp.transpile("bad_code.py")
except cp.TranspilationError as e:
    print(f"Transpilation failed: {e}")
```

---

## CLI Commands

### Build

```bash
copperhead build <file.py>              # Build single file
copperhead build <file.py> -o out.so    # Specify output
copperhead build --bundle ./src/        # Bundle all files
copperhead build --clean                # Clean cache first
```

### Lint

```bash
copperhead lint <file.py>               # Check for issues
copperhead lint <file.py> --fix         # Auto-fix issues
```

### Transpile

```bash
copperhead transpile <file.py>          # Generate Rust code
copperhead transpile <file.py> -o out.rs # Specify output
```

### Check

```bash
copperhead check <file.py>              # Type check only
```

### Cache

```bash
copperhead cache list                   # Show cached files
copperhead cache clear                  # Clear all cache
copperhead cache clear <file.py>        # Clear specific cache
```

### Generate

```bash
copperhead generate "description"       # Generate from English
copperhead generate "description" -o out.py # Specify output
```

### Interactive

```bash
copperhead interactive                  # Start session
copperhead interactive --model model    # Use specific model
```

### Debug

```bash
copperhead debug <file.py>              # Full debug
copperhead debug <file.py> --types      # Type check only
copperhead debug <file.py> --syntax     # Syntax check only
```

### Registry

```bash
copperhead registry list                # List all modules
copperhead registry search "query"      # Search modules
copperhead registry add <file.py>       # Add to registry
copperhead registry stats               # Show statistics
```

### Interpret

```bash
copperhead interpret                    # Start interpreter
copperhead interpret --load file.py     # Load workspace
```

---

## Interpreter Commands

| Command | Description |
|---------|-------------|
| `<code>` | Add code block |
| `?<description>` | Generate code with AI |
| `:debug` | Debug all code |
| `:test` | Run tests |
| `:build` | Compile to Rust |
| `:list` | Show all blocks |
| `:save <file>` | Save workspace |
| `:load <file>` | Load workspace |
| `:help` | Show help |
| `:exit` | Quit |

---

## Architecture

### Component Overview

| Component | File | Purpose |
|-----------|------|---------|
| CLI | `cli.py` | User interface, command routing |
| Interpreter | `interpreter.py` | Interactive workspace, shared state |
| LLM Agent | `llm.py` | AI code generation, natural language processing |
| Compiler | `compiler.py` | Orchestrates build pipeline, caching |
| Parser | `parser.py` | Reads Python, extracts types, detects RPBs |
| Transpiler | `transpiler.py` | Converts Python AST to Rust code |
| Debugger | `debugger.py` | Validates code, checks for issues |
| Registry | `registry.py` | Stores/retrieves modules in SQLite |

### Compilation Pipeline

```
Input: Python source code (.py file)
         |
         v
    [AST Parsing] --> Tokenize, Build AST, Extract types, Detect RPBs
         |
         v
    [Type Analysis] --> Infer types, Map to Rust, Check compatibility
         |
         v
    [Transpilation] --> Generate Rust, Add PyO3, Create bindings
         |
         v
    [Compilation] --> Type check, Optimize, Link, Generate .so
         |
         v
Output: Compiled module (.so file)
```

### Import Hook Flow

```
User Code: import my_module
         |
         v
Python Import System
         |
         v
CopperheadImporter.find_module()
         |
         +-- Found compiled .so? --Yes--> Load directly
         |
         +-- No
              |
              v
         Find .py file
              |
              v
         Compile to .so
              |
              v
         Load compiled .so
```

---

## AI Agent

### How It Works

1. User provides description in English
2. Agent checks registry for existing code
3. Agent builds context (similar code, type info)
4. Agent generates code with Ollama LLM
5. Agent validates syntax
6. Agent runs debugger
7. Agent saves to registry
8. Agent returns code to user

### System Prompt

The AI receives a detailed system prompt with:
- Full Copperhead language reference
- Type system documentation
- Best practices
- Example patterns

### Registry Integration

Before generating new code, the agent:
1. Searches for similar existing code
2. Reuses if found
3. Only generates new if needed

---

## Module Registry

### Database Schema

```sql
CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER REFERENCES modules(id),
    name TEXT NOT NULL,
    signature TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL
);
```

### Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Add module | `add(code, desc)` | Store new module |
| Search | `search(query)` | Find by description |
| Get functions | `search_functions(query)` | Find specific functions |
| List all | `list()` | Get all modules |
| Stats | `stats()` | Usage statistics |

---

## Debugger

### Checks Performed

| Check | Description | Severity |
|-------|-------------|----------|
| Syntax | Valid Python? | Error |
| Types | Correct annotations? | Warning |
| Patterns | Best practices? | Info |
| Safety | Safe to compile? | Error |

### Debug Flow

```
Input: Python code
         |
         v
    [Syntax Check] --> AST parse
         |
         v
    [Type Check] --> Check annotations
         |
         v
    [Pattern Match] --> Check best practices
         |
         v
    [Safety Check] --> Check dangerous ops
         |
         v
Output: List of issues
```

---

## Performance

### Speedup Comparison

| Task | Python | Copperhead | Speedup |
|------|--------|------------|---------|
| Sort 1M numbers | 450ms | 12ms | 37x |
| Image processing | 2.1s | 0.08s | 26x |
| Financial models | 8.5s | 0.3s | 28x |
| JSON parsing | 1.2s | 0.15s | 8x |

### Optimization Strategies

1. **Add type annotations** - 56x faster than untyped
2. **Use cp.math** - Compiles to native Rust math
3. **Use @cp.no_gil** - Enable true parallelism
4. **Bundle mode** - Cross-module optimization
5. **Incremental compilation** - Only recompile changed code

---

## Configuration

### copperhead.toml

```toml
[compiler]
target = "rust"
optimization = "release"  # "debug" or "release"
cache_dir = ".copperhead"

[llm]
model = "qwen2.5-coder"
temperature = 0.7
max_tokens = 2048

[registry]
db_path = "copperhead_registry.db"

[debugger]
syntax_check = true
type_check = true
pattern_check = true
safety_check = true
```

---

## Examples

### Basic Math

```python
import copperhead as cp

@cp.compile(target="rust")
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b

result = add(2.0, 3.0)  # Runs at Rust speed
```

### Collections

```python
@cp.compile(target="rust")
def sum_list(numbers: list[cp.f64]) -> cp.f64:
    total = 0.0
    for n in numbers:
        total += n
    return total
```

### Error Handling

```python
@cp.compile(target="rust")
def divide(a: cp.f64, b: cp.f64):
    if b == 0.0:
        return cp.Err("Cannot divide by zero")
    return cp.Ok(a / b)
```

### Ownership

```python
@cp.compile(target="rust")
def update_state(state: cp.mut[MyClass]) -> None:
    state.value += 1

@cp.compile(target="rust")
def read_data(data: cp.ref[MyClass]) -> cp.f64:
    return data.value
```

### GIL Release

```python
@cp.compile(target="rust")
@cp.no_gil
def cpu_heavy(n: int) -> float:
    total = 0.0
    for i in range(n):
        total += cp.math.sin(float(i))
    return total
```

### Linear Regression

```python
@cp.compile(target="rust")
def linear_regression(points: list[DataPoint]) -> dict:
    n = len(points)
    sum_x = 0.0
    sum_y = 0.0
    for p in points:
        sum_x += p.x
        sum_y += p.y
    mean_x = sum_x / n
    mean_y = sum_y / n
    # ... calculate slope, intercept, r_squared
    return {"slope": slope, "intercept": intercept, "r_squared": r_squared}
```

### Quicksort

```python
@cp.compile(target="rust")
def quicksort(arr: list[cp.f64]) -> list[cp.f64]:
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

---

## Testing

### Run All Tests

```bash
# 179 unit tests
pytest copperhead/tests/

# 52 comprehensive integration tests
python comprehensive_test.py
```

### Run Specific Tests

```bash
pytest copperhead/tests/test_types.py      # Type system
pytest copperhead/tests/test_parser.py     # Parser
pytest copperhead/tests/test_transpiler.py # Transpiler
pytest copperhead/tests/test_compiler.py   # Compiler
pytest copperhead/tests/test_llm.py        # AI agent
pytest copperhead/tests/test_registry.py   # Registry
pytest copperhead/tests/test_debugger.py   # Debugger
pytest copperhead/tests/test_cli.py        # CLI
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start |
| `WHITEPAPER.md` | Plain-English explanation |
| `ROADMAP.md` | Future plans |
| `LICENSE` | MIT license |
| `INDEX.md` | This file - complete reference |
| `docs/ARCHITECTURE.md` | Technical deep dive |
| `docs/API_REFERENCE.md` | Complete function list |
| `docs/GETTING_STARTED.md` | Step-by-step guide |
| `docs/TUTORIAL.md` | 10-lesson tutorial |
| `examples/*.py` | Working code samples |

---

## Suggested Documentation Site Structure

### Homepage
- Hero section with tagline
- Quick install command
- 3 key features
- Code example

### Getting Started
- Prerequisites
- Installation
- First program
- Adding types
- Running code

### Core Concepts
- Rich Python Blocks
- Type system
- Ownership
- Error handling

### API Reference
- Decorators
- Types
- Collections
- Math module
- CLI commands
- Interpreter commands

### Guides
- Basic usage
- Collections
- Error handling
- Ownership
- GIL release
- Building for production

### AI Features
- Code generation
- Interactive mode
- Interpreter
- Module registry

### Architecture
- System overview
- Compilation pipeline
- Parser and AST
- Transpiler
- Import hook
- AI agent
- Registry
- Debugger

### Examples
- Basic math
- Collections
- Error handling
- Ownership
- Linear regression
- Quicksort

### Roadmap
- Current status
- Phase 1: Foundation
- Phase 2: Core features
- Phase 3: AI agent
- Phase 4: Performance
- Phase 5: Integration
- Phase 6: Production
- Phase 7: Advanced

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Unit tests | 179 |
| Integration tests | 52 |
| Test pass rate | 100% |
| Primitive types | 16 |
| Collection types | 4 |
| CLI commands | 10 |
| Interpreter commands | 10 |
| Math functions | 20+ |
| Speedup (typed) | 56x |
| Speedup (typical) | 10-100x |

---

**This file is the single source of truth for building the Manus documentation site.**
