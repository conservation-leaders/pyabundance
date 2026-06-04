# Benchmarks

Benchmark scripts live in `benchmarks/`. Generated outputs are written to `reports/` and `data/benchmark/`, both ignored by git.

## Poisson benchmark

```bash
python benchmarks/generate_pcount_dataset.py
python benchmarks/run_py_benchmark.py
python benchmarks/run_py_loglik_benchmark.py
Rscript benchmarks/run_r_unmarked_benchmark.R || true
python benchmarks/compare_benchmarks.py
```

## Negative-binomial benchmark

```bash
python benchmarks/generate_pcount_nb_dataset.py
python benchmarks/run_py_nb_benchmark.py
python benchmarks/run_py_nb_loglik_benchmark.py
Rscript benchmarks/run_r_unmarked_nb_benchmark.R || true
python benchmarks/compare_nb_benchmarks.py
```

## Zero-inflated Poisson benchmark

```bash
python benchmarks/generate_pcount_zip_dataset.py
python benchmarks/run_py_zip_benchmark.py
python benchmarks/run_py_zip_loglik_benchmark.py
Rscript benchmarks/run_r_unmarked_zip_benchmark.R || true
python benchmarks/compare_zip_benchmarks.py
```

## Workflow benchmarks

```bash
python benchmarks/run_formula_overhead_benchmark.py
python benchmarks/run_uncertainty_benchmark.py
python benchmarks/run_reporting_workflow.py
python benchmarks/run_posterior_abundance_benchmark.py
```

## Optional R comparisons

R comparisons use `unmarked` only as a black-box validation target. If R or `unmarked` is unavailable, comparison reports should honestly say PARTIAL or NOT RUN.

## Outputs

- Generated data: `data/benchmark/`
- Generated reports: `reports/`
- Preserved local bundles: `benchmark_artifacts/`

These paths are ignored by git. CI uploads generated reports/artifacts when benchmark workflows are run.
