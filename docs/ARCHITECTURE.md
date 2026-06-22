# Copperhead Technical Deep Dive

A comprehensive guide to how Copperhead works internally.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [The Compilation Pipeline](#the-compilation-pipeline)
3. [Type System](#type-system)
4. [Parser and AST](#parser-and-ast)
5. [Transpiler](#transpiler)
6. [Import Hook](#import-hook)
7. [AI Agent Architecture](#ai-agent-architecture)
8. [Module Registry](#module-registry)
9. [Debugger](#debugger)
10. [Performance Optimizations](#performance-optimizations)

---

## System Overview

Copperhead is built as a modular system with clear separation of concerns:

```
+-----------------------------------------------------+
|                    Copperhead System                |
+-----------------------------------------------------+
|                                                     |
|  +-----------+    +------------+    +-----------+    |
|  |   CLI     |    | Interpreter|    | LLM Agent |    |
|  | (cli.py)  |    | (interp.)  |    | (llm.py)  |    |
|  +-----+-----+    +-----+------+    +-----+-----+    |
|        |                |                |            |
|        +----------------+----------------+            |
|                       |                              |
|                 +-----v-----+                        |
|                 |  Compiler |                        |
|                 | (compile) |                        |
|                 +-----+-----+                        |
|                       |                              |
|        +--------------+--------------+               |
|        |              |              |               |
|  +-----v-----+  +----v-----+  +----v------+        |
|  |  Parser   |  |Transpiler|  |  Debugger |        |
|  | (parser)  |  | (trans.) |  | (debug)   |        |
|  +-----+-----+  +----+-----+  +----+------+        |
|        |              |              |               |
|        +--------------+--------------+               |
|                       |                              |
|                 +-----v-----+                        |
|                 |  Registry |                        |
|                 | (registry)|                        |
|                 +-----------+                        |
|                                                     |
+-----------------------------------------------------+
```

### Component Responsibilities

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

---

## The Compilation Pipeline

The compilation pipeline transforms Python code into fast Rust binaries.

### Step-by-Step Process

**Status: VERIFIED WORKING (Python → parse → transpile → Cargo build → `.dll`)**

```
Input: Python source code (.py file)
         |
         v
+-----------------+
| 1. AST Parsing  |
| (parser.py)     |
|                 |
| - Tokenize code |
| - Build AST     |
| - Extract types |
| - Detect RPBs   |
+--------+--------+
         |
         v
+-----------------+
| 2. Type Analysis|
|                 |
| - Infer types   |
| - Map to Rust   |
| - Check compat  |
+--------+--------+
         |
         v
+-----------------+
| 3. Transpilation|
| (transpiler.py) |
|                 |
| - Generate Rust |
| - Add PyO3      |
| - Create bindings|
+--------+--------+
         |
         v
+-----------------+
| 4. Compilation  |
| (rustc + LLVM)  |
|                 |
| - Type check    |
| - Optimize      |
| - Link          |
| - Generate .so  |
+--------+--------+
         |
         v
Output: Compiled module (.so file)
```

### Detailed Pipeline Code

```python
# compiler.py - Main compilation logic

def compile_module(source_path: Path, output_path: Path) -> Path:
    """Compile a single Python module to Rust."""

    # Step 1: Parse the Python source
    parser = CopperheadParser()
    ast = parser.parse(source_path.read_text())

    # Step 2: Extract type information
    type_info = parser.extract_types(ast)

    # Step 3: Detect Rich Python Blocks (RPBs)
    rpbs = parser.detect_rpbs(ast)

    # Step 4: Transpile RPBs to Rust
    transpiler = RustTranspiler()
    rust_code = transpiler.transpile(ast, rpbs, type_info)

    # Step 5: Generate PyO3 bindings
    bindings = transpiler.generate_bindings(rust_code)

    # Step 6: Write Cargo.toml and lib.rs
    cargo_toml = transpiler.generate_cargo_toml()
    lib_rs = transpiler.generate_lib_rs(bindings)

    # Step 7: Compile with rustc
    result = subprocess.run(
        ["cargo", "build", "--release"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise CompilationError(result.stderr)

    return output_path
```

---

## Type System

Copperhead maps Python types to Rust types automatically.

### Type Mapping Table

| Python Type | Copperhead Type | Rust Type | Size |
|-------------|-----------------|-----------|------|
| `int` | `cp.i64` | `i64` | 8 bytes |
| `float` | `cp.f64` | `f64` | 8 bytes |
| `bool` | `cp.bool` | `bool` | 1 byte |
| `str` | `cp.str` | `String` | Heap |
| `list[T]` | `Vec[T]` | `Vec<T>` | Heap |
| `dict[K, V]` | `HashMap[K,V]` | `HashMap<K,V>` | Heap |

### Type Inference

When you don't provide explicit types, Copperhead infers them:

```python
# Explicit types (fastest)
@cp.compile(target="rust")
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b

# Inferred types (still fast)
@cp.compile(target="rust")
def add(a: float, b: float) -> float:
    return a + b

# Mixed types (some Python overhead)
@cp.compile(target="rust")
def add(a, b):
    return a + b
```

### Type Safety

Copperhead checks types at compile time:

```python
@cp.compile(target="rust")
def process(x: cp.f64) -> cp.f64:
    return x * 2

# This will error at compile time:
process("hello")  # Error: Expected f64, got str
```

---

## Parser and AST

The parser reads Python code and builds an Abstract Syntax Tree (AST).

### What the Parser Does

1. **Tokenization**: Breaks code into tokens
2. **Parsing**: Builds tree structure
3. **Type Extraction**: Finds type annotations
4. **RPB Detection**: Identifies code blocks to compile

### Example AST

Input code:
```python
@cp.compile(target="rust")
def square(x: cp.f64) -> cp.f64:
    return x * x
```

AST structure:
```
FunctionDef(
    name='square',
    args=[
        Arg(
            arg='x',
            annotation=Attribute(
                value=Name(id='cp'),
                attr='f64'
            )
        )
    ],
    returns=Attribute(
        value=Name(id='cp'),
        attr='f64'
    ),
    body=[
        Return(
            value=BinOp(
                left=Name(id='x'),
                op=Mult(),
                right=Name(id='x')
            )
        )
    ],
    decorator_list=[
        Call(
            func=Attribute(
                value=Name(id='cp'),
                attr='compile'
            ),
            args=[],
            keywords=[
                keyword(
                    arg='target',
                    value=Constant(value='rust')
                )
            ]
        )
    ]
)
```

---

## Transpiler

The transpiler converts Python AST to Rust code.

### What It Generates

For this Python function:
```python
@cp.compile(target="rust")
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b
```

It generates:

**lib.rs:**
```rust
use pyo3::prelude::*;

#[pyfunction]
fn add(a: f64, b: f64) -> PyResult<f64> {
    Ok(a + b)
}

#[pymodule]
fn _copperhead_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add, m)?)?;
    Ok(())
}
```

**Cargo.toml:**
```toml
[package]
name = "_copperhead_module"
version = "0.1.0"
edition = "2021"

[lib]
name = "_copperhead_module"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
```

### Transpiler Core Logic

{% raw %}
```python
class RustTranspiler:
    def __init__(self):
        self.imports = []
        self.functions = []

    def transpile(self, ast, rpbs, type_info):
        """Transpile Python AST to Rust code."""
        rust_code = []
        rust_code.append("use pyo3::prelude::*;")
        rust_code.append("use pyo3::types::PyModule;")

        for rpb in rpbs:
            rust_code.append(self._transpile_function(rpb, type_info))

        rust_code.append(self._generate_module_init())
        return "\n\n".join(rust_code)

    def _transpile_function(self, func, type_info):
        name = func.name
        return_type = self._get_return_type(func, type_info)
        args = self._get_arguments(func, type_info)
        body = self._get_body(func)

        return f"""
#[pyfunction]
fn {name}({args}) -> PyResult<{return_type}> {{
    {body}
}}
"""
```
{% endraw %}

---

## Import Hook

The import hook makes compiled code available to Python transparently.

### How It Works

When you `import copperhead`, it:
1. Installs a custom import hook in `sys.meta_path`
2. Intercepts imports of Copperhead modules
3. Finds compiled `.so` files or compiles on-the-fly
4. Loads the compiled module

### Import Flow Diagram

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

### Implementation

```python
class CopperheadImporter:
    def __init__(self):
        self.cache_dir = Path("__copperhead_cache__")
        self.cache_dir.mkdir(exist_ok=True)

    def find_module(self, fullname, path=None):
        module_path = self._find_compiled_module(fullname)
        if module_path:
            return self
        return None

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        module_path = self._find_compiled_module(fullname)
        if not module_path:
            module_path = self._compile_module(fullname)

        import importlib.util
        spec = importlib.util.spec_from_file_location(fullname, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[fullname] = module
        spec.loader.exec_module(module)
        return module

# Install the import hook
importer = CopperheadImporter()
sys.meta_path.insert(0, importer)
```

---

## AI Agent Architecture

The AI agent generates code from natural language descriptions.

### System Components

```
+-----------------------------------------------+
|              AI Agent System                  |
+-----------------------------------------------+
|                                               |
|  +---------------+      +---------------+     |
|  |  User Input   |      |  Ollama LLM  |     |
|  |  (English)    |----->| (qwen2.5)    |     |
|  +---------------+      +-------+-------+     |
|                                |              |
|                                v              |
|                       +---------------+       |
|                       | Code Generator|       |
|                       |   (llm.py)    |       |
|                       +-------+-------+       |
|                                |              |
|          +---------------------+-----------+  |
|          |                     |           |  |
|          v                     v           v  |
|  +-----------+         +-----------+ +------+ |
|  | Registry  |         | Debugger  | |Parser| |
|  | (search)  |         | (validate)| |(verify|
|  +-----------+         +-----------+ +------+ |
|                                               |
+-----------------------------------------------+
```

### Code Generation Process

```python
class CopperheadCoder:
    def __init__(self, model="qwen2.5-coder"):
        self.model = model
        self.registry = ModuleRegistry()
        self.debugger = CopperheadDebugger()
        self.parser = CopperheadParser()

    def generate(self, description):
        """Generate Copperhead code from description."""

        # Step 1: Check registry for existing code
        existing = self.registry.search(description)
        if existing:
            return self._reuse_existing(existing)

        # Step 2: Build context
        context = self._build_context(description)

        # Step 3: Generate code with LLM
        code = self._generate_with_llm(description, context)

        # Step 4: Validate syntax
        if not self.debugger.check_syntax(code):
            code = self._fix_syntax(code)

        # Step 5: Run debugger
        issues = self.debugger.debug(code)
        if issues:
            code = self._fix_issues(code, issues)

        # Step 6: Save to registry
        self.registry.add(code, description)

        return code
```

---

## Module Registry

The registry stores and retrieves compiled modules using SQLite.

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

### Registry Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Add module | `add(code, desc)` | Store new module |
| Search | `search(query)` | Find by description |
| Get functions | `search_functions(query)` | Find specific functions |
| List all | `list()` | Get all modules |
| Stats | `stats()` | Usage statistics |

---

## Debugger

The debugger validates code before compilation.

### What It Checks

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
+-----------------+
| Syntax Check    |
| (AST parse)     |
+--------+--------+
         |
         v
+-----------------+
| Type Check      |
| (annotations)   |
+--------+--------+
         |
         v
+-----------------+
| Pattern Match   |
| (best practices)|
+--------+--------+
         |
         v
+-----------------+
| Safety Check    |
| (dangerous ops) |
+--------+--------+
         |
         v
Output: List of issues
```

---

## Performance Optimizations

### 1. Incremental Compilation

Only recompile changed functions:

```
function_a.py  -->  function_a.so  (cached)
function_b.py  -->  function_b.so  (recompiled)
function_c.py  -->  function_c.so  (cached)
```

### 2. Smart Caching

Cache compiled modules based on content hash:

```python
def get_cache_key(source: str) -> str:
    return hashlib.md5(source.encode()).hexdigest()
```

### 3. Type-Based Optimization

More types = more optimization:

```python
# Slow (dynamic)
def add(a, b):
    return a + b

# Fast (typed)
def add(a: cp.f64, b: cp.f64) -> cp.f64:
    return a + b
```

### 4. Cross-Module Inlining

Bundle mode inlines functions across files:

```python
# utils.py
@cp.compile(target="rust")
def helper(x):
    return x * 2

# main.py
@cp.compile(target="rust")
def main():
    return helper(5)  # Inlined at compile time
```

---

## Summary

Copperhead works through a series of well-defined stages:

1. **Parse** - Read Python, build AST
2. **Analyze** - Extract types, find RPBs
3. **Transpile** - Convert to Rust code
4. **Compile** - Build fast binaries
5. **Load** - Make available to Python

The result: Write Python, run Rust.
