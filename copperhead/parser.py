"""
Copperhead AST Parser and Semantic Enrichment

This module provides functionality to parse Python source code and identify
Rich Python Blocks (RPBs) for compilation to Rust.
"""

import ast
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum, auto


class TypeKind(Enum):
    """Types of Rust-compatible types."""
    PRIMITIVE = auto()
    COLLECTION = auto()
    OWNERSHIP = auto()
    CUSTOM = auto()
    DYNAMIC = auto()


@dataclass
class TypeInfo:
    """Information about a type."""
    name: str
    kind: TypeKind
    rust_type: str
    python_type: Optional[type] = None
    is_mutable: bool = False
    is_reference: bool = False


@dataclass
class VariableInfo:
    """Information about a variable."""
    name: str
    type_info: Optional[TypeInfo]
    is_mutable: bool = False
    is_reference: bool = False
    line: int = 0
    col: int = 0


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    args: List[VariableInfo]
    return_type: Optional[TypeInfo]
    is_rpb: bool = False
    no_gil: bool = False
    line: int = 0
    col: int = 0
    body: Optional[List[Any]] = None  # AST statement list


@dataclass
class ModuleInfo:
    """Information about a module."""
    path: str
    functions: List[FunctionInfo]
    imports: List[str]
    rpb_count: int = 0


# Type mappings from Python to Rust
TYPE_MAPPINGS: Dict[str, TypeInfo] = {
    # Primitive types
    "f32": TypeInfo("f32", TypeKind.PRIMITIVE, "f32", float),
    "f64": TypeInfo("f64", TypeKind.PRIMITIVE, "f64", float),
    "i8": TypeInfo("i8", TypeKind.PRIMITIVE, "i8", int),
    "i16": TypeInfo("i16", TypeKind.PRIMITIVE, "i16", int),
    "i32": TypeInfo("i32", TypeKind.PRIMITIVE, "i32", int),
    "i64": TypeInfo("i64", TypeKind.PRIMITIVE, "i64", int),
    "u8": TypeInfo("u8", TypeKind.PRIMITIVE, "u8", int),
    "u16": TypeInfo("u16", TypeKind.PRIMITIVE, "u16", int),
    "u32": TypeInfo("u32", TypeKind.PRIMITIVE, "u32", int),
    "u64": TypeInfo("u64", TypeKind.PRIMITIVE, "u64", int),
    "usize": TypeInfo("usize", TypeKind.PRIMITIVE, "usize", int),
    "isize": TypeInfo("isize", TypeKind.PRIMITIVE, "isize", int),
    "bool": TypeInfo("bool", TypeKind.PRIMITIVE, "bool", bool),
    "str": TypeInfo("str", TypeKind.PRIMITIVE, "String", str),
    "bytes": TypeInfo("bytes", TypeKind.PRIMITIVE, "Vec<u8>", bytes),
    "char": TypeInfo("char", TypeKind.PRIMITIVE, "char", str),
    
    # Collection types
    "list": TypeInfo("list", TypeKind.COLLECTION, "Vec<Box<dyn PyObject>>", list),
    "dict": TypeInfo("dict", TypeKind.COLLECTION, "HashMap<Box<dyn PyObject>, Box<dyn PyObject>>", dict),
    "set": TypeInfo("set", TypeKind.COLLECTION, "HashSet<Box<dyn PyObject>>", set),
    "tuple": TypeInfo("tuple", TypeKind.COLLECTION, "Vec<Box<dyn PyObject>>", tuple),
    
    # Optional/Result types
    "Option": TypeInfo("Option", TypeKind.CUSTOM, "Option<Box<dyn PyObject>>"),
    "Result": TypeInfo("Result", TypeKind.CUSTOM, "Result<Box<dyn PyObject>, Box<dyn PyObject>>"),
}

# Collection type patterns
COLLECTION_PATTERNS = {
    r"list\[([^\]]+)\]": "Vec<{0}>",
    r"dict\[([^\]]+)\]": "HashMap<{0}>",
    r"set\[([^\]]+)\]": "HashSet<{0}>",
    r"tuple\[([^\]]+)\]": "({0})",
    r"Option\[([^\]]+)\]": "Option<{0}>",
    r"Result\[([^\]]+)\]": "Result<{0}>",
}


class CopperheadParser(ast.NodeVisitor):
    """Parser for Copperhead Rich Python Blocks."""
    
    def __init__(self, source: str = "", filename: str = "<unknown>"):
        self.source = source
        self.filename = filename
        self.functions: List[FunctionInfo] = []
        self.variables: Dict[str, VariableInfo] = {}
        self.imports: List[str] = []
        self.current_function: Optional[FunctionInfo] = None
        self.scope_depth: int = 0
    
    def parse(self, source: str) -> ModuleInfo:
        """Parse Python source code and extract module information."""
        self.source = source
        tree = ast.parse(source)
        self.visit(tree)
        
        rpb_count = sum(1 for f in self.functions if f.is_rpb)
        
        return ModuleInfo(
            path=self.filename,
            functions=self.functions,
            imports=self.imports,
            rpb_count=rpb_count
        )
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statements."""
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        args = self._parse_function_args(node.args)
        return_type = self._parse_type_annotation(node.returns)
        
        # Check if function is marked as RPB
        is_rpb = self._is_rpb(node)
        no_gil = self._has_no_gil_decorator(node)
        
        func_info = FunctionInfo(
            name=node.name,
            args=args,
            return_type=return_type,
            is_rpb=is_rpb,
            no_gil=no_gil,
            line=node.lineno,
            col=node.col_offset,
            body=node.body
        )
        
        self.functions.append(func_info)
        self.current_function = func_info
        self.scope_depth += 1
        
        self.generic_visit(node)
        
        self.scope_depth -= 1
        if self.scope_depth == 0:
            self.current_function = None
    
    def _is_rpb(self, node: ast.FunctionDef) -> bool:
        """Check if function is a Rich Python Block."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "compile":
                        return True
                elif isinstance(decorator.func, ast.Name):
                    if decorator.func.id == "compile":
                        return True
        return False
    
    def _has_no_gil_decorator(self, node: ast.FunctionDef) -> bool:
        """Check if function has no_gil decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == "no_gil":
                    return True
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == "no_gil":
                    return True
        return False
    
    def _parse_function_args(self, args: ast.arguments) -> List[VariableInfo]:
        """Parse function arguments."""
        result = []
        
        # Parse regular arguments
        for arg in args.args:
            type_info = self._parse_type_annotation(arg.annotation)
            var_info = VariableInfo(
                name=arg.arg,
                type_info=type_info,
                is_mutable=self._is_mutable_type(arg.annotation),
                is_reference=self._is_reference_type(arg.annotation),
                line=arg.lineno,
                col=arg.col_offset
            )
            result.append(var_info)
        
        return result
    
    def _parse_type_annotation(self, annotation: Optional[ast.expr]) -> Optional[TypeInfo]:
        """Parse type annotation."""
        if annotation is None:
            return None
        
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            if type_name in TYPE_MAPPINGS:
                return TYPE_MAPPINGS[type_name]
            return TypeInfo(type_name, TypeKind.CUSTOM, type_name)
        
        elif isinstance(annotation, ast.Subscript):
            return self._parse_generic_type(annotation)
        
        elif isinstance(annotation, ast.Attribute):
            # Handle module.type annotations like cp.f64
            if isinstance(annotation.value, ast.Name):
                if annotation.value.id in ("cp", "copperhead"):
                    type_name = annotation.attr
                    if type_name in TYPE_MAPPINGS:
                        return TYPE_MAPPINGS[type_name]
                    return TypeInfo(type_name, TypeKind.CUSTOM, type_name)
        
        return None
    
    def _parse_generic_type(self, node: ast.Subscript) -> Optional[TypeInfo]:
        """Parse generic type like list[f64]."""
        if isinstance(node.value, ast.Name):
            base_type = node.value.id
            
            # Parse inner type
            inner_type = self._parse_type_annotation(node.slice)
            inner_rust = inner_type.rust_type if inner_type else "PyObject"
            
            # Build Rust type string
            if base_type == "list":
                rust_type = f"Vec<{inner_rust}>"
            elif base_type == "dict":
                # For dict, we need key and value types
                if isinstance(node.slice, ast.Tuple):
                    key_type = self._parse_type_annotation(node.slice.elts[0])
                    val_type = self._parse_type_annotation(node.slice.elts[1])
                    key_rust = key_type.rust_type if key_type else "PyObject"
                    val_rust = val_type.rust_type if val_type else "PyObject"
                    rust_type = f"HashMap<{key_rust}, {val_rust}>"
                else:
                    rust_type = f"HashMap<{inner_rust}, PyObject>"
            elif base_type == "set":
                rust_type = f"HashSet<{inner_rust}>"
            elif base_type == "tuple":
                if isinstance(node.slice, ast.Tuple):
                    types = []
                    for elt in node.slice.elts:
                        t = self._parse_type_annotation(elt)
                        types.append(t.rust_type if t else "PyObject")
                    rust_type = f"({', '.join(types)})"
                else:
                    rust_type = f"({inner_rust},)"
            elif base_type == "Option":
                rust_type = f"Option<{inner_rust}>"
            elif base_type == "Result":
                rust_type = f"Result<{inner_rust}, PyErr>"
            else:
                rust_type = f"{base_type}<{inner_rust}>"
            
            return TypeInfo(
                name=base_type,
                kind=TypeKind.COLLECTION,
                rust_type=rust_type
            )
        
        return None
    
    def _is_mutable_type(self, annotation: Optional[ast.expr]) -> bool:
        """Check if type annotation indicates mutable reference."""
        if annotation is None:
            return False
        
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                if annotation.value.id == "mut":
                    return True
            elif isinstance(annotation.value, ast.Attribute):
                if annotation.value.attr == "mut":
                    return True
        
        return False
    
    def _is_reference_type(self, annotation: Optional[ast.expr]) -> bool:
        """Check if type annotation indicates reference."""
        if annotation is None:
            return False
        
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                if annotation.value.id == "ref":
                    return True
            elif isinstance(annotation.value, ast.Attribute):
                if annotation.value.attr == "ref":
                    return True
        
        return False


def parse_source(source: str, filename: str = "<unknown>") -> ModuleInfo:
    """Parse Python source code and return module information."""
    parser = CopperheadParser(source, filename)
    return parser.parse(source)


def parse_file(filepath: str) -> ModuleInfo:
    """Parse a Python file and return module information."""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return parse_source(source, filepath)


def find_rpbs(source: str) -> List[FunctionInfo]:
    """Find all Rich Python Blocks in source code."""
    module = parse_source(source)
    return [f for f in module.functions if f.is_rpb]


def is_rpb(function_source: str) -> bool:
    """Check if a function source code is a Rich Python Block."""
    try:
        tree = ast.parse(function_source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                parser = CopperheadParser()
                return parser._is_rpb(node)
    except SyntaxError:
        pass
    return False


def extract_type_info(source: str) -> Dict[str, TypeInfo]:
    """Extract all type information from source code."""
    module = parse_source(source)
    type_info = {}
    
    for func in module.functions:
        for arg in func.args:
            if arg.type_info:
                type_info[arg.name] = arg.type_info
        
        if func.return_type:
            type_info[f"{func.name}_return"] = func.return_type
    
    return type_info
