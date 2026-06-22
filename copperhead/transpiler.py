"""
Copperhead Rust Transpiler

This module provides functionality to transpile Python AST to Rust code
with PyO3 bindings for seamless Python-Rust interoperability.
"""

import ast
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
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
    args: List[Tuple[str, str]]  # (name, type)
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
    """Transpiler for converting Python AST to Rust code."""

    def __init__(self):
        self.indent_level = 0
        self.indent_str = "    "
        self.current_function = None
        self.local_vars: Dict[str, str] = {}
        self.pyo3_wrappers: List[str] = []

    def transpile_module(self, module_info: ModuleInfo) -> str:
        """Transpile a module to Rust code."""
        lines = []

        lines.append("use pyo3::prelude::*;")
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

        if type_info.kind == TypeKind.PRIMITIVE:
            return type_info.rust_type
        elif type_info.kind == TypeKind.COLLECTION:
            return type_info.rust_type
        elif type_info.kind == TypeKind.CUSTOM:
            return type_info.rust_type
        else:
            return "PyObject"

    def _rust_default_value(self, rust_type: str) -> str:
        """Get a default value expression for a Rust type."""
        if rust_type in ("f64", "f32"):
            return "0.0"
        elif rust_type.startswith("i") or rust_type.startswith("u"):
            return "0"
        elif rust_type == "bool":
            return "false"
        elif rust_type == "()":
            return "()"
        elif rust_type.startswith("Vec"):
            return "Vec::new()"
        elif rust_type.startswith("HashMap"):
            return "HashMap::new()"
        elif rust_type.startswith("Option"):
            return "None"
        elif rust_type.startswith("Result"):
            return "Ok(0)"
        elif rust_type == "String":
            return "String::new()"
        return "PyObject::None(py)"

    def _generate_function_body(self, func: FunctionInfo) -> str:
        """Generate Rust function body by transpiling AST statements."""
        if func.body is None:
            rt = func.return_type.rust_type if func.return_type else "PyObject"
            default = self._rust_default_value(rt)
            return f"Ok({default})"

        lines = []
        self.indent_level = 1

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

    # ── Statement Transpilation ──────────────────────────────────────────

    def _transpile_statement(self, stmt: ast.stmt) -> Optional[str]:
        """Transpile a single AST statement to Rust code."""
        if isinstance(stmt, ast.Return):
            return self._transpile_return(stmt)
        elif isinstance(stmt, ast.Assign):
            return self._transpile_assign(stmt)
        elif isinstance(stmt, ast.AugAssign):
            return self._transpile_aug_assign(stmt)
        elif isinstance(stmt, ast.If):
            return self._transpile_if(stmt)
        elif isinstance(stmt, ast.For):
            return self._transpile_for(stmt)
        elif isinstance(stmt, ast.While):
            return self._transpile_while(stmt)
        elif isinstance(stmt, ast.Break):
            return "break;"
        elif isinstance(stmt, ast.Continue):
            return "continue;"
        elif isinstance(stmt, ast.Pass):
            return None
        elif isinstance(stmt, ast.Expr):
            return self._transpile_expr_statement(stmt)
        elif isinstance(stmt, ast.Assert):
            return self._transpile_assert(stmt)
        elif isinstance(stmt, ast.FunctionDef):
            return self._transpile_nested_function(stmt)
        else:
            return f"/* unsupported: {type(stmt).__name__} */"

    def _transpile_return(self, stmt: ast.Return) -> str:
        """Transpile a return statement."""
        if stmt.value is None:
            return "return Ok(());"
        expr = self.transpile_expression(stmt.value)
        if expr.startswith("(") and expr.endswith(")"):
            inner = expr[1:-1]
            if "(" not in inner:
                expr = inner
        return f"return Ok({expr});"

    def _transpile_assign(self, stmt: ast.Assign) -> str:
        """Transpile an assignment statement."""
        if len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                value = self.transpile_expression(stmt.value)
                var_name = target.id
                rust_type = self._infer_type_from_value(stmt.value)
                if var_name not in self.local_vars:
                    self.local_vars[var_name] = rust_type
                    return f"let mut {var_name} = {value};"
                else:
                    return f"{var_name} = {value};"
        return f"/* unsupported assignment */"

    def _transpile_aug_assign(self, stmt: ast.AugAssign) -> str:
        """Transpile an augmented assignment (+=, -=, etc.)."""
        target = self.transpile_expression(stmt.target)
        value = self.transpile_expression(stmt.value)

        if isinstance(stmt.op, ast.Add):
            op = "+="
        elif isinstance(stmt.op, ast.Sub):
            op = "-="
        elif isinstance(stmt.op, ast.Mult):
            op = "*="
        elif isinstance(stmt.op, ast.Div):
            op = "/="
        elif isinstance(stmt.op, ast.Mod):
            op = "%="
        elif isinstance(stmt.op, ast.Pow):
            op = "**"
            return f"{target} = {target}.pow({value});"
        else:
            op = "+="

        return f"{target} {op} {value};"

    def _transpile_if(self, stmt: ast.If) -> str:
        """Transpile an if/elif/else block."""
        condition = self.transpile_expression(stmt.test)
        lines = [f"if {condition} {{"]
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

    def _transpile_for(self, stmt: ast.For) -> str:
        """Transpile a for loop."""
        if isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
        else:
            var_name = "_loop_var"

        iter_expr = self.transpile_expression(stmt.iter)

        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name):
            if stmt.iter.func.id == "range":
                args = stmt.iter.args
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
            elif stmt.iter.func.id == "enumerate":
                args = stmt.iter.args
                if args:
                    inner = self.transpile_expression(args[0])
                    lines = [f"for ({var_name}) in ({inner}).iter().enumerate() {{"]
                else:
                    lines = [f"for {var_name} in (0..0).enumerate() {{"]
            elif stmt.iter.func.id == "zip":
                args_str = ", ".join([self.transpile_expression(a) for a in stmt.iter.args])
                lines = [f"for {var_name} in ({args_str}).into_iter() {{"]
            else:
                lines = [f"for {var_name} in ({iter_expr}).into_iter() {{"]
        else:
            lines = [f"for {var_name} in ({iter_expr}).into_iter() {{"]

        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))
        self.indent_level -= 1
        lines.append(self._indent("}"))
        return "\n".join(lines)

    def _transpile_while(self, stmt: ast.While) -> str:
        """Transpile a while loop."""
        condition = self.transpile_expression(stmt.test)
        lines = [f"while {condition} {{"]
        self.indent_level += 1
        for s in stmt.body:
            result = self._transpile_statement(s)
            if result is not None:
                for line in result.split("\n"):
                    lines.append(self._indent(line))
        self.indent_level -= 1
        lines.append(self._indent("}"))
        return "\n".join(lines)

    def _transpile_expr_statement(self, stmt: ast.Expr) -> str:
        """Transpile an expression used as a statement."""
        expr = self.transpile_expression(stmt.value)
        if expr.endswith(")"):
            return f"{expr};"
        return f"{expr};"

    def _transpile_assert(self, stmt: ast.Assert) -> str:
        """Transpile an assert statement."""
        condition = self.transpile_expression(stmt.test)
        return f"assert!({condition});"

    def _transpile_nested_function(self, stmt: ast.FunctionDef) -> str:
        """Transpile a nested function as a closure."""
        return f"/* nested fn {stmt.name} not yet supported */"

    # ── Expression Transpilation ─────────────────────────────────────────

    def transpile_expression(self, expr: ast.expr) -> str:
        """Transpile a Python expression to Rust."""
        if isinstance(expr, ast.Name):
            return self._transpile_name(expr)
        elif isinstance(expr, ast.Constant):
            return self._transpile_constant(expr)
        elif isinstance(expr, ast.BinOp):
            return self._transpile_binary_op(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._transpile_unary_op(expr)
        elif isinstance(expr, ast.BoolOp):
            return self._transpile_bool_op(expr)
        elif isinstance(expr, ast.Compare):
            return self._transpile_compare(expr)
        elif isinstance(expr, ast.Call):
            return self._transpile_call(expr)
        elif isinstance(expr, ast.Attribute):
            return self._transpile_attribute(expr)
        elif isinstance(expr, ast.Subscript):
            return self._transpile_subscript(expr)
        elif isinstance(expr, ast.List):
            return self._transpile_list(expr)
        elif isinstance(expr, ast.Dict):
            return self._transpile_dict(expr)
        elif isinstance(expr, ast.Tuple):
            return self._transpile_tuple(expr)
        elif isinstance(expr, ast.IfExp):
            return self._transpile_if_expr(expr)
        elif isinstance(expr, ast.ListComp):
            return self._transpile_list_comp(expr)
        elif isinstance(expr, ast.Lambda):
            return self._transpile_lambda(expr)
        elif isinstance(expr, ast.NamedExpr):
            return self._transpile_named_expr(expr)
        else:
            return "PyObject::None(py)"

    def _transpile_name(self, expr: ast.Name) -> str:
        """Transpile a name reference."""
        name_map = {
            "True": "true",
            "False": "false",
            "None": "None",
            "self": "self_",
        }
        return name_map.get(expr.id, expr.id)

    def _transpile_constant(self, expr: ast.Constant) -> str:
        """Transpile a constant value."""
        if isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        elif isinstance(expr.value, int):
            return str(expr.value)
        elif isinstance(expr.value, float):
            return f"{expr.value}f64"
        elif isinstance(expr.value, str):
            escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}".to_string()'
        elif expr.value is None:
            return "None"
        else:
            return "PyObject::None(py)"

    def _transpile_binary_op(self, expr: ast.BinOp) -> str:
        """Transpile a binary operation."""
        left = self.transpile_expression(expr.left)
        right = self.transpile_expression(expr.right)

        if isinstance(expr.op, ast.Add):
            return f"{left} + {right}"
        elif isinstance(expr.op, ast.Sub):
            return f"{left} - {right}"
        elif isinstance(expr.op, ast.Mult):
            return f"{left} * {right}"
        elif isinstance(expr.op, ast.Div):
            return f"{left} / {right}"
        elif isinstance(expr.op, ast.FloorDiv):
            return f"({left} / {right}).floor() as i64"
        elif isinstance(expr.op, ast.Mod):
            return f"{left} % {right}"
        elif isinstance(expr.op, ast.Pow):
            return f"({left}).powi({right} as i32)"
        elif isinstance(expr.op, ast.BitAnd):
            return f"{left} & {right}"
        elif isinstance(expr.op, ast.BitOr):
            return f"{left} | {right}"
        elif isinstance(expr.op, ast.BitXor):
            return f"{left} ^ {right}"
        elif isinstance(expr.op, ast.LShift):
            return f"{left} << {right}"
        elif isinstance(expr.op, ast.RShift):
            return f"{left} >> {right}"
        else:
            return f"{left} /* op */ {right}"

    def _transpile_unary_op(self, expr: ast.UnaryOp) -> str:
        """Transpile a unary operation."""
        operand = self.transpile_expression(expr.operand)

        if isinstance(expr.op, ast.USub):
            return f"(-{operand})"
        elif isinstance(expr.op, ast.UAdd):
            return operand
        elif isinstance(expr.op, ast.Not):
            return f"(!{operand})"
        elif isinstance(expr.op, ast.Invert):
            return f"(!{operand})"
        else:
            return operand

    def _transpile_bool_op(self, expr: ast.BoolOp) -> str:
        """Transpile a boolean operation (and/or)."""
        op = "&&" if isinstance(expr.op, ast.And) else "||"
        parts = [self.transpile_expression(v) for v in expr.values]
        return f"({' '.join([f'({p})' if ' ' in p else p for p in parts])})"

    def _transpile_compare(self, expr: ast.Compare) -> str:
        """Transpile a comparison expression."""
        left = self.transpile_expression(expr.left)
        results = []

        for op, comparator in zip(expr.ops, expr.comparators):
            right = self.transpile_expression(comparator)
            if isinstance(op, ast.Eq):
                results.append(f"{left} == {right}")
            elif isinstance(op, ast.NotEq):
                results.append(f"{left} != {right}")
            elif isinstance(op, ast.Lt):
                results.append(f"{left} < {right}")
            elif isinstance(op, ast.LtE):
                results.append(f"{left} <= {right}")
            elif isinstance(op, ast.Gt):
                results.append(f"{left} > {right}")
            elif isinstance(op, ast.GtE):
                results.append(f"{left} >= {right}")
            elif isinstance(op, ast.Is):
                results.append(f"{left}.is_some() == {right}.is_some()")
            elif isinstance(op, ast.IsNot):
                results.append(f"{left}.is_some() != {right}.is_some()")
            elif isinstance(op, ast.In):
                results.append(f"{right}.contains(&{left})")
            elif isinstance(op, ast.NotIn):
                results.append(f"!{right}.contains(&{left})")
            left = right

        if len(results) == 1:
            return results[0]
        return " && ".join(results)

    def _transpile_call(self, expr: ast.Call) -> str:
        """Transpile a function call."""
        func_name = self.transpile_expression(expr.func)
        args = [self.transpile_expression(arg) for arg in expr.args]
        args_str = ", ".join(args)

        if func_name == "len":
            if args:
                return f"({args[0]}).len() as i64"
            return "0"
        elif func_name == "range":
            if len(args) == 1:
                return f"(0..{args[0]})"
            elif len(args) == 2:
                return f"({args[0]}..{args[1]})"
            elif len(args) == 3:
                return f"({args[0]}..{args[1]}).step_by({args[2]} as usize)"
            return "(0..0)"
        elif func_name == "print":
            if args:
                return f'println!("{{:?}}", {args_str})'
            return 'println!()'
        elif func_name == "int":
            return f"({args[0]} as i64)" if args else "0"
        elif func_name == "float":
            return f"({args[0]} as f64)" if args else "0.0"
        elif func_name == "bool":
            return f"({args[0]} as bool)" if args else "false"
        elif func_name == "str":
            return f"({args[0]}).to_string()" if args else '"".to_string()'
        elif func_name == "abs":
            return f"({args[0]}).abs()" if args else "0"
        elif func_name == "min":
            if len(args) == 2:
                return f"({args[0]}).min({args[1]})"
            return f"({args[0]}).iter().min().unwrap_or(&0)"
        elif func_name == "max":
            if len(args) == 2:
                return f"({args[0]}).max({args[1]})"
            return f"({args[0]}).iter().max().unwrap_or(&0)"
        elif func_name == "sum":
            return f"({args[0]}).iter().sum::<f64>()" if args else "0.0"
        elif func_name == "enumerate":
            if args:
                return f"({args[0]}).iter().enumerate()"
            return "(0..0).enumerate()"
        elif func_name == "reversed":
            if args:
                return f"({args[0]}).iter().rev()"
            return "(0..0).rev()"
        elif func_name == "sorted":
            if args:
                return f"({args[0]}).iter().sorted().collect::<Vec<_>>()"
            return "Vec::new()"
        elif func_name == "zip":
            return f"({args_str}).into_iter()"
        elif func_name == "isinstance":
            return "true /* isinstance */"
        elif func_name == "hasattr":
            return "true /* hasattr */"
        elif func_name == "range":
            return f"(0..{args[0]})"
        elif func_name == "panic!":
            return f'panic!("{{}}", {args_str})'

        if "." in func_name:
            parts = func_name.rsplit(".", 1)
            obj = parts[0].strip("()")
            method = parts[1]
            method_map = {
                "append": "push",
                "extend": "extend",
                "insert": "insert",
                "remove": "remove",
                "index": "position",
                "count": "iter().filter(|&&x| x == {0}).count()",
                "reverse": "reverse",
                "sort": "sort",
                "clear": "clear",
                "copy": "clone",
                "pop": "pop",
                "get": "get",
                "setdefault": "entry",
                "update": "extend",
                "items": "iter",
                "keys": "keys",
                "values": "values",
                "contains": "contains",
                "startswith": "starts_with",
                "endswith": "ends_with",
                "strip": "trim",
                "replace": "replace",
                "split": "split",
                "join": "join",
                "upper": "to_uppercase",
                "lower": "to_lowercase",
                "is_numeric": "chars().all(|c| c.is_numeric())",
            }
            mapped = method_map.get(method, method)
            if args:
                args_str_call = ", ".join(args)
            else:
                args_str_call = ""
            return f"({obj}).{mapped}({args_str_call})"

        return f"{func_name}({args_str})"

    def _transpile_attribute(self, expr: ast.Attribute) -> str:
        """Transpile an attribute access."""
        obj = self.transpile_expression(expr.value)
        attr = expr.attr

        math_funcs = {
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sqrt", "cbrt", "abs", "floor", "ceil", "round",
            "log", "log2", "log10", "exp", "pow",
        }
        if attr in math_funcs:
            return f"{obj}.{attr}()"

        vec_methods = {"push", "pop", "len", "is_empty", "sort", "reverse", "clear", "clone"}
        if attr in vec_methods:
            return f"({obj}).{attr}()"

        return f"({obj}).{attr}"

    def _transpile_subscript(self, expr: ast.Subscript) -> str:
        """Transpile a subscript operation."""
        obj = self.transpile_expression(expr.value)
        key = self.transpile_expression(expr.slice)

        if isinstance(expr.slice, ast.Constant) and isinstance(expr.slice.value, int):
            return f"({obj})[{expr.slice.value} as usize]"
        elif " " in key or "+" in key or "-" in key or "*" in key or "/" in key:
            return f"({obj})[({key}) as usize]"
        else:
            return f"({obj})[{key} as usize]"

    def _transpile_list(self, expr: ast.List) -> str:
        """Transpile a list literal."""
        if not expr.elts:
            return "Vec::new()"
        elements = [self.transpile_expression(elt) for elt in expr.elts]
        elements_str = ", ".join(elements)
        return f"vec![{elements_str}]"

    def _transpile_dict(self, expr: ast.Dict) -> str:
        """Transpile a dict literal."""
        if not expr.keys:
            return "HashMap::new()"
        pairs = []
        for key, value in zip(expr.keys, expr.values):
            k = self.transpile_expression(key)
            v = self.transpile_expression(value)
            pairs.append(f"({k}, {v})")
        pairs_str = ", ".join(pairs)
        return f"vec![{pairs_str}].into_iter().collect()"

    def _transpile_tuple(self, expr: ast.Tuple) -> str:
        """Transpile a tuple literal."""
        if not expr.elts:
            return "()"
        elements = [self.transpile_expression(elt) for elt in expr.elts]
        return f"({', '.join(elements)})"

    def _transpile_if_expr(self, expr: ast.IfExp) -> str:
        """Transpile a ternary expression (x if cond else y)."""
        condition = self.transpile_expression(expr.test)
        body = self.transpile_expression(expr.body)
        orelse = self.transpile_expression(expr.orelse)
        return f"if {condition} {{ {body} }} else {{ {orelse} }}"

    def _transpile_list_comp(self, expr: ast.ListComp) -> str:
        """Transpile a list comprehension."""
        if expr.generators:
            gen = expr.generators[0]
            if isinstance(gen.target, ast.Name):
                var = gen.target.id
            else:
                var = "_"
            iter_expr = self.transpile_expression(gen.iter)
            element = self.transpile_expression(expr.elt)
            return f"({iter_expr}).iter().map(|{var}| {element}).collect::<Vec<_>>()"
        return "Vec::new()"

    def _transpile_lambda(self, expr: ast.Lambda) -> str:
        """Transpile a lambda expression."""
        args = [a.arg for a in expr.args.args]
        body = self.transpile_expression(expr.body)
        args_str = ", ".join(args)
        return f"|{args_str}| {body}"

    def _transpile_named_expr(self, expr: ast.NamedExpr) -> str:
        """Transpile a named expression (walrus operator)."""
        target = self.transpile_expression(expr.target)
        value = self.transpile_expression(expr.value)
        return f"let {target} = {value}"

    # ── Type Inference ───────────────────────────────────────────────────

    def _infer_type_from_value(self, expr: ast.expr) -> str:
        """Infer Rust type from an expression."""
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
        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                if expr.func.id in ("int", "i64"):
                    return "i64"
                elif expr.func.id in ("float", "f64"):
                    return "f64"
                elif expr.func.id == "bool":
                    return "bool"
                elif expr.func.id == "str":
                    return "String"
            return "PyObject"
        elif isinstance(expr, ast.Name):
            if expr.id in ("True", "False"):
                return "bool"
            return self.local_vars.get(expr.id, "PyObject")
        elif isinstance(expr, ast.BinOp):
            return self._infer_type_from_value(expr.left)
        return "PyObject"

    # ── Helpers ──────────────────────────────────────────────────────────

    def _generate_rust_function(self, func: RustFunction) -> str:
        """Generate complete Rust function string."""
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
        """Add indentation to a line."""
        return self.indent_str * self.indent_level + line


# ── Module-Level API ─────────────────────────────────────────────────────

def transpile_module(module_info: ModuleInfo) -> str:
    """Transpile a module to Rust code."""
    transpiler = CopperheadTranspiler()
    return transpiler.transpile_module(module_info)


def transpile_source(source: str, filename: str = "<unknown>") -> str:
    """Transpile Python source code to Rust."""
    module_info = parse_source(source, filename)
    return transpile_module(module_info)


def generate_pyproject_toml(module_name: str) -> str:
    """Generate pyproject.toml for the Rust extension module."""
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
    """Generate Cargo.toml for the Rust project."""
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
    """Generate build.py script for compilation."""
    return '''#!/usr/bin/env python3
# Build script for Copperhead compiled modules.

import subprocess
import sys
import os

def build_module(source_file: str, output_name: str):
    """Build a Copperhead module."""
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
