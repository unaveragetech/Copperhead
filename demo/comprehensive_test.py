#!/usr/bin/env python3
"""
Comprehensive Test Script for Copperhead
Tests all features: types, parser, transpiler, compiler, LLM, registry, debugger, interpreter
"""

import sys
import os
import tempfile
import time
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def print_test(name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")

def run_all_tests() -> dict:
    """Run all comprehensive tests."""
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # ============================================================
    # TEST 1: Type System
    # ============================================================
    print_header("TEST 1: Type System")
    
    try:
        import copperhead as cp
        
        # Test primitive types
        test_cases = [
            ("f32 type", cp.f32 is float),
            ("f64 type", cp.f64 is float),
            ("i8 type", cp.i8 is int),
            ("i32 type", cp.i32 is int),
            ("u64 type", cp.u64 is int),
            ("bool type", cp.bool is bool),
            ("str type", cp.str is str),
        ]
        
        for name, result in test_cases:
            results["total"] += 1
            if result:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Type system: {name}")
            print_test(name, result)
        
        # Test Vec
        vec = cp.Vec([1, 2, 3])
        results["total"] += 1
        if len(vec) == 3 and vec[0] == 1:
            results["passed"] += 1
            print_test("Vec creation and access", True)
        else:
            results["failed"] += 1
            print_test("Vec creation and access", False)
        
        # Test HashMap
        hashmap = cp.HashMap({"a": 1, "b": 2})
        results["total"] += 1
        if hashmap["a"] == 1 and hashmap.len() == 2:
            results["passed"] += 1
            print_test("HashMap creation and access", True)
        else:
            results["failed"] += 1
            print_test("HashMap creation and access", False)
        
        # Test Option
        opt = cp.Option(42)
        results["total"] += 1
        if opt.is_some() and opt.unwrap() == 42:
            results["passed"] += 1
            print_test("Option type", True)
        else:
            results["failed"] += 1
            print_test("Option type", False)
        
        # Test Result
        res = cp.Ok(42)
        results["total"] += 1
        if res.is_ok() and res.unwrap() == 42:
            results["passed"] += 1
            print_test("Result type", True)
        else:
            results["failed"] += 1
            print_test("Result type", False)
        
        # Test Math module
        import math
        results["total"] += 1
        if abs(cp.math.sin(math.pi/2) - 1.0) < 1e-10:
            results["passed"] += 1
            print_test("Math module (sin)", True)
        else:
            results["failed"] += 1
            print_test("Math module (sin)", False)
        
        # Test decorators
        @cp.compile(target="rust")
        def test_func(x: cp.f64) -> cp.f64:
            return x
        
        results["total"] += 1
        if hasattr(test_func, '_copperhead_compile'):
            results["passed"] += 1
            print_test("Decorators", True)
        else:
            results["failed"] += 1
            print_test("Decorators", False)
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Type system error: {e}")
        print_test("Type system", False, str(e))
    
    # ============================================================
    # TEST 2: Parser
    # ============================================================
    print_header("TEST 2: Parser")
    
    try:
        from copperhead.parser import parse_source, find_rpbs, is_rpb
        
        # Test basic parsing
        source = """
import copperhead as cp

@cp.compile(target="rust")
def add(x: cp.f64, y: cp.f64) -> cp.f64:
    return x + y

def normal_func(z: int) -> int:
    return z
"""
        module = parse_source(source)
        
        results["total"] += 1
        if len(module.functions) == 2:
            results["passed"] += 1
            print_test("Parse functions", True)
        else:
            results["failed"] += 1
            print_test("Parse functions", False, f"Expected 2, got {len(module.functions)}")
        
        results["total"] += 1
        if module.rpb_count == 1:
            results["passed"] += 1
            print_test("Count RPBs", True)
        else:
            results["failed"] += 1
            print_test("Count RPBs", False, f"Expected 1, got {module.rpb_count}")
        
        # Test find_rpbs
        rpbs = find_rpbs(source)
        results["total"] += 1
        if len(rpbs) == 1 and rpbs[0].name == "add":
            results["passed"] += 1
            print_test("Find RPBs", True)
        else:
            results["failed"] += 1
            print_test("Find RPBs", False)
        
        # Test is_rpb
        results["total"] += 1
        if is_rpb("@cp.compile(target='rust')\ndef func(): pass"):
            results["passed"] += 1
            print_test("is_rpb check", True)
        else:
            results["failed"] += 1
            print_test("is_rpb check", False)
        
        # Test type extraction
        results["total"] += 1
        if module.functions[0].args[0].type_info is not None:
            results["passed"] += 1
            print_test("Type extraction", True)
        else:
            results["failed"] += 1
            print_test("Type extraction", False)
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Parser error: {e}")
        print_test("Parser", False, str(e))
    
    # ============================================================
    # TEST 3: Transpiler
    # ============================================================
    print_header("TEST 3: Transpiler")
    
    try:
        from copperhead.transpiler import transpile_source, generate_cargo_toml
        
        source = """
import copperhead as cp

@cp.compile(target="rust")
def multiply(x: cp.f64, y: cp.f64) -> cp.f64:
    return x * y
"""
        rust_code = transpile_source(source)
        
        results["total"] += 1
        if "use pyo3::prelude::*;" in rust_code:
            results["passed"] += 1
            print_test("Generate PyO3 imports", True)
        else:
            results["failed"] += 1
            print_test("Generate PyO3 imports", False)
        
        results["total"] += 1
        if "#[pyfunction]" in rust_code:
            results["passed"] += 1
            print_test("Generate pyfunction", True)
        else:
            results["failed"] += 1
            print_test("Generate pyfunction", False)
        
        results["total"] += 1
        if "fn multiply(" in rust_code:
            results["passed"] += 1
            print_test("Generate function signature", True)
        else:
            results["failed"] += 1
            print_test("Generate function signature", False)
        
        # Test Cargo.toml generation
        cargo = generate_cargo_toml("test_module")
        results["total"] += 1
        if '[package]' in cargo and 'pyo3' in cargo:
            results["passed"] += 1
            print_test("Generate Cargo.toml", True)
        else:
            results["failed"] += 1
            print_test("Generate Cargo.toml", False)
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Transpiler error: {e}")
        print_test("Transpiler", False, str(e))
    
    # ============================================================
    # TEST 4: Debugger
    # ============================================================
    print_header("TEST 4: Debugger")
    
    try:
        from copperhead.debugger import CopperheadDebugger, CodeValidator
        
        debugger = CopperheadDebugger()
        validator = CodeValidator()
        
        # Test syntax checking
        valid_source = "def func(): pass"
        result = debugger.check_syntax(valid_source)
        
        results["total"] += 1
        if result.success:
            results["passed"] += 1
            print_test("Syntax check (valid)", True)
        else:
            results["failed"] += 1
            print_test("Syntax check (valid)", False)
        
        # Test syntax error detection
        invalid_source = "def func(: pass"
        result = debugger.check_syntax(invalid_source)
        
        results["total"] += 1
        if not result.success:
            results["passed"] += 1
            print_test("Syntax check (invalid)", True)
        else:
            results["failed"] += 1
            print_test("Syntax check (invalid)", False)
        
        # Test type validation
        typed_source = """
def add(x: float, y: float) -> float:
    return x + y
"""
        result = debugger.validate_types(typed_source)
        results["total"] += 1
        if result.success:
            results["passed"] += 1
            print_test("Type validation", True)
        else:
            results["failed"] += 1
            print_test("Type validation", False)
        
        # Test dry run
        safe_source = "x = 5\ny = 10\nresult = x + y"
        result = debugger.dry_run(safe_source)
        results["total"] += 1
        if result.execution_error is None:
            results["passed"] += 1
            print_test("Dry run (safe code)", True)
        else:
            results["failed"] += 1
            print_test("Dry run (safe code)", False)
        
        # Test validation
        result = validator.validate(valid_source)
        results["total"] += 1
        if result.success:
            results["passed"] += 1
            print_test("Code validation", True)
        else:
            results["failed"] += 1
            print_test("Code validation", False)
        
        # Test improvement suggestions
        suggestions = validator.suggest_improvements("def func(x, y): return x + y")
        results["total"] += 1
        if len(suggestions) > 0:
            results["passed"] += 1
            print_test("Improvement suggestions", True)
        else:
            results["failed"] += 1
            print_test("Improvement suggestions", False)
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Debugger error: {e}")
        print_test("Debugger", False, str(e))
    
    # ============================================================
    # TEST 5: Registry
    # ============================================================
    print_header("TEST 5: Registry")
    
    try:
        from copperhead.registry import ModuleRegistry, ModuleMetadata, FunctionSignature
        
        # Create test database
        db_path = os.path.join(tempfile.gettempdir(), f"test_comprehensive_{int(time.time()*1000)}.db")
        registry = ModuleRegistry(db_path)
        
        # Test registration
        metadata = ModuleMetadata(
            id="test_math",
            name="Math Utils",
            description="Mathematical utility functions",
            functions=[
                FunctionSignature(
                    name="add",
                    args=[("x", "f64"), ("y", "f64")],
                    return_type="f64",
                    description="Add two numbers"
                ),
                FunctionSignature(
                    name="multiply",
                    args=[("x", "f64"), ("y", "f64")],
                    return_type="f64",
                    description="Multiply two numbers"
                )
            ],
            tags=["math", "utilities"]
        )
        
        module_id = registry.register_module(metadata)
        results["total"] += 1
        if module_id == "test_math":
            results["passed"] += 1
            print_test("Register module", True)
        else:
            results["failed"] += 1
            print_test("Register module", False)
        
        # Test retrieval
        retrieved = registry.get_module("test_math")
        results["total"] += 1
        if retrieved is not None and retrieved.name == "Math Utils":
            results["passed"] += 1
            print_test("Get module", True)
        else:
            results["failed"] += 1
            print_test("Get module", False)
        
        # Test search
        results_list = registry.search_modules("Math")
        results["total"] += 1
        if len(results_list) >= 1:
            results["passed"] += 1
            print_test("Search modules", True)
        else:
            results["failed"] += 1
            print_test("Search modules", False)
        
        # Test function search
        func_results = registry.search_functions("add")
        results["total"] += 1
        if len(func_results) >= 1:
            results["passed"] += 1
            print_test("Search functions", True)
        else:
            results["failed"] += 1
            print_test("Search functions", False)
        
        # Test stats
        stats = registry.get_stats()
        results["total"] += 1
        if stats["total_modules"] >= 1:
            results["passed"] += 1
            print_test("Get stats", True)
        else:
            results["failed"] += 1
            print_test("Get stats", False)
        
        # Test usage update
        registry.update_usage("test_math")
        registry.update_usage("test_math")
        module = registry.get_module("test_math")
        results["total"] += 1
        if module.usage_count == 2:
            results["passed"] += 1
            print_test("Update usage", True)
        else:
            results["failed"] += 1
            print_test("Update usage", False)
        
        # Cleanup
        registry.delete_module("test_math")
        try:
            os.remove(db_path)
        except:
            pass
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Registry error: {e}")
        print_test("Registry", False, str(e))
    
    # ============================================================
    # TEST 6: Compiler
    # ============================================================
    print_header("TEST 6: Compiler")
    
    try:
        from copperhead.compiler import BuildConfig, CopperheadCompiler, CompilationStatus
        
        # Test build config
        config = BuildConfig(source_path="test.py")
        results["total"] += 1
        if config.source_path == "test.py":
            results["passed"] += 1
            print_test("BuildConfig creation", True)
        else:
            results["failed"] += 1
            print_test("BuildConfig creation", False)
        
        # Test compiler with nonexistent file
        config = BuildConfig(source_path="nonexistent.py", use_cache=False)
        compiler = CopperheadCompiler(config)
        result = compiler.compile()
        
        results["total"] += 1
        if result.status == CompilationStatus.FAILED:
            results["passed"] += 1
            print_test("Compiler (nonexistent file)", True)
        else:
            results["failed"] += 1
            print_test("Compiler (nonexistent file)", False)
        
        # Test compiler with empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            config = BuildConfig(source_path=temp_path, use_cache=False)
            compiler = CopperheadCompiler(config)
            result = compiler.compile()
            
            results["total"] += 1
            if result.status == CompilationStatus.SUCCESS:
                results["passed"] += 1
                print_test("Compiler (empty file)", True)
            else:
                results["failed"] += 1
                print_test("Compiler (empty file)", False)
        finally:
            os.unlink(temp_path)
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Compiler error: {e}")
        print_test("Compiler", False, str(e))
    
    # ============================================================
    # TEST 7: LLM Integration
    # ============================================================
    print_header("TEST 7: LLM Integration")
    
    try:
        from copperhead.llm import (
            OllamaClient, CopperheadCoder, CodeGenerator,
            GenerationStatus, GeneratedCode, GenerationResult
        )
        
        # Test OllamaClient initialization
        client = OllamaClient()
        results["total"] += 1
        if client.model == "maryasov/qwen2.5-coder-cline:latest":
            results["passed"] += 1
            print_test("OllamaClient init", True)
        else:
            results["failed"] += 1
            print_test("OllamaClient init", False)
        
        # Test availability check (may fail if Ollama not running)
        is_available = client.is_available()
        results["total"] += 1
        if isinstance(is_available, bool):
            results["passed"] += 1
            print_test("Ollama availability check", True)
        else:
            results["failed"] += 1
            print_test("Ollama availability check", False)
        
        # Test CopperheadCoder initialization
        coder = CopperheadCoder()
        results["total"] += 1
        if coder.registry is not None:
            results["passed"] += 1
            print_test("CopperheadCoder init", True)
        else:
            results["failed"] += 1
            print_test("CopperheadCoder init", False)
        
        # Test prompt building
        prompt = coder._build_prompt(
            description="Create a function to add numbers",
            existing_code=None,
            last_code=None,
            iteration=1
        )
        results["total"] += 1
        if "Create a function" in prompt:
            results["passed"] += 1
            print_test("Prompt building", True)
        else:
            results["failed"] += 1
            print_test("Prompt building", False)
        
        # Test response parsing
        response = '''
        {
            "ambiguities": [],
            "code": {
                "source": "def func(): pass",
                "tests": "def test_func(): pass",
                "explanation": "Test"
            },
            "questions": []
        }
        '''
        parsed = coder._parse_response(response)
        results["total"] += 1
        if parsed is not None and "code" in parsed:
            results["passed"] += 1
            print_test("Response parsing", True)
        else:
            results["failed"] += 1
            print_test("Response parsing", False)
        
        # Test validation
        result_dict = {
            "code": {
                "source": "def func(): pass",
                "tests": "def test_func(): pass",
                "explanation": "Test"
            }
        }
        validated = coder._validate_code(result_dict)
        results["total"] += 1
        if validated.status == GenerationStatus.SUCCESS:
            results["passed"] += 1
            print_test("Code validation", True)
        else:
            results["failed"] += 1
            print_test("Code validation", False)
        
        # Test GeneratedCode
        code = GeneratedCode(
            source_code="def func(): pass",
            tests_code="def test_func(): pass",
            description="Test"
        )
        results["total"] += 1
        if code.source_code == "def func(): pass":
            results["passed"] += 1
            print_test("GeneratedCode creation", True)
        else:
            results["failed"] += 1
            print_test("GeneratedCode creation", False)
        
        # Test GenerationResult
        gen_result = GenerationResult(success=True, code=code)
        results["total"] += 1
        if gen_result.success:
            results["passed"] += 1
            print_test("GenerationResult creation", True)
        else:
            results["failed"] += 1
            print_test("GenerationResult creation", False)
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"LLM error: {e}")
        print_test("LLM Integration", False, str(e))
    
    # ============================================================
    # TEST 8: CLI Commands
    # ============================================================
    print_header("TEST 8: CLI Commands")
    
    try:
        from copperhead.cli import main
        
        # Test help command
        sys.argv = ["copperhead", "--help"]
        try:
            main()
        except SystemExit:
            pass
        
        results["total"] += 1
        print_test("CLI help command", True)
        results["passed"] += 1
        
        # Test version command
        sys.argv = ["copperhead", "--version"]
        try:
            main()
        except SystemExit:
            pass
        
        results["total"] += 1
        print_test("CLI version command", True)
        results["passed"] += 1
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"CLI error: {e}")
        print_test("CLI Commands", False, str(e))
    
    # ============================================================
    # TEST 9: Abstract Examples
    # ============================================================
    print_header("TEST 9: Abstract Examples")
    
    try:
        # Import and test abstract examples
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "copperhead", "examples"))
        
        # Test that examples can be imported
        from copperhead.examples import abstract_examples as ae
        
        results["total"] += 1
        if hasattr(ae, 'tree_sum'):
            results["passed"] += 1
            print_test("Import abstract examples", True)
        else:
            results["failed"] += 1
            print_test("Import abstract examples", False)
        
        # Test matrix operations
        results["total"] += 1
        try:
            a = [[1.0, 2.0], [3.0, 4.0]]
            b = [[5.0, 6.0], [7.0, 8.0]]
            result = ae.matrix_multiply(a, b)
            expected = [[19.0, 22.0], [43.0, 50.0]]
            if result == expected:
                results["passed"] += 1
                print_test("Matrix multiplication", True)
            else:
                results["failed"] += 1
                print_test("Matrix multiplication", False, f"Got {result}")
        except Exception as e:
            results["failed"] += 1
            print_test("Matrix multiplication", False, str(e))
        
        # Test error handling
        results["total"] += 1
        try:
            result = ae.safe_divide(10.0, 2.0)
            if result.is_ok() and result.unwrap() == 5.0:
                results["passed"] += 1
                print_test("Safe divide", True)
            else:
                results["failed"] += 1
                print_test("Safe divide", False)
        except Exception as e:
            results["failed"] += 1
            print_test("Safe divide", False, str(e))
        
        # Test divide by zero
        results["total"] += 1
        try:
            result = ae.safe_divide(10.0, 0.0)
            if result.is_err():
                results["passed"] += 1
                print_test("Safe divide by zero", True)
            else:
                results["failed"] += 1
                print_test("Safe divide by zero", False)
        except Exception as e:
            results["failed"] += 1
            print_test("Safe divide by zero", False, str(e))
        
        # Test quicksort
        results["total"] += 1
        try:
            import random
            arr = [random.random() * 100 for _ in range(10)]
            sorted_arr = ae.quicksort(arr)
            if sorted_arr == sorted(arr):
                results["passed"] += 1
                print_test("Quicksort", True)
            else:
                results["failed"] += 1
                print_test("Quicksort", False)
        except Exception as e:
            results["failed"] += 1
            print_test("Quicksort", False, str(e))
        
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Abstract examples error: {e}")
        print_test("Abstract Examples", False, str(e))
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print_header("TEST SUMMARY")
    
    print(f"\n  Total Tests: {results['total']}")
    print(f"  \033[92mPassed: {results['passed']}\033[0m")
    print(f"  \033[91mFailed: {results['failed']}\033[0m")
    
    if results['errors']:
        print(f"\n  Errors:")
        for error in results['errors']:
            print(f"    - {error}")
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\n  Success Rate: {success_rate:.1f}%")
    
    if results['failed'] == 0:
        print("\n  ALL TESTS PASSED!")
    else:
        print(f"\n  {results['failed']} TEST(S) FAILED")
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    sys.exit(0 if results['failed'] == 0 else 1)
