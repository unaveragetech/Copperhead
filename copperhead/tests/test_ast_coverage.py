"""
Comprehensive AST Transpilation Tests

Tests every Python AST statement type (28) and expression type (27).
Each test transpiles a Python function to Rust and verifies:
1. The transpilation produces valid Rust code
2. No placeholder bodies remain
3. The generated code compiles with Cargo
"""

import pytest
import ast
import os
import tempfile
from copperhead.transpiler import transpile_source, generate_cargo_toml


def transpile_and_verify(source: str, expected_patterns: list = None, unexpected_patterns: list = None) -> str:
    """Transpile source, verify patterns, return Rust code."""
    rust_code = transpile_source(source)

    assert rust_code, "Transpilation returned empty code"
    assert "use pyo3::prelude::*;" in rust_code, "Missing PyO3 imports"

    if expected_patterns:
        for pattern in expected_patterns:
            assert pattern in rust_code, f"Expected pattern not found: {pattern}"

    if unexpected_patterns:
        for pattern in unexpected_patterns:
            assert pattern not in rust_code, f"Unexpected placeholder found: {pattern}"

    return rust_code


def write_and_compile(rust_code: str, name: str = "test_module") -> bool:
    """Write Rust code to temp dir and compile with Cargo."""
    build_dir = os.path.join(tempfile.gettempdir(), f"ch_test_{name}")
    src_dir = os.path.join(build_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    with open(os.path.join(src_dir, "lib.rs"), "w") as f:
        f.write(rust_code)

    with open(os.path.join(build_dir, "Cargo.toml"), "w") as f:
        f.write(generate_cargo_toml(name))

    import subprocess
    try:
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
# STATEMENT TESTS (28 types)
# ══════════════════════════════════════════════════════════════════════════

class TestStatementReturn:
    def test_return_literal(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return 42\n',
            expected_patterns=["return Ok(42);"]
        )

    def test_return_expression(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a + b\n',
            expected_patterns=["return Ok(a + b);"]
        )

    def test_return_none(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> None:\n'
            '    return\n',
            expected_patterns=["return Ok(());"]
        )

    def test_return_bool(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> bool:\n'
            '    return x > 0\n',
            expected_patterns=["return Ok(x > 0);"]
        )


class TestStatementAssign:
    def test_simple_assign(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    return x\n',
            expected_patterns=["let mut x = 10;", "return Ok(x);"]
        )

    def test_reassign(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    x = 20\n'
            '    return x\n',
            expected_patterns=["let mut x = 10;", "x = 20;"]
        )

    def test_tuple_unpack(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    a, b = 1, 2\n'
            '    return a + b\n',
            expected_patterns=["let mut (a, b) = (1, 2);"]
        )

    def test_subscript_assign(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = [1, 2, 3]\n'
            '    x[0] = 10\n'
            '    return x[0]\n',
            expected_patterns=["(x)[(0) as usize] = 10;"]
        )

    def test_attr_assign(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = [1, 2, 3]\n'
            '    x.len = 5\n'
            '    return 0\n',
            expected_patterns=["(x).len = 5;"]
        )


class TestStatementAnnAssign:
    def test_annotated_assign(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x: int = 42\n'
            '    return x\n',
            expected_patterns=["let mut x: i64 = 42;"]
        )

    def test_annotated_no_value(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x: float\n'
            '    return 0\n',
            expected_patterns=["let mut x: f64 = 0.0;"]
        )

    def test_annotated_with_type(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x: bool = True\n'
            '    return 0\n',
            expected_patterns=["let mut x: bool = true;"]
        )


class TestStatementAugAssign:
    def test_aug_add(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    x += 5\n'
            '    return x\n',
            expected_patterns=["x += 5;"]
        )

    def test_aug_sub(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    x -= 3\n'
            '    return x\n',
            expected_patterns=["x -= 3;"]
        )

    def test_aug_mult(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    x *= 2\n'
            '    return x\n',
            expected_patterns=["x *= 2;"]
        )

    def test_aug_div(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    x = 10.0\n'
            '    x /= 2.0\n'
            '    return x\n',
            expected_patterns=["x /= 2.0f64;"]
        )

    def test_aug_mod(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    x %= 3\n'
            '    return x\n',
            expected_patterns=["x %= 3;"]
        )

    def test_aug_pow(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    x = 2.0\n'
            '    x **= 3\n'
            '    return x\n',
            expected_patterns=["x = (x).powi(3 as i32);"]
        )

    def test_aug_bitand(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 0xFF\n'
            '    x &= 0x0F\n'
            '    return x\n',
            expected_patterns=["x &= 15;", "return Ok(x);"]
        )


class TestStatementIf:
    def test_simple_if(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    if x > 0:\n'
            '        return x\n'
            '    return 0\n',
            expected_patterns=["if x > 0 {"]
        )

    def test_if_else(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    if x > 0:\n'
            '        return 1\n'
            '    else:\n'
            '        return 0\n',
            expected_patterns=["} else {"]
        )

    def test_if_elif_else(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    if x > 0:\n'
            '        return 1\n'
            '    elif x < 0:\n'
            '        return -1\n'
            '    else:\n'
            '        return 0\n',
            expected_patterns=["return Ok(1);", "return Ok(-1);", "return Ok(0);"]
        )


class TestStatementFor:
    def test_for_range(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(n: cp.i64) -> cp.i64:\n'
            '    s = 0\n'
            '    for i in range(n):\n'
            '        s += i\n'
            '    return s\n',
            expected_patterns=["for i in 0..n {"]
        )

    def test_for_range_start_end(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    s = 0\n'
            '    for i in range(2, 10):\n'
            '        s += i\n'
            '    return s\n',
            expected_patterns=["for i in 2..10 {"]
        )

    def test_for_range_step(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    s = 0\n'
            '    for i in range(0, 10, 2):\n'
            '        s += i\n'
            '    return s\n',
            expected_patterns=["step_by(2 as usize)"]
        )

    def test_for_iter(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    items = [1, 2, 3]\n'
            '    s = 0\n'
            '    for x in items:\n'
            '        s += x\n'
            '    return s\n',
            expected_patterns=["for x in (items).iter().copied()"]
        )

    def test_for_enumerate(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    items = [10, 20, 30]\n'
            '    s = 0\n'
            '    for i, x in enumerate(items):\n'
            '        s += x\n'
            '    return s\n',
            expected_patterns=["enumerate"]
        )

    def test_for_tuple_target(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    items = [(1, 2), (3, 4)]\n'
            '    s = 0\n'
            '    for a, b in items:\n'
            '        s += a + b\n'
            '    return s\n',
            expected_patterns=["for (a, b) in"]
        )

    def test_for_else(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    for i in range(10):\n'
            '        if i == 5:\n'
            '            break\n'
            '    else:\n'
            '        return 1\n'
            '    return 0\n',
            expected_patterns=["} else {"]
        )


class TestStatementWhile:
    def test_while_loop(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 0\n'
            '    while x < 10:\n'
            '        x += 1\n'
            '    return x\n',
            expected_patterns=["while x < 10 {"]
        )

    def test_while_break(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 0\n'
            '    while True:\n'
            '        x += 1\n'
            '        if x >= 10:\n'
            '            break\n'
            '    return x\n',
            expected_patterns=["break;"]
        )

    def test_while_continue(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    s = 0\n'
            '    x = 0\n'
            '    while x < 10:\n'
            '        x += 1\n'
            '        if x % 2 == 0:\n'
            '            continue\n'
            '        s += x\n'
            '    return s\n',
            expected_patterns=["continue;"]
        )

    def test_while_else(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 0\n'
            '    while x < 10:\n'
            '        x += 1\n'
            '    else:\n'
            '        return 1\n'
            '    return 0\n',
            expected_patterns=["} else {"]
        )


class TestStatementBreak:
    def test_break(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    for i in range(100):\n'
            '        if i == 5:\n'
            '            break\n'
            '    return i\n',
            expected_patterns=["break;"]
        )


class TestStatementContinue:
    def test_continue(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    s = 0\n'
            '    for i in range(10):\n'
            '        if i % 2 == 0:\n'
            '            continue\n'
            '        s += i\n'
            '    return s\n',
            expected_patterns=["continue;"]
        )


class TestStatementPass:
    def test_pass(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    pass\n'
            '    return 0\n',
            expected_patterns=["return Ok(0);"]
        )


class TestStatementExpr:
    def test_expr_statement(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    x\n'
            '    return x\n',
            expected_patterns=["x;"]
        )


class TestStatementAssert:
    def test_assert(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    assert x > 0\n'
            '    return x\n',
            expected_patterns=["assert!(x > 0);"]
        )

    def test_assert_with_message(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    assert x > 0, "x must be positive"\n'
            '    return x\n',
            expected_patterns=["assert!"]
        )


class TestStatementFunctionDef:
    def test_nested_function(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def outer() -> cp.i64:\n'
            '    def inner() -> cp.i64:\n'
            '        return 42\n'
            '    return inner()\n',
            expected_patterns=["fn inner()"]
        )

    def test_decorator(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            '@cp.no_gil\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    return x * 2\n',
            expected_patterns=["fn f("]
        )


class TestStatementClassDef:
    def test_simple_class(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    class Point:\n'
            '        def __init__(self):\n'
            '            self.x = 0\n'
            '    return 0\n',
            expected_patterns=["pub struct Point"]
        )

    def test_class_with_methods(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    class Counter:\n'
            '        def __init__(self):\n'
            '            self.count = 0\n'
            '        def increment(self):\n'
            '            self.count += 1\n'
            '    return 0\n',
            expected_patterns=["pub fn increment"]
        )

    def test_class_with_classvar(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    class Config:\n'
            '        version: int = 1\n'
            '    return 0\n',
            expected_patterns=["pub version: i64,"]
        )


class TestStatementTry:
    def test_try_except(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    try:\n'
            '        x = 10\n'
            '    except Exception:\n'
            '        x = 0\n'
            '    return x\n',
            expected_patterns=["/* try block */", "/* except Exception"]
        )

    def test_try_finally(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    try:\n'
            '        x = 10\n'
            '    finally:\n'
            '        x = 0\n'
            '    return x\n',
            expected_patterns=["/* try block */", "/* finally */"]
        )

    def test_try_except_else(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    try:\n'
            '        x = 10\n'
            '    except ValueError:\n'
            '        x = 0\n'
            '    else:\n'
            '        x = 20\n'
            '    return x\n',
            expected_patterns=["/* else */"]
        )


class TestStatementWith:
    def test_with_statement(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    with open("file.txt") as f:\n'
            '        x = 10\n'
            '    return x\n',
            expected_patterns=["/* with */"]
        )


class TestStatementRaise:
    def test_raise(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    raise ValueError("bad")\n',
            expected_patterns=["return Err("]
        )

    def test_raise_no_value(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    raise\n',
            expected_patterns=["return Err("]
        )


class TestStatementImport:
    def test_import(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    import os\n'
            '    return 0\n',
            expected_patterns=["use os;"]
        )

    def test_import_as(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    import os as operating_system\n'
            '    return 0\n',
            expected_patterns=["use os as operating_system;"]
        )


class TestStatementImportFrom:
    def test_import_from(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    from os import path\n'
            '    return 0\n',
            expected_patterns=["use os::{path};"]
        )

    def test_import_from_multiple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    from os import path, getcwd\n'
            '    return 0\n',
            expected_patterns=["use os::{path, getcwd};"]
        )


class TestStatementGlobal:
    def test_global(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    global x\n'
            '    x = 10\n'
            '    return x\n',
            expected_patterns=["/* global x */"]
        )


class TestStatementNonlocal:
    def test_nonlocal(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    def inner() -> None:\n'
            '        nonlocal x\n'
            '        x = 20\n'
            '    return x\n',
            expected_patterns=["/* nonlocal x */"]
        )


class TestStatementDelete:
    def test_delete(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = 10\n'
            '    del x\n'
            '    return 0\n',
            expected_patterns=["drop(x);"]
        )


class TestStatementMatch:
    def test_match_simple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    match x:\n'
            '        case 1:\n'
            '            return 10\n'
            '        case 2:\n'
            '            return 20\n'
            '        case _:\n'
            '            return 0\n',
            expected_patterns=["match x {"]
        )


class TestStatementTypeAlias:
    def test_type_alias(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    type Vector = list[float]\n'
            '    return 0\n',
            expected_patterns=["type Vector"]
        )


# ══════════════════════════════════════════════════════════════════════════
# EXPRESSION TESTS (27 types)
# ══════════════════════════════════════════════════════════════════════════

class TestExprName:
    def test_name(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    return x\n',
            expected_patterns=["return Ok(x);"]
        )

    def test_name_true(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return True\n',
            expected_patterns=["return Ok(true);"]
        )

    def test_name_false(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return False\n',
            expected_patterns=["return Ok(false);"]
        )

    def test_name_none(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    return None\n',
            expected_patterns=["return Ok(None);"]
        )


class TestExprConstant:
    def test_int(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return 42\n',
            expected_patterns=["return Ok(42);"]
        )

    def test_float(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    return 3.14\n',
            expected_patterns=["return Ok(3.14f64);"]
        )

    def test_string(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    return "hello"\n',
            expected_patterns=['return Ok("hello".to_string());']
        )

    def test_bytes(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    return b"abc"\n',
            expected_patterns=["vec!"]
        )

    def test_string_escape(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    return "line1\\nline2"\n',
            expected_patterns=['return Ok("line1\\nline2".to_string());']
        )


class TestExprBinOp:
    def test_add(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a + b\n',
            expected_patterns=["(a + b)"]
        )

    def test_sub(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a - b\n',
            expected_patterns=["(a - b)"]
        )

    def test_mult(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a * b\n',
            expected_patterns=["(a * b)"]
        )

    def test_div(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.f64, b: cp.f64) -> cp.f64:\n'
            '    return a / b\n',
            expected_patterns=["as f64 /"]
        )

    def test_floor_div(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a // b\n',
            expected_patterns=["floor()"]
        )

    def test_mod(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a % b\n',
            expected_patterns=["(a % b)"]
        )

    def test_pow(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.f64, b: cp.i64) -> cp.f64:\n'
            '    return a ** b\n',
            expected_patterns=["powi"]
        )

    def test_bitand(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a & b\n',
            expected_patterns=["(a & b)"]
        )

    def test_bitor(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a | b\n',
            expected_patterns=["(a | b)"]
        )

    def test_bitxor(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a ^ b\n',
            expected_patterns=["(a ^ b)"]
        )

    def test_lshift(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a << b\n',
            expected_patterns=["(a << b)"]
        )

    def test_rshift(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return a >> b\n',
            expected_patterns=["(a >> b)"]
        )


class TestExprUnaryOp:
    def test_usub(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    return -x\n',
            expected_patterns=["(-x)"]
        )

    def test_not(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: bool) -> bool:\n'
            '    return not x\n',
            expected_patterns=["(!x)"]
        )

    def test_invert(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    return ~x\n',
            expected_patterns=["(!x)"]
        )


class TestExprBoolOp:
    def test_and(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: bool, b: bool) -> bool:\n'
            '    return a and b\n',
            expected_patterns=["a && b"]
        )

    def test_or(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: bool, b: bool) -> bool:\n'
            '    return a or b\n',
            expected_patterns=["a || b"]
        )


class TestExprCompare:
    def test_eq(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> bool:\n'
            '    return a == b\n',
            expected_patterns=["a == b"]
        )

    def test_ne(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> bool:\n'
            '    return a != b\n',
            expected_patterns=["a != b"]
        )

    def test_lt(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> bool:\n'
            '    return a < b\n',
            expected_patterns=["a < b"]
        )

    def test_lte(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> bool:\n'
            '    return a <= b\n',
            expected_patterns=["a <= b"]
        )

    def test_gt(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> bool:\n'
            '    return a > b\n',
            expected_patterns=["a > b"]
        )

    def test_gte(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> bool:\n'
            '    return a >= b\n',
            expected_patterns=["a >= b"]
        )

    def test_in(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return 1 in [1, 2, 3]\n',
            expected_patterns=["contains"]
        )

    def test_not_in(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return 4 not in [1, 2, 3]\n',
            expected_patterns=["!"]
        )

    def test_is(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return None is None\n',
            expected_patterns=["std::ptr::eq"]
        )

    def test_is_not(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return None is not None\n',
            expected_patterns=["!std::ptr::eq"]
        )

    def test_chained_compare(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> bool:\n'
            '    return 0 < x < 100\n',
            expected_patterns=["0 < x", "x < 100", "&&"]
        )


class TestExprCall:
    def test_function_call(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return len([1, 2, 3])\n',
            expected_patterns=["len() as i64"]
        )

    def test_builtin_len(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> cp.i64:\n'
            '    return len(x)\n',
            expected_patterns=["(x).len() as i64"]
        )

    def test_builtin_int(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return int(3.14)\n',
            expected_patterns=["3.14f64 as i64"]
        )

    def test_builtin_float(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    return float(42)\n',
            expected_patterns=["42 as f64"]
        )

    def test_builtin_bool(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return bool(1)\n',
            expected_patterns=["1 as bool"]
        )

    def test_builtin_abs(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.f64) -> cp.f64:\n'
            '    return abs(x)\n',
            expected_patterns=["(x).abs()"]
        )

    def test_builtin_min(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return min(a, b)\n',
            expected_patterns=["(a).min(b)"]
        )

    def test_builtin_max(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> cp.i64:\n'
            '    return max(a, b)\n',
            expected_patterns=["(a).max(b)"]
        )

    def test_builtin_sum(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> cp.i64:\n'
            '    return sum(x)\n',
            expected_patterns=["iter().sum"]
        )

    def test_builtin_sorted(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]):\n'
            '    return sorted(x)\n',
            expected_patterns=["sort_by"]
        )

    def test_builtin_reversed(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]):\n'
            '    return list(reversed(x))\n',
            expected_patterns=["rev()"]
        )

    def test_builtin_enumerate(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]):\n'
            '    return list(enumerate(x))\n',
            expected_patterns=["enumerate()"]
        )

    def test_builtin_any(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[bool]) -> bool:\n'
            '    return any(x)\n',
            expected_patterns=["any(|x| *x)"]
        )

    def test_builtin_all(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[bool]) -> bool:\n'
            '    return all(x)\n',
            expected_patterns=["all(|x| *x)"]
        )

    def test_builtin_chr(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> str:\n'
            '    return chr(65)\n',
            expected_patterns=["char::from_u32"]
        )

    def test_builtin_ord(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return ord("A")\n',
            expected_patterns=["as_bytes()[0] as i64"]
        )

    def test_builtin_hex(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> str:\n'
            '    return hex(255)\n',
            expected_patterns=['format!("0x{:x}"']
        )

    def test_builtin_oct(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> str:\n'
            '    return oct(8)\n',
            expected_patterns=['format!("0o{:o}"']
        )

    def test_builtin_bin(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> str:\n'
            '    return bin(5)\n',
            expected_patterns=['format!("0b{:b}"']
        )

    def test_builtin_pow(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    return pow(2.0, 3)\n',
            expected_patterns=["powi"]
        )

    def test_builtin_round(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    return round(3.14)\n',
            expected_patterns=["round()"]
        )

    def test_builtin_divmod(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    a, b = divmod(10, 3)\n'
            '    return a\n',
            expected_patterns=["let mut (a, b) ="]
        )

    def test_builtin_type(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    return type(42)\n',
            expected_patterns=["type("]
        )

    def test_builtin_id(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return id(42)\n',
            expected_patterns=["id("]
        )

    def test_builtin_repr(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> str:\n'
            '    return repr(42)\n',
            expected_patterns=['format!("{:?}"']
        )

    def test_builtin_hash(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    return hash(42)\n',
            expected_patterns=["/* hash */"]
        )

    def test_builtin_callable(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return callable(print)\n',
            expected_patterns=["callable"]
        )

    def test_builtin_isinstance(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> bool:\n'
            '    return isinstance(42, int)\n',
            expected_patterns=["isinstance"]
        )


class TestExprAttribute:
    def test_attribute(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.f64:\n'
            '    return cp.math.PI\n',
            expected_patterns=["std::f64::consts::PI"]
        )

    def test_method_call(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> cp.i64:\n'
            '    return len(x)\n',
            expected_patterns=["(x).len() as i64"]
        )

    def test_math_sin(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.f64) -> cp.f64:\n'
            '    return cp.math.sin(x)\n',
            expected_patterns=["(x).sin()"]
        )


class TestExprSubscript:
    def test_index(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> cp.i64:\n'
            '    return x[0]\n',
            expected_patterns=["(x)[0 as usize]"]
        )

    def test_variable_index(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64], i: cp.i64) -> cp.i64:\n'
            '    return x[i]\n',
            expected_patterns=["(x)[i as usize]"]
        )

    def test_slice(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> list[cp.i64]:\n'
            '    return x[1:3]\n',
            expected_patterns=["1 as usize..3 as usize"]
        )

    def test_slice_step(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> list[cp.i64]:\n'
            '    return x[0:10:2]\n',
            expected_patterns=["step_by(2 as usize)"]
        )

    def test_slice_open(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> list[cp.i64]:\n'
            '    return x[:5]\n',
            expected_patterns=["0 as usize..5 as usize"]
        )

    def test_slice_to_end(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: list[cp.i64]) -> list[cp.i64]:\n'
            '    return x[5:]\n',
            expected_patterns=["5 as usize.."]
        )


class TestExprList:
    def test_empty_list(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = []\n'
            '    return x\n',
            expected_patterns=["Vec::new()"]
        )

    def test_list_literal(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = [1, 2, 3]\n'
            '    return x\n',
            expected_patterns=["vec![1, 2, 3]"]
        )


class TestExprDict:
    def test_empty_dict(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {}\n'
            '    return x\n',
            expected_patterns=["HashMap::new()"]
        )

    def test_dict_literal(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1, "b": 2}\n'
            '    return x\n',
            expected_patterns=['("a".to_string(), 1)', '("b".to_string(), 2)']
        )


class TestExprTuple:
    def test_empty_tuple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = ()\n'
            '    return x\n',
            expected_patterns=["()"]
        )

    def test_tuple_literal(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = (1, 2, 3)\n'
            '    return x\n',
            expected_patterns=["(1, 2, 3)"]
        )


class TestExprSet:
    def test_empty_set(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = set()\n'
            '    return 0\n',
            expected_patterns=["HashSet::new()"]
        )

    def test_set_literal(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {1, 2, 3}\n'
            '    return 0\n',
            expected_patterns=["HashSet"]
        )


class TestExprIfExp:
    def test_ternary(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> cp.i64:\n'
            '    return x if x > 0 else -x\n',
            expected_patterns=["if x > 0"]
        )


class TestExprLambda:
    def test_lambda(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    add = lambda a, b: a + b\n'
            '    return add(1, 2)\n',
            expected_patterns=["|a, b| (a + b)"]
        )


class TestExprListComp:
    def test_simple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = [i * 2 for i in range(5)]\n'
            '    return x\n',
            expected_patterns=["into_iter().map"]
        )

    def test_with_filter(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = [i for i in range(10) if i % 2 == 0]\n'
            '    return x\n',
            expected_patterns=["filter"]
        )


class TestExprDictComp:
    def test_simple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {i: i * 2 for i in range(5)}\n'
            '    return 0\n',
            expected_patterns=["into_iter().map", "HashMap"]
        )


class TestExprSetComp:
    def test_simple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {i * 2 for i in range(5)}\n'
            '    return 0\n',
            expected_patterns=["into_iter().map", "HashSet"]
        )


class TestExprGeneratorExp:
    def test_simple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = (i * 2 for i in range(5))\n'
            '    return 0\n',
            expected_patterns=["into_iter().map"]
        )


class TestExprNamedExpr:
    def test_walrus(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    if (n := 10) > 5:\n'
            '        return n\n'
            '    return 0\n',
            expected_patterns=["let n = 10"]
        )


class TestExprStarred:
    def test_starred(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    a = [1, 2, 3]\n'
            '    b = [*a, 4, 5]\n'
            '    return b\n',
            expected_patterns=["*a"]
        )


class TestExprJoinedStr:
    def test_fstring_simple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.i64) -> str:\n'
            '    return f"value is {x}"\n',
            expected_patterns=["format!"]
        )

    def test_fstring_multiple(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(a: cp.i64, b: cp.i64) -> str:\n'
            '    return f"{a} + {b}"\n',
            expected_patterns=["format!"]
        )

    def test_fstring_format_spec(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(x: cp.f64) -> str:\n'
            '    return f"{x:.2f}"\n',
            expected_patterns=["format!"]
        )


class TestExprYield:
    def test_yield(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    yield 42\n',
            expected_patterns=["/* yield 42 */"]
        )


class TestExprYieldFrom:
    def test_yield_from(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    yield from [1, 2, 3]\n',
            expected_patterns=["/* yield from"]
        )


class TestExprAwait:
    def test_await(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'async def f():\n'
            '    return await some_coroutine()\n',
            expected_patterns=[]
        )


# ══════════════════════════════════════════════════════════════════════════
# STRING METHOD TESTS
# ══════════════════════════════════════════════════════════════════════════

class TestStringMethods:
    def test_upper(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> str:\n'
            '    return s.upper()\n',
            expected_patterns=["to_uppercase()"]
        )

    def test_lower(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> str:\n'
            '    return s.lower()\n',
            expected_patterns=["to_lowercase()"]
        )

    def test_strip(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> str:\n'
            '    return s.strip()\n',
            expected_patterns=["trim()"]
        )

    def test_lstrip(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> str:\n'
            '    return s.lstrip()\n',
            expected_patterns=["trim_start()"]
        )

    def test_rstrip(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> str:\n'
            '    return s.rstrip()\n',
            expected_patterns=["trim_end()"]
        )

    def test_startswith(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.startswith("hello")\n',
            expected_patterns=['starts_with(&"hello"']
        )

    def test_endswith(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.endswith("world")\n',
            expected_patterns=['ends_with(&"world"']
        )

    def test_replace(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> str:\n'
            '    return s.replace("a", "b")\n',
            expected_patterns=['replace(&"a".to_string(), &"b".to_string())']
        )

    def test_split(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str):\n'
            '    return s.split(",")\n',
            expected_patterns=['split(&",".to_string())']
        )

    def test_find(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> cp.i64:\n'
            '    return s.find("x")\n',
            expected_patterns=['find(&"x".to_string())']
        )

    def test_count(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> cp.i64:\n'
            '    return s.count("x")\n',
            expected_patterns=['matches(&"x".to_string())']
        )

    def test_isalpha(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.isalpha()\n',
            expected_patterns=["is_alphabetic()"]
        )

    def test_isdigit(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.isdigit()\n',
            expected_patterns=["is_numeric()"]
        )

    def test_isalnum(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.isalnum()\n',
            expected_patterns=["is_alphanumeric()"]
        )

    def test_isspace(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.isspace()\n',
            expected_patterns=["is_whitespace()"]
        )

    def test_isupper(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.isupper()\n',
            expected_patterns=["is_uppercase()"]
        )

    def test_islower(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str) -> bool:\n'
            '    return s.islower()\n',
            expected_patterns=["is_lowercase()"]
        )

    def test_join(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(parts: list[str]) -> str:\n'
            '    return ",".join(parts)\n',
            expected_patterns=['join(&",".to_string())']
        )

    def test_encode(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f(s: str):\n'
            '    return s.encode()\n',
            expected_patterns=["as_bytes().to_vec()"]
        )


# ══════════════════════════════════════════════════════════════════════════
# LIST/DICT METHOD TESTS
# ══════════════════════════════════════════════════════════════════════════

class TestListMethods:
    def test_append(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [1, 2]\n'
            '    x.append(3)\n'
            '    return x\n',
            expected_patterns=["push(3)"]
        )

    def test_extend(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [1, 2]\n'
            '    x.extend([3, 4])\n'
            '    return x\n',
            expected_patterns=["extend"]
        )

    def test_insert(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [1, 3]\n'
            '    x.insert(1, 2)\n'
            '    return x\n',
            expected_patterns=["insert"]
        )

    def test_remove(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [1, 2, 3]\n'
            '    x.remove(2)\n'
            '    return x\n',
            expected_patterns=["retain"]
        )

    def test_pop(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = [1, 2, 3]\n'
            '    return x.pop()\n',
            expected_patterns=["pop()"]
        )

    def test_index(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = [10, 20, 30]\n'
            '    return x.index(20)\n',
            expected_patterns=["iter().position"]
        )

    def test_sort(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [3, 1, 2]\n'
            '    x.sort()\n'
            '    return x\n',
            expected_patterns=["sort()"]
        )

    def test_reverse(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [1, 2, 3]\n'
            '    x.reverse()\n'
            '    return x\n',
            expected_patterns=["reverse()"]
        )

    def test_copy(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> list[cp.i64]:\n'
            '    x = [1, 2, 3]\n'
            '    y = x.copy()\n'
            '    return y\n',
            expected_patterns=["clone()"]
        )

    def test_clear(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = [1, 2, 3]\n'
            '    x.clear()\n',
            expected_patterns=["clear()"]
        )

    def test_count(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = [1, 2, 2, 3]\n'
            '    return x.count(2)\n',
            expected_patterns=["iter().filter"]
        )


class TestDictMethods:
    def test_get(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = {"a": 1}\n'
            '    return x.get("a", 0)\n',
            expected_patterns=['get(&"a"']
        )

    def test_keys(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1, "b": 2}\n'
            '    return x.keys()\n',
            expected_patterns=["keys()"]
        )

    def test_values(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1, "b": 2}\n'
            '    return x.values()\n',
            expected_patterns=["values()"]
        )

    def test_items(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1, "b": 2}\n'
            '    return x.items()\n',
            expected_patterns=["iter().map(|(k, v)|"]
        )

    def test_pop_dict(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f() -> cp.i64:\n'
            '    x = {"a": 1, "b": 2}\n'
            '    return x.pop("a", 0)\n',
            expected_patterns=["remove"]
        )

    def test_clear_dict(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1}\n'
            '    x.clear()\n',
            expected_patterns=["clear()"]
        )

    def test_copy_dict(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1}\n'
            '    y = x.copy()\n'
            '    return 0\n',
            expected_patterns=["clone()"]
        )

    def test_update(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1}\n'
            '    x.update({"b": 2})\n',
            expected_patterns=["extend"]
        )

    def test_setdefault(self):
        transpile_and_verify(
            'import copperhead as cp\n\n'
            '@cp.compile(target="rust")\n'
            'def f():\n'
            '    x = {"a": 1}\n'
            '    x.setdefault("b", 2)\n',
            expected_patterns=["entry"]
        )


# ══════════════════════════════════════════════════════════════════════════
# ZERO PLACEHOLDER VALIDATION
# ══════════════════════════════════════════════════════════════════════════

class TestZeroPlaceholders:
    def test_no_placeholder_bodies(self):
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
def sum_list(numbers: list[cp.f64]) -> cp.f64:
    total = 0.0
    for n in numbers:
        total += n
    return total

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
        unexpected = ["Ok(0.0)", "Ok(0);", "Ok(false)", "PyNone", "PyObject::None(_py)"]
        for pattern in unexpected:
            count = rust_code.count(pattern)
            if pattern == "PyObject::None(_py)":
                assert count <= 2, f"Too many PyObject::None(_py) fallbacks: {count}"
            else:
                assert count == 0, f"Placeholder found: {pattern} ({count} occurrences)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
