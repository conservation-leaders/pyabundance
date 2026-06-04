# Cleanup inventory

Status: COMPLETED

Commands run:

```bash
git status --short
git ls-files > reports_tracked_files_before_cleanup.txt
find . -maxdepth 3 -type f | sort > reports_all_files_before_cleanup.txt
du -sh . || true
du -sh benchmark_artifacts reports dist target .venv .pytest_cache .ruff_cache .mypy_cache htmlcov 2>/dev/null || true
git ls-files reports benchmark_artifacts data/benchmark dist coverage.xml htmlcov target 2>/dev/null || true
```

Counts:
- tracked files before cleanup: 364
- files found by `find . -maxdepth 3 -type f`: 442
- working tree size: 1.2G
- `benchmark_artifacts/`: 548K
- `reports/`: 220K
- `dist/`: 380K
- `target/`: 741M
- `.venv/`: 507M

Tracked generated files found:
- `reports/`: 51 tracked files
- `benchmark_artifacts/`: 123 tracked files
- `data/benchmark/`: 10 tracked files
- `dist/`: 2 tracked files
- `coverage.xml`: tracked
- `htmlcov/`: not tracked
- `target/`: not tracked

Top tracked directories before cleanup:
- `benchmark_artifacts`: 123
- `reports`: 51
- `tests`: 48
- `docs`: 28
- `benchmarks`: 26
- `crates`: 15
- `python`: 14
- `.github`: 12
- `data`: 10

Recommended actions:
- untrack generated `reports/*`, preserving only `reports/README.md`;
- untrack `benchmark_artifacts/` and upload benchmark bundles from CI instead;
- untrack generated benchmark data in `data/benchmark/`;
- untrack `dist/` and build artifacts;
- untrack `coverage.xml` and keep it generated locally/CI only;
- keep source code, tests, docs, scripts, benchmark generators, workflows, and clean-room documentation tracked;
- add a repo hygiene check to prevent generated artifacts from being tracked again.
