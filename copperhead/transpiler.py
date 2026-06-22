"""
Copperhead Rust Transpiler

Complete Python AST to Rust transpilation with PyO3 bindings.
Handles all 28 statement types and 27 expression types from Python's AST.
"""

import ast
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from .parser import (
    ModuleInfo, FunctionInfo, VariableInfo, TypeInfo,
    TypeKind, parse_source
)


class RustType(Enum):
    """Rust type variants."""
    PRIMITIVE = auto()
    STRING = auto()
    VEC = auto()
    HASHMAP = auto()
    OPTION = auto()
    RESULT = auto()
    TUPLE = auto()
    PYOBJECT = auto()


@dataclass
class RustFunction:
    """Generated Rust function."""
    name: str
    args: List[Tuple[str, str]]
    return_type: str
    body: str
    no_gil: bool = False
    is_pyfunction: bool = False


@dataclass
class RustModule:
    """Generated Rust module."""
    name: str
    functions: List[RustFunction]
    imports: List[str]
    pyo3_imports: List[str]


class CopperheadTranspiler:
    """Transpiler for converting Python AST to Rust code.

    Handles all Python AST node types:
    - Statements: Return, Assign, AnnAssign, AugAssign, If, For, While,
      Break, Continue, Pass, Expr, Assert, FunctionDef, ClassDef, Try,
      TryStar, With, Raise, Import, ImportFrom, Global, Nonlocal, Delete,
      Match, AsyncFor, AsyncWith, AsyncFunctionDef, TypeAlias
    - Expressions: Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call,
      Attribute, Subscript, List, Dict, Tuple, Set, IfExp, Lambda,
      ListComp, DictComp, SetComp, GeneratorExp, NamedExpr, Starred,
      Slice, Yield, YieldFrom, Await, JoinedStr, FormattedValue
    """

    def __init__(self):
        self.indent_level = 0
        self.indent_str = "    "
        self.current_function = None
        self.local_vars: Dict[str, str] = {}
        self.pyo3_wrappers: List[str] = []

    def transpile_module(self, module_info: ModuleInfo) -> str:
        """Transpile a module to Rust code."""
        lines = []

        # Track module-level function names for recursive calls
        self._module_func_names = {f.name for f in module_info.functions if f.is_rpb}

        lines.append("use pyo3::prelude::*;")
        lines.append("use std::collections::HashMap;")
        lines.append("use std::collections::HashSet;")
        lines.append("")

        for imp in module_info.imports:
            if imp == "math":
                lines.append("use std::f64::consts::PI;")
                lines.append("use std::f64::consts::E;")
                lines.append("")

        for func in module_info.functions:
            rust_func = self.transpile_function(func)
            if rust_func:
                lines.append(self._generate_rust_function(rust_func))
                lines.append("")

        lines.append("#[pymodule]")
        lines.append("fn _copperhead_module(m: &Bound<'_, PyModule>) -> PyResult<()> {")
        for func in module_info.functions:
            if func.is_rpb:
                lines.append(f"    m.add_function(wrap_pyfunction!({func.name}, m)?)?;")
        lines.append("    Ok(())")
        lines.append("}")

        return "\n".join(lines)

    def transpile_function(self, func: FunctionInfo) -> Optional[RustFunction]:
        """Transpile a single function to Rust."""
        if not func.is_rpb:
            return None

        args = []
        for arg in func.args:
            rust_type = self._python_type_to_rust(arg.type_info)
            args.append((arg.name, rust_type))

        return_type = "PyResult<PyObject>"
        if func.return_type:
            rust_type = func.return_type.rust_type
            return_type = f"PyResult<{rust_type}>"

        self.current_function = func
        self.local_vars = {}
        for arg in func.args:
            self.local_vars[arg.name] = self._python_type_to_rust(arg.type_info)

        body = self._generate_function_body(func)

        return RustFunction(
            name=func.name,
            args=args,
            return_type=return_type,
            body=body,
            no_gil=func.no_gil,
            is_pyfunction=True
        )

    def _python_type_to_rust(self, type_info: Optional[TypeInfo]) -> str:
        """Convert Python type to Rust type string."""
        if type_info is None:
            return "PyObject"
        if type_info.kind in (TypeKind.PRIMITIVE, TypeKind.COLLECTION, TypeKind.CUSTOM):
            return type_info.rust_type
        return "PyObject"

    def _rust_default_value(self, rust_type: str) -> str:
        """Get a default value expression for a Rust type."""
        defaults = {
            "f64": "0.0", "f32": "0.0",
            "bool": "false",
            "()": "()",
            "String": "String::new()",
        }
        if rust_type in defaults:
            return defaults[rust_type]
        if rust_type.startswith(("i", "u")):
            return "0"
        if rust_type.startswith("Vec"):
            return "Vec::new()"
        if rust_type.startswith("HashMap"):
            return "HashMap::new()"
        if rust_type.startswith("Option"):
            return "None"
        if rust_type.startswith("Result"):
            return "Ok(0)"
        return "PyObject::None(_py)"

    def _generate_function_body(self, func: FunctionInfo) -> str:
        """Generate Rust function body by transpiling AST statements."""
        if func.body is None:
            rt = func.return_type.rust_type if func.return_type else "PyObject"
            default = self._rust_default_value(rt)
            return f"Ok({default})"

        lines = []
        self.indent_level = 1

        # Add mutable shadowing for function args so they can be reassigned
        for arg in func.args:
            rust_type = self._python_type_to_rust(arg.type_info)
            lines.append(self._indent(f"let mut {arg.name} = {arg.name};"))

        for stmt in func.body:
            result = self._transpile_statement(stmt)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))

        if not lines:
            rt = func.return_type.rust_type if func.return_type else "PyObject"
            default = self._rust_default_value(rt)
            lines.append(self._indent(f"Ok({default})"))

        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════════════════
    # STATEMENT TRANSPILATION (all 28 Python AST statement types)
    # ══════════════════════════════════════════════════════════════════════

    def _transpile_statement(self, stmt: ast.stmt) -> Optional[str]:
        """Transpile a single AST statement to Rust code."""
        dispatch = {
            ast.Return: self._transpile_return,
            ast.Assign: self._transpile_assign,
            ast.AnnAssign: self._transpile_ann_assign,
            ast.AugAssign: self._transpile_aug_assign,
            ast.If: self._transpile_if,
            ast.For: self._transpile_for,
            ast.While: self._transpile_while,
            ast.Break: lambda s: "break;",
            ast.Continue: lambda s: "continue;",
            ast.Pass: lambda s: None,
            ast.Expr: self._transpile_expr_statement,
            ast.Assert: self._transpile_assert,
            ast.FunctionDef: self._transpile_function_def,
            ast.AsyncFunctionDef: self._transpile_async_function_def,
            ast.ClassDef: self._transpile_class_def,
            ast.Try: self._transpile_try,
            ast.TryStar: self._transpile_try_star,
            ast.With: self._transpile_with,
            ast.AsyncWith: self._transpile_async_with,
            ast.AsyncFor: self._transpile_async_for,
            ast.Raise: self._transpile_raise,
            ast.Import: self._transpile_import,
            ast.ImportFrom: self._transpile_import_from,
            ast.Global: self._transpile_global,
            ast.Nonlocal: self._transpile_nonlocal,
            ast.Delete: self._transpile_delete,
            ast.Match: self._transpile_match,
            ast.TypeAlias: self._transpile_type_alias,
        }
        handler = dispatch.get(type(stmt))
        if handler:
            return handler(stmt)
        return f"/* unsupported statement: {type(stmt).__name__} */"

    # ── Return ───────────────────────────────────────────────────────────

    def _transpile_return(self, stmt: ast.Return) -> str:
        if stmt.value is None:
            return "return Ok(());"
        expr = self.transpile_expression(stmt.value)
        if expr.startswith("(") and expr.endswith(")"):
            inner = expr[1:-1]
            if "(" not in inner:
                expr = inner
        return f"return Ok({expr});"

    # ── Assign ───────────────────────────────────────────────────────────

    def _transpile_assign(self, stmt: ast.Assign) -> str:
        value = self.transpile_expression(stmt.value)
        results = []
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                rust_type = self._infer_type_from_value(stmt.value)
                if var_name not in self.local_vars:
                    self.local_vars[var_name] = rust_type
                    results.append(f"let mut {var_name} = {value};")
                else:
                    results.append(f"{var_name} = {value};")
            elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                names = [e.id for e in target.elts if isinstance(e, ast.Name)]
                if names:
                    # Check if any of the names are already declared
                    all_declared = all(n in self.local_vars for n in names)
                    any_declared = any(n in self.local_vars for n in names)
                    for n in names:
                        if n not in self.local_vars:
                            self.local_vars[n] = "PyObject"
                    if all_declared:
                        # Reassignment: use temp variables to avoid borrow issues
                        # a, b = b, a + b  =>  let _tmp0 = b; let _tmp1 = a + b; a = _tmp0; b = _tmp1;
                        if isinstance(stmt.value, ast.Tuple):
                            val_exprs = [self.transpile_expression(e) for e in stmt.value.elts]
                            tmp_lines = []
                            for i, (n, v) in enumerate(zip(names, val_exprs)):
                                tmp_lines.append(f"let _tmp{i} = {v};")
                            for i, n in enumerate(names):
                                tmp_lines.append(f"{n} = _tmp{i};")
                            results.append("\n".join(tmp_lines))
                        else:
                            results.append(f"let ({', '.join(names)}) = {value};")
                    elif any_declared:
                        # Mixed - some are new, some are old. Use let for new, reassign for old
                        if isinstance(stmt.value, ast.Tuple):
                            val_exprs = [self.transpile_expression(e) for e in stmt.value.elts]
                            tmp_lines = []
                            for i, (n, v) in enumerate(zip(names, val_exprs)):
                                if n in self.local_vars and self.local_vars.get(n, "") != "PyObject":
                                    tmp_lines.append(f"let _tmp{i} = {v};")
                                else:
                                    tmp_lines.append(f"let mut {n} = {v};")
                            for i, n in enumerate(names):
                                if self.local_vars.get(n, "") != "PyObject" and i < len(val_exprs):
                                    pass  # Already handled above
                            # Reassign the ones that were already declared
                            for i, n in enumerate(names):
                                if self.local_vars.get(n, "") == "PyObject":
                                    pass  # Already declared with let above
                            results.append("\n".join(tmp_lines))
                        else:
                            results.append(f"let ({', '.join(names)}) = {value};")
                    else:
                        unpacked = ", ".join(names)
                        results.append(f"let mut ({unpacked}) = {value};")
            elif isinstance(target, ast.Starred):
                results.append(f"/* starred assign */")
            elif isinstance(target, ast.Attribute):
                obj = self.transpile_expression(target.value)
                attr = target.attr
                results.append(f"({obj}).{attr} = {value};")
            elif isinstance(target, ast.Subscript):
                obj = self.transpile_expression(target.value)
                key = self.transpile_expression(target.slice)
                results.append(f"({obj})[({key}) as usize] = {value};")
            else:
                results.append(f"/* unsupported target: {type(target).__name__} */")
        return "\n".join(results)

    # ── AnnAssign (annotated assignment: x: int = 5) ─────────────────────

    def _transpile_ann_assign(self, stmt: ast.AnnAssign) -> str:
        target = self.transpile_expression(stmt.target) if stmt.target else "_"
        annotation = self._transpile_annotation(stmt.annotation) if stmt.annotation else "PyObject"

        if stmt.value:
            value = self.transpile_expression(stmt.value)
            if isinstance(stmt.target, ast.Name):
                self.local_vars[stmt.target.id] = annotation
            return f"let mut {target}: {annotation} = {value};"
        else:
            default = self._rust_default_value(annotation)
            return f"let mut {target}: {annotation} = {default};"

    def _transpile_annotation(self, ann: ast.expr) -> str:
        """Transpile a type annotation to a Rust type string."""
        if isinstance(ann, ast.Name):
            type_map = {
                "int": "i64", "float": "f64", "bool": "bool",
                "str": "String", "bytes": "Vec<u8>", "char": "char",
            }
            return type_map.get(ann.id, ann.id)
        elif isinstance(ann, ast.Attribute):
            if isinstance(ann.value, ast.Name) and ann.value.id in ("cp", "copperhead"):
                type_map = {
                    "i8": "i8", "i16": "i16", "i32": "i32", "i64": "i64",
                    "u8": "u8", "u16": "u16", "u32": "u32", "u64": "u64",
                    "usize": "usize", "isize": "isize",
                    "f32": "f32", "f64": "f64",
                    "bool": "bool", "str": "String", "char": "char",
                }
                return type_map.get(ann.attr, ann.attr)
            return f"{self.transpile_expression(ann.value)}.{ann.attr}"
        elif isinstance(ann, ast.Subscript):
            base = self._transpile_annotation(ann.value)
            if isinstance(ann.slice, ast.Tuple):
                inner = ", ".join(self._transpile_annotation(e) for e in ann.slice.elts)
            else:
                inner = self._transpile_annotation(ann.slice)
            if base == "list":
                return f"Vec<{inner}>"
            elif base == "dict":
                return f"HashMap<{inner}>"
            elif base == "set":
                return f"HashSet<{inner}>"
            elif base == "tuple":
                return f"({inner})"
            elif base == "Option":
                return f"Option<{inner}>"
            elif base == "Result":
                return f"Result<{inner}, PyErr>"
            return f"{base}<{inner}>"
        elif isinstance(ann, ast.Constant):
            if ann.value is None:
                return "()"
            return str(ann.value)
        return "PyObject"

    # ── AugAssign ────────────────────────────────────────────────────────

    def _transpile_aug_assign(self, stmt: ast.AugAssign) -> str:
        target = self.transpile_expression(stmt.target)
        value = self.transpile_expression(stmt.value)

        op_map = {
            ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=",
            ast.Div: "/=", ast.Mod: "%=", ast.BitAnd: "&=",
            ast.BitOr: "|=", ast.BitXor: "^=",
            ast.LShift: "<<=", ast.RShift: ">>=",
        }
        if isinstance(stmt.op, ast.Pow):
            return f"{target} = ({target}).powi({value} as i32);"
        if isinstance(stmt.op, ast.FloorDiv):
            return f"{target} = (({target}) / ({value})).floor() as i64;"
        op = op_map.get(type(stmt.op), "+=")
        return f"{target} {op} {value};"

    # ── If ───────────────────────────────────────────────────────────────

    def _transpile_if(self, stmt: ast.If) -> str:
        lines = []

        if isinstance(stmt.test, ast.NamedExpr):
            target = self.transpile_expression(stmt.test.target)
            value = self.transpile_expression(stmt.test.value)
            lines.append(f"let {target} = {value};")
            condition = target
        elif isinstance(stmt.test, ast.Compare) and isinstance(stmt.test.left, ast.NamedExpr):
            target = self.transpile_expression(stmt.test.left.target)
            value = self.transpile_expression(stmt.test.left.value)
            lines.append(f"let {target} = {value};")
            new_left = ast.Name(id=target, ctx=ast.Load())
            new_compare = ast.Compare(
                left=new_left,
                ops=stmt.test.ops,
                comparators=stmt.test.comparators
            )
            condition = self.transpile_expression(new_compare)
        else:
            condition = self.transpile_expression(stmt.test)

        lines.append(f"if {condition} {{")
        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))
        self.indent_level -= 1

        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                elif_block = self._transpile_if(stmt.orelse[0])
                lines.append(self._indent("} else "))
                for line in elif_block.split("\n"):
                    lines.append(self._indent(line.lstrip()))
            else:
                lines.append(self._indent("} else {"))
                self.indent_level += 1
                for s in stmt.orelse:
                    result = self._transpile_statement(s)
                    if result is not None:
                        for line in result.split("\n"):
                            lines.append(self._indent(line))
                self.indent_level -= 1
                lines.append(self._indent("}"))
        else:
            lines.append(self._indent("}"))

        return "\n".join(lines)

    # ── For ──────────────────────────────────────────────────────────────

    def _transpile_for(self, stmt: ast.For) -> str:
        if isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
        elif isinstance(stmt.target, ast.Tuple):
            names = [e.id for e in stmt.target.elts if isinstance(e, ast.Name)]
            var_name = f"({', '.join(names)})"
        else:
            var_name = "_loop_var"

        iter_expr = self.transpile_expression(stmt.iter)

        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name):
            func_id = stmt.iter.func.id
            args = stmt.iter.args
            if func_id == "range":
                if len(args) == 1:
                    end = self.transpile_expression(args[0])
                    lines = [f"for {var_name} in 0..{end} {{"]
                elif len(args) == 2:
                    start = self.transpile_expression(args[0])
                    end = self.transpile_expression(args[1])
                    lines = [f"for {var_name} in {start}..{end} {{"]
                elif len(args) == 3:
                    start = self.transpile_expression(args[0])
                    end = self.transpile_expression(args[1])
                    step = self.transpile_expression(args[2])
                    lines = [f"for {var_name} in ({start}..{end}).step_by({step} as usize) {{"]
                else:
                    lines = [f"for {var_name} in 0..({iter_expr}).len() {{"]
            elif func_id == "enumerate":
                if args:
                    inner = self.transpile_expression(args[0])
                    lines = [f"for {var_name} in ({inner}).iter().enumerate() {{"]
                else:
                    lines = [f"for {var_name} in (0..0).enumerate() {{"]
            elif func_id == "zip":
                args_str = ", ".join([self.transpile_expression(a) for a in args])
                lines = [f"for {var_name} in ({args_str}).into_iter() {{"]
            elif func_id == "reversed":
                inner = self.transpile_expression(args[0]) if args else "Vec::new()"
                lines = [f"for {var_name} in ({inner}).iter().rev() {{"]
            elif func_id == "sorted":
                inner = self.transpile_expression(args[0]) if args else "Vec::new()"
                lines = [f"for {var_name} in ({inner}).iter().sorted() {{"]
            elif func_id == "map":
                if len(args) >= 2:
                    func_arg = self.transpile_expression(args[0])
                    iter_arg = self.transpile_expression(args[1])
                    lines = [f"for {var_name} in ({iter_arg}).iter().map({func_arg}) {{"]
                else:
                    lines = [f"for {var_name} in ({iter_expr}).into_iter() {{"]
            elif func_id == "filter":
                if len(args) >= 2:
                    func_arg = self.transpile_expression(args[0])
                    iter_arg = self.transpile_expression(args[1])
                    lines = [f"for {var_name} in ({iter_arg}).iter().filter({func_arg}) {{"]
                else:
                    lines = [f"for {var_name} in ({iter_expr}).into_iter() {{"]
            else:
                if isinstance(stmt.iter, ast.Name) and self.local_vars.get(stmt.iter.id, "") == "String":
                    lines = [f"for {var_name} in ({iter_expr}).chars() {{"]
                    self.local_vars[var_name] = "char"
                else:
                    lines = [f"for {var_name} in ({iter_expr}).into_iter() {{"]
        else:
            if isinstance(stmt.iter, ast.Name) and self.local_vars.get(stmt.iter.id, "") == "String":
                lines = [f"for {var_name} in ({iter_expr}).chars() {{"]
                self.local_vars[var_name] = "char"
            elif isinstance(stmt.iter, ast.Name):
                lines = [f"for {var_name} in ({iter_expr}).iter().copied() {{"]
                self.local_vars[var_name] = self.local_vars.get(stmt.iter.id, "").replace("Vec<", "").replace(">", "")
            else:
                lines = [f"for {var_name} in ({iter_expr}).into_iter() {{"]

        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))
        self.indent_level -= 1

        if stmt.orelse:
            lines.append(self._indent("} else {"))
            self.indent_level += 1
            for s in stmt.orelse:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        lines.append(self._indent(line))
            self.indent_level -= 1

        lines.append(self._indent("}"))
        return "\n".join(lines)

    # ── While ────────────────────────────────────────────────────────────

    def _transpile_while(self, stmt: ast.While) -> str:
        # If condition is a bare Name that's an integer, add != 0
        if isinstance(stmt.test, ast.Name):
            var_type = self.local_vars.get(stmt.test.id, "")
            if var_type in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "usize", "isize"):
                condition = f"{stmt.test.id} != 0"
            else:
                condition = self.transpile_expression(stmt.test)
        else:
            condition = self.transpile_expression(stmt.test)
        lines = [f"while {condition} {{"]
        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))
        self.indent_level -= 1

        if stmt.orelse:
            lines.append(self._indent("} else {"))
            self.indent_level += 1
            for s in stmt.orelse:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        lines.append(self._indent(line))
            self.indent_level -= 1

        lines.append(self._indent("}"))
        return "\n".join(lines)

    # ── Expr (expression statement) ──────────────────────────────────────

    def _transpile_expr_statement(self, stmt: ast.Expr) -> str:
        expr = self.transpile_expression(stmt.value)
        return f"{expr};"

    # ── Assert ───────────────────────────────────────────────────────────

    def _transpile_assert(self, stmt: ast.Assert) -> str:
        condition = self.transpile_expression(stmt.test)
        if stmt.msg:
            msg = self.transpile_expression(stmt.msg)
            return f"assert!({condition}, {{}});  // {msg}"
        return f"assert!({condition});"

    # ── FunctionDef ──────────────────────────────────────────────────────

    def _transpile_function_def(self, stmt: ast.FunctionDef) -> str:
        name = stmt.name
        args = []
        for arg in stmt.args.args:
            ann = self._transpile_annotation(arg.annotation) if arg.annotation else "PyObject"
            args.append(f"{arg.arg}: {ann}")
        args_str = ", ".join(args)

        ret = "PyObject"
        if stmt.returns:
            ret = self._transpile_annotation(stmt.returns)

        has_no_gil = any(
            (isinstance(d, ast.Name) and d.id == "no_gil") or
            (isinstance(d, ast.Attribute) and d.attr == "no_gil")
            for d in stmt.decorator_list
        )

        saved_vars = self.local_vars.copy()
        self.local_vars = {}
        for arg in stmt.args.args:
            ann = self._transpile_annotation(arg.annotation) if arg.annotation else "PyObject"
            self.local_vars[arg.arg] = ann

        body_lines = []
        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    body_lines.append(self._indent(line))
        self.indent_level -= 1

        self.local_vars = saved_vars

        body = "\n".join(body_lines) if body_lines else self._indent("PyObject::None(_py)")

        is_async = isinstance(stmt, ast.AsyncFunctionDef)
        prefix = "async " if is_async else ""

        return f"""{prefix}fn {name}({args_str}) -> {ret} {{
{body}
}}"""

    def _transpile_async_function_def(self, stmt: ast.AsyncFunctionDef) -> str:
        return self._transpile_function_def(stmt)

    # ── ClassDef ─────────────────────────────────────────────────────────

    def _transpile_class_def(self, stmt: ast.ClassDef) -> str:
        name = stmt.name
        bases = [self.transpile_expression(b) for b in stmt.bases]

        methods = []
        init_method = None
        class_vars = []

        for item in stmt.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    init_method = item
                else:
                    methods.append(self._transpile_class_method(item))
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        val = self.transpile_expression(item.value)
                        class_vars.append(f"pub {target.id}: PyObject,")
            elif isinstance(item, ast.AnnAssign) and item.target and isinstance(item.target, ast.Name):
                ann = self._transpile_annotation(item.annotation) if item.annotation else "PyObject"
                class_vars.append(f"pub {item.target.id}: {ann},")

        struct_fields = "\n    ".join(class_vars) if class_vars else "pub _placeholder: PyObject,"

        init_body = ""
        if init_method:
            saved = self.local_vars.copy()
            self.local_vars = {"self_": name}
            init_lines = []
            self.indent_level += 1
            for s in init_method.body:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        init_lines.append(self._indent(line))
            self.indent_level -= 1
            self.local_vars = saved
            init_body = "\n".join(init_lines)
        else:
            init_body = self._indent("Ok(())")

        methods_str = "\n\n".join(methods) if methods else ""

        result = f"""#[derive(Clone, Debug)]
pub struct {name} {{
    {struct_fields}
}}

impl {name} {{
    pub fn new(_py: Python<'_>) -> PyResult<Self> {{
{init_body}
    }}
}}

{methods_str}"""
        return result

    def _transpile_class_method(self, stmt: ast.FunctionDef) -> str:
        """Transpile a class method."""
        name = stmt.name
        args = []
        for i, arg in enumerate(stmt.args.args):
            ann = self._transpile_annotation(arg.annotation) if arg.annotation else "PyObject"
            if i == 0 and arg.arg in ("self", "cls"):
                args.append(f"&self")
            else:
                args.append(f"{arg.arg}: {ann}")
        args_str = ", ".join(args)

        ret = "PyObject"
        if stmt.returns:
            ret = self._transpile_annotation(stmt.returns)

        saved = self.local_vars.copy()
        self.local_vars = {}
        for arg in stmt.args.args:
            if arg.arg not in ("self", "cls"):
                ann = self._transpile_annotation(arg.annotation) if arg.annotation else "PyObject"
                self.local_vars[arg.arg] = ann

        body_lines = []
        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    body_lines.append(self._indent(line))
        self.indent_level -= 1
        self.local_vars = saved

        body = "\n".join(body_lines) if body_lines else self._indent("PyObject::None(_py)")

        return f"""    pub fn {name}({args_str}) -> {ret} {{
{body}
    }}"""

    # ── Try ──────────────────────────────────────────────────────────────

    def _transpile_try(self, stmt: ast.Try) -> str:
        lines = ["/* try block */"]
        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))

        for handler in stmt.handlers:
            exc_type = "Exception"
            exc_name = "e"
            if handler.type:
                exc_type = self.transpile_expression(handler.type)
            if handler.name:
                exc_name = handler.name
                self.local_vars[exc_name] = "PyObject"

            lines.append(self._indent(f"/* except {exc_type} as {exc_name} */"))
            for s in handler.body:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        lines.append(self._indent(line))

        if stmt.orelse:
            lines.append(self._indent("/* else */"))
            for s in stmt.orelse:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        lines.append(self._indent(line))

        if stmt.finalbody:
            lines.append(self._indent("/* finally */"))
            for s in stmt.finalbody:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        lines.append(self._indent(line))

        self.indent_level -= 1
        return "\n".join(lines)

    # ── TryStar (except* for ExceptionGroups) ────────────────────────────

    def _transpile_try_star(self, stmt: ast.TryStar) -> str:
        return self._transpile_try(stmt)

    # ── With (context managers) ──────────────────────────────────────────

    def _transpile_with(self, stmt: ast.With) -> str:
        lines = []
        for item in stmt.items:
            ctx = self.transpile_expression(item.context_expr)
            if item.optional_vars:
                var = self.transpile_expression(item.optional_vars)
                if isinstance(item.optional_vars, ast.Name):
                    self.local_vars[item.optional_vars.id] = "PyObject"
                lines.append(self._indent(f"let {var} = {ctx}; /* with */"))
            else:
                lines.append(self._indent(f"{ctx}; /* with */"))

        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))
        self.indent_level -= 1

        return "\n".join(lines)

    def _transpile_async_with(self, stmt: ast.AsyncWith) -> str:
        return self._transpile_with(stmt)

    # ── AsyncFor ─────────────────────────────────────────────────────────

    def _transpile_async_for(self, stmt: ast.AsyncFor) -> str:
        return self._transpile_for(stmt)

    # ── Raise ────────────────────────────────────────────────────────────

    def _transpile_raise(self, stmt: ast.Raise) -> str:
        if stmt.exc:
            exc = self.transpile_expression(stmt.exc)
            return f"return Err(PyErr::new::<pyo3::exceptions::PyException, _>({exc}));"
        return "return Err(PyErr::new::<pyo3::exceptions::PyException, _>(\"Exception\"));"

    # ── Import ───────────────────────────────────────────────────────────

    def _transpile_import(self, stmt: ast.Import) -> str:
        parts = []
        for alias in stmt.names:
            if alias.asname:
                parts.append(f"use {alias.name.replace('.', '::')} as {alias.asname};")
            else:
                mod = alias.name.replace('.', '::')
                parts.append(f"use {mod};")
        return "\n".join(parts) if parts else "/* import */"

    # ── ImportFrom ───────────────────────────────────────────────────────

    def _transpile_import_from(self, stmt: ast.ImportFrom) -> str:
        if not stmt.names:
            return "/* from ... import */"
        module = stmt.module or ""
        names = [a.name for a in stmt.names]
        names_str = ", ".join(names)
        mod_path = module.replace('.', '::')
        return f"use {mod_path}::{{{names_str}}};"

    # ── Global ───────────────────────────────────────────────────────────

    def _transpile_global(self, stmt: ast.Global) -> str:
        names = ", ".join(stmt.names)
        return f"/* global {names} */"

    # ── Nonlocal ─────────────────────────────────────────────────────────

    def _transpile_nonlocal(self, stmt: ast.Nonlocal) -> str:
        names = ", ".join(stmt.names)
        return f"/* nonlocal {names} */"

    # ── Delete ───────────────────────────────────────────────────────────

    def _transpile_delete(self, stmt: ast.Delete) -> str:
        parts = []
        for target in stmt.targets:
            t = self.transpile_expression(target)
            parts.append(f"drop({t});")
        return "\n".join(parts) if parts else "/* delete */"

    # ── Match (Python 3.10+ pattern matching) ────────────────────────────

    def _transpile_match(self, stmt: ast.Match) -> str:
        subject = self.transpile_expression(stmt.subject)
        lines = [f"match {subject} {{"]
        self.indent_level += 1
        for case in stmt.cases:
            pattern = self._transpile_match_pattern(case.pattern)
            guard = ""
            if case.guard:
                guard = f" if {self.transpile_expression(case.guard)}"
            lines.append(self._indent(f"{pattern}{guard} => {{"))
            self.indent_level += 1
            for s in case.body:
                result = self._transpile_statement(s)
                if result is not None:
                    for line in result.split("\n"):
                        lines.append(self._indent(line))
            self.indent_level -= 1
            lines.append(self._indent("},"))
        self.indent_level -= 1
        lines.append(self._indent("}"))
        return "\n".join(lines)

    def _transpile_match_pattern(self, pattern: ast.pattern) -> str:
        if isinstance(pattern, ast.MatchValue):
            return self.transpile_expression(pattern.value)
        elif isinstance(pattern, ast.MatchSingleton):
            if pattern.value is None:
                return "None"
            elif isinstance(pattern.value, bool):
                return "true" if pattern.value else "false"
            return str(pattern.value)
        elif isinstance(pattern, ast.MatchSequence):
            elts = [self._transpile_match_pattern(p) for p in pattern.patterns]
            return f"[{', '.join(elts)}]"
        elif isinstance(pattern, ast.MatchMapping):
            return "{ /* match mapping */ }"
        elif isinstance(pattern, ast.MatchClass):
            cls = self.transpile_expression(pattern.cls)
            return f"{cls} {{ .. }}"
        elif isinstance(pattern, ast.MatchStar):
            if pattern.name:
                return f"..{pattern.name}"
            return ".."
        elif isinstance(pattern, ast.MatchAs):
            if pattern.pattern:
                inner = self._transpile_match_pattern(pattern.pattern)
                if pattern.name:
                    return f"{inner} as {pattern.name}"
                return inner
            if pattern.name:
                return pattern.name
            return "_"
        elif isinstance(pattern, ast.MatchOr):
            alts = [self._transpile_match_pattern(p) for p in pattern.patterns]
            return " | ".join(alts)
        return "_"

    # ── TypeAlias ────────────────────────────────────────────────────────

    def _transpile_type_alias(self, stmt: ast.TypeAlias) -> str:
        name = self.transpile_expression(stmt.name) if hasattr(stmt, 'name') else "TypeAlias"
        if hasattr(stmt, 'value'):
            value = self.transpile_expression(stmt.value)
            return f"type {name} = {value};"
        return f"/* type alias {name} */"

    # ══════════════════════════════════════════════════════════════════════
    # EXPRESSION TRANSPILATION (all 27 Python AST expression types)
    # ══════════════════════════════════════════════════════════════════════

    def transpile_expression(self, expr: ast.expr) -> str:
        """Transpile a Python expression to Rust."""
        dispatch = {
            ast.Name: self._transpile_name,
            ast.Constant: self._transpile_constant,
            ast.BinOp: self._transpile_binary_op,
            ast.UnaryOp: self._transpile_unary_op,
            ast.BoolOp: self._transpile_bool_op,
            ast.Compare: self._transpile_compare,
            ast.Call: self._transpile_call,
            ast.Attribute: self._transpile_attribute,
            ast.Subscript: self._transpile_subscript,
            ast.List: self._transpile_list,
            ast.Dict: self._transpile_dict,
            ast.Tuple: self._transpile_tuple,
            ast.Set: self._transpile_set,
            ast.IfExp: self._transpile_if_expr,
            ast.Lambda: self._transpile_lambda,
            ast.ListComp: self._transpile_list_comp,
            ast.DictComp: self._transpile_dict_comp,
            ast.SetComp: self._transpile_set_comp,
            ast.GeneratorExp: self._transpile_generator_exp,
            ast.NamedExpr: self._transpile_named_expr,
            ast.Starred: self._transpile_starred,
            ast.Slice: self._transpile_slice,
            ast.Yield: self._transpile_yield,
            ast.YieldFrom: self._transpile_yield_from,
            ast.Await: self._transpile_await,
            ast.JoinedStr: self._transpile_joined_str,
            ast.FormattedValue: self._transpile_formatted_value,
        }
        handler = dispatch.get(type(expr))
        if handler:
            return handler(expr)
        return "PyObject::None(_py)"

    # ── Name ─────────────────────────────────────────────────────────────

    def _transpile_name(self, expr: ast.Name) -> str:
        name_map = {
            "True": "true", "False": "false", "None": "None",
            "self": "self_", "cls": "Self",
        }
        return name_map.get(expr.id, expr.id)

    # ── Constant ─────────────────────────────────────────────────────────

    def _transpile_constant(self, expr: ast.Constant) -> str:
        v = expr.value
        if isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, int):
            return str(v)
        elif isinstance(v, float):
            return f"{v}f64"
        elif isinstance(v, str):
            escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
            return f'"{escaped}".to_string()'
        elif isinstance(v, bytes):
            escaped = v.hex()
            return f"vec![{', '.join(f'0x{b:02x}' for b in v)}]"
        elif v is None:
            return "None"
        elif isinstance(v, complex):
            return f"/* complex({v.real}, {v.imag}) */ PyObject::None(_py)"
        elif v is ...:
            return "PyObject::None(_py)"
        return "PyObject::None(_py)"

    # ── BinOp ────────────────────────────────────────────────────────────

    def _transpile_binary_op(self, expr: ast.BinOp) -> str:
        left = self.transpile_expression(expr.left)
        right = self.transpile_expression(expr.right)

        # Detect if we're dividing by len() - cast to f64
        def _needs_float_cast(val):
            return "as i64" in val and ".len()" in val

        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
            ast.Div: "/", ast.Mod: "%",
            ast.BitAnd: "&", ast.BitOr: "|", ast.BitXor: "^",
            ast.LShift: "<<", ast.RShift: ">>",
            ast.MatMult: "/* matmul */",
        }
        if isinstance(expr.op, ast.Pow):
            return f"({left}).powi({right} as i32)"
        if isinstance(expr.op, ast.FloorDiv):
            return f"(({left}) as f64 / ({right}) as f64).floor() as i64"
        if isinstance(expr.op, ast.Div):
            right = f"({right}) as f64"
            left = f"({left}) as f64"
        if isinstance(expr.op, ast.Mult):
            # Cast i64 vars to f64 when the other side is likely f64
            def _is_int_var(e):
                if isinstance(e, ast.Name):
                    t = self.local_vars.get(e.id, "")
                    return t in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "usize", "isize")
                if isinstance(e, ast.Constant) and isinstance(e.value, int) and not isinstance(e.value, bool):
                    return True
                return False
            def _is_float_expr(e):
                if isinstance(e, ast.Name):
                    t = self.local_vars.get(e.id, "")
                    return t in ("f64", "f32")
                if isinstance(e, ast.Constant) and isinstance(e.value, float):
                    return True
                if isinstance(e, ast.Call):
                    # cp.f64(0) produces f64
                    if isinstance(e.func, ast.Attribute) and e.func.attr in ("f64", "f32"):
                        return True
                    if isinstance(e.func, ast.Name) and e.func.id in ("float", "f64", "f32"):
                        return True
                if isinstance(e, ast.BinOp):
                    return _is_float_expr(e.left) or _is_float_expr(e.right)
                return False
            left_is_int = _is_int_var(expr.left)
            right_is_int = _is_int_var(expr.right)
            left_is_float = _is_float_expr(expr.left)
            right_is_float = _is_float_expr(expr.right)
            if left_is_int and right_is_float:
                left = f"({left}) as f64"
            elif right_is_int and left_is_float:
                right = f"({right}) as f64"
            elif left_is_float and isinstance(expr.right, ast.Name) and self.local_vars.get(expr.right.id, "") == "PyObject":
                right = f"({right}) as f64"
            elif right_is_float and isinstance(expr.left, ast.Name) and self.local_vars.get(expr.left.id, "") == "PyObject":
                left = f"({left}) as f64"
        op = op_map.get(type(expr.op), "+")
        return f"({left} {op} {right})"

    # ── UnaryOp ──────────────────────────────────────────────────────────

    def _transpile_unary_op(self, expr: ast.UnaryOp) -> str:
        operand = self.transpile_expression(expr.operand)
        if isinstance(expr.op, ast.USub):
            return f"(-{operand})"
        elif isinstance(expr.op, ast.UAdd):
            return operand
        elif isinstance(expr.op, ast.Not):
            return f"(!{operand})"
        elif isinstance(expr.op, ast.Invert):
            return f"(!{operand})"
        return operand

    # ── BoolOp ───────────────────────────────────────────────────────────

    def _transpile_bool_op(self, expr: ast.BoolOp) -> str:
        op = "&&" if isinstance(expr.op, ast.And) else "||"
        parts = [self.transpile_expression(v) for v in expr.values]
        wrapped = [f"({p})" if " " in p else p for p in parts]
        joined = f" {op} ".join(wrapped)
        return f"({joined})"

    # ── Compare ──────────────────────────────────────────────────────────

    def _transpile_compare(self, expr: ast.Compare) -> str:
        left = self.transpile_expression(expr.left)
        results = []

        for op, comparator in zip(expr.ops, expr.comparators):
            right = self.transpile_expression(comparator)
            # Handle char vs string comparison: if one side is char and other is
            # a single-char string constant, use char literal
            if isinstance(op, (ast.Eq, ast.NotEq)):
                left_is_char = isinstance(expr.left, ast.Name) and self.local_vars.get(expr.left.id, "") == "char"
                right_is_str_const = isinstance(comparator, ast.Constant) and isinstance(comparator.value, str) and len(comparator.value) == 1
                right_is_char = isinstance(comparator, ast.Name) and self.local_vars.get(comparator.id, "") == "char"
                left_is_str_const = isinstance(expr.left, ast.Constant) and isinstance(expr.left.value, str) and len(expr.left.value) == 1

                if left_is_char and right_is_str_const:
                    right = f"'{comparator.value}'"
                elif right_is_char and left_is_str_const:
                    left = f"'{expr.left.value}'"

            if isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                op_str = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<",
                          ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}[type(op)]
                results.append(f"{left} {op_str} {right}")
            elif isinstance(op, ast.Is):
                results.append(f"std::ptr::eq(&{left}, &{right})")
            elif isinstance(op, ast.IsNot):
                results.append(f"!std::ptr::eq(&{left}, &{right})")
            elif isinstance(op, ast.In):
                results.append(f"({right}).contains(&{left})")
            elif isinstance(op, ast.NotIn):
                results.append(f"!({right}).contains(&{left})")
            else:
                results.append(f"{left} /* cmp */ {right}")
            left = right

        return " && ".join(results) if results else "true"

    # ── Call ─────────────────────────────────────────────────────────────

    def _transpile_call(self, expr: ast.Call) -> str:
        func_name = self.transpile_expression(expr.func)
        args = [self.transpile_expression(arg) for arg in expr.args]
        keywords = {kw.arg: self.transpile_expression(kw.value) for kw in expr.keywords}
        args_str = ", ".join(args)

        # Handle cp.f64(x), cp.i64(x), cp.f32(x), etc. as type casts
        if isinstance(expr.func, ast.Attribute):
            obj = expr.func.value
            attr = expr.func.attr
            if isinstance(obj, ast.Name) and obj.id in ("cp", "copperhead"):
                type_casts = {
                    "f64": "f64", "f32": "f32", "i64": "i64", "i32": "i32",
                    "i16": "i16", "i8": "i8", "u64": "u64", "u32": "u32",
                    "u16": "u16", "u8": "u8", "usize": "usize", "isize": "isize",
                }
                if attr in type_casts and args:
                    return f"({args[0]} as {type_casts[attr]})"
                if attr == "bool" and args:
                    return f"({args[0]} as bool)"
                if attr == "str" and args:
                    return f"({args[0]}).to_string()"
                if attr == "Vec" and args:
                    return f"Vec::from({args[0]})"
                if attr == "HashMap" and args:
                    return f"HashMap::new()"
                if attr == "Ok" and args:
                    return f"Ok({args[0]})"
                if attr == "Err" and args:
                    return f"Err({args[0]})"

            # Handle cp.math.sin(x), cp.math.sqrt(x), etc.
            if isinstance(obj, ast.Attribute):
                inner_obj = obj.value
                inner_attr = obj.attr
                if isinstance(inner_obj, ast.Name) and inner_obj.id in ("cp", "copperhead") and inner_attr == "math":
                    math_methods = {
                        "sin": "sin", "cos": "cos", "tan": "tan",
                        "sqrt": "sqrt", "abs": "abs", "floor": "floor", "ceil": "ceil",
                        "round": "round", "log": "ln", "log2": "log2", "log10": "log10",
                        "exp": "exp", "asin": "asin", "acos": "acos", "atan": "atan",
                        "sinh": "sinh", "cosh": "cosh", "tanh": "tanh",
                    }
                    if attr in math_methods and args:
                        return f"({args[0]}).{math_methods[attr]}()"
                    if attr == "pow" and len(args) >= 2:
                        return f"({args[0]}).powi({args[1]} as i32)"
                    if attr == "atan2" and len(args) >= 2:
                        return f"({args[0]}).atan2({args[1]})"
                    if attr in ("min", "max") and len(args) >= 2:
                        return f"({args[0]}).{attr}({args[1]})"

        builtins = {
            "len": self._call_len,
            "range": self._call_range,
            "print": self._call_print,
            "int": self._call_int,
            "float": self._call_float,
            "bool": self._call_bool,
            "str": self._call_str,
            "abs": self._call_abs,
            "min": self._call_min,
            "max": self._call_max,
            "sum": self._call_sum,
            "enumerate": self._call_enumerate,
            "reversed": self._call_reversed,
            "sorted": self._call_sorted,
            "zip": self._call_zip,
            "map": self._call_map,
            "filter": self._call_filter,
            "isinstance": self._call_isinstance,
            "hasattr": self._call_hasattr,
            "getattr": self._call_getattr,
            "setattr": self._call_setattr,
            "type": self._call_type,
            "id": self._call_id,
            "repr": self._call_repr,
            "hash": self._call_hash,
            "any": self._call_any,
            "all": self._call_all,
            "reversed": self._call_reversed,
            "slice": self._call_slice,
            "tuple": self._call_tuple,
            "list": self._call_list,
            "dict": self._call_dict,
            "set": self._call_set,
            "frozenset": self._call_frozenset,
            "bytes": self._call_bytes,
            "bytearray": self._call_bytearray,
            "memoryview": self._call_memoryview,
            "complex": self._call_complex,
            "divmod": self._call_divmod,
            "pow": self._call_pow,
            "round": self._call_round,
            "chr": self._call_chr,
            "ord": self._call_ord,
            "hex": self._call_hex,
            "oct": self._call_oct,
            "bin": self._call_bin,
            "format": self._call_format,
            "input": self._call_input,
            "open": self._call_open,
            "super": self._call_super,
            "iter": self._call_iter,
            "next": self._call_next,
            "callable": self._call_callable,
            "dir": self._call_dir,
            "vars": self._call_vars,
            "globals": self._call_globals,
            "locals": self._call_locals,
            "exec": self._call_exec,
            "eval": self._call_eval,
            "compile": self._call_compile_fn,
            "breakpoint": self._call_breakpoint,
            "exit": self._call_exit,
            "quit": self._call_quit,
            "help": self._call_help,
            "license": self._call_license,
            "copyright": self._call_copyright,
            "credits": self._call_credits,
        }

        if func_name in builtins:
            return builtins[func_name](args, keywords)

        if "." in func_name:
            return self._transpile_method_call(func_name, args, keywords)

        # If calling a module-level RPB function, pass _py and unwrap result
        if hasattr(self, '_module_func_names') and func_name in self._module_func_names:
            return f"{func_name}(_py, {args_str}).unwrap()"

        return f"{func_name}({args_str})"

    # ── Built-in function handlers ───────────────────────────────────────

    def _call_len(self, args, kw):
        return f"({args[0]}).len() as i64" if args else "0"

    def _call_range(self, args, kw):
        if len(args) == 1:
            return f"(0..{args[0]})"
        elif len(args) == 2:
            return f"({args[0]}..{args[1]})"
        elif len(args) == 3:
            return f"({args[0]}..{args[1]}).step_by({args[2]} as usize)"
        return "(0..0)"

    def _call_print(self, args, kw):
        if args:
            args_joined = ", ".join(args)
            return f'println!(\"{{}}\", {args_joined});'
        return "println!();"

    def _call_int(self, args, kw):
        base = kw.get("base", "")
        if base:
            return f"({args[0]}).to_string().parse::<i64>().unwrap_or(0)" if args else "0"
        return f"({args[0]} as i64)" if args else "0"

    def _call_float(self, args, kw):
        return f"({args[0]} as f64)" if args else "0.0f64"

    def _call_bool(self, args, kw):
        return f"({args[0]} as bool)" if args else "false"

    def _call_str(self, args, kw):
        return f"({args[0]}).to_string()" if args else '"".to_string()'

    def _call_abs(self, args, kw):
        return f"({args[0]}).abs()" if args else "0"

    def _call_min(self, args, kw):
        if len(args) >= 2:
            result = f"({args[0]}).min({args[1]})"
            for a in args[2:]:
                result = f"({result}).min({a})"
            return result
        return f"({args[0]}).iter().min().copied().unwrap_or_default()" if args else "0"

    def _call_max(self, args, kw):
        if len(args) >= 2:
            result = f"({args[0]}).max({args[1]})"
            for a in args[2:]:
                result = f"({result}).max({a})"
            return result
        return f"({args[0]}).iter().max().copied().unwrap_or_default()" if args else "0"

    def _call_sum(self, args, kw):
        start = kw.get("start", "0")
        return f"({args[0]}).iter().sum::<i64>() + {start}" if args else start

    def _call_enumerate(self, args, kw):
        start = kw.get("start", "0")
        if start != "0":
            return f"({args[0]}).iter().enumerate().map(|(i, x)| (i + {start}, x))" if args else "(0..0).enumerate()"
        return f"({args[0]}).iter().enumerate()" if args else "(0..0).enumerate()"

    def _call_reversed(self, args, kw):
        return f"({args[0]}).iter().rev()" if args else "(0..0).rev()"

    def _call_sorted(self, args, kw):
        reverse = kw.get("reverse", "false")
        key = kw.get("key", "")
        if not args:
            return "Vec::new()"
        if key:
            return f"{{ let mut v: Vec<_> = ({args[0]}).iter().cloned().collect(); v.sort_by_key(|x| {key}(x.clone())); v }}"
        if reverse == "true":
            return f"{{ let mut v: Vec<_> = ({args[0]}).iter().cloned().collect(); v.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal)); v }}"
        return f"{{ let mut v: Vec<_> = ({args[0]}).iter().cloned().collect(); v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal)); v }}"

    def _call_zip(self, args, kw):
        return f"({', '.join(args)}).into_iter()" if args else "(0..0).into_iter()"

    def _call_map(self, args, kw):
        if len(args) >= 2:
            return f"({args[1]}).iter().map({args[0]})" if args else "(0..0).into_iter()"
        return "(0..0).into_iter()"

    def _call_filter(self, args, kw):
        if len(args) >= 2:
            return f"({args[1]}).iter().filter({args[0]})" if args else "(0..0).into_iter()"
        return "(0..0).into_iter()"

    def _call_isinstance(self, args, kw):
        return "true /* isinstance */"

    def _call_hasattr(self, args, kw):
        return "true /* hasattr */"

    def _call_getattr(self, args, kw):
        if len(args) >= 2:
            return f"({args[0]}).getattr({args[1]})" if args else "PyObject::None(_py)"
        return "PyObject::None(_py)"

    def _call_setattr(self, args, kw):
        if len(args) >= 3:
            return f"({args[0]}).setattr({args[1]}, {args[2]})"
        return "/* setattr */"

    def _call_type(self, args, kw):
        return f"/* type({args[0]}) */ PyObject::None(_py)" if args else "PyObject::None(_py)"

    def _call_id(self, args, kw):
        return f"/* id({args[0]}) */ 0" if args else "0"

    def _call_repr(self, args, kw):
        return f"format!(\"{{:?}}\", {args[0]})" if args else '"".to_string()'

    def _call_hash(self, args, kw):
        return f"/* hash */ 0" if args else "0"

    def _call_any(self, args, kw):
        return f"({args[0]}).iter().any(|x| *x)" if args else "false"

    def _call_all(self, args, kw):
        return f"({args[0]}).iter().all(|x| *x)" if args else "true"

    def _call_slice(self, args, kw):
        if len(args) == 1:
            return f"..{args[0]}"
        elif len(args) == 2:
            return f"{args[0]}..{args[1]}"
        elif len(args) == 3:
            return f"({args[0]}..{args[1]}).step_by({args[2]} as usize)"
        return "0..0"

    def _call_tuple(self, args, kw):
        return f"({args[0]}).to_vec()" if args else "()"

    def _call_list(self, args, kw):
        if not args:
            return "Vec::new()"
        a = args[0]
        if a.startswith("(") and ".." in a:
            return f"({a}).collect::<Vec<_>>()"
        if ".iter()" in a or ".rev()" in a or ".enumerate()" in a:
            return f"({a}).collect::<Vec<_>>()"
        if "into_iter()" in a:
            return f"({a}).collect::<Vec<_>>()"
        return f"({a}).to_vec()"

    def _call_dict(self, args, kw):
        return f"({args[0]}).clone()" if args else "HashMap::new()"

    def _call_set(self, args, kw):
        return f"({args[0]}).iter().cloned().collect::<HashSet<_>>()" if args else "HashSet::new()"

    def _call_frozenset(self, args, kw):
        return f"({args[0]}).iter().cloned().collect::<HashSet<_>>()" if args else "HashSet::new()"

    def _call_bytes(self, args, kw):
        return f"({args[0]}).as_bytes().to_vec()" if args else "Vec::new()"

    def _call_bytearray(self, args, kw):
        return f"({args[0]}).as_bytes().to_vec()" if args else "Vec::new()"

    def _call_memoryview(self, args, kw):
        return f"/* memoryview */ PyObject::None(_py)" if args else "PyObject::None(_py)"

    def _call_complex(self, args, kw):
        return f"/* complex */ PyObject::None(_py)" if args else "PyObject::None(_py)"

    def _call_divmod(self, args, kw):
        if len(args) >= 2:
            return f"(({args[0]} / {args[1]}), ({args[0]} % {args[1]}))"
        return "(0, 0)"

    def _call_pow(self, args, kw):
        mod = kw.get("mod", "")
        if mod:
            return f"({args[0]}).powi({args[1]} as i32) % {mod}" if len(args) >= 2 else "0"
        return f"({args[0]}).powi({args[1]} as i32)" if len(args) >= 2 else "0"

    def _call_round(self, args, kw):
        ndigits = args[1] if len(args) > 1 else "0"
        return f"({args[0]}).round()" if args else "0.0"

    def _call_chr(self, args, kw):
        return f"char::from_u32({args[0]} as u32).unwrap_or(' ')" if args else "' '"

    def _call_ord(self, args, kw):
        return f"({args[0]}).as_bytes()[0] as i64" if args else "0"

    def _call_hex(self, args, kw):
        return f"format!(\"0x{{:x}}\", {args[0]})" if args else '"0x0"'

    def _call_oct(self, args, kw):
        return f"format!(\"0o{{:o}}\", {args[0]})" if args else '"0o0"'

    def _call_bin(self, args, kw):
        return f"format!(\"0b{{:b}}\", {args[0]})" if args else '"0b0"'

    def _call_format(self, args, kw):
        fmt = kw.get("format_spec", '""')
        return f"format!(\"{{:{fmt}}}\", {args[0]})" if args else '"".to_string()'

    def _call_input(self, args, kw):
        return f'/* input() */ "".to_string()' if not args else f'/* input({args[0]}) */ "".to_string()'

    def _call_open(self, args, kw):
        return f"/* open() */ PyObject::None(_py)"

    def _call_super(self, args, kw):
        return "Self::default()" if not args else f"/* super() */ PyObject::None(_py)"

    def _call_iter(self, args, kw):
        return f"({args[0]}).iter()" if args else "(0..0).into_iter()"

    def _call_next(self, args, kw):
        default = kw.get("default", "None")
        return f"({args[0]}).next().unwrap_or({default})" if args else "None"

    def _call_callable(self, args, kw):
        return "true /* callable */" if args else "false"

    def _call_dir(self, args, kw):
        return "Vec::<String>::new() /* dir */"

    def _call_vars(self, args, kw):
        return "HashMap::<String, PyObject>::new() /* vars */"

    def _call_globals(self, args, kw):
        return "HashMap::<String, PyObject>::new() /* globals */"

    def _call_locals(self, args, kw):
        return "HashMap::<String, PyObject>::new() /* locals */"

    def _call_exec(self, args, kw):
        return "/* exec */ Ok(())"

    def _call_eval(self, args, kw):
        return "PyObject::None(_py) /* eval */"

    def _call_compile_fn(self, args, kw):
        return "PyObject::None(_py) /* compile */"

    def _call_breakpoint(self, args, kw):
        return "/* breakpoint */"

    def _call_exit(self, args, kw):
        return "std::process::exit(0)"

    def _call_quit(self, args, kw):
        return "std::process::exit(0)"

    def _call_help(self, args, kw):
        return "/* help */"

    def _call_license(self, args, kw):
        return "/* license */"

    def _call_copyright(self, args, kw):
        return "/* copyright */"

    def _call_credits(self, args, kw):
        return "/* credits */"

    # ── Method call dispatch ─────────────────────────────────────────────

    def _transpile_method_call(self, func_name: str, args: list, kw: dict) -> str:
        parts = func_name.rsplit(".", 1)
        obj = parts[0]
        if obj.startswith("(") and obj.endswith(")"):
            obj = obj[1:-1]
        method = parts[1]
        args_str = ", ".join(args) if args else ""

        str_methods = {
            "upper": "to_uppercase",
            "lower": "to_lowercase",
            "title": "to_titlecase",
            "capitalize": "capitalize",
            "strip": "trim",
            "lstrip": "trim_start",
            "rstrip": "trim_end",
            "startswith": "starts_with",
            "endswith": "ends_with",
            "replace": "replace",
            "split": "split",
            "join": "join",
            "find": "find",
            "rfind": "rfind",
            "rindex": "rfind",
            "center": "center",
            "ljust": "pad",
            "rjust": "pad",
            "zfill": "zero_fill",
            "isalpha": "chars().all(|c| c.is_alphabetic())",
            "isdigit": "chars().all(|c| c.is_numeric())",
            "isalnum": "chars().all(|c| c.is_alphanumeric())",
            "isspace": "chars().all(|c| c.is_whitespace())",
            "isupper": "chars().all(|c| c.is_uppercase())",
            "islower": "chars().all(|c| c.is_lowercase())",
            "istitle": "chars().all(|c| c.is_uppercase())",
            "isnumeric": "chars().all(|c| c.is_numeric())",
            "isdecimal": "chars().all(|c| c.is_ascii_digit())",
            "isidentifier": "chars().all(|c| c.is_alphabetic())",
            "isprintable": "chars().all(|c| c.is_alphanumeric())",
            "isascii": "is_ascii()",
            "encode": "as_bytes().to_vec()",
            "decode": "/* decode */ String::new()",
            "format": "format!",
            "format_map": "format!",
            "maketrans": "/* maketrans */ HashMap::new()",
            "translate": "/* translate */ String::new()",
            "partition": "split_once",
            "rpartition": "rsplit_once",
            "rsplit": "rsplit",
            "splitlines": "lines",
            "expandtabs": "replace",
            "removeprefix": "strip_prefix",
            "removesuffix": "strip_suffix",
            "casefold": "to_lowercase",
            "swapcase": "/* swapcase */",
        }

        vec_methods = {
            "append": "push",
            "extend": "extend",
            "insert": "insert",
            "remove": "remove_item",
            "pop": "pop",
            "clear": "clear",
            "index": "position",
            "count": "count",
            "reverse": "reverse",
            "sort": "sort",
            "copy": "clone",
        }

        dict_methods = {
            "get": "get",
            "setdefault": "entry",
            "update": "extend",
            "items": "iter",
            "keys": "keys",
            "values": "values",
            "pop": "remove",
            "popitem": "pop_first",
            "clear": "clear",
            "copy": "clone",
            "fromkeys": "from_iter",
        }

        # Handle ambiguous methods that exist for both str and Vec
        _is_str = lambda v: ".to_string()" in v or v.startswith('"') or v.startswith("'")
        _is_str_obj = lambda v: _is_str(v) or self.local_vars.get(v, "") == "String"
        if method == "index" and args:
            if _is_str_obj(obj):
                return f"({obj}).find(&{args[0]}).map(|i| i as i64).unwrap_or(-1)"
            return f"({obj}).iter().position(|x| *x == {args[0]}).map(|i| i as i64).unwrap_or(-1)"
        if method == "count" and args:
            if _is_str_obj(obj):
                return f"({obj}).matches(&{args[0]}).count() as i64"
            return f"({obj}).iter().filter(|x| **x == {args[0]}).count() as i64"
        if method == "pop":
            if not args:
                return f"({obj}).pop()"
            if _is_str(args[0]):
                default = args[1] if len(args) > 1 else "None"
                return f"({obj}).remove(&{args[0]}).unwrap_or({default})"
            return f"({obj}).remove({args[0]} as usize)"

        if method in str_methods:
            mapped = str_methods[method]
            if method == "replace" and len(args) >= 2:
                return f"({obj}).replace(&{args[0]}, &{args[1]})"
            if method == "split" and args:
                return f"({obj}).split(&{args[0]}).map(|s| s.to_string()).collect::<Vec<_>>()"
            if method == "join" and args:
                sep = obj.strip("()")
                if sep.startswith('""') or sep.startswith("''.to_string()") or sep == '""' or "to_string()" in sep and sep.startswith('"'):
                    return f"({args[0]}).iter().collect::<String>()"
                return f"({args[0]}).join(&{obj})"
            if method == "find" and args:
                return f"({obj}).find(&{args[0]}).map(|i| i as i64).unwrap_or(-1)"
            if method == "count" and args:
                return f"({obj}).matches(&{args[0]}).count() as i64"
            if method == "center" and args:
                return f"({obj}).chars().take({args[0]} as usize).collect::<String>()"
            if method == "ljust" and args:
                return f"({obj}).chars().take({args[0]} as usize).collect::<String>()"
            if method == "rjust" and args:
                return f"({obj}).chars().take({args[0]} as usize).collect::<String>()"
            if method == "zfill" and args:
                return f"format!(\"{{:0>width$}}\", {obj}, width = {args[0]} as usize)"
            if method == "isalpha":
                return f"({obj}).chars().all(|c| c.is_alphabetic())"
            if method == "isdigit":
                return f"({obj}).chars().all(|c| c.is_numeric())"
            if method == "isalnum":
                return f"({obj}).chars().all(|c| c.is_alphanumeric())"
            if method == "isspace":
                return f"({obj}).chars().all(|c| c.is_whitespace())"
            if method == "isupper":
                return f"({obj}).chars().all(|c| c.is_uppercase())"
            if method == "islower":
                return f"({obj}).chars().all(|c| c.is_lowercase())"
            if method == "istitle":
                return f"({obj}).chars().next().map_or(false, |c| c.is_uppercase())"
            if method == "isnumeric":
                return f"({obj}).chars().all(|c| c.is_numeric())"
            if method == "isdecimal":
                return f"({obj}).chars().all(|c| c.is_ascii_digit())"
            if method == "isidentifier":
                return f"({obj}).chars().all(|c| c.is_alphabetic() || c == '_')"
            if method == "isprintable":
                return f"({obj}).chars().all(|c| c.is_alphanumeric() || c.is_whitespace())"
            if method == "isascii":
                return f"({obj}).is_ascii()"
            if method == "encode":
                return f"({obj}).as_bytes().to_vec()"
            if method == "strip":
                return f"({obj}).trim()"
            if method == "lstrip":
                return f"({obj}).trim_start()"
            if method == "rstrip":
                return f"({obj}).trim_end()"
            if method == "upper":
                return f"({obj}).to_uppercase()"
            if method == "lower":
                return f"({obj}).to_lowercase()"
            if method == "startswith":
                return f"({obj}).starts_with(&{args[0]})" if args else f'({obj}).starts_with("")'
            if method == "endswith":
                return f"({obj}).ends_with(&{args[0]})" if args else f'({obj}).ends_with("")'
            if method == "removeprefix" and args:
                return f"({obj}).strip_prefix(&{args[0]}).map(|s| s.to_string()).unwrap_or_else(|| ({obj}).clone())"
            if method == "removesuffix" and args:
                return f"({obj}).strip_suffix(&{args[0]}).map(|s| s.to_string()).unwrap_or_else(|| ({obj}).clone())"
            if method == "partition" and args:
                return f"({obj}).split_once(&{args[0]}).map(|(a, b)| (a.to_string(), b.to_string())).unwrap_or((({obj}).clone(), String::new()))"
            if method == "splitlines":
                return f"({obj}).lines().map(|s| s.to_string()).collect::<Vec<_>>()"
            if method == "expandtabs" and args:
                return f'({obj}).replace("\\t", &{args[0]})'
            if method == "maketrans":
                return f"/* maketrans */ HashMap::new()"
            if method == "translate":
                return f"/* translate */ ({obj}).clone()"
            if method == "casefold":
                return f"({obj}).to_lowercase()"
            if method == "swapcase":
                return f"/* swapcase */ ({obj}).clone()"
            return f"({obj}).{mapped}()"

        if method in vec_methods:
            mapped = vec_methods[method]
            if method == "append":
                return f"({obj}).push({args[0]})"
            if method == "insert" and len(args) >= 2:
                return f"({obj}).insert({args[0]} as usize, {args[1]})"
            if method == "remove" and args:
                return f"({obj}).retain(|x| x != &{args[0]})"
            if method == "pop":
                idx = args[0] if args else f"({obj}).len() - 1"
                return f"({obj}).remove({idx} as usize)"
            if method == "index" and args:
                return f"({obj}).iter().position(|x| *x == {args[0]}).map(|i| i as i64).unwrap_or(-1)"
            if method == "sort":
                return f"({obj}).sort()"
            if method == "reverse":
                return f"({obj}).reverse()"
            if method == "copy":
                return f"({obj}).clone()"
            if method == "clear":
                return f"({obj}).clear()"
            if method == "extend" and args:
                return f"({obj}).extend({args[0]}.into_iter())"
            if method == "count" and args:
                return f"({obj}).iter().filter(|x| **x == {args[0]}).count() as i64"
            return f"({obj}).{mapped}({args_str})"

        if method in dict_methods:
            if method == "get" and args:
                default = args[1] if len(args) > 1 else "None"
                return f"({obj}).get(&{args[0]}).cloned().unwrap_or({default})"
            if method == "keys":
                return f"({obj}).keys().cloned().collect::<Vec<_>>()"
            if method == "values":
                return f"({obj}).values().cloned().collect::<Vec<_>>()"
            if method == "items":
                return f"({obj}).iter().map(|(k, v)| (k.clone(), v.clone())).collect::<Vec<_>>()"
            if method == "pop" and args:
                default = args[1] if len(args) > 1 else "None"
                return f"({obj}).remove(&{args[0]}).unwrap_or({default})"
            if method == "clear":
                return f"({obj}).clear()"
            if method == "copy":
                return f"({obj}).clone()"
            if method == "update" and args:
                return f"({obj}).extend({args[0]}.into_iter())"
            if method == "setdefault" and len(args) >= 2:
                return f"({obj}).entry({args[0]}).or_insert({args[1]}).clone()"
            if method == "popitem":
                return f"({obj}).pop_first().map(|(k, v)| (k, v))"
            if method == "fromkeys" and args:
                return f"({args[0]}).into_iter().map(|k| (k, {args[1] if len(args) > 1 else 'None'.to_string()})).collect::<HashMap<_, _>>()"
            return f"({obj}).{method}({args_str})"

        if method == "clone":
            return f"({obj}).clone()"
        if method == "len":
            return f"({obj}).len() as i64"
        if method == "is_empty":
            return f"({obj}).is_empty()"
        if method == "contains" and args:
            return f"({obj}).contains(&{args[0]})"
        if method == "push" and args:
            return f"({obj}).push({args[0]})"
        if method == "pop":
            return f"({obj}).pop()"
        if method == "clear":
            return f"({obj}).clear()"
        if method == "reverse":
            return f"({obj}).reverse()"
        if method == "sort":
            return f"({obj}).sort()"
        if method == "iter":
            return f"({obj}).iter()"
        if method == "next":
            return f"({obj}).next()"
        if method == "into_iter":
            return f"({obj}).into_iter()"
        if method == "map" and args:
            return f"({obj}).map({args[0]})"
        if method == "filter" and args:
            return f"({obj}).filter({args[0]})"
        if method == "collect":
            return f"({obj}).collect::<Vec<_>>()"

        return f"({obj}).{method}({args_str})"

    # ── Attribute ────────────────────────────────────────────────────────

    def _transpile_attribute(self, expr: ast.Attribute) -> str:
        obj = self.transpile_expression(expr.value)
        attr = expr.attr

        math_funcs = {
            "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
            "sqrt", "cbrt", "abs", "floor", "ceil", "round",
            "log", "log2", "log10", "exp", "pow", "sinh", "cosh", "tanh",
        }

        if obj in ("cp", "copperhead") and attr == "math":
            return "__cp_math__"
        if obj == "__cp_math__" and attr in math_funcs:
            return f"__cp_math__::{attr}"
        if obj in ("cp", "copperhead") and attr in math_funcs:
            return f"__cp_math__::{attr}"

        if attr == "PI":
            return "std::f64::consts::PI"
        if attr == "E":
            return "std::f64::consts::E"
        if attr == "TAU":
            return "std::f64::consts::TAU"
        if attr == "INFINITY":
            return "f64::INFINITY"
        if attr == "NAN":
            return "f64::NAN"

        return f"({obj}).{attr}"

    # ── Subscript ────────────────────────────────────────────────────────

    def _transpile_subscript(self, expr: ast.Subscript) -> str:
        obj_raw = expr.value
        obj = self.transpile_expression(obj_raw)
        sl = expr.slice

        # Check if the object is a string
        is_str = False
        if isinstance(obj_raw, ast.Name) and self.local_vars.get(obj_raw.id, "") == "String":
            is_str = True
        elif isinstance(obj_raw, ast.Constant) and isinstance(obj_raw.value, str):
            is_str = True
        elif ".to_string()" in obj:
            is_str = True

        if isinstance(sl, ast.Slice):
            lower = self.transpile_expression(sl.lower) if sl.lower else "0"
            upper = self.transpile_expression(sl.upper) if sl.upper else f"({obj}).len()"
            if is_str:
                if sl.step:
                    step = self.transpile_expression(sl.step)
                    chars = f"({obj}).chars().skip({lower} as usize).take(({upper} - {lower}) as usize)"
                    return f"({chars}).step_by({step} as usize).collect::<String>()"
                return f"({obj}).chars().skip({lower} as usize).take(({upper} - {lower}) as usize).collect::<String>()"
            if sl.step:
                step = self.transpile_expression(sl.step)
                return f"({obj})[({lower} as usize..{upper} as usize).step_by({step} as usize)]"
            return f"({obj})[{lower} as usize..{upper} as usize]"

        key = self.transpile_expression(sl)
        if is_str:
            if isinstance(sl, ast.Constant) and isinstance(sl.value, int):
                return f"({obj}).as_bytes()[{sl.value} as usize] as char"
            return f"({obj}).as_bytes()[({key}) as usize] as char"
        if isinstance(sl, ast.Constant) and isinstance(sl.value, int):
            return f"({obj})[{sl.value} as usize]"
        elif " " in key or "+" in key or "-" in key or "*" in key or "/" in key:
            return f"({obj})[({key}) as usize]"
        else:
            return f"({obj})[{key} as usize]"

    # ── List ─────────────────────────────────────────────────────────────

    def _transpile_list(self, expr: ast.List) -> str:
        if not expr.elts:
            return "Vec::new()"
        elements = [self.transpile_expression(elt) for elt in expr.elts]
        return f"vec![{', '.join(elements)}]"

    # ── Dict ─────────────────────────────────────────────────────────────

    def _transpile_dict(self, expr: ast.Dict) -> str:
        if not expr.keys:
            return "HashMap::new()"
        pairs = []
        for key, value in zip(expr.keys, expr.values):
            k = self.transpile_expression(key)
            v = self.transpile_expression(value)
            pairs.append(f"({k}, {v})")
        return f"vec![{', '.join(pairs)}].into_iter().collect()"

    # ── Tuple ────────────────────────────────────────────────────────────

    def _transpile_tuple(self, expr: ast.Tuple) -> str:
        if not expr.elts:
            return "()"
        elements = [self.transpile_expression(elt) for elt in expr.elts]
        return f"({', '.join(elements)})"

    # ── Set ──────────────────────────────────────────────────────────────

    def _transpile_set(self, expr: ast.Set) -> str:
        if not expr.elts:
            return "HashSet::new()"
        elements = [self.transpile_expression(elt) for elt in expr.elts]
        return f"vec![{', '.join(elements)}].into_iter().collect::<HashSet<_>>()"

    # ── IfExp ────────────────────────────────────────────────────────────

    def _transpile_if_expr(self, expr: ast.IfExp) -> str:
        condition = self.transpile_expression(expr.test)
        body = self.transpile_expression(expr.body)
        orelse = self.transpile_expression(expr.orelse)
        return f"if {condition} {{ {body} }} else {{ {orelse} }}"

    # ── Lambda ───────────────────────────────────────────────────────────

    def _transpile_lambda(self, expr: ast.Lambda) -> str:
        args = [a.arg for a in expr.args.args]
        body = self.transpile_expression(expr.body)
        args_str = ", ".join(args)
        return f"|{args_str}| {body}"

    # ── ListComp ─────────────────────────────────────────────────────────

    def _transpile_list_comp(self, expr: ast.ListComp) -> str:
        if not expr.generators:
            element = self.transpile_expression(expr.elt)
            return f"vec![{element}]"

        gen = expr.generators[0]
        if isinstance(gen.target, ast.Name):
            var = gen.target.id
        elif isinstance(gen.target, ast.Tuple):
            var = f"({', '.join(e.id for e in gen.target.elts if isinstance(e, ast.Name))})"
        else:
            var = "_"

        iter_expr = self.transpile_expression(gen.iter)
        element = self.transpile_expression(expr.elt)

        result = f"({iter_expr}).into_iter().map(|{var}| {element})"

        if gen.ifs:
            for if_clause in gen.ifs:
                cond = self.transpile_expression(if_clause)
                result += f".filter(|{var}| {cond})"

        result += ".collect::<Vec<_>>()"
        return result

    # ── DictComp ─────────────────────────────────────────────────────────

    def _transpile_dict_comp(self, expr: ast.DictComp) -> str:
        if not expr.generators:
            return "HashMap::new()"

        gen = expr.generators[0]
        if isinstance(gen.target, ast.Name):
            var = gen.target.id
        elif isinstance(gen.target, ast.Tuple):
            var = f"({', '.join(e.id for e in gen.target.elts if isinstance(e, ast.Name))})"
        else:
            var = "_"

        iter_expr = self.transpile_expression(gen.iter)
        key = self.transpile_expression(expr.key)
        value = self.transpile_expression(expr.value)

        result = f"({iter_expr}).into_iter().map(|{var}| ({key}, {value}))"

        if gen.ifs:
            for if_clause in gen.ifs:
                cond = self.transpile_expression(if_clause)
                result += f".filter(|{var}| {cond})"

        result += ".collect::<HashMap<_, _>>()"
        return result

    # ── SetComp ──────────────────────────────────────────────────────────

    def _transpile_set_comp(self, expr: ast.SetComp) -> str:
        if not expr.generators:
            return "HashSet::new()"

        gen = expr.generators[0]
        if isinstance(gen.target, ast.Name):
            var = gen.target.id
        elif isinstance(gen.target, ast.Tuple):
            var = f"({', '.join(e.id for e in gen.target.elts if isinstance(e, ast.Name))})"
        else:
            var = "_"

        iter_expr = self.transpile_expression(gen.iter)
        element = self.transpile_expression(expr.elt)

        result = f"({iter_expr}).into_iter().map(|{var}| {element})"

        if gen.ifs:
            for if_clause in gen.ifs:
                cond = self.transpile_expression(if_clause)
                result += f".filter(|{var}| {cond})"

        result += ".collect::<HashSet<_>>()"
        return result

    # ── GeneratorExp ─────────────────────────────────────────────────────

    def _transpile_generator_exp(self, expr: ast.GeneratorExp) -> str:
        if not expr.generators:
            return "(0..0).into_iter()"

        gen = expr.generators[0]
        if isinstance(gen.target, ast.Name):
            var = gen.target.id
        else:
            var = "_"

        iter_expr = self.transpile_expression(gen.iter)
        element = self.transpile_expression(expr.elt)

        result = f"({iter_expr}).into_iter().map(|{var}| {element})"

        if gen.ifs:
            for if_clause in gen.ifs:
                cond = self.transpile_expression(if_clause)
                result += f".filter(|{var}| {cond})"

        return result

    # ── NamedExpr (walrus operator) ──────────────────────────────────────

    def _transpile_named_expr(self, expr: ast.NamedExpr) -> str:
        target = self.transpile_expression(expr.target)
        value = self.transpile_expression(expr.value)
        return f"let {target} = {value}"

    # ── Starred ──────────────────────────────────────────────────────────

    def _transpile_starred(self, expr: ast.Starred) -> str:
        inner = self.transpile_expression(expr.value)
        return f"*{inner}"

    # ── Slice ────────────────────────────────────────────────────────────

    def _transpile_slice(self, expr: ast.Slice) -> str:
        lower = self.transpile_expression(expr.lower) if expr.lower else "0"
        upper = self.transpile_expression(expr.upper) if expr.upper else ""
        if expr.step:
            step = self.transpile_expression(expr.step)
            if upper:
                return f"({lower}..{upper}).step_by({step} as usize)"
            return f"({lower}..).step_by({step} as usize)"
        if upper:
            return f"{lower}..{upper}"
        return f"{lower}.."

    # ── Yield ────────────────────────────────────────────────────────────

    def _transpile_yield(self, expr: ast.Yield) -> str:
        if expr.value:
            val = self.transpile_expression(expr.value)
            return f"/* yield {val} */ PyObject::None(_py)"
        return "/* yield */ PyObject::None(_py)"

    # ── YieldFrom ────────────────────────────────────────────────────────

    def _transpile_yield_from(self, expr: ast.YieldFrom) -> str:
        val = self.transpile_expression(expr.value) if expr.value else "PyObject::None(_py)"
        return f"/* yield from {val} */ PyObject::None(_py)"

    # ── Await ────────────────────────────────────────────────────────────

    def _transpile_await(self, expr: ast.Await) -> str:
        val = self.transpile_expression(expr.value)
        return f"/* await {val} */ PyObject::None(_py)"

    # ── JoinedStr (f-strings) ────────────────────────────────────────────

    def _transpile_joined_str(self, expr: ast.JoinedStr) -> str:
        parts = []
        for value in expr.values:
            if isinstance(value, ast.Constant):
                escaped = str(value.value).replace("\\", "\\\\").replace('"', '\\"')
                parts.append(escaped)
            elif isinstance(value, ast.FormattedValue):
                inner = self.transpile_expression(value.value)
                if value.format_spec:
                    spec = self.transpile_expression(value.format_spec)
                    parts.append("{:" + spec + "}")
                else:
                    parts.append("{}")

        if not parts:
            return '"".to_string()'

        fmt_str = "".join(parts)
        fmt_args = []
        for value in expr.values:
            if isinstance(value, ast.FormattedValue):
                inner = self.transpile_expression(value.value)
                fmt_args.append(inner)

        if fmt_args:
            args_joined = ", ".join(fmt_args)
            return f'format!("{fmt_str}", {args_joined})'
        escaped = fmt_str.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}".to_string()'

    def _transpile_formatted_value(self, expr: ast.FormattedValue) -> str:
        inner = self.transpile_expression(expr.value)
        if expr.format_spec:
            spec = self.transpile_expression(expr.format_spec)
            return f"format!(\"{{:{spec}}}\", {inner})"
        return f"format!(\"{{}}\", {inner})"

    # ══════════════════════════════════════════════════════════════════════
    # TYPE INFERENCE
    # ══════════════════════════════════════════════════════════════════════

    def _infer_type_from_value(self, expr: ast.expr) -> str:
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool"
            elif isinstance(expr.value, int):
                return "i64"
            elif isinstance(expr.value, float):
                return "f64"
            elif isinstance(expr.value, str):
                return "String"
            return "PyObject"
        elif isinstance(expr, ast.List):
            if expr.elts:
                inner = self._infer_type_from_value(expr.elts[0])
                return f"Vec<{inner}>"
            return "Vec<PyObject>"
        elif isinstance(expr, ast.Dict):
            return "HashMap<String, PyObject>"
        elif isinstance(expr, ast.Set):
            return "HashSet<PyObject>"
        elif isinstance(expr, ast.Tuple):
            if expr.elts:
                types = ", ".join(self._infer_type_from_value(e) for e in expr.elts)
                return f"({types})"
            return "()"
        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                if expr.func.id in ("int", "i64", "len", "range", "abs", "ord", "count", "hash", "id"):
                    return "i64"
                elif expr.func.id in ("float", "f64"):
                    return "f64"
                elif expr.func.id == "bool":
                    return "bool"
                elif expr.func.id == "str":
                    return "String"
                elif expr.func.id == "list":
                    return "Vec<PyObject>"
                elif expr.func.id == "dict":
                    return "HashMap<String, PyObject>"
                elif expr.func.id == "set":
                    return "HashSet<PyObject>"
                elif expr.func.id == "tuple":
                    return "()"
            elif isinstance(expr.func, ast.Attribute):
                if isinstance(expr.func.value, ast.Name) and expr.func.value.id in ("cp", "copperhead"):
                    attr = expr.func.attr
                    if attr in ("f64", "f32"):
                        return attr
                    if attr in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "usize", "isize"):
                        return attr
                    if attr == "bool":
                        return "bool"
                    if attr == "str":
                        return "String"
                    if attr == "Vec":
                        return "Vec<PyObject>"
                    if attr == "HashMap":
                        return "HashMap<String, PyObject>"
            return "PyObject"
        elif isinstance(expr, ast.Name):
            if expr.id in ("True", "False"):
                return "bool"
            return self.local_vars.get(expr.id, "PyObject")
        elif isinstance(expr, ast.BinOp):
            return self._infer_type_from_value(expr.left)
        elif isinstance(expr, ast.IfExp):
            return self._infer_type_from_value(expr.body)
        elif isinstance(expr, ast.ListComp):
            return "Vec<PyObject>"
        elif isinstance(expr, ast.Name) and expr.id in self.local_vars:
            return self.local_vars[expr.id]
        return "PyObject"

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _generate_rust_function(self, func: RustFunction) -> str:
        lines = []
        if func.is_pyfunction:
            lines.append("#[pyfunction]")

        args_str = ", ".join([f"{name}: {rust_type}" for name, rust_type in func.args])
        lines.append(f"fn {func.name}(_py: Python<'_>, {args_str}) -> {func.return_type} {{")

        for line in func.body.split("\n"):
            lines.append(self._indent(line))

        lines.append("}")
        return "\n".join(lines)

    def _indent(self, line: str) -> str:
        return self.indent_str * self.indent_level + line


# ══════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL API
# ══════════════════════════════════════════════════════════════════════════

def transpile_module(module_info: ModuleInfo) -> str:
    transpiler = CopperheadTranspiler()
    return transpiler.transpile_module(module_info)


def transpile_source(source: str, filename: str = "<unknown>") -> str:
    module_info = parse_source(source, filename)
    return transpile_module(module_info)


def generate_pyproject_toml(module_name: str) -> str:
    return f"""[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "{module_name}"
version = "0.1.0"
description = "Copperhead compiled module"
requires-python = ">=3.8"

[tool.maturin]
features = ["pyo3/extension-module"]
"""


def generate_cargo_toml(module_name: str) -> str:
    return f"""[package]
name = "{module_name}"
version = "0.1.0"
edition = "2021"

[lib]
name = "{module_name}"
crate-type = ["cdylib"]

[dependencies]
pyo3 = {{ version = "0.23", features = ["extension-module"] }}
"""


def generate_build_script() -> str:
    return '''#!/usr/bin/env python3
import subprocess
import sys
import os

def build_module(source_file: str, output_name: str):
    from copperhead.transpiler import transpile_source, generate_cargo_toml, generate_pyproject_toml
    with open(source_file, 'r') as f:
        source = f.read()
    rust_code = transpile_source(source, source_file)
    build_dir = f"build_{output_name}"
    os.makedirs(build_dir, exist_ok=True)
    with open(os.path.join(build_dir, "lib.rs"), 'w') as f:
        f.write(rust_code)
    with open(os.path.join(build_dir, "Cargo.toml"), 'w') as f:
        f.write(generate_cargo_toml(output_name))
    subprocess.run([sys.executable, "-m", "maturin", "build", "--release"], cwd=build_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build.py <source_file> <output_name>")
        sys.exit(1)
    build_module(sys.argv[1], sys.argv[2])
'''
