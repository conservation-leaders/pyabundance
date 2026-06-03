# Third Party Notices

pyabundance depends on open-source Python and Rust packages listed in `pyproject.toml` and crate manifests. The implementation is clean-room and does not copy or translate GPL source code.

Python runtime dependencies include:

- NumPy for array handling.
- SciPy for numerical optimization.
- pandas for DataFrame workflows.
- Formulaic for fixed-effect formula parsing and design-matrix construction in the v0.4 DataFrame API.

The Rust core directly depends on `libm` for portable log-gamma evaluation used by the negative-binomial PMF.
