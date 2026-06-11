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

Open GitHub Actions, choose **Publish to TestPyPI**, and run the workflow manually. It builds PyPI-compatible Linux/macOS/Windows wheels and an sdist, runs `twine check`, uploads the `dist/` artifact, then publishes to TestPyPI through Trusted Publishing. The workflow uses `maturin build`; it does not use `maturin develop`.

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
  pyabundance==1.0.0rc2
```

## 5. Run smoke tests

```bash
python scripts/smoke_test_installed.py --expected-version 1.0.0rc2
```

The smoke test imports pyabundance, loads a bundled example dataset, fits a tiny Poisson `pcount_df` model, computes posterior abundance, and runs a small model comparison.

## 6. If project name/version already exists

Package versions cannot be overwritten on TestPyPI. If `1.0.0rc2` already exists, bump to a development or post release such as `1.0.0rc2.post1` or `1.0.0rc2`, rebuild, and rerun the workflow.

## 7. Clean up or bump dev versions

After a successful rehearsal, decide whether to keep the exact version for the alpha tag or bump the development tree to the next planned version. Do not commit generated release evidence from `reports/` or `benchmark_artifacts/`; keep generated artifacts in GitHub Actions artifacts or release assets.

## Wheel matrix platforms

pyabundance includes a Rust/PyO3 native extension, so wheels are platform-specific. Release-candidate wheels must be built and smoke-tested for:

- Linux x86_64
- macOS x86_64
- macOS arm64
- Windows x86_64

The package may have been developed on macOS, but Linux and Windows users need platform-specific wheels. Without Linux/Windows wheels, pip may fall back to source builds requiring Rust and native build tooling.

Current runner labels:

- Linux x86_64: `ubuntu-latest`
- macOS x86_64: `macos-15-intel`
- macOS arm64: `macos-15`
- Windows x86_64: `windows-latest`

Do not use `macos-13`.


## Trusted Publishing debug claims for rc1

The rc1 publish workflow builds all artifacts successfully, but TestPyPI currently rejects the publish token until a maintainer configures the matching Trusted Publisher. The failed main-branch run reported these GitHub OIDC claims:

- `sub`: `repo:conservation-leaders/pyabundance:ref:refs/heads/main`
- `repository`: `conservation-leaders/pyabundance`
- `workflow_ref`: `conservation-leaders/pyabundance/.github/workflows/publish-testpypi.yml@refs/heads/main`
- `ref`: `refs/heads/main`
- `environment`: `MISSING`

Configure TestPyPI to trust repository `conservation-leaders/pyabundance` and workflow file `publish-testpypi.yml`. Leave the environment blank unless the workflow is changed to use a named GitHub environment.
