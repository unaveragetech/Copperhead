"""
Tests for Copperhead module registry.
"""

import pytest
import sys
import os
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copperhead.registry import (
    ModuleRegistry, ModuleMetadata, FunctionSignature,
    ModuleStatus, get_registry
)


class TestModuleRegistry:
    """Test ModuleRegistry class."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            assert os.path.exists(db_path)
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_register_module(self):
        """Test module registration."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            metadata = ModuleMetadata(
                id="test_module",
                name="Test Module",
                description="A test module",
                functions=[
                    FunctionSignature(
                        name="add",
                        args=[("x", "f64"), ("y", "f64")],
                        return_type="f64",
                        description="Add two numbers"
                    )
                ]
            )
            
            module_id = registry.register_module(metadata)
            assert module_id == "test_module"
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_get_module(self):
        """Test getting a module."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            metadata = ModuleMetadata(
                id="test_module",
                name="Test Module",
                description="A test module"
            )
            
            registry.register_module(metadata)
            retrieved = registry.get_module("test_module")
            
            assert retrieved is not None
            assert retrieved.name == "Test Module"
            assert retrieved.description == "A test module"
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_get_nonexistent_module(self):
        """Test getting a nonexistent module."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            retrieved = registry.get_module("nonexistent")
            assert retrieved is None
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_search_modules(self):
        """Test searching modules."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            # Register some modules
            for i in range(5):
                metadata = ModuleMetadata(
                    id=f"module_{i}",
                    name=f"Module {i}",
                    description=f"Module number {i}"
                )
                registry.register_module(metadata)
            
            # Search
            results = registry.search_modules("Module", limit=3)
            assert len(results) <= 3
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_search_functions(self):
        """Test searching functions."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            metadata = ModuleMetadata(
                id="math_module",
                name="Math Module",
                description="Math functions",
                functions=[
                    FunctionSignature(
                        name="add",
                        args=[("x", "f64"), ("y", "f64")],
                        return_type="f64"
                    ),
                    FunctionSignature(
                        name="multiply",
                        args=[("x", "f64"), ("y", "f64")],
                        return_type="f64"
                    )
                ]
            )
            
            registry.register_module(metadata)
            
            results = registry.search_functions("add")
            assert len(results) >= 1
            assert results[0][1].name == "add"
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_delete_module(self):
        """Test deleting a module."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            metadata = ModuleMetadata(
                id="to_delete",
                name="Delete Me",
                description="Will be deleted"
            )
            
            registry.register_module(metadata)
            assert registry.get_module("to_delete") is not None
            
            result = registry.delete_module("to_delete")
            assert result is True
            assert registry.get_module("to_delete") is None
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_update_usage(self):
        """Test updating usage count."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            metadata = ModuleMetadata(
                id="used_module",
                name="Used Module",
                description="Used module"
            )
            
            registry.register_module(metadata)
            
            # Update usage
            for _ in range(5):
                registry.update_usage("used_module")
            
            module = registry.get_module("used_module")
            assert module.usage_count == 5
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
    
    def test_get_stats(self):
        """Test getting statistics."""
        db_path = os.path.join(tempfile.gettempdir(), f"test_registry_{int(time.time()*1000)}.db")
        try:
            registry = ModuleRegistry(db_path)
            
            # Add some modules
            for i in range(3):
                metadata = ModuleMetadata(
                    id=f"module_{i}",
                    name=f"Module {i}",
                    description=f"Module {i}"
                )
                registry.register_module(metadata)
            
            stats = registry.get_stats()
            assert stats["total_modules"] == 3
            assert stats["total_functions"] == 0
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass


class TestModuleMetadata:
    """Test ModuleMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test metadata creation."""
        metadata = ModuleMetadata(
            id="test",
            name="Test",
            description="Test module"
        )
        assert metadata.id == "test"
        assert metadata.name == "Test"
        assert metadata.version == "1.0.0"
        assert metadata.status == ModuleStatus.DRAFT
    
    def test_metadata_with_functions(self):
        """Test metadata with functions."""
        func = FunctionSignature(
            name="add",
            args=[("x", "f64")],
            return_type="f64"
        )
        metadata = ModuleMetadata(
            id="test",
            name="Test",
            description="Test",
            functions=[func]
        )
        assert len(metadata.functions) == 1
        assert metadata.functions[0].name == "add"


class TestModuleStatus:
    """Test ModuleStatus enum."""
    
    def test_status_values(self):
        """Test status enum values."""
        assert ModuleStatus.DRAFT.value == 1
        assert ModuleStatus.COMPILED.value == 2
        assert ModuleStatus.FAILED.value == 3
        assert ModuleStatus.DEPRECATED.value == 4


class TestGlobalRegistry:
    """Test global registry singleton."""
    
    def test_get_registry(self):
        """Test getting global registry."""
        registry = get_registry()
        assert registry is not None
        assert isinstance(registry, ModuleRegistry)
    
    def test_registry_singleton(self):
        """Test that get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
