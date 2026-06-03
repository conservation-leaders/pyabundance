# TestPyPI Rehearsal

pyabundance uses PyPI Trusted Publishing for TestPyPI rehearsal releases. Do not store TestPyPI API tokens in the repository.

## 1. Configure TestPyPI Trusted Publisher

In TestPyPI, create or select the `pyabundance` project and add a Trusted Publisher for this repository:

- owner: repository owner or organization
- repository: `pyabundance`
- workflow filename: `publish-testpypi.yml`
- environment: leave blank unless maintainers add one later

The workflow needs GitHub `id-token: write` permission and TestPyPI must trust the exact workflow filename.

## 2. Run workflow_dispatch

Open GitHub Actions, choose **Publish to TestPyPI**, and run the workflow manually. It builds wheels and an sdist, runs `twine check`, uploads the `dist/` artifact, then publishes to TestPyPI through Trusted Publishing.

## 3. Inspect artifacts

Download the `testpypi-dist` artifact and verify it contains:

- one or more `.whl` files;
- one `.tar.gz` source distribution;
- filenames matching the intended version.

## 4. Install from TestPyPI

Use PyPI as the dependency fallback because TestPyPI usually does not mirror dependencies:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pyabundance==1.0.0rc1
```

## 5. Run smoke tests

```bash
python scripts/smoke_test_installed.py --expected-version 1.0.0rc1
```

The smoke test imports pyabundance, loads a bundled example dataset, fits a tiny Poisson `pcount_df` model, computes posterior abundance, and runs a small model comparison.

## 6. If project name/version already exists

Package versions cannot be overwritten on TestPyPI. If `1.0.0rc1` already exists, bump to a development or post release such as `1.0.0rc1.post1` or `1.0.0rc2`, rebuild, and rerun the workflow.

## 7. Clean up or bump dev versions

After a successful rehearsal, decide whether to keep the exact version for the alpha tag or bump the development tree to the next planned version. Do not delete release evidence from `reports/` or `benchmark_artifacts/`.
