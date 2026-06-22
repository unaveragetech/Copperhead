# Copperhead Benchmarks

True head-to-head performance comparisons: **Python vs Rust-compiled Copperhead**.

## Quick Results

| Metric | Value |
|--------|-------|
| Modules benchmarked | 40 |
| Average speedup | 6.6x |
| Max speedup | 38.5x (mandelbrot) |
| Top speedup (sorting) | 13.3x (bubble_sort) |
| Top speedup (data processing) | 23.9x (convolve_1d) |
| Top speedup (math) | 28.2x (is_prime) |

## How It Works

1. **Registry**: 40 vetted modules stored in SQLite with source code, tags, categories
2. **Python benchmark**: Each module's pure Python equivalent is timed over 1000 iterations
3. **Rust compilation**: All 40 Copperhead functions are transpiled to Rust and compiled into a single `.dll` via Cargo
4. **Rust benchmark**: The compiled `.dll` is loaded as a Python module and each function is timed over 1000 iterations
5. **CSV output**: Results saved to `results/benchmark_results.csv` with full metadata

## Files

```
benchmarks/
├── expand_registry.py       # Populates registry with 40 vetted modules
├── benchmark_runner.py       # Runs Python vs Rust benchmarks, outputs CSV
├── export_catalog.py         # Exports registry DB to CSV catalog
├── results/
│   ├── benchmark_results.csv # Head-to-head timing results (Python vs Rust)
│   └── module_catalog.csv    # Full registry catalog with rich metadata
└── build/                    # Cargo build artifacts (gitignored)
```

## Running the Benchmarks

```bash
# 1. Populate the registry with 40 modules
python benchmarks/expand_registry.py

# 2. Export the catalog to CSV
python benchmarks/export_catalog.py

# 3. Run the full benchmark suite (takes ~2 minutes for compilation)
python benchmarks/benchmark_runner.py
```

## Module Categories

| Category | Count | Modules |
|----------|-------|---------|
| math | 11 | sum, max, clamp, average, fibonacci, prime_check, gcd, factorial, prime_sieve, sqrt_newton, mandelbrot |
| statistics | 6 | variance, stddev, median, moving_average, pearson_correlation, linear_regression |
| sort | 4 | bubble_sort, quick_sort, merge_sort, insertion_sort |
| search | 3 | count_occurrences, linear_search, binary_search |
| string | 4 | levenshtein, reverse_string, count_words, is_palindrome |
| linear-algebra | 5 | dot_product, vector_add, vector_scale, matrix_multiply, matrix_transpose |
| distance | 3 | euclidean, manhattan, cosine_similarity |
| data-processing | 4 | histogram, normalize, convolve_1d, zscore |

## Sample Results

### Top 10 Speedups

| Module | Python (us) | Rust (us) | Speedup |
|--------|------------|-----------|---------|
| misc_mandelbrot | 127.47 | 3.31 | 38.5x |
| adv_prime_check | 48.50 | 1.72 | 28.2x |
| dp_convolve | 934.31 | 39.14 | 23.9x |
| dp_histogram | 249.05 | 14.89 | 16.7x |
| adv_bubblesort | 337.90 | 25.44 | 13.3x |
| adv_insertion_sort | 136.62 | 10.36 | 13.2x |
| dist_cosine | 198.23 | 17.44 | 11.4x |
| dp_zscore | 262.33 | 26.02 | 10.1x |
| stat_stddev | 116.39 | 12.64 | 9.2x |
| dist_levenshtein | 14.01 | 1.52 | 9.2x |

### Cases Where Rust is Slower

For very small operations (clamp, gcd, binary_search), the PyO3 FFI call overhead exceeds the computation time. These functions are so fast in Python that the Rust FFI boundary adds latency.

## Methodology

- **Iterations**: 1000 per function (with 50 warmup iterations)
- **Timing**: `time.perf_counter()` for Python, same for Rust (called through PyO3)
- **Input sizes**: 100-10000 elements depending on function complexity
- **Compilation**: Rust release mode (`cargo build --release`) with PyO3 0.23
- **Environment**: Python 3.13.3, Rust 1.89.0, Windows 11