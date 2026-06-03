# Benchmarks

Run from the repository root after installing the local package:

```bash
python benchmarks/generate_pcount_dataset.py
python benchmarks/run_py_benchmark.py
Rscript benchmarks/run_r_unmarked_benchmark.R || true
python benchmarks/compare_benchmarks.py
```

The R benchmark is optional and writes a `not_run` JSON file when R or `unmarked` is unavailable.
