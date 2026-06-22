"""
Export the Copperhead registry database to a rich CSV catalog.

Outputs every module with full metadata: name, description, category,
difficulty, function signatures, tags, status, source code, etc.

Output: benchmarks/results/module_catalog.csv
"""

import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copperhead.registry import ModuleRegistry, ModuleStatus

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BENCHMARK_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

STATUS_MAP = {
    ModuleStatus.DRAFT: "Draft",
    ModuleStatus.COMPILED: "Compiled",
    ModuleStatus.FAILED: "Failed",
    ModuleStatus.DEPRECATED: "Deprecated",
}


def export_catalog():
    """Export all modules to CSV."""
    registry = ModuleRegistry()
    modules = registry.get_all_modules()
    
    csv_path = os.path.join(RESULTS_DIR, "module_catalog.csv")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "module_id",
            "module_name",
            "version",
            "author",
            "status",
            "category",
            "difficulty",
            "description",
            "function_name",
            "function_args",
            "return_type",
            "function_description",
            "is_rpb",
            "no_gil",
            "examples",
            "tags",
            "dependencies",
            "usage_count",
            "rating",
            "created_at",
            "source_code",
            "has_rust_code",
            "has_tests",
        ])
        
        categories = ["math", "statistics", "sort", "search", "string",
                       "linear-algebra", "distance", "data-processing",
                       "number-theory"]
        difficulties = ["basic", "intermediate", "advanced"]
        
        for mod in modules:
            # Extract category and difficulty from tags
            category = "other"
            difficulty = "basic"
            for tag in mod.tags:
                if tag in categories:
                    category = tag
                if tag in difficulties:
                    difficulty = tag
            
            # Get primary function (first one)
            func = mod.functions[0] if mod.functions else None
            
            writer.writerow([
                mod.id,
                mod.name,
                mod.version,
                mod.author,
                STATUS_MAP.get(mod.status, "Unknown"),
                category,
                difficulty,
                mod.description,
                func.name if func else "",
                "; ".join(f"{name}: {typ}" for name, typ in func.args) if func else "",
                func.return_type if func else "",
                func.description if func else "",
                "Yes" if (func and func.is_rpb) else "No",
                "Yes" if (func and func.no_gil) else "No",
                " | ".join(func.examples) if func else "",
                ";".join(mod.tags),
                ";".join(mod.dependencies),
                mod.usage_count,
                f"{mod.rating:.1f}" if mod.rating else "0.0",
                f"{mod.created_at:.0f}" if mod.created_at else "",
                mod.rust_code or "",
                "Yes" if mod.rust_code else "No",
                "Yes" if mod.tests_code else "No",
            ])
    
    return csv_path, len(modules)


def print_summary(csv_path, count):
    """Print a summary of the catalog."""
    print(f"\n{'=' * 70}")
    print("Copperhead Module Catalog")
    print(f"{'=' * 70}")
    print(f"Total modules: {count}")
    print(f"CSV file: {csv_path}")
    print()
    
    # Read back and print summary
    registry = ModuleRegistry()
    modules = registry.get_all_modules()
    
    # Group by category
    categories = {}
    for mod in modules:
        cat = "other"
        for tag in mod.tags:
            if tag in ("math", "statistics", "sort", "search", "string",
                       "linear-algebra", "distance", "data-processing",
                       "number-theory"):
                cat = tag
                break
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(mod)
    
    print(f"{'Category':<20s} {'Count':>5s}  Modules")
    print("-" * 70)
    for cat in sorted(categories.keys()):
        mods = categories[cat]
        names = ", ".join(m.name for m in mods)
        print(f"{cat:<20s} {len(mods):>5d}  {names}")
    
    print(f"\n{'=' * 70}")
    print(f"Full catalog: {csv_path}")
    
    # Print stats
    stats = registry.get_stats()
    print(f"\nRegistry Statistics:")
    print(f"  Total modules:   {stats['total_modules']}")
    print(f"  Total functions: {stats['total_functions']}")
    print(f"  Total usage:     {stats['total_usage']}")


def main():
    csv_path, count = export_catalog()
    print_summary(csv_path, count)


if __name__ == "__main__":
    main()
